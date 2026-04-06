"""SQLAlchemy ORM models and session factory for JobPilot.

All tables per Section 6.1 of the architecture doc:
users, resumes, candidate_preferences, search_campaigns, source_policies,
raw_job_artifacts, canonical_jobs, job_matches, companies, outreach_contacts,
approval_tasks, user_actions, audit_logs.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.config.settings import settings

engine = create_async_engine(settings.database_url, echo=settings.is_dev)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all ORM models."""

    pass


# ---------------------------------------------------------------------------
# Users & Resumes
# ---------------------------------------------------------------------------


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    resumes: Mapped[list[Resume]] = relationship(back_populates="user")
    campaigns: Mapped[list[SearchCampaign]] = relationship(back_populates="user")


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_hash: Mapped[str | None] = mapped_column(String(64))
    parsing_status: Mapped[str] = mapped_column(String(32), default="pending")
    parsed_profile: Mapped[dict | None] = mapped_column(JSONB)
    parsing_metadata: Mapped[dict | None] = mapped_column(JSONB)
    embedding_ids: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="resumes")


class CandidatePreference(Base):
    __tablename__ = "candidate_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    target_roles: Mapped[list | None] = mapped_column(JSONB)
    target_companies: Mapped[list | None] = mapped_column(JSONB)
    target_locations: Mapped[list | None] = mapped_column(JSONB)
    open_to_remote: Mapped[bool] = mapped_column(Boolean, default=True)
    min_experience_years: Mapped[int | None] = mapped_column(Integer)
    max_experience_years: Mapped[int | None] = mapped_column(Integer)
    scoring_weight_overrides: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


# ---------------------------------------------------------------------------
# Campaigns
# ---------------------------------------------------------------------------


class SearchCampaign(Base):
    __tablename__ = "search_campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="created")
    config: Mapped[dict | None] = mapped_column(JSONB)
    workflow_id: Mapped[str | None] = mapped_column(String(255))
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="campaigns")
    jobs: Mapped[list[CanonicalJob]] = relationship(back_populates="campaign")
    matches: Mapped[list[JobMatch]] = relationship(back_populates="campaign")


# ---------------------------------------------------------------------------
# Source Policies
# ---------------------------------------------------------------------------


class SourcePolicy(Base):
    __tablename__ = "source_policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    allowed_modes: Mapped[list] = mapped_column(JSONB, nullable=False)
    rate_limits: Mapped[dict | None] = mapped_column(JSONB)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.8)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------


class RawJobArtifact(Base):
    """Raw job data as fetched from a source, before deduplication."""

    __tablename__ = "raw_job_artifacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("search_campaigns.id"), nullable=False
    )
    source_platform: Mapped[str] = mapped_column(String(64), nullable=False)
    retrieval_strategy: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class CanonicalJob(Base):
    """Deduplicated, normalized job record."""

    __tablename__ = "canonical_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("search_campaigns.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255))
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str | None] = mapped_column(Text)
    required_skills: Mapped[list | None] = mapped_column(JSONB)
    preferred_skills: Mapped[list | None] = mapped_column(JSONB)
    min_experience_years: Mapped[int | None] = mapped_column(Integer)
    max_experience_years: Mapped[int | None] = mapped_column(Integer)
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    salary_currency: Mapped[str | None] = mapped_column(String(8))
    posted_date: Mapped[datetime | None] = mapped_column(DateTime)
    application_url_board: Mapped[str | None] = mapped_column(Text)
    application_url_employer: Mapped[str | None] = mapped_column(Text)
    apply_channel: Mapped[str | None] = mapped_column(String(32))
    source_refs: Mapped[list | None] = mapped_column(JSONB)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    embedding_id: Mapped[str | None] = mapped_column(String(128))
    risk_flags: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    campaign: Mapped[SearchCampaign] = relationship(back_populates="jobs")
    matches: Mapped[list[JobMatch]] = relationship(back_populates="job")


# ---------------------------------------------------------------------------
# Scoring / Matches
# ---------------------------------------------------------------------------


class JobMatch(Base):
    """Score result linking a candidate to a canonical job."""

    __tablename__ = "job_matches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("search_campaigns.id"), nullable=False
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("canonical_jobs.id"), nullable=False
    )
    final_score: Mapped[float] = mapped_column(Float, nullable=False)
    tier: Mapped[str] = mapped_column(String(16), nullable=False)
    score_breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False)
    reasoning_trace: Mapped[str | None] = mapped_column(Text)
    skill_gaps: Mapped[list | None] = mapped_column(JSONB)
    user_decision: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    campaign: Mapped[SearchCampaign] = relationship(back_populates="matches")
    job: Mapped[CanonicalJob] = relationship(back_populates="matches")


# ---------------------------------------------------------------------------
# Companies & Outreach
# ---------------------------------------------------------------------------


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255))
    industry: Mapped[str | None] = mapped_column(String(128))
    size_range: Mapped[str | None] = mapped_column(String(64))
    research_data: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class OutreachContact(Base):
    __tablename__ = "outreach_contacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("search_campaigns.id"), nullable=False
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("canonical_jobs.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255))
    company: Mapped[str | None] = mapped_column(String(255))
    linkedin_url: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(String(255))
    contact_type: Mapped[str] = mapped_column(String(32))
    priority_rank: Mapped[int] = mapped_column(Integer, default=0)
    message_draft: Mapped[str | None] = mapped_column(Text)
    message_status: Mapped[str] = mapped_column(String(32), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ---------------------------------------------------------------------------
# Approval & Tracking
# ---------------------------------------------------------------------------


class ApprovalTask(Base):
    __tablename__ = "approval_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("search_campaigns.id"), nullable=False
    )
    approval_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    decided_at: Mapped[datetime | None] = mapped_column(DateTime)
    decision_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class UserAction(Base):
    """Tracks user interactions for feedback learning."""

    __tablename__ = "user_actions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False)
    action_data: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(128))
    details: Mapped[dict | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ---------------------------------------------------------------------------
# Indexes (per Section 6.1)
# ---------------------------------------------------------------------------

Index("idx_canonical_jobs_campaign", CanonicalJob.campaign_id)
Index("idx_canonical_jobs_content_hash", CanonicalJob.content_hash)
Index("idx_matches_campaign_score", JobMatch.campaign_id, JobMatch.final_score.desc())
Index("idx_contacts_campaign_job", OutreachContact.campaign_id, OutreachContact.job_id)
Index("idx_user_actions_user", UserAction.user_id, UserAction.created_at.desc())
Index("idx_resumes_user", Resume.user_id)
Index("idx_raw_artifacts_campaign", RawJobArtifact.campaign_id)
