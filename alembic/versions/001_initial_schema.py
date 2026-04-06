"""Initial schema — all Phase 1 tables.

Revision ID: 001
Revises:
Create Date: 2026-04-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Users ---
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # --- Resumes ---
    op.create_table(
        "resumes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("file_path", sa.String(1024), nullable=False),
        sa.Column("file_hash", sa.String(64)),
        sa.Column("parsing_status", sa.String(32), default="pending"),
        sa.Column("parsed_profile", JSONB),
        sa.Column("parsing_metadata", JSONB),
        sa.Column("embedding_ids", JSONB),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_resumes_user", "resumes", ["user_id"])

    # --- Candidate Preferences ---
    op.create_table(
        "candidate_preferences",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("target_roles", JSONB),
        sa.Column("target_companies", JSONB),
        sa.Column("target_locations", JSONB),
        sa.Column("open_to_remote", sa.Boolean, default=True),
        sa.Column("min_experience_years", sa.Integer),
        sa.Column("max_experience_years", sa.Integer),
        sa.Column("scoring_weight_overrides", JSONB),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # --- Search Campaigns ---
    op.create_table(
        "search_campaigns",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("resume_id", UUID(as_uuid=True), sa.ForeignKey("resumes.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), default="created"),
        sa.Column("config", JSONB),
        sa.Column("workflow_id", sa.String(255)),
        sa.Column("started_at", sa.DateTime),
        sa.Column("completed_at", sa.DateTime),
        sa.Column("total_tokens_used", sa.Integer, default=0),
        sa.Column("total_cost_usd", sa.Float, default=0.0),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # --- Source Policies ---
    op.create_table(
        "source_policies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("source_name", sa.String(64), unique=True, nullable=False),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("allowed_modes", JSONB, nullable=False),
        sa.Column("rate_limits", JSONB),
        sa.Column("confidence_score", sa.Float, default=0.8),
        sa.Column("is_enabled", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # --- Raw Job Artifacts ---
    op.create_table(
        "raw_job_artifacts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "campaign_id",
            UUID(as_uuid=True),
            sa.ForeignKey("search_campaigns.id"),
            nullable=False,
        ),
        sa.Column("source_platform", sa.String(64), nullable=False),
        sa.Column("retrieval_strategy", sa.String(64), nullable=False),
        sa.Column("raw_data", JSONB, nullable=False),
        sa.Column("source_url", sa.Text),
        sa.Column("fetched_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_raw_artifacts_campaign", "raw_job_artifacts", ["campaign_id"])

    # --- Canonical Jobs ---
    op.create_table(
        "canonical_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "campaign_id",
            UUID(as_uuid=True),
            sa.ForeignKey("search_campaigns.id"),
            nullable=False,
        ),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("company", sa.String(255), nullable=False),
        sa.Column("location", sa.String(255)),
        sa.Column("is_remote", sa.Boolean, default=False),
        sa.Column("description", sa.Text),
        sa.Column("required_skills", JSONB),
        sa.Column("preferred_skills", JSONB),
        sa.Column("min_experience_years", sa.Integer),
        sa.Column("max_experience_years", sa.Integer),
        sa.Column("salary_min", sa.Integer),
        sa.Column("salary_max", sa.Integer),
        sa.Column("salary_currency", sa.String(8)),
        sa.Column("posted_date", sa.DateTime),
        sa.Column("application_url_board", sa.Text),
        sa.Column("application_url_employer", sa.Text),
        sa.Column("apply_channel", sa.String(32)),
        sa.Column("source_refs", JSONB),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("embedding_id", sa.String(128)),
        sa.Column("risk_flags", JSONB),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_canonical_jobs_campaign", "canonical_jobs", ["campaign_id"])
    op.create_index("idx_canonical_jobs_content_hash", "canonical_jobs", ["content_hash"])

    # --- Job Matches ---
    op.create_table(
        "job_matches",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "campaign_id",
            UUID(as_uuid=True),
            sa.ForeignKey("search_campaigns.id"),
            nullable=False,
        ),
        sa.Column(
            "job_id", UUID(as_uuid=True), sa.ForeignKey("canonical_jobs.id"), nullable=False
        ),
        sa.Column("final_score", sa.Float, nullable=False),
        sa.Column("tier", sa.String(16), nullable=False),
        sa.Column("score_breakdown", JSONB, nullable=False),
        sa.Column("reasoning_trace", sa.Text),
        sa.Column("skill_gaps", JSONB),
        sa.Column("user_decision", sa.String(32)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index(
        "idx_matches_campaign_score", "job_matches", ["campaign_id", sa.text("final_score DESC")]
    )

    # --- Companies ---
    op.create_table(
        "companies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("domain", sa.String(255)),
        sa.Column("industry", sa.String(128)),
        sa.Column("size_range", sa.String(64)),
        sa.Column("research_data", JSONB),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # --- Outreach Contacts ---
    op.create_table(
        "outreach_contacts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "campaign_id",
            UUID(as_uuid=True),
            sa.ForeignKey("search_campaigns.id"),
            nullable=False,
        ),
        sa.Column(
            "job_id", UUID(as_uuid=True), sa.ForeignKey("canonical_jobs.id"), nullable=False
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("title", sa.String(255)),
        sa.Column("company", sa.String(255)),
        sa.Column("linkedin_url", sa.Text),
        sa.Column("email", sa.String(255)),
        sa.Column("contact_type", sa.String(32)),
        sa.Column("priority_rank", sa.Integer, default=0),
        sa.Column("message_draft", sa.Text),
        sa.Column("message_status", sa.String(32), default="draft"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index(
        "idx_contacts_campaign_job", "outreach_contacts", ["campaign_id", "job_id"]
    )

    # --- Approval Tasks ---
    op.create_table(
        "approval_tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "campaign_id",
            UUID(as_uuid=True),
            sa.ForeignKey("search_campaigns.id"),
            nullable=False,
        ),
        sa.Column("approval_type", sa.String(64), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("status", sa.String(32), default="pending"),
        sa.Column("decided_at", sa.DateTime),
        sa.Column("decision_notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # --- User Actions ---
    op.create_table(
        "user_actions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action_type", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(128), nullable=False),
        sa.Column("action_data", JSONB),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index(
        "idx_user_actions_user", "user_actions", ["user_id", sa.text("created_at DESC")]
    )

    # --- Audit Logs ---
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True)),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("resource_id", sa.String(128)),
        sa.Column("details", JSONB),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("user_actions")
    op.drop_table("approval_tasks")
    op.drop_table("outreach_contacts")
    op.drop_table("companies")
    op.drop_table("job_matches")
    op.drop_table("canonical_jobs")
    op.drop_table("raw_job_artifacts")
    op.drop_table("source_policies")
    op.drop_table("search_campaigns")
    op.drop_table("candidate_preferences")
    op.drop_table("resumes")
    op.drop_table("users")
