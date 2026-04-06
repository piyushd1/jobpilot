"""Unit tests for the deduplication engine.

Covers:
  - Exact hash matching (identical normalized jobs produce same hash)
  - Fuzzy threshold (near-duplicate titles with slight variation -> merge)
  - Non-duplicate cases (different jobs stay separate)
  - Canonical URL preference (employer URL preferred over board)
  - normalize_title, normalize_company, normalize_location
"""

import pytest

from src.models.schemas import JobDescription
from src.utils.canonicalization import (
    normalize_company,
    normalize_location,
    normalize_title,
)
from src.utils.deduplication import deduplicate_jobs
from src.utils.hashing import compute_job_hash

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_job(**overrides) -> JobDescription:
    defaults = dict(
        title="Software Engineer",
        company="Acme Corp",
        location="San Francisco, CA",
        required_skills=["Python"],
        preferred_skills=[],
        source_platform="linkedin",
    )
    defaults.update(overrides)
    return JobDescription(**defaults)


# ===================================================================
# normalize_title
# ===================================================================


class TestNormalizeTitle:
    def test_strips_senior(self):
        assert normalize_title("Sr. Software Engineer") == "Software Engineer"

    def test_strips_junior(self):
        result = normalize_title("Junior Data Scientist")
        assert "Junior" not in result and "junior" not in result

    def test_strips_lead(self):
        result = normalize_title("Lead Backend Engineer")
        assert "Lead" not in result

    def test_strips_staff(self):
        result = normalize_title("Staff Software Engineer")
        assert "Staff" not in result

    def test_strips_principal(self):
        result = normalize_title("Principal Engineer")
        assert "Principal" not in result

    def test_strips_roman_numeral_ii(self):
        assert normalize_title("Software Engineer II") == "Software Engineer"

    def test_strips_roman_numeral_iii(self):
        assert normalize_title("Software Engineer III") == "Software Engineer"

    def test_strips_level_numeric(self):
        assert normalize_title("Software Engineer Level 3") == "Software Engineer"

    def test_collapses_whitespace(self):
        result = normalize_title("  JUNIOR   Data  Scientist  ")
        assert result == "Data Scientist"

    def test_title_case(self):
        result = normalize_title("software engineer")
        assert result == "Software Engineer"

    def test_preserves_core(self):
        result = normalize_title("Backend Engineer")
        assert "Backend" in result and "Engineer" in result

    def test_preserves_meaningful_words(self):
        assert normalize_title("Machine Learning Engineer") == "Machine Learning Engineer"


# ===================================================================
# normalize_company
# ===================================================================


class TestNormalizeCompany:
    def test_strips_inc(self):
        assert normalize_company("Google Inc.") == "Google"

    def test_strips_llc(self):
        assert normalize_company("Acme LLC") == "Acme"

    def test_strips_pvt_ltd(self):
        result = normalize_company("Infosys Pvt. Ltd.")
        assert "Pvt" not in result and "Ltd" not in result

    def test_strips_tcs_pvt_ltd(self):
        result = normalize_company("Tata Consultancy Services Pvt. Ltd.")
        assert result == "Tata Consultancy Services"

    def test_strips_corporation(self):
        assert normalize_company("Microsoft Corporation") == "Microsoft"

    def test_strips_corp(self):
        assert normalize_company("Intel Corp.") == "Intel"

    def test_strips_ltd(self):
        assert normalize_company("Amazon Ltd") == "Amazon"

    def test_title_case(self):
        assert normalize_company("acme inc") == "Acme"

    def test_preserves_base_name(self):
        assert normalize_company("Stripe") == "Stripe"

    def test_collapses_whitespace(self):
        result = normalize_company("  Acme   Corp  Inc. ")
        assert "  " not in result


# ===================================================================
# normalize_location
# ===================================================================


class TestNormalizeLocation:
    def test_bengaluru_india(self):
        assert normalize_location("Bengaluru, India") == "Bengaluru, India"

    def test_bangalore_alias(self):
        result = normalize_location("Bangalore, IN")
        assert "Bengaluru" in result
        assert "India" in result

    def test_nyc_alias(self):
        result = normalize_location("NYC, US")
        assert "New York" in result
        assert "United States" in result

    def test_sf_alias(self):
        result = normalize_location("SF, US")
        assert "San Francisco" in result

    def test_bombay_alias(self):
        result = normalize_location("Bombay, India")
        assert "Mumbai" in result

    def test_gurgaon_alias(self):
        result = normalize_location("Gurgaon, India")
        assert "Gurugram" in result

    def test_dc_alias(self):
        result = normalize_location("DC, US")
        assert "Washington" in result

    def test_us_state_abbreviation(self):
        result = normalize_location("Austin, TX")
        assert "United States" in result

    def test_empty_string(self):
        assert normalize_location("") == ""

    def test_whitespace_only(self):
        assert normalize_location("   ") == ""

    def test_single_city(self):
        result = normalize_location("London")
        assert result == "London"


# ===================================================================
# compute_job_hash
# ===================================================================


class TestComputeJobHash:
    def test_identical_inputs_same_hash(self):
        h1 = compute_job_hash("Software Engineer", "Google", "San Francisco, CA")
        h2 = compute_job_hash("Software Engineer", "Google", "San Francisco, CA")
        assert h1 == h2

    def test_different_inputs_different_hash(self):
        h1 = compute_job_hash("Software Engineer", "Google", "San Francisco, CA")
        h2 = compute_job_hash("Data Scientist", "Google", "San Francisco, CA")
        assert h1 != h2

    def test_normalization_makes_variants_equal(self):
        h1 = compute_job_hash("Sr. Software Engineer", "Google Inc.", "Bangalore, IN")
        h2 = compute_job_hash("Senior Software Engineer", "Google Inc", "Bengaluru, India")
        assert h1 == h2

    def test_seniority_stripping(self):
        h1 = compute_job_hash("Junior Software Engineer", "Acme", "NYC, US")
        h2 = compute_job_hash("Senior Software Engineer", "Acme", "New York, US")
        assert h1 == h2

    def test_company_suffix_stripping(self):
        h1 = compute_job_hash("Engineer", "Acme Corp.", "London")
        h2 = compute_job_hash("Engineer", "Acme Corporation", "London")
        assert h1 == h2

    def test_hash_format(self):
        h = compute_job_hash("Engineer", "Acme", "NYC")
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex digest
        assert all(c in "0123456789abcdef" for c in h)

    def test_same_job_same_hash_legacy(self):
        h1 = compute_job_hash("Software Engineer", "Google Inc.", "Bangalore, India")
        h2 = compute_job_hash("Software Engineer", "Google Inc", "Bangalore, India")
        assert h1 == h2

    def test_different_jobs_different_hash_legacy(self):
        h1 = compute_job_hash("Software Engineer", "Google", "Bangalore")
        h2 = compute_job_hash("Data Scientist", "Microsoft", "Seattle")
        assert h1 != h2


# ===================================================================
# deduplicate_jobs: exact hash matching
# ===================================================================


class TestExactHashMatching:
    def test_identical_jobs_deduplicated(self):
        job1 = _make_job(title="Software Engineer", company="Google", location="NYC, US")
        job2 = _make_job(title="Software Engineer", company="Google", location="NYC, US")
        result = deduplicate_jobs([job1, job2])
        assert len(result) == 1

    def test_normalized_duplicates_deduplicated(self):
        job1 = _make_job(
            title="Sr. Software Engineer", company="Google Inc.", location="Bangalore, IN",
        )
        job2 = _make_job(
            title="Senior Software Engineer", company="Google Inc", location="Bengaluru, India",
        )
        result = deduplicate_jobs([job1, job2])
        assert len(result) == 1

    def test_richer_record_preferred(self):
        job_sparse = _make_job(
            title="Software Engineer", company="Google", location="NYC",
            description=None, required_skills=[],
        )
        job_rich = _make_job(
            title="Software Engineer", company="Google", location="NYC",
            description="Great opportunity", required_skills=["Python", "Go"],
            preferred_skills=["Kubernetes"],
        )
        result = deduplicate_jobs([job_sparse, job_rich])
        assert len(result) == 1
        assert result[0].description == "Great opportunity"

    def test_content_hash_populated(self):
        job = _make_job()
        result = deduplicate_jobs([job])
        assert len(result) == 1
        assert result[0].content_hash is not None
        assert len(result[0].content_hash) == 64

    def test_employer_url_preserved(self):
        jobs = [
            JobDescription(
                title="Software Engineer", company="Google", location="Bangalore",
                required_skills=["Python"],
                application_url_board="https://board.com/123",
            ),
            JobDescription(
                title="Software Engineer", company="Google Inc.", location="Bangalore, India",
                required_skills=["Python", "Go"],
                application_url_employer="https://google.com/careers/123",
            ),
        ]
        result = deduplicate_jobs(jobs)
        assert len(result) == 1
        assert result[0].content_hash is not None


# ===================================================================
# deduplicate_jobs: fuzzy matching
# ===================================================================


class TestFuzzyMatching:
    def test_near_duplicate_titles_merged(self):
        job1 = _make_job(
            title="Software Engineer - Backend", company="Acme Corp", location="NYC",
        )
        job2 = _make_job(
            title="Software Engineer, Backend", company="Acme Corp", location="NYC",
        )
        result = deduplicate_jobs([job1, job2])
        assert len(result) == 1

    def test_employer_url_preferred_in_merge(self):
        job_board = _make_job(
            title="Software Engineer", company="Acme Corp", location="NYC",
            application_url_board="https://linkedin.com/jobs/123",
            application_url_employer=None,
        )
        job_employer = _make_job(
            title="Software Engineer", company="Acme Corp", location="NYC",
            application_url_board=None,
            application_url_employer="https://acme.com/careers/swe",
        )
        result = deduplicate_jobs([job_board, job_employer])
        assert len(result) == 1
        assert result[0].application_url_employer == "https://acme.com/careers/swe"


# ===================================================================
# Non-duplicate cases
# ===================================================================


class TestNonDuplicateCases:
    def test_different_titles_stay_separate(self):
        job1 = _make_job(title="Software Engineer", company="Acme Corp", location="NYC")
        job2 = _make_job(title="Product Manager", company="Acme Corp", location="NYC")
        result = deduplicate_jobs([job1, job2])
        assert len(result) == 2

    def test_different_companies_stay_separate(self):
        job1 = _make_job(title="Software Engineer", company="Google", location="NYC")
        job2 = _make_job(title="Software Engineer", company="Apple", location="NYC")
        result = deduplicate_jobs([job1, job2])
        assert len(result) == 2

    def test_different_locations_different_hash(self):
        # Same title/company but different locations produce different hashes
        h1 = compute_job_hash("Software Engineer", "Google", "NYC, US")
        h2 = compute_job_hash("Software Engineer", "Google", "London, UK")
        assert h1 != h2

    def test_empty_list(self):
        assert deduplicate_jobs([]) == []

    def test_single_job_passthrough(self):
        job = _make_job()
        result = deduplicate_jobs([job])
        assert len(result) == 1

    def test_different_jobs_not_merged(self):
        jobs = [
            JobDescription(
                title="Software Engineer", company="Google", location="Bangalore",
                required_skills=["Python"],
            ),
            JobDescription(
                title="Data Scientist", company="Microsoft", location="Seattle",
                required_skills=["Python"],
            ),
        ]
        result = deduplicate_jobs(jobs)
        assert len(result) == 2

    def test_single_job_legacy(self):
        jobs = [JobDescription(title="SWE", company="ACME", required_skills=["Go"])]
        result = deduplicate_jobs(jobs)
        assert len(result) == 1
        assert result[0].content_hash is not None


# ===================================================================
# Cross-platform URL dedup
# ===================================================================


class TestCrossplatformUrlDedup:
    def test_same_employer_url_deduplicated(self):
        job1 = _make_job(
            title="Frontend Engineer", company="Stripe", location="SF, US",
            application_url_employer="https://stripe.com/careers/frontend",
            source_platform="linkedin",
        )
        job2 = _make_job(
            title="Frontend Developer", company="Stripe Inc.", location="San Francisco, US",
            application_url_employer="https://stripe.com/careers/frontend",
            source_platform="indeed",
        )
        result = deduplicate_jobs([job1, job2])
        assert len(result) == 1

    def test_no_employer_url_not_affected(self):
        job1 = _make_job(
            title="Engineer A", company="Acme A", location="NYC",
            application_url_employer=None,
        )
        job2 = _make_job(
            title="Engineer B", company="Acme B", location="London",
            application_url_employer=None,
        )
        result = deduplicate_jobs([job1, job2])
        assert len(result) == 2


# ===================================================================
# Merge behavior
# ===================================================================


class TestMergeBehavior:
    def test_backfill_missing_fields(self):
        job1 = _make_job(
            title="Software Engineer", company="Google", location="NYC, US",
            description="Build amazing things", salary_min=None,
        )
        job2 = _make_job(
            title="Software Engineer", company="Google", location="NYC, US",
            description=None, salary_min=120000, salary_max=180000,
        )
        result = deduplicate_jobs([job1, job2])
        assert len(result) == 1
        merged = result[0]
        assert merged.description == "Build amazing things"
        assert merged.salary_min == 120000
