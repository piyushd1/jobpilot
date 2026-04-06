"""Shared context persisted as Temporal workflow state."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

@dataclass
class SharedContext:
    """Mutable state shared across all agents within a campaign workflow.
    Persisted as Temporal workflow state — survives crashes and replays."""
    campaign_id: str = ""
    user_id: str = ""
    resume_id: str = ""

    # Parsed resume profile
    candidate_profile: dict[str, Any] = field(default_factory=dict)

    # Discovered jobs (raw artifacts before dedup)
    raw_jobs: list[dict[str, Any]] = field(default_factory=list)

    # Canonical (deduplicated) jobs
    canonical_jobs: list[dict[str, Any]] = field(default_factory=list)

    # Scored matches
    scored_matches: list[dict[str, Any]] = field(default_factory=list)

    # Outreach contacts
    outreach_contacts: list[dict[str, Any]] = field(default_factory=list)

    # Token tracking
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0

    # Execution metadata
    current_phase: str = "init"
    errors: list[dict[str, Any]] = field(default_factory=list)
    started_at: str = ""

    def add_tokens(self, usage: dict[str, int]) -> None:
        self.total_tokens_used += usage.get("total_tokens", 0)

    def add_error(self, agent: str, error: str) -> None:
        self.errors.append({
            "agent": agent,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
        })
