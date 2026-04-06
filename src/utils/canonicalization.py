"""Normalization utilities for job titles, company names, and locations.

Used by the deduplication pipeline to produce canonical forms before hashing
and fuzzy matching.
"""

from __future__ import annotations

import re

# ── Title normalization ──────────────────────────────────────────────────────

# Seniority prefixes / words to strip (case-insensitive).
_SENIORITY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"\b(?:Sr\.?|Senior|Jr\.?|Junior|Lead|Staff|Principal|Distinguished|Associate)\b",
        re.IGNORECASE,
    ),
]

# Common Roman-numeral or numeric level suffixes (e.g. "Engineer II", "Level 3").
_LEVEL_PATTERN = re.compile(
    r"\b(?:I{1,3}|IV|V|Level\s*\d+)\b",
    re.IGNORECASE,
)

_EXTRA_WHITESPACE = re.compile(r"\s{2,}")
_SURROUNDING_PUNCTUATION = re.compile(r"^\W+|\W+$")


def normalize_title(title: str) -> str:
    """Strip seniority variants, standardize casing, collapse whitespace.

    >>> normalize_title("Sr. Software Engineer")
    'Software Engineer'
    >>> normalize_title("  JUNIOR   Data  Scientist  ")
    'Data Scientist'
    """
    text = title.strip()

    for pat in _SENIORITY_PATTERNS:
        text = pat.sub("", text)

    text = _LEVEL_PATTERN.sub("", text)

    # Collapse runs of whitespace / stray separators.
    text = _EXTRA_WHITESPACE.sub(" ", text).strip()
    text = _SURROUNDING_PUNCTUATION.sub("", text).strip()

    return text.title()


# ── Company normalization ────────────────────────────────────────────────────

# Legal suffixes to strip.  Order matters: longer suffixes first so that
# "Pvt. Ltd." is matched before a bare "Ltd.".
_COMPANY_SUFFIXES = re.compile(
    r",?\s*\b(?:"
    r"Private\s+Limited|Pvt\.?\s*Ltd\.?|Ltd\.?|Limited|"
    r"Incorporated|Inc\.?|"
    r"Corporation|Corp\.?|"
    r"L\.?L\.?C\.?|"
    r"GmbH|AG|S\.?A\.?|S\.?L\.?|"
    r"PLC|LLP|LP|"
    r"Co\.?|Company"
    r")\s*$",
    re.IGNORECASE,
)

_TRAILING_PUNCTUATION = re.compile(r"[,.\s]+$")


def normalize_company(company: str) -> str:
    """Strip legal suffixes, extra whitespace, and title-case the result.

    >>> normalize_company("Google Inc.")
    'Google'
    >>> normalize_company("Tata Consultancy Services Pvt. Ltd.")
    'Tata Consultancy Services'
    """
    text = company.strip()
    text = _COMPANY_SUFFIXES.sub("", text)
    text = _TRAILING_PUNCTUATION.sub("", text)
    text = _EXTRA_WHITESPACE.sub(" ", text).strip()
    return text.title()


# ── Location normalization ───────────────────────────────────────────────────

# City alias map: common alternative names -> canonical form.
_CITY_ALIASES: dict[str, str] = {
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "bombay": "Mumbai",
    "mumbai": "Mumbai",
    "calcutta": "Kolkata",
    "kolkata": "Kolkata",
    "madras": "Chennai",
    "chennai": "Chennai",
    "nyc": "New York",
    "new york city": "New York",
    "new york": "New York",
    "sf": "San Francisco",
    "san francisco": "San Francisco",
    "la": "Los Angeles",
    "los angeles": "Los Angeles",
    "dc": "Washington",
    "washington dc": "Washington",
    "washington d.c.": "Washington",
    "london": "London",
    "berlin": "Berlin",
    "tokyo": "Tokyo",
    "singapore": "Singapore",
    "sydney": "Sydney",
    "toronto": "Toronto",
    "vancouver": "Vancouver",
    "amsterdam": "Amsterdam",
    "dublin": "Dublin",
    "paris": "Paris",
    "gurgaon": "Gurugram",
    "gurugram": "Gurugram",
    "noida": "Noida",
    "hyderabad": "Hyderabad",
    "pune": "Pune",
}

# Country alias map (short forms -> canonical).
_COUNTRY_ALIASES: dict[str, str] = {
    "us": "United States",
    "usa": "United States",
    "u.s.": "United States",
    "u.s.a.": "United States",
    "united states of america": "United States",
    "united states": "United States",
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "united kingdom": "United Kingdom",
    "india": "India",
    "in": "India",
    "germany": "Germany",
    "de": "Germany",
    "canada": "Canada",
    "ca": "Canada",
    "australia": "Australia",
    "au": "Australia",
    "singapore": "Singapore",
    "sg": "Singapore",
    "japan": "Japan",
    "jp": "Japan",
    "france": "France",
    "fr": "France",
    "netherlands": "Netherlands",
    "nl": "Netherlands",
    "ireland": "Ireland",
    "ie": "Ireland",
}

# State / region abbreviations commonly seen in US locations.
_US_STATE_ABBRS: dict[str, str] = {
    "ca": "CA",
    "ny": "NY",
    "tx": "TX",
    "wa": "WA",
    "il": "IL",
    "ma": "MA",
    "co": "CO",
    "ga": "GA",
    "pa": "PA",
    "nc": "NC",
    "va": "VA",
    "fl": "FL",
    "or": "OR",
    "oh": "OH",
    "mi": "MI",
    "az": "AZ",
    "mn": "MN",
    "md": "MD",
    "nj": "NJ",
    "ct": "CT",
}


def normalize_location(location: str) -> str:
    """Extract city + country standard forms, handling common variations.

    >>> normalize_location("Bengaluru, India")
    'Bengaluru, India'
    >>> normalize_location("NYC, US")
    'New York, United States'
    >>> normalize_location("Bangalore, IN")
    'Bengaluru, India'
    """
    if not location or not location.strip():
        return ""

    text = location.strip()

    # Split on comma to separate parts (city, state/country).
    parts = [p.strip() for p in text.split(",") if p.strip()]

    if not parts:
        return ""

    # Attempt to resolve the *first* part as a city.
    city_raw = parts[0]
    city_key = city_raw.lower().strip()
    city = _CITY_ALIASES.get(city_key, city_raw.title())

    # Attempt to resolve the *last* part as a country (or state).
    country = ""
    if len(parts) >= 2:
        last_raw = parts[-1].strip()
        last_key = last_raw.lower().strip().rstrip(".")

        # Check country aliases first.
        if last_key in _COUNTRY_ALIASES:
            country = _COUNTRY_ALIASES[last_key]
        elif last_key in _US_STATE_ABBRS or last_key.upper() in _US_STATE_ABBRS.values():
            # It's a US state abbreviation -- normalise to "United States".
            state = _US_STATE_ABBRS.get(last_key, last_key.upper())
            country = "United States"
            # If there was a middle part (city, state, country), keep state.
            if len(parts) == 2:
                return f"{city}, {state}, United States"
        else:
            country = last_raw.title()

    if country:
        return f"{city}, {country}"

    return city
