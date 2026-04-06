"""Source Capability Registry — policy enforcement for platform access.

Every platform integration checks this registry before making requests.
Official/licensed access comes first; browser automation is gated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.models.enums import RetrievalStrategy
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SourcePolicy:
    """Policy definition for a single job platform."""

    source_name: str
    display_name: str
    allowed_modes: list[str] = field(default_factory=list)
    blocked_modes: list[str] = field(default_factory=list)
    rate_limit: dict[str, Any] = field(default_factory=lambda: {"max_rpm": 10, "burst": 3})
    confidence_score: float = 0.8
    is_enabled: bool = True
    notes: str = ""


# ---------------------------------------------------------------------------
# Seed data per Section 8.2 compliance positions
# ---------------------------------------------------------------------------

_DEFAULT_POLICIES: dict[str, SourcePolicy] = {
    "linkedin": SourcePolicy(
        source_name="linkedin",
        display_name="LinkedIn",
        allowed_modes=[
            RetrievalStrategy.LICENSED_VENDOR,
            RetrievalStrategy.ALERT_INGESTION,
            RetrievalStrategy.EMPLOYER_ATS,
            RetrievalStrategy.MANUAL_INPUT,
        ],
        blocked_modes=["stealth_scraping", "captcha_bypass", "auto_apply", "auto_message"],
        rate_limit={"max_rpm": 5, "burst": 2},
        confidence_score=0.90,
        notes="No direct scraping. Use licensed data vendors or alert ingestion only.",
    ),
    "naukri": SourcePolicy(
        source_name="naukri",
        display_name="Naukri.com",
        allowed_modes=[
            RetrievalStrategy.LICENSED_VENDOR,
            RetrievalStrategy.ALERT_INGESTION,
            RetrievalStrategy.EMPLOYER_ATS,
            RetrievalStrategy.MANUAL_INPUT,
        ],
        blocked_modes=["stealth_scraping", "captcha_bypass", "auto_apply"],
        rate_limit={"max_rpm": 20, "burst": 5},
        confidence_score=0.80,
        notes="SerpAPI or Apify for search. Respect robots.txt.",
    ),
    "indeed": SourcePolicy(
        source_name="indeed",
        display_name="Indeed",
        allowed_modes=[
            RetrievalStrategy.API,
            RetrievalStrategy.LICENSED_VENDOR,
            RetrievalStrategy.ALERT_INGESTION,
            RetrievalStrategy.EMPLOYER_ATS,
            RetrievalStrategy.MANUAL_INPUT,
        ],
        blocked_modes=["stealth_scraping", "captcha_bypass", "auto_apply"],
        rate_limit={"max_rpm": 10, "burst": 3},
        confidence_score=0.75,
        notes="Indeed Publisher API (if approved) or RapidAPI vendor.",
    ),
    "iimjobs": SourcePolicy(
        source_name="iimjobs",
        display_name="IIMJobs",
        allowed_modes=[
            RetrievalStrategy.LICENSED_VENDOR,
            RetrievalStrategy.ALERT_INGESTION,
            RetrievalStrategy.MANUAL_INPUT,
        ],
        blocked_modes=["stealth_scraping", "captcha_bypass"],
        rate_limit={"max_rpm": 15, "burst": 4},
        confidence_score=0.70,
        notes="Limited public API. Alerts + manual input preferred.",
    ),
    "employer_ats": SourcePolicy(
        source_name="employer_ats",
        display_name="Employer Career Pages",
        allowed_modes=[
            RetrievalStrategy.EMPLOYER_ATS,
            RetrievalStrategy.BROWSER_AUTOMATION,
        ],
        blocked_modes=["captcha_bypass"],
        rate_limit={"max_rpm": 15, "burst": 5},
        confidence_score=1.0,
        notes="Direct employer pages. Allowlisted domains only for browser automation.",
    ),
    "manual_input": SourcePolicy(
        source_name="manual_input",
        display_name="Manual Input",
        allowed_modes=[RetrievalStrategy.MANUAL_INPUT],
        blocked_modes=[],
        rate_limit={"max_rpm": 100, "burst": 50},
        confidence_score=0.50,
        notes="User-provided URLs or pasted text.",
    ),
}


class SourcePolicyRegistry:
    """Registry for platform source policies.

    In production, policies are fetched from the `source_policies` DB table.
    Falls back to hard-coded defaults for development.
    """

    def __init__(self, policies: dict[str, SourcePolicy] | None = None) -> None:
        self._policies = policies or dict(_DEFAULT_POLICIES)

    def get_policy(self, source_name: str) -> SourcePolicy | None:
        """Fetch policy for a source. Returns None if unknown."""
        return self._policies.get(source_name.lower())

    def is_mode_allowed(self, source_name: str, mode: str) -> bool:
        """Check if a retrieval mode is allowed for the given source."""
        policy = self.get_policy(source_name)
        if policy is None:
            logger.warning(f"No policy found for source: {source_name}")
            return False
        if not policy.is_enabled:
            return False
        if mode in policy.blocked_modes:
            return False
        return mode in policy.allowed_modes

    def is_action_allowed(self, source_name: str, action: str) -> bool:
        """Check if a specific action is allowed (not in blocked list)."""
        policy = self.get_policy(source_name)
        if policy is None:
            return False
        return action not in policy.blocked_modes

    def get_rate_limit(self, source_name: str) -> dict[str, Any]:
        """Get rate limit config for a source."""
        policy = self.get_policy(source_name)
        if policy is None:
            return {"max_rpm": 5, "burst": 1}
        return policy.rate_limit

    def get_confidence(self, source_name: str) -> float:
        """Get confidence score for a source."""
        policy = self.get_policy(source_name)
        if policy is None:
            return 0.4
        return policy.confidence_score

    def list_sources(self) -> list[str]:
        """List all registered source names."""
        return list(self._policies.keys())

    def get_allowed_strategies(self, source_name: str) -> list[str]:
        """Return the allowed retrieval strategies for a source, in order."""
        policy = self.get_policy(source_name)
        if policy is None:
            return [RetrievalStrategy.MANUAL_INPUT]
        return [m for m in policy.allowed_modes if m not in policy.blocked_modes]


# Singleton
source_registry = SourcePolicyRegistry()
