"""Job Risk Detector -- fraud/scam signal rules for job postings.

Evaluates each canonical job against rule-based signals:
  RED flags (scam_likely, high_risk)   -> mandatory review gate
  YELLOW flags (suspicious)            -> warning badge in shortlist
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.models.schemas import JobDescription
from src.utils.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


class RiskLevel:
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"


@dataclass
class RiskFlag:
    level: str  # "red", "yellow"
    rule: str  # rule identifier
    message: str  # human-readable explanation
    evidence: str = ""  # the text that triggered the flag


@dataclass
class RiskAssessment:
    job_title: str
    job_company: str
    overall_level: str = RiskLevel.GREEN  # worst flag level
    flags: list[RiskFlag] = field(default_factory=list)
    requires_review: bool = False  # True if any RED flag


# ---------------------------------------------------------------------------
# RED flag patterns (case-insensitive)
# ---------------------------------------------------------------------------

_FEE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"pay\s+to\s+apply",
        r"training\s+fee",
        r"deposit\s+required",
        r"registration\s+fee",
        r"processing\s+fee",
        r"advance\s+payment",
    ]
]

_SENSITIVE_DOC_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"send\s+aadhaar",
        r"bank\s+details",
        r"passport\s+copy",
        r"pan\s+card",
        r"credit\s+card",
    ]
]

_GUARANTEED_JOB_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"guaranteed\s+placement",
        r"100\s*%\s*job\s+guarantee",
        r"no\s+interview\s+needed",
    ]
]

# ---------------------------------------------------------------------------
# YELLOW flag patterns
# ---------------------------------------------------------------------------

_OFF_PLATFORM_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"whatsapp\s+us",
        r"contact\s+(?:us\s+)?(?:on\s+)?whatsapp",
        r"message\s+(?:us\s+)?(?:on\s+)?whatsapp",
        r"reach\s+(?:us\s+)?(?:on\s+)?whatsapp",
        r"telegram\s+(?:us|me|group|channel)",
        r"contact\s+(?:us\s+)?(?:on\s+)?telegram",
        r"(?:dm|message)\s+(?:us\s+)?(?:on\s+)?telegram",
        r"(?:mail|email)\s+(?:us\s+)?(?:at\s+)?\S+@(?:gmail|yahoo|hotmail)",
        r"send\s+(?:your\s+)?(?:cv|resume)\s+(?:to\s+)?\S+@(?:gmail|yahoo|hotmail)",
    ]
]

_PERSONAL_EMAIL_RE = re.compile(
    r"@(?:gmail|yahoo|hotmail|outlook|aol|rediffmail|ymail)\.\w+",
    re.IGNORECASE,
)

_VAGUE_PHRASES: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"^great\s+opportunity$",
        r"^work\s+from\s+home$",
        r"^earn\s+money$",
        r"^easy\s+money$",
        r"^make\s+money\s+online$",
        r"^hiring\s+now$",
    ]
]

_URL_SHORTENER_RE = re.compile(
    r"https?://(?:bit\.ly|tinyurl\.com|goo\.gl|t\.co|ow\.ly|is\.gd|buff\.ly"
    r"|tiny\.cc|lnkd\.in|shorturl\.at|rb\.gy|cutt\.ly)/",
    re.IGNORECASE,
)

_NON_HTTPS_URL_RE = re.compile(r"^http://", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Salary benchmarks (INR LPA = lakhs per annum)
# ---------------------------------------------------------------------------

_SALARY_MAX_INR: dict[str, int] = {
    "entry": 30_00_000,  # 30 LPA
    "mid": 50_00_000,  # 50 LPA
    "senior": 80_00_000,  # 80 LPA
    "staff": 1_20_00_000,  # 120 LPA
}

_SALARY_MAX_USD: dict[str, int] = {
    "entry": 120_000,
    "mid": 200_000,
    "senior": 350_000,
    "staff": 500_000,
}

# Keywords used to infer seniority from job title
_SENIORITY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("staff", re.compile(r"\b(?:staff|principal|distinguished|fellow)\b", re.IGNORECASE)),
    ("senior", re.compile(r"\b(?:senior|sr\.?|lead|architect)\b", re.IGNORECASE)),
    ("mid", re.compile(r"\b(?:mid|intermediate|ii|iii)\b", re.IGNORECASE)),
    # "entry" is the fallback
]


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------


class JobRiskDetector:
    """Rule-based risk detector for job postings.

    All checks are pure regex / threshold logic -- no LLM calls.
    """

    def assess(self, job: JobDescription) -> RiskAssessment:
        """Evaluate a single job posting for scam/fraud signals."""
        assessment = RiskAssessment(
            job_title=job.title,
            job_company=job.company,
        )

        text = self._full_text(job)

        # --- RED flags ---
        self._check_fee_request(text, assessment)
        self._check_sensitive_docs(text, assessment)
        self._check_guaranteed_job(text, assessment)

        # --- YELLOW flags ---
        self._check_off_platform_chat(text, assessment)
        self._check_personal_email(job, assessment)
        self._check_salary_implausible(job, assessment)
        self._check_vague_description(job, assessment)
        self._check_suspicious_url(job, assessment)

        # Finalise overall level
        self._finalise(assessment)

        logger.info(
            "risk_assessment_complete",
            job_title=job.title,
            company=job.company,
            level=assessment.overall_level,
            flag_count=len(assessment.flags),
            requires_review=assessment.requires_review,
        )

        return assessment

    def assess_batch(self, jobs: list[JobDescription]) -> list[RiskAssessment]:
        """Evaluate a batch of job postings."""
        return [self.assess(job) for job in jobs]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _full_text(job: JobDescription) -> str:
        """Concatenate all text fields for pattern matching."""
        parts = [
            job.title or "",
            job.company or "",
            job.description or "",
            " ".join(job.required_skills),
            " ".join(job.preferred_skills),
        ]
        return " ".join(parts)

    @staticmethod
    def _finalise(assessment: RiskAssessment) -> None:
        """Set overall_level and requires_review based on collected flags."""
        has_red = any(f.level == RiskLevel.RED for f in assessment.flags)
        has_yellow = any(f.level == RiskLevel.YELLOW for f in assessment.flags)

        if has_red:
            assessment.overall_level = RiskLevel.RED
            assessment.requires_review = True
        elif has_yellow:
            assessment.overall_level = RiskLevel.YELLOW
        else:
            assessment.overall_level = RiskLevel.GREEN

    # ------------------------------------------------------------------
    # RED flag checks
    # ------------------------------------------------------------------

    @staticmethod
    def _check_fee_request(text: str, assessment: RiskAssessment) -> None:
        for pattern in _FEE_PATTERNS:
            match = pattern.search(text)
            if match:
                assessment.flags.append(
                    RiskFlag(
                        level=RiskLevel.RED,
                        rule="FEE_REQUEST",
                        message="Job posting asks for payment or fee from the applicant.",
                        evidence=match.group(0),
                    )
                )
                return  # one flag per rule is enough

    @staticmethod
    def _check_sensitive_docs(text: str, assessment: RiskAssessment) -> None:
        for pattern in _SENSITIVE_DOC_PATTERNS:
            match = pattern.search(text)
            if match:
                assessment.flags.append(
                    RiskFlag(
                        level=RiskLevel.RED,
                        rule="SENSITIVE_DOCS",
                        message="Job posting requests sensitive personal documents early in the process.",
                        evidence=match.group(0),
                    )
                )
                return

    @staticmethod
    def _check_guaranteed_job(text: str, assessment: RiskAssessment) -> None:
        for pattern in _GUARANTEED_JOB_PATTERNS:
            match = pattern.search(text)
            if match:
                assessment.flags.append(
                    RiskFlag(
                        level=RiskLevel.RED,
                        rule="GUARANTEED_JOB",
                        message="Job posting makes unrealistic guarantees about placement or hiring.",
                        evidence=match.group(0),
                    )
                )
                return

    # ------------------------------------------------------------------
    # YELLOW flag checks
    # ------------------------------------------------------------------

    @staticmethod
    def _check_off_platform_chat(text: str, assessment: RiskAssessment) -> None:
        for pattern in _OFF_PLATFORM_PATTERNS:
            match = pattern.search(text)
            if match:
                assessment.flags.append(
                    RiskFlag(
                        level=RiskLevel.YELLOW,
                        rule="OFF_PLATFORM_CHAT",
                        message="Job posting pressures applicants to move to WhatsApp, Telegram, or personal email.",
                        evidence=match.group(0),
                    )
                )
                return

    @staticmethod
    def _check_personal_email(job: JobDescription, assessment: RiskAssessment) -> None:
        """Flag enterprise companies using free-tier email providers."""
        text = (job.description or "") + " " + (job.company or "")
        match = _PERSONAL_EMAIL_RE.search(text)
        if not match:
            return

        # Only flag if the company name sounds like a proper enterprise.
        # Simple heuristic: company name has >1 word or contains enterprise
        # keywords. This deliberately errs on the side of flagging -- the
        # user can dismiss.
        company_lower = (job.company or "").lower()
        enterprise_hints = [
            "technologies",
            "solutions",
            "systems",
            "consulting",
            "services",
            "global",
            "enterprises",
            "corp",
            "inc",
            "ltd",
            "pvt",
            "llp",
            "limited",
            "group",
        ]
        looks_enterprise = (
            any(kw in company_lower for kw in enterprise_hints)
            or len((job.company or "").split()) > 1
        )

        if looks_enterprise:
            assessment.flags.append(
                RiskFlag(
                    level=RiskLevel.YELLOW,
                    rule="PERSONAL_EMAIL_ENTERPRISE",
                    message=(
                        f"Company '{job.company}' appears to be an enterprise but uses "
                        f"a free email provider ({match.group(0)})."
                    ),
                    evidence=match.group(0),
                )
            )

    @staticmethod
    def _infer_seniority(title: str) -> str:
        """Infer seniority bucket from job title."""
        for level, pattern in _SENIORITY_PATTERNS:
            if pattern.search(title):
                return level
        return "entry"

    def _check_salary_implausible(self, job: JobDescription, assessment: RiskAssessment) -> None:
        """Flag salary ranges that exceed reasonable benchmarks."""
        if job.salary_max is None and job.salary_min is None:
            return

        salary_val = job.salary_max or job.salary_min
        if salary_val is None or salary_val <= 0:
            return

        currency = (job.salary_currency or "INR").upper()
        seniority = self._infer_seniority(job.title)

        if currency == "USD":
            benchmark = _SALARY_MAX_USD.get(seniority, _SALARY_MAX_USD["entry"])
        else:
            # Default to INR for unrecognised currencies
            benchmark = _SALARY_MAX_INR.get(seniority, _SALARY_MAX_INR["entry"])

        if salary_val > benchmark:
            assessment.flags.append(
                RiskFlag(
                    level=RiskLevel.YELLOW,
                    rule="SALARY_IMPLAUSIBLE",
                    message=(
                        f"Salary {salary_val:,} {currency} for a {seniority}-level "
                        f"'{job.title}' role exceeds the {benchmark:,} {currency} benchmark."
                    ),
                    evidence=f"{salary_val} {currency}",
                )
            )

    @staticmethod
    def _check_vague_description(job: JobDescription, assessment: RiskAssessment) -> None:
        """Flag postings with very short or entirely generic descriptions."""
        desc = (job.description or "").strip()

        if len(desc) < 50:
            assessment.flags.append(
                RiskFlag(
                    level=RiskLevel.YELLOW,
                    rule="VAGUE_DESCRIPTION",
                    message=(
                        f"Description is only {len(desc)} characters -- too short to "
                        f"be a legitimate posting."
                    ),
                    evidence=desc[:100] if desc else "(empty)",
                )
            )
            return

        # Check for entirely generic single-phrase descriptions
        for pattern in _VAGUE_PHRASES:
            if pattern.match(desc):
                assessment.flags.append(
                    RiskFlag(
                        level=RiskLevel.YELLOW,
                        rule="VAGUE_DESCRIPTION",
                        message="Description is entirely generic and lacks substantive detail.",
                        evidence=desc[:100],
                    )
                )
                return

    @staticmethod
    def _check_suspicious_url(job: JobDescription, assessment: RiskAssessment) -> None:
        """Flag application URLs that use shorteners or plain HTTP."""
        urls = [u for u in [job.application_url_board, job.application_url_employer] if u]
        for url in urls:
            if _URL_SHORTENER_RE.search(url):
                assessment.flags.append(
                    RiskFlag(
                        level=RiskLevel.YELLOW,
                        rule="SUSPICIOUS_URL",
                        message="Application URL uses a URL shortener, which can mask the real destination.",
                        evidence=url,
                    )
                )
                return

            if _NON_HTTPS_URL_RE.match(url):
                assessment.flags.append(
                    RiskFlag(
                        level=RiskLevel.YELLOW,
                        rule="SUSPICIOUS_URL",
                        message="Application URL uses HTTP instead of HTTPS.",
                        evidence=url,
                    )
                )
                return
