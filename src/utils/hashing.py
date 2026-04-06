"""Content hashing utilities for job deduplication."""

from __future__ import annotations

import hashlib

from src.utils.canonicalization import (
    normalize_company,
    normalize_location,
    normalize_title,
)


def compute_job_hash(title: str, company: str, location: str) -> str:
    """Return a SHA-256 hex digest of the normalized title + company + location.

    The three fields are individually normalized, joined with ``|``, and hashed
    so that minor surface variations (casing, legal suffixes, city aliases) do
    not produce different hashes.

    >>> compute_job_hash("Sr. Software Engineer", "Google Inc.", "Bengaluru, India")  # doctest: +ELLIPSIS
    '...'
    """
    normalized = "|".join(
        [
            normalize_title(title),
            normalize_company(company),
            normalize_location(location or ""),
        ]
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
