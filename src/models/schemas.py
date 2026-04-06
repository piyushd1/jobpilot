"""Shared Pydantic models used across agents and services."""

from datetime import datetime

from pydantic import BaseModel, Field


class CandidateProfile(BaseModel):
    """Structured output from resume parsing (Agent 1 output schema)."""

    full_name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    summary: str | None = None

    # Target preferences
    target_roles: list[str] = Field(default_factory=list)
    target_companies: list[str] = Field(default_factory=list)
    target_locations: list[str] = Field(default_factory=list)
    open_to_remote: bool = True
    min_experience_years: int | None = None
    max_experience_years: int | None = None

    # Skills
    skills: list[str] = Field(default_factory=list)
    skills_normalized: list[str] = Field(default_factory=list)

    # Experience
    work_experience: list["WorkExperience"] = Field(default_factory=list)
    total_experience_years: float | None = None

    # Education
    education: list["Education"] = Field(default_factory=list)

    # Certifications
    certifications: list[str] = Field(default_factory=list)


class WorkExperience(BaseModel):
    """A single work experience entry."""

    company: str
    title: str
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False
    description: str | None = None
    skills_used: list[str] = Field(default_factory=list)
    location: str | None = None


class Education(BaseModel):
    """A single education entry."""

    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    graduation_year: int | None = None


class JobDescription(BaseModel):
    """Normalized job description, stored as canonical_jobs."""

    title: str
    company: str
    location: str | None = None
    is_remote: bool = False
    description: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    min_experience_years: int | None = None
    max_experience_years: int | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str | None = None
    posted_date: datetime | None = None
    application_url_board: str | None = None
    application_url_employer: str | None = None
    source_platform: str | None = None
    content_hash: str | None = None


class ScoreBreakdown(BaseModel):
    """Detailed scoring breakdown for a job match."""

    skills_score: float = 0.0
    title_alignment_score: float = 0.0
    experience_fit_score: float = 0.0
    semantic_similarity_score: float = 0.0
    company_preference_score: float = 0.0
    location_fit_score: float = 0.0
    recency_score: float = 0.0
    source_confidence_score: float = 0.0
    final_score: float = 0.0
    tier: str = "weak"
    reasoning_trace: str = ""


class ReasoningTrace(BaseModel):
    """Structured reasoning trace from agent execution."""

    agent_name: str
    task_type: str
    input_summary: str
    steps: list[str] = Field(default_factory=list)
    output_summary: str
    token_usage: dict[str, int] = Field(default_factory=dict)
    duration_seconds: float = 0.0


class RawJobArtifact(BaseModel):
    """Raw job data as fetched from a source, before deduplication."""

    job_id: str = ""
    source_platform: str = ""
    title: str = ""
    company: str = ""
    description_raw: str = ""
    application_url: str = ""
    scraped_at: str = ""
    location: str | None = None
    salary_range: str | None = None
    experience_range: str | None = None
