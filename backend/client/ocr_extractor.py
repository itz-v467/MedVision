"""Document text extraction for OCR pipeline."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

from backend.client.document_ocr_client import extract_image_text, extract_pdf_text
from backend.client.lab_text_parser import (
    build_alias_map,
    parse_by_core_patterns,
    parse_lines_by_alias,
    parse_numeric,
)
from backend.logger import get_logger
from backend.utils.lab_reference_ranges import REFERENCE_RANGES, enrich_biomarkers
from backend.utils.lab_value_normalizer import clean_ocr_lab_text, normalize_biomarker

logger = get_logger()


NAME_ALIASES: dict[str, str] = build_alias_map()

DISEASE_KEYWORDS = [
    "pneumonia",
    "diabetes",
    "anemia",
    "tuberculosis",
    "hypertension",
    "copd",
    "asthma",
]
SYMPTOM_KEYWORDS = [
    "cough",
    "fever",
    "dyspnea",
    "chest pain",
    "fatigue",
    "nausea",
]
MEDICATION_KEYWORDS = [
    "amoxicillin",
    "metformin",
    "aspirin",
    "ibuprofen",
    "insulin",
    "azithromycin",
]
ALLERGY_KEYWORDS = ["penicillin", "sulfa", "latex", "peanut", "shellfish"]

ICD10_MAP = {
    "pneumonia": "J18.9",
    "diabetes": "E11.9",
    "anemia": "D64.9",
    "tuberculosis": "A15.0",
    "hypertension": "I10",
}
SNOMED_MAP = {
    "pneumonia": "233604007",
    "diabetes": "73211009",
    "anemia": "271737000",
    "tuberculosis": "56717001",
    "hypertension": "38341003",
}

def extract_text_from_file(storage_path: str, mime_type: str) -> tuple[str, float, str]:
    """Extract raw text from uploaded clinical files.

    Returns:
        Tuple of raw text, confidence, and extraction method name.
    """
    path = Path(storage_path)
    if not path.exists():
        return "", 0.0, "missing_file"

    if mime_type == "text/plain":
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
        return text, (0.95 if text else 0.3), "plain_text"

    if mime_type == "text/csv":
        text = _extract_csv_text(path)
        return text, (0.9 if text else 0.3), "csv"

    if mime_type == "application/pdf":
        return extract_pdf_text(path)

    if mime_type in {"image/png", "image/jpeg"}:
        return extract_image_text(path)

    return "", 0.2, "unsupported"


_parse_numeric = parse_numeric


def _pick_best_reading(name: str, candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Choose the most plausible OCR reading after unit normalization."""
    if not candidates:
        return None
    ref = REFERENCE_RANGES.get(name)
    best: dict[str, Any] | None = None
    best_score = -1
    for candidate in candidates:
        norm = normalize_biomarker(name, candidate["value"], candidate.get("unit", ""))
        value = float(norm["value"])
        score = 0
        if ref:
            low, high = float(ref["low"]), float(ref["high"])
            if low <= value <= high:
                score += 3
            elif value < low * 0.5 or value > high * 50:
                score -= 2
        if norm.get("normalization_note"):
            score += 1
        if best is None or score > best_score:
            best = {**candidate, "value": value, "unit": norm["unit"]}
            best_score = score
    return best


def parse_biomarkers(text: str) -> list[dict[str, Any]]:
    """Parse all lab biomarkers from OCR text with unit normalization."""
    text = clean_ocr_lab_text(text)
    candidates_by_name: dict[str, list[dict[str, Any]]] = {}

    for row in parse_by_core_patterns(text):
        candidates_by_name.setdefault(row["name"], []).append(row)
    for row in parse_lines_by_alias(text, NAME_ALIASES):
        candidates_by_name.setdefault(row["name"], []).append(row)

    biomarkers: list[dict[str, Any]] = []
    for name, candidates in candidates_by_name.items():
        picked = _pick_best_reading(name, candidates)
        if picked:
            biomarkers.append(picked)

    biomarkers.sort(key=lambda item: item["name"])
    logger.debug("Parsed %d biomarkers from OCR text (%d chars)", len(biomarkers), len(text))
    return enrich_biomarkers(biomarkers)


def extraction_warning_for_text(text: str, mime_type: str, method: str = "") -> str | None:
    """Return a user-facing warning when extraction likely failed."""
    if text.strip():
        return None
    if mime_type == "application/pdf":
        return (
            "We could not read this PDF. Try a clearer scan or photo, "
            "or upload a text-based PDF. Ask your lab for a digital copy if possible."
        )
    if mime_type in {"image/png", "image/jpeg"}:
        return (
            "We could not read text from this image. Use good lighting, "
            "a flat photo of the full report, and try again."
        )
    if method == "none":
        return "No clinical text could be extracted from this file."
    return "No clinical text could be extracted from this file."


def extract_clinical_entities(text: str) -> dict[str, Any]:
    """Extract rule-based clinical entities from free text."""
    lowered = text.lower()
    diseases = [term.title() for term in DISEASE_KEYWORDS if term in lowered]
    symptoms = [term.title() for term in SYMPTOM_KEYWORDS if term in lowered]
    medications = [term.title() for term in MEDICATION_KEYWORDS if term in lowered]
    allergies = [term.title() for term in ALLERGY_KEYWORDS if term in lowered]

    icd10_codes = {
        disease: ICD10_MAP[disease.lower()]
        for disease in diseases
        if disease.lower() in ICD10_MAP
    }
    snomed_codes = {
        disease: SNOMED_MAP[disease.lower()]
        for disease in diseases
        if disease.lower() in SNOMED_MAP
    }
    confidence = 0.35
    if not text.strip():
        confidence = 0.2
    elif diseases or symptoms or medications:
        confidence = 0.82
    elif len(text.strip()) > 50:
        confidence = 0.65
    if len(text.strip()) > 100:
        confidence = min(confidence + 0.05, 0.92)

    return {
        "entities": {
            "diseases": diseases,
            "symptoms": symptoms,
            "medications": medications,
            "allergies": allergies,
        },
        "icd10_codes": icd10_codes,
        "snomed_codes": snomed_codes,
        "confidence": round(confidence, 4),
    }


def _extract_csv_text(path: Path) -> str:
    """Flatten CSV rows to text."""
    lines: list[str] = []
    with path.open(encoding="utf-8", errors="ignore") as handle:
        reader = csv.reader(handle)
        for row in reader:
            lines.append(", ".join(row))
    return "\n".join(lines)
