"""QA/Critic Agent -- verification checks after major pipeline stages.

Three modes:
  Mode 1 -- Post-extraction: schema completeness, consistency, prompt injection scan
  Mode 2 -- Post-ranking: contradiction detection, hallucination flagging
  Mode 3 -- Post-outreach: contact confidence check, fabrication detection

Never blocks pipeline -- only flags issues. Manager decides whether to surface.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from src.agents.base import AgentShell
from src.models.schemas import ScoreBreakdown
from src.utils.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Prompt-injection patterns
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+previous\s+instructions", re.IGNORECASE),
    re.compile(r"ignore\s+all\s+prior\s+instructions", re.IGNORECASE),
    re.compile(r"ignore\s+above\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions", re.IGNORECASE),
    re.compile(r"system\s*:", re.IGNORECASE),
    re.compile(r"```\s*tool_call", re.IGNORECASE),
    re.compile(r"<\|im_start\|>", re.IGNORECASE),
    re.compile(r"<\|im_end\|>", re.IGNORECASE),
    re.compile(r"<\|endoftext\|>", re.IGNORECASE),
    re.compile(r"\[INST\]", re.IGNORECASE),
    re.compile(r"\[/INST\]", re.IGNORECASE),
    re.compile(r"<<SYS>>", re.IGNORECASE),
    re.compile(r"<</SYS>>", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(a|an|in)\s+", re.IGNORECASE),
    re.compile(r"act\s+as\s+(a|an)\s+", re.IGNORECASE),
    re.compile(r"new\s+instructions?\s*:", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# Draft length bounds (characters)
# ---------------------------------------------------------------------------

_DRAFT_MIN_LENGTH = 50
_DRAFT_MAX_LENGTH = 5000

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class QACheckInput(BaseModel):
    """Input for the QA/Critic agent."""

    mode: str  # "post_extraction", "post_ranking", "post_outreach"
    jobs: list[dict[str, Any]] = Field(default_factory=list)
    matches: list[dict[str, Any]] = Field(default_factory=list)
    contacts: list[dict[str, Any]] = Field(default_factory=list)
    drafts: list[dict[str, Any]] = Field(default_factory=list)


class QAFlag(BaseModel):
    """A single quality-assurance flag raised by a check."""

    severity: str  # "error", "warning", "info"
    category: str  # "schema", "consistency", "injection", "hallucination", "contradiction", "confidence"
    entity_id: str = ""
    message: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class QACheckOutput(BaseModel):
    """Result of a QA check run."""

    mode: str
    total_checked: int = 0
    flags: list[QAFlag] = Field(default_factory=list)
    passed: bool = True
    summary: str = ""


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class QACriticAgent(AgentShell[QACheckInput, QACheckOutput]):
    """Runs verification checks after major pipeline stages.

    All checks are synchronous (no LLM calls needed). The agent inspects
    data produced by upstream agents and flags issues. It never blocks
    the pipeline -- the Manager decides whether to surface flags to the user.
    """

    agent_name: str = "qa_critic"
    persona: str = (
        "You are a quality assurance agent that verifies data integrity "
        "across the pipeline."
    )

    # --- Schema properties ---

    @property
    def input_type(self) -> type[QACheckInput]:
        return QACheckInput

    @property
    def output_type(self) -> type[QACheckOutput]:
        return QACheckOutput

    # --- Core execution ---

    async def reason_and_act(self, task_input: QACheckInput) -> QACheckOutput:
        """Dispatch to the appropriate check mode."""
        if task_input.mode == "post_extraction":
            return self._check_extraction(task_input.jobs)
        elif task_input.mode == "post_ranking":
            return self._check_ranking(task_input.matches)
        elif task_input.mode == "post_outreach":
            return self._check_outreach(task_input.contacts, task_input.drafts)

        return QACheckOutput(mode=task_input.mode, summary="Unknown mode")

    # ------------------------------------------------------------------
    # Mode 1 -- Post-extraction checks
    # ------------------------------------------------------------------

    def _check_extraction(self, jobs: list[dict[str, Any]]) -> QACheckOutput:
        """Validate extracted job data for schema, consistency, and injection."""
        flags: list[QAFlag] = []

        for idx, job in enumerate(jobs):
            entity_id = job.get("content_hash") or job.get("title", f"job_{idx}")

            # -- Schema completeness --
            title = job.get("title")
            if not title or not isinstance(title, str) or not title.strip():
                flags.append(QAFlag(
                    severity="error",
                    category="schema",
                    entity_id=entity_id,
                    message="Missing or empty 'title' field",
                ))

            company = job.get("company")
            if not company or not isinstance(company, str) or not company.strip():
                flags.append(QAFlag(
                    severity="error",
                    category="schema",
                    entity_id=entity_id,
                    message="Missing or empty 'company' field",
                ))

            # -- Consistency: experience range --
            min_exp = job.get("min_experience_years")
            max_exp = job.get("max_experience_years")
            if (
                min_exp is not None
                and max_exp is not None
                and min_exp > max_exp
            ):
                flags.append(QAFlag(
                    severity="warning",
                    category="consistency",
                    entity_id=entity_id,
                    message=(
                        f"min_experience_years ({min_exp}) > "
                        f"max_experience_years ({max_exp})"
                    ),
                    details={"min": min_exp, "max": max_exp},
                ))

            # -- Consistency: posted_date not in the future --
            posted_date = job.get("posted_date")
            if posted_date is not None:
                try:
                    if isinstance(posted_date, str):
                        pd = datetime.fromisoformat(posted_date)
                    elif isinstance(posted_date, datetime):
                        pd = posted_date
                    else:
                        pd = None

                    if pd is not None:
                        # Ensure timezone-aware comparison
                        now = datetime.now(UTC)
                        if pd.tzinfo is None:
                            pd = pd.replace(tzinfo=UTC)
                        if pd > now:
                            flags.append(QAFlag(
                                severity="warning",
                                category="consistency",
                                entity_id=entity_id,
                                message=f"posted_date is in the future: {pd.isoformat()}",
                                details={"posted_date": pd.isoformat()},
                            ))
                except (ValueError, TypeError):
                    flags.append(QAFlag(
                        severity="warning",
                        category="consistency",
                        entity_id=entity_id,
                        message=f"posted_date could not be parsed: {posted_date!r}",
                    ))

            # -- Consistency: salary range --
            salary_min = job.get("salary_min")
            salary_max = job.get("salary_max")
            if (
                salary_min is not None
                and salary_max is not None
                and salary_min > salary_max
            ):
                flags.append(QAFlag(
                    severity="warning",
                    category="consistency",
                    entity_id=entity_id,
                    message=(
                        f"salary_min ({salary_min}) > salary_max ({salary_max})"
                    ),
                    details={"salary_min": salary_min, "salary_max": salary_max},
                ))

            # -- Prompt injection scan --
            description = job.get("description") or ""
            if isinstance(description, str):
                for pattern in _INJECTION_PATTERNS:
                    match = pattern.search(description)
                    if match:
                        flags.append(QAFlag(
                            severity="error",
                            category="injection",
                            entity_id=entity_id,
                            message=(
                                f"Possible prompt injection detected: "
                                f"'{match.group()}'"
                            ),
                            details={
                                "pattern": pattern.pattern,
                                "match": match.group(),
                                "position": match.start(),
                            },
                        ))

        has_errors = any(f.severity == "error" for f in flags)
        error_count = sum(1 for f in flags if f.severity == "error")
        warning_count = sum(1 for f in flags if f.severity == "warning")

        return QACheckOutput(
            mode="post_extraction",
            total_checked=len(jobs),
            flags=flags,
            passed=not has_errors,
            summary=(
                f"Checked {len(jobs)} jobs: "
                f"{error_count} errors, {warning_count} warnings"
            ),
        )

    # ------------------------------------------------------------------
    # Mode 2 -- Post-ranking checks
    # ------------------------------------------------------------------

    def _check_ranking(self, matches: list[dict[str, Any]]) -> QACheckOutput:
        """Validate ranked matches for contradictions and hallucinations."""
        flags: list[QAFlag] = []

        for idx, match in enumerate(matches):
            entity_id = match.get("job_id") or match.get("title", f"match_{idx}")

            # -- Contradiction: reasoning says "strong" but score is low --
            breakdown = match.get("score_breakdown", {})
            reasoning_trace = ""
            final_score: float = 0.0

            if isinstance(breakdown, dict):
                reasoning_trace = str(breakdown.get("reasoning_trace", ""))
                try:
                    final_score = float(breakdown.get("final_score", 0.0))
                except (ValueError, TypeError):
                    final_score = 0.0
            elif isinstance(breakdown, ScoreBreakdown):
                reasoning_trace = breakdown.reasoning_trace
                final_score = breakdown.final_score

            strong_keywords = ["strong", "excellent", "outstanding", "exceptional"]
            reasoning_lower = reasoning_trace.lower()
            mentions_strong = any(kw in reasoning_lower for kw in strong_keywords)

            if mentions_strong and final_score < 0.5:
                flags.append(QAFlag(
                    severity="warning",
                    category="contradiction",
                    entity_id=entity_id,
                    message=(
                        f"Reasoning mentions positive language but "
                        f"final_score is low ({final_score:.2f})"
                    ),
                    details={
                        "final_score": final_score,
                        "reasoning_excerpt": reasoning_trace[:200],
                    },
                ))

            # -- Hallucination: high skills_score but low actual overlap --
            skills_score: float = 0.0
            if isinstance(breakdown, dict):
                try:
                    skills_score = float(breakdown.get("skills_score", 0.0))
                except (ValueError, TypeError):
                    skills_score = 0.0
            elif isinstance(breakdown, ScoreBreakdown):
                skills_score = breakdown.skills_score

            if skills_score > 0.8:
                # Check actual skill overlap if data is available
                required_skills = match.get("required_skills", [])
                candidate_skills = match.get("candidate_skills", [])

                if required_skills and candidate_skills:
                    required_set = {s.lower().strip() for s in required_skills}
                    candidate_set = {s.lower().strip() for s in candidate_skills}
                    overlap = required_set & candidate_set
                    overlap_ratio = (
                        len(overlap) / len(required_set) if required_set else 0.0
                    )

                    if overlap_ratio < 0.3:
                        flags.append(QAFlag(
                            severity="warning",
                            category="hallucination",
                            entity_id=entity_id,
                            message=(
                                f"skills_score is {skills_score:.2f} but "
                                f"actual skill overlap is only "
                                f"{overlap_ratio:.0%} "
                                f"({len(overlap)}/{len(required_set)})"
                            ),
                            details={
                                "skills_score": skills_score,
                                "overlap_ratio": overlap_ratio,
                                "overlap_count": len(overlap),
                                "required_count": len(required_set),
                                "overlapping_skills": sorted(overlap),
                            },
                        ))

        has_errors = any(f.severity == "error" for f in flags)
        warning_count = sum(1 for f in flags if f.severity == "warning")

        return QACheckOutput(
            mode="post_ranking",
            total_checked=len(matches),
            flags=flags,
            passed=not has_errors,
            summary=(
                f"Checked {len(matches)} matches: "
                f"{warning_count} warnings"
            ),
        )

    # ------------------------------------------------------------------
    # Mode 3 -- Post-outreach checks
    # ------------------------------------------------------------------

    def _check_outreach(
        self,
        contacts: list[dict[str, Any]],
        drafts: list[dict[str, Any]],
    ) -> QACheckOutput:
        """Validate outreach contacts and message drafts."""
        flags: list[QAFlag] = []

        # -- Contact confidence checks --
        for idx, contact in enumerate(contacts):
            entity_id = (
                contact.get("contact_id")
                or contact.get("name")
                or f"contact_{idx}"
            )

            email = contact.get("email")
            linkedin_url = contact.get("linkedin_url")

            has_email = bool(email and isinstance(email, str) and email.strip())
            has_linkedin = bool(
                linkedin_url
                and isinstance(linkedin_url, str)
                and linkedin_url.strip()
            )

            if not has_email and not has_linkedin:
                flags.append(QAFlag(
                    severity="warning",
                    category="confidence",
                    entity_id=entity_id,
                    message=(
                        "Contact has neither email nor linkedin_url -- "
                        "outreach may not be possible"
                    ),
                    details={
                        "available_fields": [
                            k for k, v in contact.items()
                            if v and k not in ("email", "linkedin_url")
                        ],
                    },
                ))

        # -- Draft checks --
        for idx, draft in enumerate(drafts):
            entity_id = (
                draft.get("draft_id")
                or draft.get("subject")
                or f"draft_{idx}"
            )
            body = draft.get("body") or draft.get("message") or ""

            if not isinstance(body, str):
                body = str(body)

            # Length bounds
            if len(body) < _DRAFT_MIN_LENGTH:
                flags.append(QAFlag(
                    severity="warning",
                    category="confidence",
                    entity_id=entity_id,
                    message=(
                        f"Draft body is too short ({len(body)} chars, "
                        f"minimum {_DRAFT_MIN_LENGTH})"
                    ),
                    details={"length": len(body), "min": _DRAFT_MIN_LENGTH},
                ))

            if len(body) > _DRAFT_MAX_LENGTH:
                flags.append(QAFlag(
                    severity="warning",
                    category="confidence",
                    entity_id=entity_id,
                    message=(
                        f"Draft body is too long ({len(body)} chars, "
                        f"maximum {_DRAFT_MAX_LENGTH})"
                    ),
                    details={"length": len(body), "max": _DRAFT_MAX_LENGTH},
                ))

            # Fabricated quotes detection: look for double-quoted text that
            # is suspiciously specific (long, contains names or numbers that
            # look invented). We flag any quoted passage over 80 chars as
            # potentially fabricated -- the Manager can review.
            quoted_passages = re.findall(r'"([^"]{80,})"', body)
            for passage in quoted_passages:
                flags.append(QAFlag(
                    severity="warning",
                    category="hallucination",
                    entity_id=entity_id,
                    message=(
                        "Draft contains a long quoted passage that may be "
                        "fabricated"
                    ),
                    details={
                        "quote_length": len(passage),
                        "quote_preview": passage[:120],
                    },
                ))

            # Also flag shorter quotes that contain specific numbers, dollar
            # amounts, or percentages -- these are common hallucination tells.
            short_quotes = re.findall(r'"([^"]{20,80})"', body)
            for quote in short_quotes:
                if re.search(r"\$[\d,]+|[\d]+%|\d{4,}", quote):
                    flags.append(QAFlag(
                        severity="info",
                        category="hallucination",
                        entity_id=entity_id,
                        message=(
                            "Draft contains a quoted passage with specific "
                            "numbers that should be verified"
                        ),
                        details={
                            "quote_preview": quote,
                        },
                    ))

        has_errors = any(f.severity == "error" for f in flags)
        error_count = sum(1 for f in flags if f.severity == "error")
        warning_count = sum(1 for f in flags if f.severity == "warning")
        total_checked = len(contacts) + len(drafts)

        return QACheckOutput(
            mode="post_outreach",
            total_checked=total_checked,
            flags=flags,
            passed=not has_errors,
            summary=(
                f"Checked {len(contacts)} contacts + {len(drafts)} drafts: "
                f"{error_count} errors, {warning_count} warnings"
            ),
        )
