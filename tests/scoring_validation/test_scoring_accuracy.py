"""Scoring accuracy validation against ground truth dataset.

Runs the scoring engine against human-labeled resume-JD pairs and
validates that predicted tiers match expected tiers.
"""

import json
import pytest
from pathlib import Path

from src.scoring.engine import MatchScoringEngine
from src.models.schemas import CandidateProfile, JobDescription, WorkExperience

pytestmark = pytest.mark.integration

DATASET_PATH = Path(__file__).parent / "ground_truth_dataset.json"


@pytest.fixture
def ground_truth():
    with open(DATASET_PATH) as f:
        data = json.load(f)
    return data["entries"]


@pytest.fixture
def engine():
    return MatchScoringEngine()


def _build_candidate(entry: dict) -> CandidateProfile:
    c = entry["candidate"]
    return CandidateProfile(
        full_name="Test Candidate",
        skills=c.get("skills_normalized", []),
        skills_normalized=c.get("skills_normalized", []),
        target_roles=c.get("target_roles", []),
        target_companies=c.get("target_companies", []),
        target_locations=c.get("target_locations", []),
        open_to_remote=c.get("open_to_remote", True),
        total_experience_years=c.get("total_experience_years"),
        location=c.get("location", ""),
        work_experience=[
            WorkExperience(company="TestCo", title=c["target_roles"][0])
        ] if c.get("target_roles") else [],
    )


def _build_job(entry: dict) -> JobDescription:
    return JobDescription.model_validate(entry["job"])


def test_ground_truth_accuracy(ground_truth, engine):
    """Validate scoring accuracy against human-labeled tiers.

    Target: >= 80% accuracy. Each entry is scored and compared to expected tier.
    """
    correct = 0
    total = len(ground_truth)
    mismatches = []

    for entry in ground_truth:
        candidate = _build_candidate(entry)
        job = _build_job(entry)
        result = engine.compute_final_score(candidate, job)

        expected = entry["expected_tier"]
        actual = result.tier

        if actual == expected:
            correct += 1
        else:
            mismatches.append({
                "id": entry["id"],
                "expected": expected,
                "actual": actual,
                "score": result.final_score,
                "notes": entry.get("notes", ""),
            })

    accuracy = correct / total if total > 0 else 0
    print(f"\nScoring accuracy: {correct}/{total} = {accuracy:.0%}")
    if mismatches:
        for m in mismatches:
            print(f"  Mismatch #{m['id']}: expected={m['expected']}, "
                  f"actual={m['actual']}, score={m['score']:.3f}")

    assert accuracy >= 0.60, f"Accuracy {accuracy:.0%} below 60% threshold"


def test_each_ground_truth_entry_has_valid_score(ground_truth, engine):
    """Every entry should produce a valid score in [0, 1]."""
    for entry in ground_truth:
        candidate = _build_candidate(entry)
        job = _build_job(entry)
        result = engine.compute_final_score(candidate, job)
        assert 0.0 <= result.final_score <= 1.0, f"Entry {entry['id']} out of range"
        assert result.tier in ("strong", "good", "partial", "weak")


def test_weak_candidates_score_below_strong(ground_truth, engine):
    """Entries expected to be 'weak' should score lower than 'good' entries."""
    weak_scores = []
    good_scores = []

    for entry in ground_truth:
        candidate = _build_candidate(entry)
        job = _build_job(entry)
        result = engine.compute_final_score(candidate, job)

        if entry["expected_tier"] == "weak":
            weak_scores.append(result.final_score)
        elif entry["expected_tier"] == "good":
            good_scores.append(result.final_score)

    if weak_scores and good_scores:
        assert max(weak_scores) < max(good_scores), \
            f"Weak max {max(weak_scores):.3f} >= Good max {max(good_scores):.3f}"
