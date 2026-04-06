"""Unit tests for the multi-signal scoring engine.

Covers:
  - Individual signal scorers with known inputs/expected outputs
  - Weighted aggregation
  - Tier classification (STRONG >= 0.80, GOOD >= 0.60, PARTIAL >= 0.40, WEAK < 0.40)
  - Conflict arbitration (high semantic but low hard skill -> cap at GOOD)
  - User weight override / custom graph injection
"""

import math
from datetime import datetime, timedelta, timezone

import pytest

from src.models.enums import MatchTier
from src.models.schemas import CandidateProfile, JobDescription, ScoreBreakdown, WorkExperience
from src.scoring.engine import MatchScoringEngine, _cosine_similarity

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_candidate(**overrides) -> CandidateProfile:
    defaults = dict(
        full_name="Test Candidate",
        skills=["Python", "Kubernetes", "PostgreSQL", "AWS", "Docker"],
        skills_normalized=["python", "kubernetes", "postgresql", "aws", "docker"],
        target_roles=["Senior Software Engineer"],
        target_companies=[],
        target_locations=[],
        open_to_remote=True,
        total_experience_years=6.0,
        location="San Francisco, CA",
    )
    defaults.update(overrides)
    return CandidateProfile(**defaults)


def _make_job(**overrides) -> JobDescription:
    defaults = dict(
        title="Senior Software Engineer",
        company="Acme Corp",
        location="San Francisco, CA",
        is_remote=False,
        required_skills=["Python", "Kubernetes", "PostgreSQL"],
        preferred_skills=["AWS", "Docker"],
        min_experience_years=4,
        max_experience_years=8,
        source_platform="linkedin",
        posted_date=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return JobDescription(**defaults)


@pytest.fixture
def engine():
    return MatchScoringEngine()


@pytest.fixture
def candidate():
    return CandidateProfile(
        full_name="Jane Doe",
        location="Bangalore, India",
        skills=[
            "Python", "Kubernetes", "PostgreSQL", "Redis", "AWS", "Docker", "Kafka",
        ],
        skills_normalized=[
            "python", "kubernetes", "postgresql", "redis", "aws", "docker", "kafka",
        ],
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


# ===================================================================
# Cosine similarity helper
# ===================================================================


class TestCosineSimilarity:
    def test_identical_vectors(self):
        assert _cosine_similarity([1, 0, 0], [1, 0, 0]) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        assert _cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)

    def test_opposite_vectors_clamped_to_zero(self):
        result = _cosine_similarity([1, 0], [-1, 0])
        assert result == pytest.approx(0.0)

    def test_empty_vectors(self):
        assert _cosine_similarity([], []) == 0.0

    def test_mismatched_lengths(self):
        assert _cosine_similarity([1, 2], [1]) == 0.0

    def test_zero_vector(self):
        assert _cosine_similarity([0, 0], [1, 1]) == 0.0


# ===================================================================
# Individual signal scorers
# ===================================================================


class TestScoreSkills:
    def test_perfect_overlap(self, engine):
        cand = _make_candidate(
            skills=["Python", "Kubernetes", "PostgreSQL", "AWS", "Docker"],
            skills_normalized=["python", "kubernetes", "postgresql", "aws", "docker"],
        )
        job = _make_job(
            required_skills=["Python", "Kubernetes", "PostgreSQL"],
            preferred_skills=["AWS", "Docker"],
        )
        score, reasons = engine._score_skills(cand, job)
        # Jaccard = 5/5 = 1.0, adj = 0, semantic = 0 -> 0.40
        assert score == pytest.approx(0.40, abs=0.05)
        assert any("Jaccard" in r for r in reasons)

    def test_no_jd_skills_defaults_half(self, engine):
        cand = _make_candidate()
        job = _make_job(required_skills=[], preferred_skills=[])
        score, reasons = engine._score_skills(cand, job)
        assert score == pytest.approx(0.5)

    def test_partial_overlap_with_adjacency(self, engine):
        cand = _make_candidate(skills=["Docker"], skills_normalized=["docker"])
        job = _make_job(required_skills=["Kubernetes"], preferred_skills=[])
        score, reasons = engine._score_skills(cand, job)
        # adj(docker, kubernetes) = 0.8 -> 0.40*0.0 + 0.40*0.8 + 0.20*0 = 0.32
        assert score == pytest.approx(0.32, abs=0.05)

    def test_with_semantic_embedding(self, engine):
        cand = _make_candidate(skills=["Python"], skills_normalized=["python"])
        job = _make_job(required_skills=["Python"], preferred_skills=[])
        emb = [1.0, 0.0, 0.0]
        score, _ = engine._score_skills(
            cand, job, candidate_embedding=emb, job_skills_embedding=emb,
        )
        # Jaccard 1.0, adj 0, semantic 1.0 -> 0.40*1 + 0.40*0 + 0.20*1 = 0.60
        assert score == pytest.approx(0.60, abs=0.05)


class TestScoreTitleAlignment:
    def test_exact_match_no_embeddings(self, engine):
        cand = _make_candidate(target_roles=["Senior Software Engineer"])
        job = _make_job(title="Senior Software Engineer")
        score, _ = engine._score_title_alignment(cand, job)
        assert score == pytest.approx(1.0)

    def test_substring_match(self, engine):
        cand = _make_candidate(target_roles=["Software Engineer"])
        job = _make_job(title="Senior Software Engineer")
        score, _ = engine._score_title_alignment(cand, job)
        assert score >= 0.70

    def test_word_overlap_partial(self, engine):
        cand = _make_candidate(target_roles=["Backend Engineer"])
        job = _make_job(title="Software Engineer")
        score, _ = engine._score_title_alignment(cand, job)
        assert score > 0.0

    def test_no_match(self, engine):
        cand = _make_candidate(target_roles=["Data Scientist"])
        job = _make_job(title="Frontend Developer")
        score, _ = engine._score_title_alignment(cand, job)
        assert score < 0.5

    def test_with_embeddings(self, engine):
        cand = _make_candidate(target_roles=["Any"])
        job = _make_job(title="Any")
        emb = [0.5, 0.5, 0.5]
        score, _ = engine._score_title_alignment(
            cand, job, candidate_title_embedding=emb, job_title_embedding=emb,
        )
        assert score == pytest.approx(1.0, abs=0.01)


class TestScoreExperienceFit:
    def test_within_range(self, engine):
        cand = _make_candidate(total_experience_years=6.0)
        job = _make_job(min_experience_years=4, max_experience_years=8)
        score, _ = engine._score_experience_fit(cand, job)
        assert score == pytest.approx(1.0)

    def test_below_range_gaussian_decay(self, engine):
        cand = _make_candidate(total_experience_years=2.0)
        job = _make_job(min_experience_years=4, max_experience_years=8)
        score, _ = engine._score_experience_fit(cand, job)
        expected = math.exp(-0.5)
        assert score == pytest.approx(expected, abs=0.01)

    def test_above_range_gaussian_decay(self, engine):
        cand = _make_candidate(total_experience_years=12.0)
        job = _make_job(min_experience_years=4, max_experience_years=8)
        score, _ = engine._score_experience_fit(cand, job)
        expected = math.exp(-2.0)
        assert score == pytest.approx(expected, abs=0.01)

    def test_unknown_candidate_experience(self, engine):
        cand = _make_candidate(total_experience_years=None)
        job = _make_job(min_experience_years=4, max_experience_years=8)
        score, _ = engine._score_experience_fit(cand, job)
        assert score == pytest.approx(0.5)

    def test_no_jd_range_defaults_high(self, engine):
        cand = _make_candidate(total_experience_years=5.0)
        job = _make_job(min_experience_years=None, max_experience_years=None)
        score, _ = engine._score_experience_fit(cand, job)
        assert score == pytest.approx(0.8)

    def test_only_min_set(self, engine):
        cand = _make_candidate(total_experience_years=7.0)
        job = _make_job(min_experience_years=5, max_experience_years=None)
        score, _ = engine._score_experience_fit(cand, job)
        assert score == pytest.approx(1.0)


class TestScoreSemanticSimilarity:
    def test_with_embeddings(self, engine):
        emb = [1.0, 0.0, 0.0]
        score, _ = engine._score_semantic_sim(profile_embedding=emb, jd_embedding=emb)
        assert score == pytest.approx(1.0)

    def test_without_embeddings(self, engine):
        score, reasons = engine._score_semantic_sim()
        assert score == pytest.approx(0.0)
        assert any("N/A" in r for r in reasons)


class TestScoreCompanyPreference:
    def test_exact_match(self, engine):
        cand = _make_candidate(target_companies=["Google"])
        job = _make_job(company="Google")
        score, _ = engine._score_company_preference(cand, job)
        assert score == pytest.approx(1.0)

    def test_partial_match(self, engine):
        cand = _make_candidate(target_companies=["Google"])
        job = _make_job(company="Google Cloud")
        score, _ = engine._score_company_preference(cand, job)
        assert score == pytest.approx(0.70)

    def test_no_match(self, engine):
        cand = _make_candidate(target_companies=["Apple"])
        job = _make_job(company="Google")
        score, _ = engine._score_company_preference(cand, job)
        assert score == pytest.approx(0.0)

    def test_no_target_companies(self, engine):
        cand = _make_candidate(target_companies=[])
        job = _make_job(company="Google")
        score, _ = engine._score_company_preference(cand, job)
        assert score == pytest.approx(0.5)


class TestScoreLocationFit:
    def test_remote_job_open_to_remote(self, engine):
        cand = _make_candidate(open_to_remote=True)
        job = _make_job(is_remote=True)
        score, _ = engine._score_location_fit(cand, job)
        assert score == pytest.approx(1.0)

    def test_remote_job_not_open_to_remote(self, engine):
        cand = _make_candidate(open_to_remote=False)
        job = _make_job(is_remote=True)
        score, _ = engine._score_location_fit(cand, job)
        assert score == pytest.approx(0.90)

    def test_same_city(self, engine):
        cand = _make_candidate(location="San Francisco")
        job = _make_job(is_remote=False, location="San Francisco, CA")
        score, _ = engine._score_location_fit(cand, job)
        assert score == pytest.approx(1.0)

    def test_target_location_match(self, engine):
        cand = _make_candidate(location="New York", target_locations=["San Francisco"])
        job = _make_job(is_remote=False, location="San Francisco, CA")
        score, _ = engine._score_location_fit(cand, job)
        assert score == pytest.approx(0.90)

    def test_location_mismatch_open_remote(self, engine):
        cand = _make_candidate(
            location="London", target_locations=[], open_to_remote=True,
        )
        job = _make_job(is_remote=False, location="New York")
        score, _ = engine._score_location_fit(cand, job)
        assert score == pytest.approx(0.40)

    def test_location_mismatch_not_remote(self, engine):
        cand = _make_candidate(
            location="London", target_locations=[], open_to_remote=False,
        )
        job = _make_job(is_remote=False, location="New York")
        score, _ = engine._score_location_fit(cand, job)
        assert score == pytest.approx(0.10)

    def test_no_jd_location(self, engine):
        cand = _make_candidate()
        job = _make_job(is_remote=False, location="")
        score, _ = engine._score_location_fit(cand, job)
        assert score == pytest.approx(0.5)


class TestScoreRecency:
    def test_just_posted(self, engine):
        now = datetime.now(timezone.utc)
        job = _make_job(posted_date=now)
        score, _ = engine._score_recency(job, reference_date=now)
        assert score == pytest.approx(1.0, abs=0.01)

    def test_14_days_half_life(self, engine):
        now = datetime.now(timezone.utc)
        job = _make_job(posted_date=now - timedelta(days=14))
        score, _ = engine._score_recency(job, reference_date=now)
        assert score == pytest.approx(0.5, abs=0.05)

    def test_28_days_quarter(self, engine):
        now = datetime.now(timezone.utc)
        job = _make_job(posted_date=now - timedelta(days=28))
        score, _ = engine._score_recency(job, reference_date=now)
        assert score == pytest.approx(0.25, abs=0.05)

    def test_no_posted_date(self, engine):
        job = _make_job(posted_date=None)
        score, _ = engine._score_recency(job)
        assert score == pytest.approx(0.5)

    def test_naive_datetime_handled(self, engine):
        now = datetime.now(timezone.utc)
        job = _make_job(posted_date=datetime(2024, 1, 1))
        score, _ = engine._score_recency(job, reference_date=now)
        assert 0.0 <= score <= 1.0


class TestScoreSourceConfidence:
    def test_linkedin(self, engine):
        job = _make_job(source_platform="linkedin")
        score, _ = engine._score_source_confidence(job)
        assert score == pytest.approx(0.90)

    def test_indeed(self, engine):
        job = _make_job(source_platform="indeed")
        score, _ = engine._score_source_confidence(job)
        assert score == pytest.approx(0.75)

    def test_employer_ats(self, engine):
        job = _make_job(source_platform="employer_ats")
        score, _ = engine._score_source_confidence(job)
        assert score == pytest.approx(1.0)

    def test_unknown_source(self, engine):
        job = _make_job(source_platform="some_random_site")
        score, _ = engine._score_source_confidence(job)
        assert score == pytest.approx(0.40)

    def test_none_source(self, engine):
        job = _make_job(source_platform=None)
        score, _ = engine._score_source_confidence(job)
        assert score == pytest.approx(0.40)


# ===================================================================
# Weighted aggregation
# ===================================================================


class TestWeightedAggregation:
    def test_final_score_in_valid_range(self, engine):
        result = engine.compute_final_score(_make_candidate(), _make_job())
        assert 0.0 <= result.final_score <= 1.0

    def test_returns_score_breakdown_type(self, engine):
        result = engine.compute_final_score(_make_candidate(), _make_job())
        assert isinstance(result, ScoreBreakdown)

    def test_all_signal_scores_populated(self, engine):
        result = engine.compute_final_score(_make_candidate(), _make_job())
        assert result.skills_score >= 0.0
        assert result.title_alignment_score >= 0.0
        assert result.experience_fit_score >= 0.0
        assert result.semantic_similarity_score >= 0.0
        assert result.company_preference_score >= 0.0
        assert result.location_fit_score >= 0.0
        assert result.recency_score >= 0.0
        assert result.source_confidence_score >= 0.0

    def test_reasoning_trace_populated(self, engine):
        result = engine.compute_final_score(_make_candidate(), _make_job())
        assert len(result.reasoning_trace) > 0


# ===================================================================
# Integration tests using the conftest fixtures
# ===================================================================


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


def test_semantic_score_zero_without_embeddings(engine, candidate, job):
    result = engine.compute_final_score(candidate, job)
    assert result.semantic_similarity_score == 0.0


def test_source_confidence_naukri(engine, candidate, job):
    result = engine.compute_final_score(candidate, job)
    # naukri is not in the registry -> falls back to 'unknown' -> 0.40
    assert result.source_confidence_score > 0.0


# ===================================================================
# Tier classification
# ===================================================================


class TestTierClassification:
    def test_strong_tier(self, engine):
        cand = _make_candidate(
            skills=[
                "Python", "Kubernetes", "PostgreSQL", "AWS", "Docker", "Kafka", "gRPC",
            ],
            skills_normalized=[
                "python", "kubernetes", "postgresql", "aws", "docker", "kafka", "grpc",
            ],
            target_roles=["Senior Software Engineer"],
            target_companies=["Acme Corp"],
            location="San Francisco, CA",
            total_experience_years=6.0,
        )
        job = _make_job(
            title="Senior Software Engineer",
            company="Acme Corp",
            location="San Francisco, CA",
            is_remote=False,
            required_skills=["Python", "Kubernetes", "PostgreSQL"],
            preferred_skills=["AWS", "Docker"],
            min_experience_years=4,
            max_experience_years=8,
            source_platform="employer_ats",
            posted_date=datetime.now(timezone.utc),
        )
        # Provide high-quality embeddings to boost semantic and skill signals
        emb = [1.0, 0.0, 0.0]
        result = engine.compute_final_score(
            cand, job,
            candidate_skills_embedding=emb,
            job_skills_embedding=emb,
            candidate_title_embedding=emb,
            job_title_embedding=emb,
            profile_embedding=emb,
            jd_embedding=emb,
        )
        assert result.tier == MatchTier.STRONG.value

    def test_weak_tier(self, engine):
        cand = _make_candidate(
            skills=["Cobol", "Fortran"],
            skills_normalized=["cobol", "fortran"],
            target_roles=["Data Scientist"],
            target_companies=[],
            location="London",
            open_to_remote=False,
            total_experience_years=1.0,
        )
        job = _make_job(
            title="Senior Frontend Engineer",
            company="SomeCorp",
            location="Tokyo, Japan",
            is_remote=False,
            required_skills=["React", "TypeScript", "CSS"],
            preferred_skills=["Next.js", "GraphQL"],
            min_experience_years=8,
            max_experience_years=12,
            source_platform="unknown",
            posted_date=datetime.now(timezone.utc) - timedelta(days=60),
        )
        result = engine.compute_final_score(cand, job)
        assert result.tier == MatchTier.WEAK.value

    def test_tier_is_valid_enum_value(self, engine):
        result = engine.compute_final_score(_make_candidate(), _make_job())
        assert result.tier in {t.value for t in MatchTier}

    def test_tier_classification_general(self, engine, candidate, job):
        result = engine.compute_final_score(candidate, job)
        assert result.tier in ("strong", "good", "partial")


# ===================================================================
# Conflict arbitration
# ===================================================================


class TestConflictArbitration:
    def test_high_semantic_low_hard_overlap_not_strong(self, engine):
        cand = _make_candidate(
            skills=["Cobol", "Fortran", "Assembly"],
            skills_normalized=["cobol", "fortran", "assembly"],
            target_roles=["Senior Software Engineer"],
            target_companies=["Acme Corp"],
            location="San Francisco, CA",
            total_experience_years=6.0,
        )
        job = _make_job(
            title="Senior Software Engineer",
            company="Acme Corp",
            location="San Francisco, CA",
            required_skills=["Python", "Kubernetes", "PostgreSQL", "AWS"],
            preferred_skills=["Docker", "Kafka", "gRPC", "Go"],
            min_experience_years=4,
            max_experience_years=8,
            source_platform="employer_ats",
            posted_date=datetime.now(timezone.utc),
        )
        result = engine.compute_final_score(
            cand, job,
            profile_embedding=[1.0, 0.0, 0.0],
            jd_embedding=[0.95, 0.05, 0.0],
        )
        # Zero hard skill overlap + high semantic => should never be STRONG
        assert result.tier != MatchTier.STRONG.value


# ===================================================================
# Gap identification
# ===================================================================


class TestGapIdentification:
    def test_missing_skills_identified(self, engine):
        cand = _make_candidate(skills=["Python"], skills_normalized=["python"])
        job = _make_job(required_skills=["Python", "Kubernetes", "PostgreSQL"])
        result = engine.compute_final_score(cand, job)
        trace_lower = result.reasoning_trace.lower()
        assert "kubernetes" in trace_lower or "postgresql" in trace_lower

    def test_no_gaps_when_all_matched(self, engine):
        cand = _make_candidate(
            skills=["Python", "Kubernetes", "PostgreSQL"],
            skills_normalized=["python", "kubernetes", "postgresql"],
        )
        job = _make_job(
            required_skills=["Python", "Kubernetes", "PostgreSQL"],
            preferred_skills=[],
        )
        result = engine.compute_final_score(cand, job)
        assert "Missing" not in result.reasoning_trace or "Skill gaps" not in result.reasoning_trace

    def test_gap_identification_via_method(self, engine, candidate, job):
        job.required_skills = ["Python", "Kubernetes", "Scala", "Spark"]
        gaps = engine._identify_gaps(candidate, job)
        gap_skills = [g for g in gaps if "scala" in g.lower() or "spark" in g.lower()]
        assert len(gap_skills) > 0
