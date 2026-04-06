"""Match scoring engine that computes a weighted composite score.

Each signal scorer produces a value in [0, 1].  The final score is the weighted
sum, optionally adjusted by conflict-arbitration rules.  A :class:`ScoreBreakdown`
Pydantic model is returned with full transparency into every signal.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import UTC, datetime

from src.models.enums import MatchTier
from src.models.schemas import CandidateProfile, JobDescription, ScoreBreakdown
from src.scoring.skill_graph import TechAdjacencyGraph

# ---------------------------------------------------------------------------
# Signal weights (must sum to 1.0)
# ---------------------------------------------------------------------------
_WEIGHTS = {
    "skills": 0.30,
    "title_alignment": 0.15,
    "experience_fit": 0.15,
    "semantic_similarity": 0.10,
    "company_preference": 0.10,
    "location_fit": 0.08,
    "recency": 0.07,
    "source_confidence": 0.05,
}

# ---------------------------------------------------------------------------
# Tier thresholds
# ---------------------------------------------------------------------------
_TIER_STRONG = 0.80
_TIER_GOOD = 0.60
_TIER_PARTIAL = 0.40

# ---------------------------------------------------------------------------
# Source confidence registry
# ---------------------------------------------------------------------------
_SOURCE_CONFIDENCE: dict[str, float] = {
    "employer_ats": 1.0,
    "linkedin": 0.90,
    "greenhouse": 0.90,
    "lever": 0.90,
    "workday": 0.85,
    "indeed": 0.75,
    "glassdoor": 0.70,
    "ziprecruiter": 0.65,
    "monster": 0.60,
    "dice": 0.70,
    "builtin": 0.75,
    "stackoverflow": 0.80,
    "ycombinator": 0.80,
    "wellfound": 0.75,
    "angellist": 0.75,
    "remoteok": 0.65,
    "weworkremotely": 0.65,
    "hackernews": 0.70,
    "manual_input": 0.50,
    "unknown": 0.40,
}


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Compute cosine similarity between two vectors.  Returns 0.0 on degenerate input."""
    if len(a) != len(b) or len(a) == 0:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm_a * norm_b)))


class MatchScoringEngine:
    """Compute a multi-signal match score between a candidate and a job.

    Parameters
    ----------
    graph:
        Optional pre-built :class:`TechAdjacencyGraph`.  One is created
        automatically if not supplied.
    """

    def __init__(self, graph: TechAdjacencyGraph | None = None) -> None:
        self._graph = graph or TechAdjacencyGraph()

    # ------------------------------------------------------------------
    # Individual signal scorers
    # ------------------------------------------------------------------

    def _score_skills(
        self,
        candidate: CandidateProfile,
        job: JobDescription,
        *,
        candidate_embedding: Sequence[float] | None = None,
        job_skills_embedding: Sequence[float] | None = None,
    ) -> tuple[float, list[str]]:
        """Skill score = Jaccard hard match + adjacency credit + optional semantic cosine.

        Returns ``(score, reasoning_lines)``.
        """
        reasons: list[str] = []

        # Build canonical skill sets
        cand_skills_raw = set(candidate.skills) | set(candidate.skills_normalized)
        cand_canonical = {self._graph.canonicalize(s) for s in cand_skills_raw}

        required_canonical = {self._graph.canonicalize(s) for s in job.required_skills}
        preferred_canonical = {self._graph.canonicalize(s) for s in job.preferred_skills}
        all_jd_skills = required_canonical | preferred_canonical

        if not all_jd_skills:
            reasons.append("JD lists no skills; defaulting skill score to 0.5")
            return 0.5, reasons

        # --- 1. Jaccard hard match (40% of skill signal) ---
        intersection = cand_canonical & all_jd_skills
        union = cand_canonical | all_jd_skills
        jaccard = len(intersection) / len(union) if union else 0.0
        reasons.append(f"Jaccard overlap: {len(intersection)}/{len(union)} = {jaccard:.2f}")

        # --- 2. Adjacency credit (40% of skill signal) ---
        # For each JD skill NOT matched exactly, find best adjacency from candidate
        unmatched_jd = all_jd_skills - cand_canonical
        adjacency_credits: list[float] = []
        for jd_skill in unmatched_jd:
            best = 0.0
            for cand_skill in cand_canonical:
                score = self._graph.adjacency_score(cand_skill, jd_skill)
                if score > best:
                    best = score
            adjacency_credits.append(best)

        adj_score = sum(adjacency_credits) / len(all_jd_skills) if all_jd_skills else 0.0
        reasons.append(
            f"Adjacency credit for {len(unmatched_jd)} unmatched JD skills: {adj_score:.2f}"
        )

        # --- 3. Semantic cosine (20% of skill signal) ---
        if candidate_embedding is not None and job_skills_embedding is not None:
            semantic = _cosine_similarity(candidate_embedding, job_skills_embedding)
            reasons.append(f"Skill semantic cosine: {semantic:.2f}")
        else:
            semantic = 0.0
            reasons.append("Skill semantic cosine: N/A (no embeddings)")

        combined = 0.40 * jaccard + 0.40 * adj_score + 0.20 * semantic
        return min(1.0, combined), reasons

    def _score_title_alignment(
        self,
        candidate: CandidateProfile,
        job: JobDescription,
        *,
        candidate_title_embedding: Sequence[float] | None = None,
        job_title_embedding: Sequence[float] | None = None,
    ) -> tuple[float, list[str]]:
        """Embedding cosine between candidate target titles and JD title."""
        reasons: list[str] = []

        if candidate_title_embedding is not None and job_title_embedding is not None:
            sim = _cosine_similarity(candidate_title_embedding, job_title_embedding)
            reasons.append(f"Title embedding cosine: {sim:.2f}")
            return sim, reasons

        # Fallback: simple lowercase substring heuristic
        jd_title_lower = job.title.lower()
        best = 0.0
        for role in candidate.target_roles:
            role_lower = role.lower()
            if role_lower == jd_title_lower:
                best = 1.0
                break
            if role_lower in jd_title_lower or jd_title_lower in role_lower:
                best = max(best, 0.70)
            # Check individual words overlap
            role_words = set(role_lower.split())
            title_words = set(jd_title_lower.split())
            common = role_words & title_words
            if common:
                word_overlap = len(common) / max(len(role_words), len(title_words))
                best = max(best, word_overlap * 0.8)

        reasons.append(f"Title heuristic match: {best:.2f} (no embeddings)")
        return best, reasons

    def _score_experience_fit(
        self,
        candidate: CandidateProfile,
        job: JobDescription,
    ) -> tuple[float, list[str]]:
        """Range overlap + Gaussian decay outside JD's experience range."""
        reasons: list[str] = []
        cand_exp = candidate.total_experience_years

        if cand_exp is None:
            reasons.append("Candidate experience unknown; defaulting to 0.5")
            return 0.5, reasons

        jd_min = job.min_experience_years
        jd_max = job.max_experience_years

        if jd_min is None and jd_max is None:
            reasons.append("JD specifies no experience range; defaulting to 0.8")
            return 0.8, reasons

        low = jd_min if jd_min is not None else 0
        high = jd_max if jd_max is not None else low + 10

        if low <= cand_exp <= high:
            score = 1.0
            reasons.append(f"Experience {cand_exp}y within [{low}, {high}]")
        else:
            # Gaussian decay: sigma = 2 years
            sigma = 2.0
            distance = low - cand_exp if cand_exp < low else cand_exp - high
            score = math.exp(-0.5 * (distance / sigma) ** 2)
            reasons.append(
                f"Experience {cand_exp}y outside [{low}, {high}]; "
                f"distance={distance:.1f}y, decay={score:.2f}"
            )

        return score, reasons

    def _score_semantic_sim(
        self,
        *,
        profile_embedding: Sequence[float] | None = None,
        jd_embedding: Sequence[float] | None = None,
    ) -> tuple[float, list[str]]:
        """Full profile embedding vs full JD embedding cosine similarity."""
        reasons: list[str] = []
        if profile_embedding is not None and jd_embedding is not None:
            sim = _cosine_similarity(profile_embedding, jd_embedding)
            reasons.append(f"Full semantic cosine: {sim:.2f}")
            return sim, reasons

        reasons.append("Full semantic cosine: N/A (no embeddings)")
        return 0.0, reasons

    def _score_company_preference(
        self,
        candidate: CandidateProfile,
        job: JobDescription,
    ) -> tuple[float, list[str]]:
        """Exact name match or domain-level match against target companies."""
        reasons: list[str] = []

        if not candidate.target_companies:
            reasons.append("No target companies specified; defaulting to 0.5")
            return 0.5, reasons

        jd_company_lower = job.company.lower().strip()
        for tc in candidate.target_companies:
            if tc.lower().strip() == jd_company_lower:
                reasons.append(f"Exact company match: {job.company}")
                return 1.0, reasons

        # Domain match: check if company name appears as substring
        for tc in candidate.target_companies:
            tc_lower = tc.lower().strip()
            if tc_lower in jd_company_lower or jd_company_lower in tc_lower:
                reasons.append(f"Partial company match: {tc} ~ {job.company}")
                return 0.70, reasons

        reasons.append(f"No company match for {job.company}")
        return 0.0, reasons

    def _score_location_fit(
        self,
        candidate: CandidateProfile,
        job: JobDescription,
    ) -> tuple[float, list[str]]:
        """Rule-based: remote preference, same city, relocation flag."""
        reasons: list[str] = []

        # Remote job + candidate open to remote => perfect fit
        if job.is_remote and candidate.open_to_remote:
            reasons.append("Remote job and candidate is open to remote")
            return 1.0, reasons

        if job.is_remote:
            reasons.append("Remote job (candidate remote pref unknown, good default)")
            return 0.90, reasons

        # Check same city / target location
        jd_loc = (job.location or "").lower().strip()
        if not jd_loc:
            reasons.append("JD location unknown; defaulting to 0.5")
            return 0.5, reasons

        cand_loc = (candidate.location or "").lower().strip()
        target_locs = [loc.lower().strip() for loc in candidate.target_locations]

        # Exact city match with candidate location
        if cand_loc and (cand_loc in jd_loc or jd_loc in cand_loc):
            reasons.append(f"Candidate location '{cand_loc}' matches JD '{jd_loc}'")
            return 1.0, reasons

        # Target location match
        for tloc in target_locs:
            if tloc in jd_loc or jd_loc in tloc:
                reasons.append(f"Target location '{tloc}' matches JD '{jd_loc}'")
                return 0.90, reasons

        # Candidate is open to remote but job is not remote
        if candidate.open_to_remote:
            reasons.append(f"Location mismatch ({jd_loc}) but candidate open to remote")
            return 0.40, reasons

        reasons.append(f"Location mismatch: candidate='{cand_loc}', job='{jd_loc}'")
        return 0.10, reasons

    def _score_recency(
        self,
        job: JobDescription,
        *,
        reference_date: datetime | None = None,
    ) -> tuple[float, list[str]]:
        """Exponential decay by days since posting.

        Half-life is 14 days: a job posted 14 days ago scores ~0.5.
        """
        reasons: list[str] = []

        if job.posted_date is None:
            reasons.append("No posted date; defaulting recency to 0.5")
            return 0.5, reasons

        now = reference_date or datetime.now(UTC)
        posted = job.posted_date
        if posted.tzinfo is None:
            posted = posted.replace(tzinfo=UTC)

        days_old = max(0.0, (now - posted).total_seconds() / 86400)
        half_life = 14.0
        decay = math.exp(-math.log(2) * days_old / half_life)
        decay = max(0.0, min(1.0, decay))
        reasons.append(f"Posted {days_old:.0f} days ago; recency decay={decay:.2f}")
        return decay, reasons

    def _score_source_confidence(
        self,
        job: JobDescription,
    ) -> tuple[float, list[str]]:
        """Look up source platform in the confidence registry."""
        reasons: list[str] = []
        platform = (job.source_platform or "unknown").lower().strip()
        confidence = _SOURCE_CONFIDENCE.get(platform, _SOURCE_CONFIDENCE["unknown"])
        reasons.append(f"Source '{platform}' confidence: {confidence:.2f}")
        return confidence, reasons

    # ------------------------------------------------------------------
    # Gap identification
    # ------------------------------------------------------------------

    def _identify_gaps(
        self,
        candidate: CandidateProfile,
        job: JobDescription,
    ) -> list[str]:
        """Identify missing required skills and suggest adjacent alternatives."""
        cand_raw = set(candidate.skills) | set(candidate.skills_normalized)
        cand_canonical = {self._graph.canonicalize(s) for s in cand_raw}
        required_canonical = {self._graph.canonicalize(s) for s in job.required_skills}

        missing = required_canonical - cand_canonical
        gap_lines: list[str] = []

        for skill in sorted(missing):
            # Find candidate's closest adjacent skill
            best_adj: str | None = None
            best_score = 0.0
            for cs in cand_canonical:
                adj = self._graph.adjacency_score(cs, skill)
                if adj > best_score:
                    best_score = adj
                    best_adj = cs

            if best_adj and best_score >= 0.30:
                gap_lines.append(f"Missing '{skill}' (closest: '{best_adj}' @ {best_score:.2f})")
            else:
                gap_lines.append(f"Missing '{skill}' (no close alternative found)")

        return gap_lines

    # ------------------------------------------------------------------
    # Composite score
    # ------------------------------------------------------------------

    def compute_final_score(
        self,
        candidate: CandidateProfile,
        job: JobDescription,
        *,
        candidate_skills_embedding: Sequence[float] | None = None,
        job_skills_embedding: Sequence[float] | None = None,
        candidate_title_embedding: Sequence[float] | None = None,
        job_title_embedding: Sequence[float] | None = None,
        profile_embedding: Sequence[float] | None = None,
        jd_embedding: Sequence[float] | None = None,
        reference_date: datetime | None = None,
    ) -> ScoreBreakdown:
        """Run all signal scorers and return a :class:`ScoreBreakdown`."""
        trace_lines: list[str] = []

        # 1. Skills
        skills_score, skills_reasons = self._score_skills(
            candidate,
            job,
            candidate_embedding=candidate_skills_embedding,
            job_skills_embedding=job_skills_embedding,
        )
        trace_lines.extend(skills_reasons)

        # 2. Title alignment
        title_score, title_reasons = self._score_title_alignment(
            candidate,
            job,
            candidate_title_embedding=candidate_title_embedding,
            job_title_embedding=job_title_embedding,
        )
        trace_lines.extend(title_reasons)

        # 3. Experience fit
        exp_score, exp_reasons = self._score_experience_fit(candidate, job)
        trace_lines.extend(exp_reasons)

        # 4. Semantic similarity
        sem_score, sem_reasons = self._score_semantic_sim(
            profile_embedding=profile_embedding,
            jd_embedding=jd_embedding,
        )
        trace_lines.extend(sem_reasons)

        # 5. Company preference
        company_score, company_reasons = self._score_company_preference(candidate, job)
        trace_lines.extend(company_reasons)

        # 6. Location fit
        location_score, location_reasons = self._score_location_fit(candidate, job)
        trace_lines.extend(location_reasons)

        # 7. Recency
        recency_score, recency_reasons = self._score_recency(job, reference_date=reference_date)
        trace_lines.extend(recency_reasons)

        # 8. Source confidence
        source_score, source_reasons = self._score_source_confidence(job)
        trace_lines.extend(source_reasons)

        # --- Weighted sum ---
        final = (
            _WEIGHTS["skills"] * skills_score
            + _WEIGHTS["title_alignment"] * title_score
            + _WEIGHTS["experience_fit"] * exp_score
            + _WEIGHTS["semantic_similarity"] * sem_score
            + _WEIGHTS["company_preference"] * company_score
            + _WEIGHTS["location_fit"] * location_score
            + _WEIGHTS["recency"] * recency_score
            + _WEIGHTS["source_confidence"] * source_score
        )
        final = max(0.0, min(1.0, final))

        # --- Tier classification ---
        if final >= _TIER_STRONG:
            tier = MatchTier.STRONG
        elif final >= _TIER_GOOD:
            tier = MatchTier.GOOD
        elif final >= _TIER_PARTIAL:
            tier = MatchTier.PARTIAL
        else:
            tier = MatchTier.WEAK

        # --- Conflict arbitration ---
        # Semantic > 0.80 but hard skill overlap < 0.50 => cap at GOOD
        cand_canonical = {
            self._graph.canonicalize(s)
            for s in (set(candidate.skills) | set(candidate.skills_normalized))
        }
        all_jd_canonical = {
            self._graph.canonicalize(s)
            for s in (set(job.required_skills) | set(job.preferred_skills))
        }
        if all_jd_canonical:
            hard_overlap = len(cand_canonical & all_jd_canonical) / len(all_jd_canonical)
        else:
            hard_overlap = 1.0

        if sem_score > 0.80 and hard_overlap < 0.50 and tier == MatchTier.STRONG:
            tier = MatchTier.GOOD
            trace_lines.append(
                f"Conflict arbitration: semantic={sem_score:.2f} but "
                f"hard overlap={hard_overlap:.2f} < 0.50 => tier capped at GOOD"
            )

        # --- Gap identification ---
        gaps = self._identify_gaps(candidate, job)
        if gaps:
            trace_lines.append("--- Skill gaps ---")
            trace_lines.extend(gaps)

        return ScoreBreakdown(
            skills_score=round(skills_score, 4),
            title_alignment_score=round(title_score, 4),
            experience_fit_score=round(exp_score, 4),
            semantic_similarity_score=round(sem_score, 4),
            company_preference_score=round(company_score, 4),
            location_fit_score=round(location_score, 4),
            recency_score=round(recency_score, 4),
            source_confidence_score=round(source_score, 4),
            final_score=round(final, 4),
            tier=tier.value,
            reasoning_trace="\n".join(trace_lines),
        )
