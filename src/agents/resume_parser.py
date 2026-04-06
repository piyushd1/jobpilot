"""ResumeParserAgent — extracts structured CandidateProfile from a PDF resume.

Pipeline:
  1. Extract raw text from PDF (PyMuPDF -> pdfplumber -> vision fallback flag)
  2. If vision-needed, note it in reasoning trace (mock — actual vision call TBD)
  3. Send extracted text to LLM for structured JSON extraction
  4. Normalize skills via synonym dictionary
  5. Return validated CandidateProfile
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from src.agents.base import AgentShell
from src.models.schemas import CandidateProfile
from src.scoring.normalizer import normalize_skills
from src.services.llm_gateway import llm_gateway
from src.tools.pdf_extractor import extract_pdf_text
from src.utils.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------

class ResumeParserInput(BaseModel):
    """Input for the resume parser agent."""

    pdf_bytes: bytes | None = Field(
        default=None,
        description="Raw PDF file content as bytes.",
    )
    pdf_path: str | None = Field(
        default=None,
        description="Filesystem path to PDF (alternative to pdf_bytes).",
    )
    user_id: str = Field(
        ...,
        description="Unique identifier of the user who uploaded the resume.",
    )


# ---------------------------------------------------------------------------
# Extraction prompt
# ---------------------------------------------------------------------------

_EXTRACTION_SYSTEM_PROMPT = """\
You are an expert resume parser for the JobPilot platform. Your task is to
extract structured data from a candidate's resume text and return it as a
JSON object matching the CandidateProfile schema.

Extract the following fields precisely:
- full_name: The candidate's full name.
- email: Email address if present.
- phone: Phone number if present.
- location: City/state/country if mentioned.
- linkedin_url: LinkedIn profile URL if present.
- github_url: GitHub profile URL if present.
- portfolio_url: Personal website or portfolio URL if present.
- summary: A brief 2-3 sentence professional summary synthesized from the resume.
- target_roles: Job titles the candidate appears to be targeting (infer from most recent roles and summary).
- target_companies: Companies mentioned as targets (usually empty unless stated).
- target_locations: Preferred locations if stated.
- open_to_remote: true if the resume mentions remote work preference, else true by default.
- skills: A comprehensive list of ALL technical and professional skills mentioned anywhere in the resume.
- work_experience: Array of objects, each with: company, title, start_date, end_date, is_current, description, skills_used, location.
  - For dates, use formats like "Jan 2020", "2020", "Present" etc.
  - is_current should be true if end_date is "Present" or similar.
- total_experience_years: Approximate total years of professional experience (float).
- education: Array of objects, each with: institution, degree, field_of_study, graduation_year.
- certifications: List of certification names.

Rules:
- Return ONLY valid JSON, no markdown or explanation.
- If a field is not found in the resume, use null for optional fields or empty arrays for list fields.
- Be thorough — extract every skill mentioned, including those embedded in job descriptions.
- Normalize date formats consistently.
- Do NOT fabricate information that is not in the resume.
"""

_EXTRACTION_USER_PROMPT = """\
Parse the following resume text and extract a structured CandidateProfile JSON.

--- RESUME TEXT ---
{resume_text}
--- END RESUME TEXT ---

Return the JSON object now.
"""


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class ResumeParserAgent(AgentShell[ResumeParserInput, CandidateProfile]):
    """Parses a PDF resume into a structured CandidateProfile."""

    agent_name: str = "resume_parser"
    persona: str = (
        "You are JobPilot's Resume Parser agent. You receive raw PDF resumes, "
        "extract their text content using PDF extraction tools, then call an LLM "
        "to produce a comprehensive, structured CandidateProfile. You normalize "
        "all skill names to canonical forms for consistent downstream scoring. "
        "You handle scanned PDFs by flagging them for vision-based extraction. "
        "You are meticulous, never fabricate data, and always note which fields "
        "could not be extracted."
    )

    # --- Schema properties ---

    @property
    def input_type(self) -> type[ResumeParserInput]:
        return ResumeParserInput

    @property
    def output_type(self) -> type[CandidateProfile]:
        return CandidateProfile

    # --- Core logic ---

    async def reason_and_act(self, task_input: ResumeParserInput) -> CandidateProfile:
        """Execute the full resume-parsing pipeline."""
        reasoning_steps: list[str] = []

        # ------------------------------------------------------------------
        # Step 1: Obtain PDF bytes
        # ------------------------------------------------------------------
        pdf_bytes = task_input.pdf_bytes
        if pdf_bytes is None and task_input.pdf_path:
            reasoning_steps.append(f"Reading PDF from path: {task_input.pdf_path}")
            with open(task_input.pdf_path, "rb") as f:
                pdf_bytes = f.read()

        if pdf_bytes is None:
            raise ValueError("Either pdf_bytes or pdf_path must be provided.")

        # ------------------------------------------------------------------
        # Step 2: Extract text from PDF
        # ------------------------------------------------------------------
        reasoning_steps.append("Extracting text from PDF")
        extraction = await extract_pdf_text(pdf_bytes)
        resume_text: str = extraction["text"]
        extraction_method: str = extraction["method"]
        page_count: int = extraction["page_count"]
        confidence: float = extraction["confidence"]

        reasoning_steps.append(
            f"Extraction method={extraction_method}, "
            f"pages={page_count}, confidence={confidence}, "
            f"chars={len(resume_text)}"
        )

        # ------------------------------------------------------------------
        # Step 3: Handle vision-needed case
        # ------------------------------------------------------------------
        if extraction_method == "vision_needed":
            reasoning_steps.append(
                "Text extraction insufficient — flagging for vision-based extraction. "
                "Vision extraction via LLM with base64 page images is not yet "
                "implemented; returning a minimal profile with extraction metadata."
            )
            # In production this would encode pages as base64 images and send
            # them to a vision-capable LLM. For now we note the gap.
            logger.info(
                "Vision extraction needed but not yet implemented",
                user_id=task_input.user_id,
            )
            # Store metadata and return a minimal profile
            self._memory["parsing_metadata"] = {
                "extraction_method": extraction_method,
                "confidence": confidence,
                "page_count": page_count,
                "missing_fields": ["all — vision extraction required"],
            }
            self._memory["token_usage"] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }
            return CandidateProfile(
                full_name="Unknown (vision extraction required)",
                skills=[],
                skills_normalized=[],
            )

        # ------------------------------------------------------------------
        # Step 4: Call LLM to extract structured data
        # ------------------------------------------------------------------
        reasoning_steps.append("Calling LLM for structured extraction")
        messages: list[dict[str, str]] = [
            {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _EXTRACTION_USER_PROMPT.format(resume_text=resume_text),
            },
        ]

        llm_result = await llm_gateway.complete_json(messages=messages)
        parsed: dict[str, Any] = llm_result.get("parsed", {})
        token_usage: dict[str, int] = llm_result.get("token_usage", {})

        reasoning_steps.append(
            f"LLM returned {len(json.dumps(parsed))} chars of JSON, "
            f"tokens={token_usage.get('total_tokens', 0)}"
        )

        # ------------------------------------------------------------------
        # Step 5: Normalize skills
        # ------------------------------------------------------------------
        raw_skills: list[str] = parsed.get("skills", [])
        normalized = normalize_skills(raw_skills)
        parsed["skills_normalized"] = normalized

        reasoning_steps.append(
            f"Normalized {len(raw_skills)} raw skills to {len(normalized)} canonical skills"
        )

        # Also normalize skills_used inside each work experience entry
        for exp in parsed.get("work_experience", []):
            if isinstance(exp, dict) and "skills_used" in exp:
                exp["skills_used"] = normalize_skills(exp["skills_used"])

        # ------------------------------------------------------------------
        # Step 6: Build and validate CandidateProfile
        # ------------------------------------------------------------------
        reasoning_steps.append("Validating extracted data against CandidateProfile schema")

        # Identify missing fields for metadata
        missing_fields: list[str] = []
        for field_name in ["full_name", "email", "phone", "location", "summary"]:
            if not parsed.get(field_name):
                missing_fields.append(field_name)

        profile = CandidateProfile.model_validate(parsed)

        # ------------------------------------------------------------------
        # Store metadata in memory
        # ------------------------------------------------------------------
        self._memory["token_usage"] = token_usage
        self._memory["parsing_metadata"] = {
            "extraction_method": extraction_method,
            "confidence": confidence,
            "page_count": page_count,
            "missing_fields": missing_fields,
            "raw_skill_count": len(raw_skills),
            "normalized_skill_count": len(normalized),
        }
        self._memory["reasoning_steps"] = reasoning_steps

        logger.info(
            "Resume parsing complete",
            user_id=task_input.user_id,
            extraction_method=extraction_method,
            skills=len(normalized),
            missing=missing_fields,
        )

        return profile
