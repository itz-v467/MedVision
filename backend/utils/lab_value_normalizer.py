"""Normalize lab values to standard clinical units before range comparison."""

from __future__ import annotations

import re
from typing import Any

from backend.utils.lab_catalog import LAB_CATALOG

STANDARD_UNITS: dict[str, str] = {
    name: str(cfg["unit"]) for name, cfg in LAB_CATALOG.items()
}


def normalize_biomarker(
    name: str, value: float, unit: str = ""
) -> dict[str, Any]:
    """Convert raw OCR value to standard scale for the test."""
    unit_lower = (unit or "").lower().replace(" ", "")
    raw_value = value
    raw_unit = unit or ""
    note = ""

    if name == "Platelets":
        value, note = _normalize_cell_count(value, unit_lower, 150, 400, "10^3/uL")
    elif name == "WBC":
        value, note = _normalize_cell_count(value, unit_lower, 4.5, 11.0, "10^3/uL")
    elif name == "RBC":
        if value > 20 and "/ul" not in unit_lower:
            value = value / 1_000_000
            note = "Converted from absolute count to 10^6/uL"
        elif value > 20:
            value = value / 1_000_000
            note = "Scaled to 10^6/uL"
    elif name == "Glucose":
        if "mmol" in unit_lower:
            value = value * 18.018
            note = "Converted mmol/L to mg/dL"
        elif value < 20 and not unit_lower:
            value = value * 18.018
            note = "Assumed mmol/L, converted to mg/dL"
    elif name == "Hemoglobin":
        if value > 25 and ("g/l" in unit_lower or not unit_lower):
            value = value / 10.0
            note = "Converted g/L to g/dL"
    elif name == "Creatinine":
        if "umol" in unit_lower or "µmol" in unit_lower:
            value = value / 88.4
            note = "Converted µmol/L to mg/dL"
    elif name == "Urea":
        if "mmol" in unit_lower:
            value = value * 6.006
            note = "Converted mmol/L to mg/dL (urea)"
    elif name == "Vitamin D":
        if "nmol" in unit_lower:
            value = value / 2.496
            note = "Converted nmol/L to ng/mL"

    standard_unit = STANDARD_UNITS.get(name, unit or "")
    return {
        "value": round(value, 3),
        "unit": standard_unit,
        "raw_value": raw_value,
        "raw_unit": raw_unit,
        "normalization_note": note,
    }


def _normalize_cell_count(
    value: float,
    unit_lower: str,
    low: float,
    high: float,
    target_unit: str,
) -> tuple[float, str]:
    """Normalize WBC/platelet counts to 10^3/uL scale."""
    if value >= 10_000:
        return value / 1000.0, f"Converted absolute count ({value:g}) to {target_unit}"
    if value > high * 10 and value < 10_000:
        return value / 1000.0, f"Scaled {value:g} to {target_unit} (÷1000)"
    if low <= value <= high:
        return value, ""
    if value > high and value < low * 1000:
        scaled = value / 1000.0
        if low <= scaled <= high:
            return scaled, f"Converted {value:g} to {scaled:g} {target_unit}"
    return value, ""


def clean_ocr_lab_text(text: str) -> str:
    """Fix common OCR artifacts in lab reports."""
    if not text:
        return text
    cleaned = text
    # Remove Indian-style commas in numbers: 2,26,000 -> 226000
    cleaned = re.sub(r"(\d),(\d{2}),(\d{3})\b", r"\1\2\3", cleaned)
    cleaned = re.sub(r"(\d),(\d{3})\b", r"\1\2", cleaned)
    replacements = [
        (r"(\d+(?:\.\d+)?)\s*gdL", r"\1 g/dL"),
        (r"(\d+(?:\.\d+)?)\s*mgdl", r"\1 mg/dL"),
        (r"(\d+(?:\.\d+)?)\s*mg/dL", r"\1 mg/dL"),
        (r"platelet(?:s)?\s*[:\-]?\s*", "platelets "),
        (r"haemoglobin", "hemoglobin"),
        (r"\bhgb\b", "hemoglobin"),
        (r"\bplt\b", "platelets"),
        (r"/cumm", "/cu mm"),
    ]
    for pattern, repl in replacements:
        cleaned = re.sub(pattern, repl, cleaned, flags=re.IGNORECASE)
    return cleaned
