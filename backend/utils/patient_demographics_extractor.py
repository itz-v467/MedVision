"""Extract patient identity fields from OCR lab report text."""

from __future__ import annotations

import re
from typing import Any

# Lab report name labels — avoid bare "name:" which matches test names in tables.
NAME_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"(?i)(?:patient\s*name|name\s*of\s*(?:the\s*)?patient|pt\.?\s*name|"
        r"patient(?:\'s)?\s*name)\s*[:\-]\s*([A-Za-z][A-Za-z\s\.\']{1,60})"
    ),
    re.compile(
        r"(?i)^\s*name\s+([A-Za-z][A-Za-z\s\.\']{1,60}?)\s+(?:age|sex|gender|dob|mrn|uhid)",
        re.MULTILINE,
    ),
]

INVALID_NAME_TERMS = frozenset({
    "glucose", "hemoglobin", "blood", "report", "laboratory", "lab", "test",
    "sample", "male", "female", "years", "year", "patient", "doctor", "ref",
    "range", "normal", "abnormal", "platelet", "serum", "urine", "fasting",
})

AGE_PATTERN = re.compile(
    r"(?i)(?:age|aged)\s*[:\-]?\s*(\d{1,3})\s*(?:years?|yrs?|y)?\b"
)
GENDER_PATTERN = re.compile(
    r"(?i)(?:sex|gender)\s*[:\-]?\s*(male|female|other|m|f)\b"
)
MRN_PATTERN = re.compile(
    r"(?i)(?:mrn|uhid|patient\s*id|hospital\s*id)\s*[:\-]\s*([A-Za-z0-9\-/]+)"
)


def extract_patient_demographics(text: str) -> dict[str, Any]:
    """Parse patient name and related demographics from OCR text."""
    if not text or not text.strip():
        return {}

    demographics: dict[str, Any] = {}
    for pattern in NAME_PATTERNS:
        match = pattern.search(text)
        if match:
            name = _clean_name(match.group(1))
            if len(name) >= 3 and _is_plausible_patient_name(name):
                demographics["full_name"] = name
                demographics["name_extraction_confidence"] = "high"
                break

    age_match = AGE_PATTERN.search(text)
    if age_match:
        demographics["age"] = age_match.group(1)

    gender_match = GENDER_PATTERN.search(text)
    if gender_match:
        token = gender_match.group(1).lower()
        demographics["gender"] = {
            "m": "Male",
            "f": "Female",
            "male": "Male",
            "female": "Female",
        }.get(token, gender_match.group(1).title())

    mrn_match = MRN_PATTERN.search(text)
    if mrn_match:
        demographics["medical_record_id"] = mrn_match.group(1).strip()

    return demographics


def _is_plausible_patient_name(name: str) -> bool:
    """Reject OCR false positives such as test names."""
    tokens = [t.lower() for t in name.split() if t]
    if not tokens or len(tokens) > 5:
        return False
    if any(token in INVALID_NAME_TERMS for token in tokens):
        return False
    if any(not token.replace(".", "").replace("'", "").isalpha() for token in tokens):
        return False
    return True


def _clean_name(raw: str) -> str:
    """Normalize extracted patient name."""
    name = re.sub(r"\s+", " ", raw).strip(" .,-")
    name = re.sub(r"(?i)\b(age|sex|gender|years?)\b.*$", "", name).strip()
    return name.title() if name.isupper() or name.islower() else name
