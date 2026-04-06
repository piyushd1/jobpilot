"""Smoke tests to verify the project scaffold is correctly set up."""

import pytest

pytestmark = pytest.mark.unit


def test_imports():
    """Verify all core packages are importable."""
    from src.config.settings import settings
    from src.models.enums import CampaignStatus, MatchTier, TaskStatus, TaskType

    assert settings.app_env == "development"
    assert TaskType.PARSE_RESUME == "parse_resume"
    assert TaskStatus.PENDING == "pending"
    assert CampaignStatus.CREATED == "created"
    assert MatchTier.STRONG == "strong"


def test_candidate_profile_validation():
    """Verify CandidateProfile Pydantic model validates correctly."""
    from src.models.schemas import CandidateProfile

    profile = CandidateProfile(full_name="Test User", skills=["Python", "Go"])
    assert profile.full_name == "Test User"
    assert len(profile.skills) == 2
    assert profile.open_to_remote is True


def test_job_description_validation():
    """Verify JobDescription Pydantic model validates correctly."""
    from src.models.schemas import JobDescription

    jd = JobDescription(title="SWE", company="ACME", required_skills=["Python"])
    assert jd.title == "SWE"
    assert jd.company == "ACME"


def test_score_breakdown_defaults():
    """Verify ScoreBreakdown defaults to zero scores."""
    from src.models.schemas import ScoreBreakdown

    breakdown = ScoreBreakdown()
    assert breakdown.final_score == 0.0
    assert breakdown.tier == "weak"
