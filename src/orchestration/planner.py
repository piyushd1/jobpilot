"""Build the initial 6-phase execution DAG from user inputs."""

from __future__ import annotations

from src.models.enums import TaskType
from src.orchestration.dag import Task, TaskDAG


def build_campaign_dag(
    campaign_id: str,
    enabled_platforms: list[str] | None = None,
) -> TaskDAG:
    """Build the standard campaign execution DAG.

    Phases:
    1. Parse resume
    2. Discover jobs (parallel per platform)
    3. Deduplicate & canonicalize
    4. Score & rank
    5. Approval gate
    6. Compile report
    """
    dag = TaskDAG()
    enabled_platforms = enabled_platforms or ["manual_input"]

    # Phase 1: Parse resume
    parse_id = f"{campaign_id}_parse_resume"
    dag.add_task(
        Task(
            task_id=parse_id,
            task_type=TaskType.PARSE_RESUME,
            assigned_agent="resume_parser",
            priority=1,
            idempotency_key=f"parse_{campaign_id}",
        )
    )

    # Phase 2: Discover jobs per platform (parallel)
    scout_ids = []
    for platform in enabled_platforms:
        scout_id = f"{campaign_id}_scout_{platform}"
        dag.add_task(
            Task(
                task_id=scout_id,
                task_type=TaskType.DISCOVER_JOBS,
                assigned_agent="job_scout",
                dependencies=[parse_id],
                input_payload={"platform": platform},
                priority=2,
                idempotency_key=f"scout_{campaign_id}_{platform}",
            )
        )
        scout_ids.append(scout_id)

    # Phase 3: Deduplicate
    dedup_id = f"{campaign_id}_deduplicate"
    dag.add_task(
        Task(
            task_id=dedup_id,
            task_type=TaskType.DEDUPLICATE,
            assigned_agent="manager",
            dependencies=scout_ids,
            priority=3,
            idempotency_key=f"dedup_{campaign_id}",
        )
    )

    # Phase 4: Score & rank
    score_id = f"{campaign_id}_score_matches"
    dag.add_task(
        Task(
            task_id=score_id,
            task_type=TaskType.SCORE_MATCHES,
            assigned_agent="preference_analyst",
            dependencies=[dedup_id],
            priority=4,
            idempotency_key=f"score_{campaign_id}",
        )
    )

    return dag
