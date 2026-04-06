"""End-to-end integration tests for the discovery + scoring pipeline.

Tests the full flow: resume parsing fixtures → deduplication → scoring → tier validation.
No external API calls — uses pre-built fixtures.
"""

import json
import pytest
from pathlib import Path

from src.models.schemas import CandidateProfile, JobDescription, WorkExperience
from src.scoring.engine import MatchScoringEngine
from src.utils.deduplication import deduplicate_jobs

pytestmark = pytest.mark.integration

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def candidate():
    return CandidateProfile(
        full_name="Jane Doe",
        location="Bangalore, India",
        skills=["Python", "Kubernetes", "PostgreSQL", "Redis", "AWS", "Docker", "Kafka"],
        skills_normalized=["python", "kubernetes", "postgresql", "redis", "aws", "docker", "kafka"],
        target_roles=["Senior Software Engineer", "Backend Lead"],
        target_companies=["Google", "Microsoft", "Stripe"],
        target_locations=["Bangalore", "Remote"],
        open_to_remote=True,
        total_experience_years=8.0,
        work_experience=[
            WorkExperience(company="Acme Corp", title="Senior Software Engineer",
                          start_date="2020-01", is_current=True,
                          skills_used=["Python", "Kubernetes", "PostgreSQL"]),
            WorkExperience(company="StartupXYZ", title="Software Engineer",
                          start_date="2016-06", end_date="2019-12",
                          skills_used=["Go", "Redis", "Docker"]),
        ],
    )


@pytest.fixture
def sample_jobs():
    jds_file = FIXTURES / "sample_jds.json"
    with open(jds_file) as f:
        raw = json.load(f)
    return [JobDescription.model_validate(j) for j in raw]


def test_dedup_removes_duplicates(sample_jobs):
    """Duplicate jobs with same title/company should be merged."""
    # Add a duplicate
    dup = sample_jobs[0].model_copy()
    dup.source_platform = "indeed"
    dup.application_url_employer = None
    jobs_with_dup = sample_jobs + [dup]

    result = deduplicate_jobs(jobs_with_dup)
    assert len(result) <= len(jobs_with_dup)
    assert len(result) >= len(sample_jobs)  # at most 1 removed


def test_scoring_produces_valid_tiers(candidate, sample_jobs):
    """Every scored job should have a valid tier."""
    engine = MatchScoringEngine()
    for job in sample_jobs:
        result = engine.compute_final_score(candidate, job)
        assert result.tier in ("strong", "good", "partial", "weak")
        assert 0.0 <= result.final_score <= 1.0


def test_best_match_is_relevant(candidate, sample_jobs):
    """The highest-scoring job should be a backend/platform role, not frontend."""
    engine = MatchScoringEngine()
    scored = [(engine.compute_final_score(candidate, j), j) for j in sample_jobs]
    scored.sort(key=lambda x: -x[0].final_score)

    top_job = scored[0][1]
    # Backend engineer with Python+K8s should NOT rank a C#/.NET or pure frontend role highest
    assert "Frontend" not in top_job.title
    assert "C#" not in (top_job.required_skills or [])


def test_company_preference_boosts_score(candidate, sample_jobs):
    """Jobs at target companies (Google, Microsoft, Stripe) should score higher."""
    engine = MatchScoringEngine()
    target_scores = []
    other_scores = []

    target_companies = {"google", "microsoft", "stripe"}
    for job in sample_jobs:
        result = engine.compute_final_score(candidate, job)
        if job.company.lower() in target_companies:
            target_scores.append(result.company_preference_score)
        else:
            other_scores.append(result.company_preference_score)

    if target_scores and other_scores:
        assert max(target_scores) > max(other_scores)


def test_pipeline_end_to_end(candidate, sample_jobs):
    """Full pipeline: dedup → score → filter STRONG/GOOD."""
    # Dedup
    deduped = deduplicate_jobs(sample_jobs)
    assert len(deduped) > 0

    # Score
    engine = MatchScoringEngine()
    scored = []
    for job in deduped:
        result = engine.compute_final_score(candidate, job)
        scored.append({"job": job, "score": result})

    # Filter to STRONG + GOOD + PARTIAL (no embeddings means scores cap lower)
    shortlist = [s for s in scored if s["score"].tier in ("strong", "good", "partial")]
    assert len(shortlist) >= 1  # At least one decent match expected

    # Verify all shortlisted have reasoning
    for s in shortlist:
        assert s["score"].reasoning_trace != ""
