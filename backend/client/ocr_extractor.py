"""Document text extraction for OCR pipeline."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

from backend.logger import get_logger

logger = get_logger()

BIOMARKER_PATTERNS: list[tuple[str, str, str]] = [
    (r"hemoglobin[\s:]*([\d.]+)\s*(g/dL|g/dl)?", "Hemoglobin", "g/dL"),
    (r"glucose[\s:]*([\d.]+)\s*(mg/dL|mg/dl|mmol/L)?", "Glucose", "mg/dL"),
    (r"\bhgb[\s:]*([\d.]+)", "Hemoglobin", "g/dL"),
    (r"\bwbc[\s:]*([\d.]+)", "WBC", "10^3/uL"),
    (r"creatinine[\s:]*([\d.]+)", "Creatinine", "mg/dL"),
]

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


def extract_text_from_file(storage_path: str, mime_type: str) -> tuple[str, float]:
    """Extract raw text from uploaded clinical files.

    Args:
        storage_path: Saved file path.
        mime_type: MIME type of the upload.

    Returns:
        Tuple of raw text and extraction confidence.
    """
    path = Path(storage_path)
    if not path.exists():
        return "", 0.0

    if mime_type == "text/plain":
        text = path.read_text(encoding="utf-8", errors="ignore")
        return text.strip(), 0.95 if text.strip() else 0.3

    if mime_type == "text/csv":
        return _extract_csv_text(path), 0.9

    if mime_type == "application/pdf":
        return _extract_pdf_text(path)

    if mime_type in {"image/png", "image/jpeg"}:
        return _extract_image_text(path)

    return "", 0.2


def parse_biomarkers(text: str) -> list[dict[str, Any]]:
    """Parse lab biomarkers from OCR text."""
    biomarkers: list[dict[str, Any]] = []
    seen: set[str] = set()
    lowered = text.lower()
    for pattern, name, unit in BIOMARKER_PATTERNS:
        match = re.search(pattern, lowered, re.IGNORECASE)
        if match is None or name in seen:
            continue
        seen.add(name)
        try:
            value = float(match.group(1))
        except ValueError:
            continue
        biomarkers.append({"name": name, "value": value, "unit": unit})
    return biomarkers


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
    confidence = 0.55
    if diseases or symptoms or medications:
        confidence = 0.82
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


def _extract_pdf_text(path: Path) -> tuple[str, float]:
    """Extract text from PDF using pdfplumber."""
    try:
        import pdfplumber

        chunks: list[str] = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    chunks.append(page_text)
        text = "\n".join(chunks).strip()
        confidence = 0.88 if text else 0.35
        return text, confidence
    except ImportError:
        logger.warning("pdfplumber not installed; PDF OCR unavailable")
        return "", 0.2
    except Exception as exc:
        logger.warning("PDF extraction failed: %s", exc)
        return "", 0.2


def _extract_image_text(path: Path) -> tuple[str, float]:
    """Extract text from image using pytesseract when available."""
    try:
        import pytesseract
        from PIL import Image

        text = pytesseract.image_to_string(Image.open(path))
        text = text.strip()
        confidence = 0.75 if text else 0.25
        return text, confidence
    except ImportError:
        logger.warning("pytesseract not installed; image OCR unavailable")
        return "", 0.2
    except Exception as exc:
        logger.warning("Image OCR failed: %s", exc)
        return "", 0.2
