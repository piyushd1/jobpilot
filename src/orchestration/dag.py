"""Task DAG engine for managing execution dependencies."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from src.models.enums import TaskType, TaskStatus

@dataclass
class Task:
    task_id: str
    task_type: TaskType
    assigned_agent: str
    dependencies: list[str] = field(default_factory=list)
    input_payload: dict = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 3
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 120
    result: dict | None = None
    error: str | None = None
    reasoning_trace: str | None = None
    idempotency_key: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cost_tokens_used: int | None = None

class TaskDAG:
    """Directed acyclic graph of tasks with dependency resolution."""
    def __init__(self):
        self._tasks: dict[str, Task] = {}

    def add_task(self, task: Task) -> None:
        self._tasks[task.task_id] = task

    def get_task(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    @property
    def tasks(self) -> list[Task]:
        return list(self._tasks.values())

    def get_ready_tasks(self) -> list[Task]:
        """Return tasks whose dependencies are all completed and that are PENDING."""
        ready = []
        for task in self._tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            deps_met = all(
                self._tasks[dep].status == TaskStatus.COMPLETED
                for dep in task.dependencies
                if dep in self._tasks
            )
            if deps_met:
                ready.append(task)
        return sorted(ready, key=lambda t: t.priority)

    def mark_running(self, task_id: str) -> None:
        task = self._tasks[task_id]
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()

    def mark_completed(self, task_id: str, result: dict | None = None) -> None:
        task = self._tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.result = result

    def mark_failed(self, task_id: str, error: str) -> None:
        task = self._tasks[task_id]
        task.status = TaskStatus.FAILED
        task.error = error
        task.completed_at = datetime.utcnow()

    def all_terminal(self) -> bool:
        """Check if all tasks are in a terminal state (completed, failed, skipped)."""
        terminal = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED}
        return all(t.status in terminal for t in self._tasks.values())

    def has_failed(self) -> bool:
        return any(t.status == TaskStatus.FAILED for t in self._tasks.values())
