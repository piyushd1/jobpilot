"""AgentShell base class — the uniform structural contract for all JobPilot agents.

Every agent follows a 5-step execution loop:
  1. Receive task input from Manager
  2. Reason about approach (LLM call with persona + tools)
  3. Select & invoke tools
  4. Validate output against Pydantic schema
  5. Return result + reasoning trace

Agents are stateless — they run as Temporal activities. State lives in
SharedContext within the Temporal workflow.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ValidationError

from src.models.schemas import ReasoningTrace
from src.utils.logging import get_logger

logger = get_logger(__name__)

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class AgentResult(BaseModel, Generic[OutputT]):
    """Wrapper around agent output with metadata."""

    success: bool
    output: OutputT | None = None
    error: str | None = None
    reasoning_trace: ReasoningTrace | None = None
    token_usage: dict[str, int] = {}
    duration_seconds: float = 0.0


class ToolDefinition(BaseModel):
    """Registry entry for a tool available to the agent."""

    name: str
    description: str
    parameters_schema: dict[str, Any] = {}


class AgentShell(ABC, Generic[InputT, OutputT]):
    """Abstract base class that all JobPilot agents inherit from.

    Subclasses must define:
      - agent_name: human-readable name
      - persona: system prompt defining the agent's role
      - input_type / output_type: Pydantic model classes
      - reason_and_act(): the core LLM + tool execution logic
    """

    agent_name: str = "base_agent"
    persona: str = "You are a helpful assistant."

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self._tool_handlers: dict[str, Any] = {}
        self._memory: dict[str, Any] = {}

    # --- Schema declarations (override in subclass) ---

    @property
    @abstractmethod
    def input_type(self) -> type[InputT]:
        """Pydantic model class for this agent's input."""
        ...

    @property
    @abstractmethod
    def output_type(self) -> type[OutputT]:
        """Pydantic model class for this agent's output."""
        ...

    # --- Tool registry ---

    def register_tool(
        self,
        name: str,
        description: str,
        handler: Any,
        parameters_schema: dict[str, Any] | None = None,
    ) -> None:
        """Register a callable tool that the agent can invoke during execution."""
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            parameters_schema=parameters_schema or {},
        )
        self._tool_handlers[name] = handler

    def get_tools_for_llm(self) -> list[dict[str, Any]]:
        """Return tool definitions formatted for LLM function-calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters_schema,
                },
            }
            for t in self._tools.values()
        ]

    async def invoke_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Invoke a registered tool by name."""
        handler = self._tool_handlers.get(name)
        if handler is None:
            raise ValueError(f"Unknown tool: {name}")

        import asyncio

        if asyncio.iscoroutinefunction(handler):
            return await handler(**arguments)
        return handler(**arguments)

    # --- Memory ---

    @property
    def memory(self) -> dict[str, Any]:
        """Short-term memory for this execution. Cleared between runs."""
        return self._memory

    # --- Callback hooks (override in subclass as needed) ---

    async def on_start(self, task_input: InputT) -> None:
        """Called before execution begins."""
        logger.info(f"[{self.agent_name}] Starting execution")

    async def on_end(self, result: AgentResult[OutputT]) -> None:
        """Called after execution completes (success or failure)."""
        status = "success" if result.success else "failed"
        logger.info(
            f"[{self.agent_name}] Execution {status}",
            duration=result.duration_seconds,
            tokens=result.token_usage,
        )

    async def on_error(self, error: Exception) -> None:
        """Called when an unhandled error occurs."""
        logger.error(f"[{self.agent_name}] Error: {error}")

    # --- Core execution ---

    @abstractmethod
    async def reason_and_act(self, task_input: InputT) -> OutputT:
        """The core agent logic: reason about the task, invoke tools, produce output.

        This is where subclasses implement their LLM calls and tool usage.
        Must return a valid instance of self.output_type.
        """
        ...

    async def execute(self, raw_input: dict[str, Any]) -> AgentResult[OutputT]:
        """The 5-step execution loop.

        1. Parse and validate input
        2. Call on_start hook
        3. Run reason_and_act (LLM reasoning + tool calls)
        4. Validate output against schema
        5. Build result with reasoning trace
        """
        start_time = time.monotonic()
        reasoning_steps: list[str] = []
        token_usage: dict[str, int] = {}
        self._memory.clear()

        try:
            # Step 1: Validate input
            reasoning_steps.append("Validating input against schema")
            try:
                task_input = self.input_type.model_validate(raw_input)
            except ValidationError as e:
                return AgentResult(
                    success=False,
                    error=f"Input validation failed: {e}",
                    duration_seconds=time.monotonic() - start_time,
                )

            # Step 2: on_start callback
            await self.on_start(task_input)

            # Step 3: Reason and act (LLM + tools)
            reasoning_steps.append("Executing reason_and_act")
            output = await self.reason_and_act(task_input)

            # Step 4: Validate output
            reasoning_steps.append("Validating output against schema")
            try:
                validated_output = self.output_type.model_validate(
                    output.model_dump() if isinstance(output, BaseModel) else output
                )
            except ValidationError as e:
                return AgentResult(
                    success=False,
                    error=f"Output validation failed: {e}",
                    duration_seconds=time.monotonic() - start_time,
                )

            # Collect token usage from memory if the agent stored it there
            token_usage = self._memory.get("token_usage", {})

            # Step 5: Build result
            duration = time.monotonic() - start_time
            reasoning_steps.append(f"Completed in {duration:.2f}s")

            trace = ReasoningTrace(
                agent_name=self.agent_name,
                task_type=self.agent_name,
                input_summary=str(raw_input)[:500],
                steps=reasoning_steps,
                output_summary=str(validated_output)[:500],
                token_usage=token_usage,
                duration_seconds=duration,
            )

            result: AgentResult[OutputT] = AgentResult(
                success=True,
                output=validated_output,
                reasoning_trace=trace,
                token_usage=token_usage,
                duration_seconds=duration,
            )

            await self.on_end(result)
            return result

        except Exception as e:
            duration = time.monotonic() - start_time
            await self.on_error(e)
            return AgentResult(
                success=False,
                error=f"{type(e).__name__}: {e}",
                reasoning_trace=ReasoningTrace(
                    agent_name=self.agent_name,
                    task_type=self.agent_name,
                    input_summary=str(raw_input)[:500],
                    steps=reasoning_steps + [f"Error: {e}"],
                    output_summary="",
                    duration_seconds=duration,
                ),
                duration_seconds=duration,
            )
