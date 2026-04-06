"""PlatformAdapter ABC — base class for all job platform integrations.

Every adapter follows a strategy cascade: attempt retrieval strategies in
preference order, checking policy compliance before each attempt. Falls
back gracefully through the chain.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from src.models.enums import RetrievalStrategy
from src.platforms.source_policy import SourcePolicyRegistry, source_registry
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SearchParams:
    """Parameters for a job search request."""

    query: str = ""
    roles: list[str] = field(default_factory=list)
    location: str = ""
    remote_only: bool = False
    experience_min: int | None = None
    experience_max: int | None = None
    skills: list[str] = field(default_factory=list)
    companies: list[str] = field(default_factory=list)
    max_results: int = 50
    campaign_id: str = ""


@dataclass
class StrategyResult:
    """Result of a retrieval strategy attempt."""

    status: str  # "success", "failed", "blocked", "challenge_detected"
    results: list[dict[str, Any]] = field(default_factory=list)
    strategy_used: str = ""
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class PlatformAdapter(ABC):
    """Abstract base class for job platform adapters.

    Subclasses define their preferred strategy order. The base class handles
    the cascade loop, policy enforcement, and error handling.
    """

    platform_name: str = "unknown"

    def __init__(
        self,
        registry: SourcePolicyRegistry | None = None,
        proxy_pool: Any | None = None,
        rate_limiter: Any | None = None,
        session_manager: Any | None = None,
    ) -> None:
        self._registry = registry or source_registry
        self._proxy_pool = proxy_pool
        self._rate_limiter = rate_limiter
        self._session_manager = session_manager

        self._policy = self._registry.get_policy(self.platform_name)
        self._strategies = self._configure_strategies()

    def _configure_strategies(self) -> list[str]:
        """Filter preferred strategy order against policy allowlist."""
        preferred = self._preferred_strategy_order()
        if self._policy is None:
            logger.warning(f"No policy for {self.platform_name}, using manual_input only")
            return [RetrievalStrategy.MANUAL_INPUT]

        allowed = set(self._policy.allowed_modes)
        blocked = set(self._policy.blocked_modes)
        return [s for s in preferred if s in allowed and s not in blocked]

    @abstractmethod
    def _preferred_strategy_order(self) -> list[str]:
        """Return the preferred retrieval strategy order for this platform.

        Subclasses define this based on what's available for their platform.
        """
        ...

    def _policy_allows(self, strategy: str) -> bool:
        """Check if a strategy is currently allowed by policy."""
        return self._registry.is_mode_allowed(self.platform_name, strategy)

    async def search(self, params: SearchParams) -> StrategyResult:
        """Execute the strategy cascade for a search request.

        Attempts each configured strategy in order, checking policy before
        each attempt. Returns on first success or after all strategies fail.
        """
        last_error: str | None = None

        for strategy in self._strategies:
            if not self._policy_allows(strategy):
                logger.info(
                    f"[{self.platform_name}] Strategy {strategy} blocked by policy, skipping"
                )
                continue

            # Rate limiting
            if self._rate_limiter:
                try:
                    await self._rate_limiter.acquire(self.platform_name)
                except Exception as e:
                    logger.warning(
                        f"[{self.platform_name}] Rate limit exceeded for {strategy}",
                        error=str(e),
                    )
                    last_error = f"Rate limited: {e}"
                    continue

            logger.info(f"[{self.platform_name}] Attempting strategy: {strategy}")

            try:
                result = await self._execute_strategy(strategy, params)

                if result.status == "challenge_detected":
                    logger.warning(
                        f"[{self.platform_name}] Challenge detected on {strategy}"
                    )
                    # Do NOT bypass — log and move to next strategy
                    last_error = f"Challenge detected on {strategy}"
                    continue

                if result.status == "success" and result.results:
                    result.strategy_used = strategy
                    logger.info(
                        f"[{self.platform_name}] Strategy {strategy} succeeded",
                        result_count=len(result.results),
                    )
                    return result

                last_error = result.error or f"Strategy {strategy} returned no results"

            except Exception as e:
                logger.error(
                    f"[{self.platform_name}] Strategy {strategy} failed",
                    error=str(e),
                )
                last_error = str(e)

        # All strategies exhausted
        return StrategyResult(
            status="failed",
            error=f"All strategies exhausted for {self.platform_name}. Last: {last_error}",
        )

    @abstractmethod
    async def _execute_strategy(
        self, strategy: str, params: SearchParams
    ) -> StrategyResult:
        """Execute a specific retrieval strategy.

        Subclasses implement the actual logic for each strategy they support.
        """
        ...

    async def _handle_challenge(
        self, strategy: str, screenshot_path: str | None = None
    ) -> StrategyResult:
        """Handle a detected challenge (CAPTCHA, login wall, etc).

        Creates an approval task for human review instead of bypassing.
        """
        logger.warning(
            f"[{self.platform_name}] Challenge on {strategy}, creating approval task",
            screenshot=screenshot_path,
        )
        return StrategyResult(
            status="challenge_detected",
            error=f"Challenge detected on {self.platform_name}/{strategy}",
            metadata={"screenshot_path": screenshot_path},
        )
