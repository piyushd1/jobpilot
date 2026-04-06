"""Three-stage job deduplication pipeline.

Stages
------
1. **Exact hash** -- SHA-256 of normalized title + company + location.
   On collision the richer record (more non-null fields) is kept.

2. **Fuzzy match** -- RapidFuzz title similarity > 85 % *and* company
   similarity > 90 %, with an optional embedding cosine threshold of 0.92.
   When two records match, the one with an employer ATS link is preferred.

3. **Cross-platform URL** -- Canonical employer URL dedup across board
   listings.  If two surviving records share the same
   ``application_url_employer``, they are merged.
"""

from __future__ import annotations

import math
from urllib.parse import urlparse

from rapidfuzz import fuzz

from src.models.schemas import JobDescription
from src.utils.canonicalization import (
    normalize_company,
    normalize_title,
)
from src.utils.hashing import compute_job_hash

# ── Thresholds ───────────────────────────────────────────────────────────────

TITLE_SIM_THRESHOLD = 85.0
COMPANY_SIM_THRESHOLD = 90.0
EMBEDDING_COSINE_THRESHOLD = 0.92


# ── Helpers ──────────────────────────────────────────────────────────────────


def _richness(job: JobDescription) -> int:
    """Count the number of non-None, non-empty fields on *job*."""
    score = 0
    for field_name in job.model_fields:
        value = getattr(job, field_name)
        if value is None:
            continue
        if isinstance(value, str) and not value:
            continue
        if isinstance(value, list) and len(value) == 0:
            continue
        score += 1
    return score


def _merge_jobs(primary: JobDescription, secondary: JobDescription) -> JobDescription:
    """Merge *secondary* into *primary*, preferring employer URLs.

    The *primary* record is used as the base; any field that is ``None`` or
    empty on the primary is back-filled from the secondary.
    """
    data = primary.model_dump()

    for field_name in primary.model_fields:
        pri_val = data.get(field_name)
        sec_val = getattr(secondary, field_name)

        # Back-fill missing values.
        if pri_val is None or (isinstance(pri_val, (str, list)) and not pri_val):
            data[field_name] = sec_val

    # Always prefer an employer URL when available.
    employer_url = primary.application_url_employer or secondary.application_url_employer
    if employer_url:
        data["application_url_employer"] = employer_url

    return JobDescription(**data)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two equal-length vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _canonical_url(url: str | None) -> str | None:
    """Reduce a URL to a comparable canonical form (scheme + host + path)."""
    if not url:
        return None
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower().removeprefix("www.")
        path = parsed.path.rstrip("/").lower()
        if not host:
            return None
        return f"{host}{path}"
    except Exception:
        return None


# ── Stage implementations ────────────────────────────────────────────────────


def _stage1_exact_hash(jobs: list[JobDescription]) -> list[JobDescription]:
    """Deduplicate by exact content hash (SHA-256 of normalised fields).

    When two records share the same hash, the richer record is kept.
    """
    bucket: dict[str, JobDescription] = {}

    for job in jobs:
        h = compute_job_hash(job.title, job.company, job.location or "")
        job = job.model_copy(update={"content_hash": h})

        existing = bucket.get(h)
        if existing is None:
            bucket[h] = job
        else:
            # Keep the richer record, merging in any missing fields.
            if _richness(job) > _richness(existing):
                bucket[h] = _merge_jobs(job, existing)
            else:
                bucket[h] = _merge_jobs(existing, job)

    return list(bucket.values())


def _stage2_fuzzy_match(
    jobs: list[JobDescription],
    embeddings: dict[int, list[float]] | None = None,
) -> list[JobDescription]:
    """Pairwise fuzzy matching on title + company, optionally gated by embedding cosine."""
    if len(jobs) <= 1:
        return jobs

    # Build an id -> original-index map so we can look up embeddings.
    # We key embeddings by the *position* the job had in the list passed to
    # ``deduplicate_jobs``, but after Stage 1 the list has been filtered.
    # Therefore we pass the index of each item in the *current* list.
    merged_flags: list[bool] = [False] * len(jobs)
    result: list[JobDescription] = []

    for i in range(len(jobs)):
        if merged_flags[i]:
            continue
        current = jobs[i]
        norm_title_i = normalize_title(current.title)
        norm_company_i = normalize_company(current.company)

        for j in range(i + 1, len(jobs)):
            if merged_flags[j]:
                continue
            other = jobs[j]
            norm_title_j = normalize_title(other.title)
            norm_company_j = normalize_company(other.company)

            title_sim = fuzz.ratio(norm_title_i, norm_title_j)
            company_sim = fuzz.ratio(norm_company_i, norm_company_j)

            if title_sim < TITLE_SIM_THRESHOLD or company_sim < COMPANY_SIM_THRESHOLD:
                continue

            # Optional embedding gate.
            if embeddings is not None:
                emb_i = embeddings.get(i)
                emb_j = embeddings.get(j)
                if emb_i is not None and emb_j is not None:
                    if _cosine_similarity(emb_i, emb_j) < EMBEDDING_COSINE_THRESHOLD:
                        continue

            # Merge -- prefer the record with an employer ATS link.
            if other.application_url_employer and not current.application_url_employer:
                current = _merge_jobs(other, current)
            else:
                current = _merge_jobs(current, other)
            merged_flags[j] = True

        result.append(current)

    return result


def _stage3_cross_platform_url(jobs: list[JobDescription]) -> list[JobDescription]:
    """Deduplicate across platforms by canonical employer URL."""
    url_bucket: dict[str, JobDescription] = {}
    no_url: list[JobDescription] = []

    for job in jobs:
        canon = _canonical_url(job.application_url_employer)
        if canon is None:
            no_url.append(job)
            continue

        existing = url_bucket.get(canon)
        if existing is None:
            url_bucket[canon] = job
        else:
            if _richness(job) > _richness(existing):
                url_bucket[canon] = _merge_jobs(job, existing)
            else:
                url_bucket[canon] = _merge_jobs(existing, job)

    return list(url_bucket.values()) + no_url


# ── Public API ───────────────────────────────────────────────────────────────


def deduplicate_jobs(
    jobs: list[JobDescription],
    embeddings: dict[int, list[float]] | None = None,
) -> list[JobDescription]:
    """Run the full 3-stage deduplication pipeline and return unique jobs.

    Parameters
    ----------
    jobs:
        Raw job descriptions, possibly with duplicates across platforms.
    embeddings:
        Optional mapping of *original* list index -> embedding vector.
        When provided, Stage 2 additionally checks cosine similarity > 0.92.

    Returns
    -------
    list[JobDescription]
        Deduplicated jobs, each with ``content_hash`` populated.
    """
    if not jobs:
        return []

    # Stage 1 -- exact hash dedup.
    deduped = _stage1_exact_hash(jobs)

    # Stage 2 -- fuzzy match dedup.
    deduped = _stage2_fuzzy_match(deduped, embeddings)

    # Stage 3 -- cross-platform employer URL dedup.
    deduped = _stage3_cross_platform_url(deduped)

    # Ensure every surviving record has content_hash set.
    result: list[JobDescription] = []
    for job in deduped:
        if not job.content_hash:
            h = compute_job_hash(job.title, job.company, job.location or "")
            job = job.model_copy(update={"content_hash": h})
        result.append(job)

    return result
