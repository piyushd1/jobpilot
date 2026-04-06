"""Shared enums used across the application."""

from enum import StrEnum


class TaskType(StrEnum):
    """Types of tasks the Manager Agent can dispatch."""

    PARSE_RESUME = "parse_resume"
    DISCOVER_JOBS = "discover_jobs"
    RESEARCH_COMPANY = "research_company"
    SCORE_MATCHES = "score_matches"
    DEDUPLICATE = "deduplicate"
    FIND_CONTACTS = "find_contacts"
    GENERATE_OUTREACH = "generate_outreach"
    QA_REVIEW = "qa_review"


class TaskStatus(StrEnum):
    """Lifecycle states of a task in the DAG."""

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING_APPROVAL = "waiting_approval"


class CampaignStatus(StrEnum):
    """Lifecycle states of a search campaign."""

    CREATED = "created"
    PARSING = "parsing"
    DISCOVERING = "discovering"
    SCORING = "scoring"
    REVIEWING = "reviewing"
    OUTREACH = "outreach"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ParsingStatus(StrEnum):
    """Status of resume parsing."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class MatchTier(StrEnum):
    """Score tier classification for job matches."""

    STRONG = "strong"
    GOOD = "good"
    PARTIAL = "partial"
    WEAK = "weak"


class RetrievalStrategy(StrEnum):
    """Job discovery retrieval strategies, in preference order."""

    API = "api"
    LICENSED_VENDOR = "licensed_vendor"
    ALERT_INGESTION = "alert_ingestion"
    EMPLOYER_ATS = "employer_ats"
    BROWSER_AUTOMATION = "browser_automation"
    MANUAL_INPUT = "manual_input"


class ApprovalStatus(StrEnum):
    """Status of approval tasks requiring human review."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
