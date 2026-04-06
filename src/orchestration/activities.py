"""Temporal Activity definitions wrapping agent execution."""

from __future__ import annotations

from typing import Any

from temporalio import activity


@activity.defn
async def execute_agent_activity(
    agent_name: str,
    input_payload: dict[str, Any],
) -> dict[str, Any]:
    """Generic activity that instantiates and runs an agent by name.

    Returns the AgentResult as a dict.
    """

    agent = _get_agent(agent_name)
    result = await agent.execute(input_payload)
    return result.model_dump()


def _get_agent(name: str):
    """Agent registry — returns an instance of the named agent."""
    # Import lazily to avoid circular imports
    registry = {}

    # Agents are registered as they are implemented
    try:
        from src.agents.resume_parser import ResumeParserAgent

        registry["resume_parser"] = ResumeParserAgent
    except ImportError:
        pass

    agent_class = registry.get(name)
    if agent_class is None:
        raise ValueError(f"Unknown agent: {name}. Available: {list(registry.keys())}")
    return agent_class()
