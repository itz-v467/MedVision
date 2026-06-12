"""Compare entered patient name with OCR-extracted name."""

from __future__ import annotations

import re
from typing import Any

PLACEHOLDER_NAMES = {"", "unknown patient", "unknown", "patient", "n/a", "na", "none"}


def normalize_name(name: str) -> str:
    """Lowercase, strip titles and punctuation for comparison."""
    token = name.lower().strip()
    for prefix in ("mr.", "mrs.", "ms.", "dr.", "mr ", "mrs ", "ms ", "dr "):
        if token.startswith(prefix):
            token = token[len(prefix) :].strip()
    token = re.sub(r"[^a-z\s]", "", token)
    return " ".join(token.split())


def compare_patient_names(entered: str, extracted: str) -> dict[str, Any]:
    """Return match result with confidence score and user-facing message."""
    entered_norm = normalize_name(entered)
    extracted_norm = normalize_name(extracted)

    if entered_norm in PLACEHOLDER_NAMES:
        return {
            "matched": False,
            "confidence": 0.0,
            "message": "Please enter the patient's full name as shown on the report.",
            "entered_name": entered,
            "extracted_name": extracted,
            "skipped": False,
            "blocks_upload": True,
        }

    if not extracted_norm:
        return {
            "matched": True,
            "confidence": 1.0,
            "message": "We could not read the name from the document. Please confirm it is the correct report.",
            "entered_name": entered,
            "extracted_name": "",
            "skipped": True,
            "blocks_upload": False,
        }

    if entered_norm == extracted_norm:
        return _result(True, 1.0, entered, extracted, "")

    entered_tokens = set(entered_norm.split())
    extracted_tokens = set(extracted_norm.split())
    if entered_tokens and extracted_tokens:
        overlap = len(entered_tokens & extracted_tokens) / max(
            len(entered_tokens), len(extracted_tokens)
        )
        if overlap >= 0.67:
            return _result(
                True,
                round(overlap, 2),
                entered,
                extracted,
                "Name on the form matches the report.",
            )

    return _result(
        False,
        0.0,
        entered,
        extracted,
        (
            f"The name you entered ({entered.strip()}) does not match the name on the "
            f"report ({extracted.strip()}). Please check you uploaded the correct document."
        ),
        blocks_upload=False,
    )


def _result(
    matched: bool,
    confidence: float,
    entered: str,
    extracted: str,
    message: str,
    *,
    blocks_upload: bool = False,
) -> dict[str, Any]:
    return {
        "matched": matched,
        "confidence": confidence,
        "message": message,
        "entered_name": entered,
        "extracted_name": extracted,
        "skipped": False,
        "blocks_upload": blocks_upload,
        "warning_only": not matched and not blocks_upload,
    }
