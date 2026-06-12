"""Reliable lab value parsing from OCR text (medical report formats)."""

from __future__ import annotations

import re
from typing import Any

from backend.utils.lab_catalog import LAB_CATALOG

# Hand-tested patterns for common Indian/international lab reports.
CORE_PATTERNS: list[tuple[str, str, str]] = [
    (r"(?i)(?:hemoglobin|hgb|hb)\b[\s:=-]*([\d,]+(?:\.\d+)?)\s*(g/dL|g/dl|gm%)?", "Hemoglobin", "g/dL"),
    (r"(?i)(?:glucose|fasting glucose|blood sugar|fbs|rbs)\b[\s:=-]*([\d,]+(?:\.\d+)?)\s*(mg/dL|mg/dl|mmol/L)?", "Glucose", "mg/dL"),
    (r"(?i)\bwbc\b[\s:=-]*([\d,]+(?:\.\d+)?)\s*(10\^?3/?uL|/cumm|/cu\.?mm|thou)?", "WBC", "10^3/uL"),
    (r"(?i)\brbc\b[\s:=-]*([\d,]+(?:\.\d+)?)\s*(10\^?6/?uL|million/cumm)?", "RBC", "10^6/uL"),
    (r"(?i)(?:platelet(?:s)?|plt)\b[\s:=-]*([\d,]+(?:\.\d+)?)\s*(10\^?3/?uL|/cumm)?", "Platelets", "10^3/uL"),
    (r"(?i)(?:hematocrit|hct|pcv)\b[\s:=-]*([\d,]+(?:\.\d+)?)\s*%?", "Hematocrit", "%"),
    (r"(?i)\bmcv\b[\s:=-]*([\d,]+(?:\.\d+)?)\s*(fL|fl)?", "MCV", "fL"),
    (r"(?i)\bmch\b[\s:=-]*([\d,]+(?:\.\d+)?)\s*(pg)?", "MCH", "pg"),
    (r"(?i)\bmchc\b[\s:=-]*([\d,]+(?:\.\d+)?)\s*(g/dL)?", "MCHC", "g/dL"),
    (r"(?i)\brdw\b[\s:=-]*([\d,]+(?:\.\d+)?)\s*%?", "RDW", "%"),
    (r"(?i)(?:creatinine|s\.?\s*creatinine)\b[\s:=-]*([\d,]+(?:\.\d+)?)\s*(mg/dL|mg/dl)?", "Creatinine", "mg/dL"),
    (r"(?i)(?:urea|bun|blood urea)\b[\s:=-]*([\d,]+(?:\.\d+)?)\s*(mg/dL|mg/dl)?", "Urea", "mg/dL"),
    (r"(?i)(?:alt|sgpt)\b[\s:=-]*([\d,]+(?:\.\d+)?)\s*(U/L|IU/L)?", "ALT", "U/L"),
    (r"(?i)(?:ast|sgot)\b[\s:=-]*([\d,]+(?:\.\d+)?)\s*(U/L|IU/L)?", "AST", "U/L"),
    (r"(?i)(?:bilirubin|total bilirubin)\b[\s:=-]*([\d,]+(?:\.\d+)?)\s*(mg/dL|mg/dl)?", "Bilirubin", "mg/dL"),
    (r"(?i)(?:cholesterol|total cholesterol)\b[\s:=-]*([\d,]+(?:\.\d+)?)\s*(mg/dL|mg/dl)?", "Cholesterol", "mg/dL"),
    (r"(?i)\bhdl\b[\s:=-]*([\d,]+(?:\.\d+)?)\s*(mg/dL|mg/dl)?", "HDL", "mg/dL"),
    (r"(?i)\bldl\b[\s:=-]*([\d,]+(?:\.\d+)?)\s*(mg/dL|mg/dl)?", "LDL", "mg/dL"),
    (r"(?i)(?:triglycerides|tg)\b[\s:=-]*([\d,]+(?:\.\d+)?)\s*(mg/dL|mg/dl)?", "Triglycerides", "mg/dL"),
    (r"(?i)\btsh\b[\s:=-]*([\d,]+(?:\.\d+)?)\s*(mIU/L|uIU/mL)?", "TSH", "mIU/L"),
    (r"(?i)(?:vitamin d|vit d|25[\s\-]*oh vitamin d)\b[\s:=-]*([\d,]+(?:\.\d+)?)\s*(ng/mL|nmol/L)?", "Vitamin D", "ng/mL"),
    (r"(?i)(?:hba1c|hb a1c)\b[\s:=-]*([\d,]+(?:\.\d+)?)\s*%?", "HbA1c", "%"),
]

UNIT_HINTS = (
    "mg/dl", "mg/dL", "g/dl", "g/dL", "u/l", "U/L", "iu/l", "IU/L",
    "meq/l", "mEq/L", "ng/ml", "ng/mL", "pg/ml", "pg/mL", "%", "fl", "fL",
    "pg", "/cumm", "cumm", "mmol/l",
)


def build_alias_map() -> dict[str, str]:
    """Map report labels to canonical test names (longest match first)."""
    aliases: dict[str, str] = {}
    for name, cfg in LAB_CATALOG.items():
        for alias in cfg.get("aliases", []):
            key = alias.lower().strip()
            if len(key) >= 2:
                aliases[key] = name
    return aliases


def parse_numeric(raw: str) -> float | None:
    """Parse numbers with comma grouping (e.g. 2,26,000)."""
    cleaned = raw.replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_lines_by_alias(text: str, alias_map: dict[str, str]) -> list[dict[str, Any]]:
    """Parse table rows by matching known test names at line start."""
    rows: list[dict[str, Any]] = []
    sorted_aliases = sorted(alias_map.keys(), key=len, reverse=True)

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or len(stripped) < 4:
            continue
        lower = stripped.lower()

        for alias in sorted_aliases:
            if len(alias) < 3 and alias not in {"hb", "alt", "ast", "mch", "mcv", "rdw", "tsh", "hdl", "ldl", "tg", "wbc", "rbc", "cl", "na", "k"}:
                continue
            if not (lower.startswith(alias + " ") or lower.startswith(alias + ":") or lower.startswith(alias + "-") or lower == alias):
                continue
            if lower.startswith(alias):
                remainder = stripped[len(alias):].lstrip(" :|-\t")
            else:
                continue

            value, unit = _extract_value_unit(remainder)
            if value is None:
                continue
            rows.append({"name": alias_map[alias], "value": value, "unit": unit})
            break

    return rows


def _extract_value_unit(fragment: str) -> tuple[float | None, str]:
    """Pull numeric value and optional unit from remainder of a lab row."""
    if not fragment:
        return None, ""

    parts = re.split(r"\s{2,}|\t", fragment.strip())
    token = parts[0] if parts else fragment

    num_match = re.search(r"([\d,]+(?:\.\d+)?)", token)
    if not num_match:
        return None, ""

    value = parse_numeric(num_match.group(1))
    if value is None:
        return None, ""

    unit = ""
    after = token[num_match.end():].strip()
    if after:
        unit = after
    elif len(parts) > 1:
        unit = parts[1].strip()

    for hint in UNIT_HINTS:
        if hint.lower() in fragment.lower():
            unit = hint
            break

    return value, unit


def parse_by_core_patterns(text: str) -> list[dict[str, Any]]:
    """Apply hand-crafted regex patterns."""
    found: list[dict[str, Any]] = []
    for pattern, name, default_unit in CORE_PATTERNS:
        for match in re.finditer(pattern, text):
            value = parse_numeric(match.group(1))
            if value is None:
                continue
            unit = default_unit
            try:
                if match.group(2):
                    unit = match.group(2).strip()
            except IndexError:
                pass
            found.append({"name": name, "value": value, "unit": unit})
    return found
