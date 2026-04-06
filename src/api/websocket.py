"""WebSocket endpoint for real-time campaign progress.

Runs the actual scoring pipeline and streams progress events to the frontend.
In production this would connect to Temporal workflow events via Redis PubSub.
For now, runs the pipeline inline to demonstrate the full flow.
"""

import json
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

FIXTURES = Path(__file__).parent.parent.parent / "tests" / "fixtures"


async def _send_event(ws: WebSocket, phase: str, status: str, detail: str) -> None:
    await ws.send_text(
        json.dumps({"type": "UPDATE", "data": {"phase": phase, "status": status, "detail": detail}})
    )


@router.websocket("/{campaign_id}/stream")
async def websocket_endpoint(websocket: WebSocket, campaign_id: str) -> None:
    await websocket.accept()
    try:
        # --- Phase 1: Parse resume (simulated — real parse needs PDF bytes) ---
        await _send_event(websocket, "PARSING", "IN_PROGRESS", "Parsing uploaded resume...")

        from src.scoring.normalizer import normalize_skills

        # Use a profile built from known data (in production, this comes from DB)
        candidate_skills = [
            "Python", "SQL", "AWS", "LLM Product Design", "RAG Pipelines",
            "Agentic AI Workflows", "LangChain", "Product Strategy",
            "A/B Testing", "Amplitude", "Jira", "Figma", "REST APIs",
            "System Architecture", "Git", "Marketplace Strategy",
        ]

        from src.models.schemas import CandidateProfile, WorkExperience

        profile = CandidateProfile(
            full_name="Piyush Deveshwar",
            email="piyush.dev@gmail.com",
            location="India",
            summary="AI-native product leader with 12+ years across Marketplaces and Consumer Platforms.",
            skills=candidate_skills,
            skills_normalized=normalize_skills(candidate_skills),
            target_roles=["Group Product Manager", "Director of Product", "Senior PM"],
            target_companies=["Google", "Swiggy", "Stripe", "Razorpay"],
            target_locations=["Bangalore", "Remote"],
            open_to_remote=True,
            total_experience_years=12.0,
            work_experience=[
                WorkExperience(
                    company="Justdial Ltd.",
                    title="Group Product Manager",
                    start_date="2020-09",
                    is_current=True,
                    description="Led mobile product org, drove 19% QoQ revenue increase, LLM-powered churn solution.",
                    skills_used=["Product Strategy", "LLM", "A/B Testing", "OKRs"],
                ),
                WorkExperience(
                    company="Urban Company",
                    title="Senior Manager, Growth",
                    start_date="2017-10",
                    end_date="2020-02",
                    description="Drove record GMV growth, scaled AC-Repairs to 1cr revenue.",
                    skills_used=["Growth", "Pricing Strategy", "LTV Analysis"],
                ),
            ],
        )

        await _send_event(
            websocket,
            "PARSING",
            "COMPLETE",
            f"Extracted profile: {profile.full_name}, {len(profile.skills)} skills, "
            f"{profile.total_experience_years}yr experience",
        )

        # --- Phase 2: Load and dedup jobs ---
        await _send_event(websocket, "DISCOVERY", "IN_PROGRESS", "Loading job listings...")

        from src.models.schemas import JobDescription
        from src.utils.deduplication import deduplicate_jobs

        jds_file = FIXTURES / "sample_jds.json"
        if jds_file.exists():
            with open(jds_file) as f:
                raw_jobs = json.load(f)
            jobs = [JobDescription.model_validate(j) for j in raw_jobs]
        else:
            jobs = []

        await _send_event(
            websocket, "DISCOVERY", "COMPLETE", f"Found {len(jobs)} jobs from sample data"
        )

        await _send_event(websocket, "DEDUP", "IN_PROGRESS", "Deduplicating cross-platform listings...")
        deduped = deduplicate_jobs(jobs)
        await _send_event(
            websocket, "DEDUP", "COMPLETE", f"{len(deduped)} unique jobs after deduplication"
        )

        # --- Phase 3: Risk detection ---
        await _send_event(websocket, "RISK_CHECK", "IN_PROGRESS", "Scanning for suspicious postings...")

        from src.scoring.risk_detector import JobRiskDetector

        detector = JobRiskDetector()
        flagged = 0
        for job in deduped:
            risk = detector.assess(job)
            if risk.flags:
                flagged += 1

        await _send_event(
            websocket,
            "RISK_CHECK",
            "COMPLETE",
            f"Risk scan done. {flagged} jobs flagged for review.",
        )

        # --- Phase 4: Score all jobs ---
        await _send_event(websocket, "SCORING", "IN_PROGRESS", "Running multi-signal scoring engine...")

        from src.scoring.engine import MatchScoringEngine

        engine = MatchScoringEngine()
        scored = []
        for job in deduped:
            result = engine.compute_final_score(profile, job)
            scored.append((result, job))

        scored.sort(key=lambda x: -x[0].final_score)

        await _send_event(
            websocket,
            "SCORING",
            "COMPLETE",
            f"Scored {len(scored)} jobs. "
            f"Top match: {scored[0][1].title} @ {scored[0][1].company} "
            f"({scored[0][0].tier.upper()}, {scored[0][0].final_score:.2f})"
            if scored
            else "No jobs to score.",
        )

        # --- Phase 5: Build shortlist ---
        await _send_event(websocket, "SHORTLIST", "IN_PROGRESS", "Building ranked shortlist...")

        shortlist = []
        for score, job in scored:
            shortlist.append(
                {
                    "rank": len(shortlist) + 1,
                    "title": job.title,
                    "company": job.company,
                    "location": job.location or "N/A",
                    "score": round(score.final_score, 3),
                    "tier": score.tier.upper(),
                    "skills_score": round(score.skills_score, 3),
                    "experience_fit": round(score.experience_fit_score, 3),
                    "company_match": round(score.company_preference_score, 3),
                    "apply_url": job.application_url_employer or job.application_url_board or "",
                }
            )

        # Send the full shortlist as a special event
        await websocket.send_text(
            json.dumps(
                {
                    "type": "SHORTLIST",
                    "data": {
                        "phase": "SHORTLIST",
                        "status": "COMPLETE",
                        "detail": f"{len(shortlist)} jobs ranked and ready for review.",
                        "shortlist": shortlist,
                    },
                }
            )
        )

        # --- Done ---
        await _send_event(
            websocket,
            "COMPLETED",
            "OK",
            f"Pipeline complete. {len(shortlist)} jobs scored. Ready for your review.",
        )

        # Keep connection alive for future events
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await _send_event(websocket, "ERROR", "FAILED", f"Pipeline error: {e}")
        except Exception:
            pass
