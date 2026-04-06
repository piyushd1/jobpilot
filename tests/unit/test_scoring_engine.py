"""Unit tests for the multi-signal scoring engine."""

import pytest
from datetime import datetime, timezone, timedelta

from src.scoring.engine import MatchScoringEngine
from src.models.schemas import CandidateProfile, JobDescription, WorkExperience

pytestmark = pytest.mark.unit


@pytest.fixture
def engine():
    return MatchScoringEngine()


@pytest.fixture
def candidate():
    return CandidateProfile(
        full_name="Jane Doe",
        location="Bangalore, India",
        skills=["Python", "Kubernetes", "PostgreSQL", "Redis", "AWS", "Docker", "Kafka"],
        skills_normalized=["python", "kubernetes", "postgresql", "redis", "aws", "docker", "kafka"],
        target_roles=["Senior Software Engineer", "Backend Lead"],
        target_companies=["Google", "Microsoft"],
        target_locations=["Bangalore", "Remote"],
        open_to_remote=True,
        total_experience_years=8.0,
        work_experience=[
            WorkExperience(company="Acme Corp", title="Senior Software Engineer"),
        ],
    )


@pytest.fixture
def job():
    return JobDescription(
        title="Senior Backend Engineer",
        company="TechCorp",
        location="Bangalore, India",
        required_skills=["Python", "Kubernetes", "PostgreSQL", "AWS"],
        preferred_skills=["Kafka", "gRPC", "Go"],
        min_experience_years=5,
        max_experience_years=10,
        source_platform="naukri",
        posted_date=datetime.now(timezone.utc) - timedelta(days=3),
    )


def test_compute_final_score_returns_breakdown(engine, candidate, job):
    result = engine.compute_final_score(candidate, job)
    assert 0.0 <= result.final_score <= 1.0
    assert result.tier in ("strong", "good", "partial", "weak")
    assert result.reasoning_trace != ""


def test_experience_in_range_scores_1(engine, candidate, job):
    result = engine.compute_final_score(candidate, job)
    assert result.experience_fit_score == 1.0


def test_experience_outside_range_decays(engine, candidate, job):
    candidate.total_experience_years = 2.0
    result = engine.compute_final_score(candidate, job)
    assert result.experience_fit_score < 1.0
    assert result.experience_fit_score > 0.0


def test_location_remote_match(engine, candidate, job):
    job.is_remote = True
    result = engine.compute_final_score(candidate, job)
    assert result.location_fit_score == 1.0


def test_company_exact_match(engine, candidate, job):
    job.company = "Google"
    result = engine.compute_final_score(candidate, job)
    assert result.company_preference_score == 1.0


def test_company_no_match(engine, candidate, job):
    job.company = "RandomStartup"
    result = engine.compute_final_score(candidate, job)
    assert result.company_preference_score < 0.5


def test_recency_fresh_job_high_score(engine, candidate, job):
    job.posted_date = datetime.now(timezone.utc) - timedelta(days=1)
    result = engine.compute_final_score(candidate, job)
    assert result.recency_score > 0.9


def test_recency_old_job_low_score(engine, candidate, job):
    job.posted_date = datetime.now(timezone.utc) - timedelta(days=60)
    result = engine.compute_final_score(candidate, job)
    assert result.recency_score < 0.2


def test_tier_classification(engine, candidate, job):
    # With good skills match + experience + location, should be at least partial
    result = engine.compute_final_score(candidate, job)
    assert result.tier in ("strong", "good", "partial")


def test_semantic_score_zero_without_embeddings(engine, candidate, job):
    result = engine.compute_final_score(candidate, job)
    assert result.semantic_similarity_score == 0.0


def test_source_confidence_naukri(engine, candidate, job):
    result = engine.compute_final_score(candidate, job)
    # naukri should have some confidence from the registry
    assert result.source_confidence_score > 0.0


def test_gap_identification(engine, candidate, job):
    job.required_skills = ["Python", "Kubernetes", "Scala", "Spark"]
    gaps = engine._identify_gaps(candidate, job)
    gap_skills = [g for g in gaps if "scala" in g.lower() or "spark" in g.lower()]
    assert len(gap_skills) > 0
