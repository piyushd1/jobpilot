"""Temporal Workflow definition for JobPilot campaigns."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from src.orchestration.activities import execute_agent_activity
    from src.orchestration.dag import TaskDAG
    from src.orchestration.planner import build_campaign_dag
    from src.orchestration.shared_context import SharedContext


@workflow.defn
class JobPilotWorkflow:
    """Main campaign workflow — the Manager Agent runs here.

    Executes the TaskDAG by dispatching ready tasks as Temporal activities,
    monitoring progress, and handling approval gates.
    """

    def __init__(self) -> None:
        self._context = SharedContext()
        self._dag: TaskDAG | None = None
        self._approved = False
        self._approval_decision: str | None = None

    @workflow.signal
    async def user_approval(self, decision: str) -> None:
        """Signal handler for user approval gate."""
        self._approval_decision = decision
        self._approved = True

    @workflow.query
    def get_status(self) -> dict[str, Any]:
        """Query handler returning current workflow state."""
        return {
            "campaign_id": self._context.campaign_id,
            "phase": self._context.current_phase,
            "total_tokens": self._context.total_tokens_used,
            "errors": self._context.errors,
            "tasks": [
                {"id": t.task_id, "status": t.status, "type": t.task_type}
                for t in (self._dag.tasks if self._dag else [])
            ],
        }

    @workflow.run
    async def run(self, campaign_config: dict[str, Any]) -> dict[str, Any]:
        """Execute the campaign DAG."""
        self._context.campaign_id = campaign_config.get("campaign_id", "")
        self._context.user_id = campaign_config.get("user_id", "")
        self._context.resume_id = campaign_config.get("resume_id", "")

        # Build DAG
        platforms = campaign_config.get("platforms", ["manual_input"])
        self._dag = build_campaign_dag(self._context.campaign_id, platforms)
        self._context.current_phase = "executing"

        retry_policy = RetryPolicy(
            maximum_attempts=3,
            backoff_coefficient=2.0,
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
        )

        # Execute DAG loop
        while not self._dag.all_terminal():
            ready_tasks = self._dag.get_ready_tasks()

            if not ready_tasks:
                if self._dag.has_failed():
                    break
                await workflow.wait_condition(
                    lambda: (
                        bool(self._dag and self._dag.get_ready_tasks())
                        or (self._dag is not None and self._dag.all_terminal())
                    ),
                    timeout=timedelta(minutes=30),
                )
                continue

            # Launch ready tasks in parallel
            handles = []
            for task in ready_tasks:
                self._dag.mark_running(task.task_id)
                handle = workflow.start_activity(
                    execute_agent_activity,
                    args=[task.assigned_agent, task.input_payload],
                    start_to_close_timeout=timedelta(seconds=task.timeout_seconds),
                    retry_policy=retry_policy,
                    task_queue=workflow.info().task_queue,
                )
                handles.append((task.task_id, handle))

            # Await all
            for task_id, handle in handles:
                try:
                    result = await handle
                    self._dag.mark_completed(task_id, result)
                    # Update shared context with tokens
                    if isinstance(result, dict) and "token_usage" in result:
                        self._context.add_tokens(result["token_usage"])
                except Exception as e:
                    self._dag.mark_failed(task_id, str(e))
                    self._context.add_error(task_id, str(e))

        self._context.current_phase = "completed" if not self._dag.has_failed() else "failed"

        return {
            "campaign_id": self._context.campaign_id,
            "status": self._context.current_phase,
            "total_tokens": self._context.total_tokens_used,
            "errors": self._context.errors,
        }
