"""Scraping canary runs — weekly health checks against platform strategies.

Validates that the strategy cascade still works for each platform
without hitting real APIs. Uses saved fixtures.

Run: python -m tests.load.canary
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from src.platforms.source_policy import source_registry
from src.scoring.engine import MatchScoringEngine
from src.scoring.risk_detector import JobRiskDetector
from src.models.schemas import CandidateProfile, JobDescription, WorkExperience
from src.utils.deduplication import deduplicate_jobs

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _load_sample_jobs() -> list[JobDescription]:
    jds_file = FIXTURES / "sample_jds.json"
    with open(jds_file) as f:
        raw = json.load(f)
    return [JobDescription.model_validate(j) for j in raw]


def _sample_candidate() -> CandidateProfile:
    return CandidateProfile(
        full_name="Canary Candidate",
        skills=["Python", "Kubernetes", "PostgreSQL", "AWS", "Docker", "Kafka"],
        skills_normalized=["python", "kubernetes", "postgresql", "aws", "docker", "kafka"],
        target_roles=["Senior Software Engineer"],
        target_companies=["Google", "Microsoft"],
        target_locations=["Bangalore", "Remote"],
        open_to_remote=True,
        total_experience_years=8.0,
        work_experience=[
            WorkExperience(company="TestCo", title="Senior Software Engineer"),
        ],
    )


async def run_canary() -> dict:
    """Run canary checks on all core pipeline components."""
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {},
    }

    # 1. Source registry check
    try:
        sources = source_registry.list_sources()
        for source in sources:
            strategies = source_registry.get_allowed_strategies(source)
            assert len(strategies) > 0, f"No strategies for {source}"
        results["checks"]["source_registry"] = {"status": "pass", "sources": len(sources)}
    except Exception as e:
        results["checks"]["source_registry"] = {"status": "fail", "error": str(e)}

    # 2. Deduplication check
    try:
        jobs = _load_sample_jobs()
        deduped = deduplicate_jobs(jobs)
        assert len(deduped) > 0
        assert len(deduped) <= len(jobs)
        results["checks"]["deduplication"] = {
            "status": "pass",
            "input": len(jobs),
            "output": len(deduped),
        }
    except Exception as e:
        results["checks"]["deduplication"] = {"status": "fail", "error": str(e)}

    # 3. Scoring engine check
    try:
        engine = MatchScoringEngine()
        candidate = _sample_candidate()
        for job in _load_sample_jobs()[:3]:
            score = engine.compute_final_score(candidate, job)
            assert 0.0 <= score.final_score <= 1.0
            assert score.tier in ("strong", "good", "partial", "weak")
        results["checks"]["scoring_engine"] = {"status": "pass"}
    except Exception as e:
        results["checks"]["scoring_engine"] = {"status": "fail", "error": str(e)}

    # 4. Risk detector check
    try:
        detector = JobRiskDetector()
        scam = JobDescription(
            title="Data Entry",
            company="FakeCo",
            description="Pay training fee to start. WhatsApp us.",
            required_skills=[],
        )
        assessment = detector.assess(scam)
        assert assessment.requires_review
        results["checks"]["risk_detector"] = {"status": "pass", "flags": len(assessment.flags)}
    except Exception as e:
        results["checks"]["risk_detector"] = {"status": "fail", "error": str(e)}

    # Summary
    all_pass = all(c["status"] == "pass" for c in results["checks"].values())
    results["overall"] = "pass" if all_pass else "fail"

    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    asyncio.run(run_canary())
