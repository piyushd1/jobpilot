"""Unified LLM gateway using LiteLLM for multi-provider support.

Supports OpenAI, Anthropic, and OpenRouter with a unified interface.
LiteLLM routes to the correct provider based on model prefix:
  - "openrouter/..." → OpenRouter API
  - "gpt-..." → OpenAI
  - "claude-..." → Anthropic

Configure via .env: set OPENROUTER_API_KEY to use OpenRouter.
"""

from __future__ import annotations

import os
from typing import Any

import litellm

from src.config.settings import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Suppress LiteLLM's verbose logging
litellm.suppress_debug_info = True

# Configure API keys for LiteLLM based on what's available
if settings.openrouter_api_key:
    os.environ["OPENROUTER_API_KEY"] = settings.openrouter_api_key
if settings.openai_api_key:
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key
if settings.anthropic_api_key:
    os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key


class LLMGateway:
    """Unified interface to LLM providers via LiteLLM."""

    def __init__(self) -> None:
        self._total_tokens: dict[str, int] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

    @property
    def total_tokens(self) -> dict[str, int]:
        return self._total_tokens.copy()

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        tools: list[dict[str, Any]] | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a completion request to the LLM.

        Returns:
            dict with keys: content, tool_calls, token_usage, model
        """
        model = model or settings.llm_primary_model

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
        if response_format:
            kwargs["response_format"] = response_format

        try:
            response = await litellm.acompletion(**kwargs)
        except Exception as e:
            logger.error("LLM call failed", model=model, error=str(e))
            raise

        # Extract response
        choice = response.choices[0]
        usage = response.usage

        token_usage = {
            "prompt_tokens": usage.prompt_tokens or 0,
            "completion_tokens": usage.completion_tokens or 0,
            "total_tokens": usage.total_tokens or 0,
        }

        # Accumulate
        for key, val in token_usage.items():
            self._total_tokens[key] = self._total_tokens.get(key, 0) + val

        logger.info(
            "LLM call completed",
            model=model,
            tokens=token_usage["total_tokens"],
        )

        return {
            "content": choice.message.content,
            "tool_calls": getattr(choice.message, "tool_calls", None),
            "token_usage": token_usage,
            "model": model,
        }

    async def complete_json(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        """Convenience method for JSON-mode completions."""
        result = await self.complete(
            messages=messages,
            model=model,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        import json

        content = result["content"] or "{}"
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            logger.warning("LLM returned invalid JSON, attempting repair")
            parsed = {}
        return {**result, "parsed": parsed}

    async def embed(
        self,
        texts: list[str],
        model: str | None = None,
    ) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Batches up to 50 texts per API call.
        """
        model = model or settings.embedding_model
        all_embeddings: list[list[float]] = []

        batch_size = 50
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = await litellm.aembedding(model=model, input=batch)

            for item in response.data:
                all_embeddings.append(item["embedding"])

            if response.usage:
                tokens = response.usage.total_tokens or 0
                self._total_tokens["total_tokens"] = (
                    self._total_tokens.get("total_tokens", 0) + tokens
                )

        return all_embeddings


# Singleton for convenience
llm_gateway = LLMGateway()
