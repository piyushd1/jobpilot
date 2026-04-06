"""Unit tests for the deduplication engine."""

import pytest

from src.utils.canonicalization import normalize_title, normalize_company, normalize_location
from src.utils.hashing import compute_job_hash
from src.utils.deduplication import deduplicate_jobs
from src.models.schemas import JobDescription

pytestmark = pytest.mark.unit


# --- Canonicalization tests ---

def test_normalize_title_strips_seniority():
    assert normalize_title("Sr. Software Engineer") == "Software Engineer"


def test_normalize_title_strips_junior():
    result = normalize_title("Junior Data Scientist")
    assert "Junior" not in result and "junior" not in result


def test_normalize_title_preserves_core():
    result = normalize_title("Backend Engineer")
    assert "Backend" in result and "Engineer" in result


def test_normalize_company_strips_inc():
    assert normalize_company("Google Inc.") == "Google"


def test_normalize_company_strips_pvt_ltd():
    result = normalize_company("Infosys Pvt. Ltd.")
    assert "Pvt" not in result and "Ltd" not in result


def test_normalize_location_bangalore():
    result = normalize_location("Bangalore, India")
    assert "Bengaluru" in result or "Bangalore" in result


def test_normalize_location_nyc():
    result = normalize_location("NYC, US")
    assert "New York" in result


# --- Hashing tests ---

def test_same_job_same_hash():
    h1 = compute_job_hash("Software Engineer", "Google Inc.", "Bangalore, India")
    h2 = compute_job_hash("Software Engineer", "Google Inc", "Bangalore, India")
    # Both should normalize "Google Inc." and "Google Inc" to "Google"
    assert h1 == h2


def test_different_jobs_different_hash():
    h1 = compute_job_hash("Software Engineer", "Google", "Bangalore")
    h2 = compute_job_hash("Data Scientist", "Microsoft", "Seattle")
    assert h1 != h2


# --- Deduplication tests ---

def test_exact_duplicates_merged():
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


def test_different_jobs_not_merged():
    jobs = [
        JobDescription(title="Software Engineer", company="Google", location="Bangalore",
                       required_skills=["Python"]),
        JobDescription(title="Data Scientist", company="Microsoft", location="Seattle",
                       required_skills=["Python"]),
    ]
    result = deduplicate_jobs(jobs)
    assert len(result) == 2


def test_empty_input():
    result = deduplicate_jobs([])
    assert result == []


def test_single_job():
    jobs = [JobDescription(title="SWE", company="ACME", required_skills=["Go"])]
    result = deduplicate_jobs(jobs)
    assert len(result) == 1
    assert result[0].content_hash is not None
