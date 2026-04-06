"""Temporal worker entry point. Runs as: python -m src.worker"""

import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from src.config.settings import settings


async def main() -> None:
    """Start the Temporal worker."""
    client = await Client.connect(settings.temporal_address, namespace=settings.temporal_namespace)

    # Activities and workflows will be registered as they are implemented
    from src.orchestration.activities import execute_agent_activity
    from src.orchestration.workflows import JobPilotWorkflow

    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[JobPilotWorkflow],
        activities=[execute_agent_activity],
    )

    print(f"Worker started, listening on task queue: {settings.temporal_task_queue}")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
