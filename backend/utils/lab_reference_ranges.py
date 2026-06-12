"""Adult reference ranges and abnormal/normal classification for lab biomarkers."""

from __future__ import annotations

from typing import Any

from backend.utils.lab_catalog import LAB_CATALOG
from backend.utils.lab_value_normalizer import normalize_biomarker

def _default_note(name: str) -> str:
    cat = LAB_CATALOG.get(name, {}).get("category", "Lab")
    return f"{cat} parameter — compare with local laboratory reference interval."


REFERENCE_RANGES: dict[str, dict[str, Any]] = {
    name: {
        k: cfg[k]
        for k in ("low", "high", "unit", "high_only", "low_only")
        if k in cfg
    }
    for name, cfg in LAB_CATALOG.items()
}

CLINICAL_NOTES: dict[str, str] = {
    name: cfg.get("description", _default_note(name))
    for name, cfg in LAB_CATALOG.items()
}


def get_precaution(name: str, flag: str, is_abnormal: bool) -> str:
    """Return standard precaution text for a test result."""
    catalog = LAB_CATALOG.get(name, {})
    precautions = catalog.get("precautions", {})
    if is_abnormal:
        return precautions.get(
            flag,
            f"Abnormal {name}. Follow up with your physician for correlation and repeat testing.",
        )
    return (
        f"{name} is within standard range. Maintain balanced diet, hydration, sleep, "
        "and routine check-ups."
    )


def classify_biomarker(name: str, value: float) -> dict[str, Any]:
    """Classify a lab value as normal or abnormal with clinical detail."""
    ref = REFERENCE_RANGES.get(name)
    if ref is None:
        return {
            "status": "unknown",
            "flag": "N/A",
            "is_abnormal": False,
            "reference_range": "Not configured",
            "interpretation": "No reference range available for this test.",
            "clinical_note": CLINICAL_NOTES.get(name, ""),
            "precaution": "",
        }

    low = float(ref["low"])
    high = float(ref["high"])
    unit = ref.get("unit", "")
    range_text = f"{low:g}–{high:g} {unit}".strip()

    if ref.get("high_only"):
        if value > high:
            return _abnormal(
                name, value, unit, range_text, "HIGH",
                f"Above desirable limit ({value:g} > {high:g} {unit})",
            )
        return _normal(name, value, unit, range_text, f"Within desirable range (≤ {high:g} {unit})")

    if ref.get("low_only"):
        if value < low:
            return _abnormal(
                name, value, unit, range_text, "LOW",
                f"Below desirable level ({value:g} < {low:g} {unit})",
            )
        return _normal(name, value, unit, range_text, f"At or above desirable level (≥ {low:g} {unit})")

    if value < low:
        return _abnormal(
            name, value, unit, range_text, "LOW",
            f"Below reference range ({value:g} < {low:g} {unit})",
        )
    if value > high:
        return _abnormal(
            name, value, unit, range_text, "HIGH",
            f"Above reference range ({value:g} > {high:g} {unit})",
        )
    return _normal(
        name, value, unit, range_text,
        f"Within reference range ({low:g}–{high:g} {unit})",
    )


def enrich_biomarkers(biomarkers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize units, then attach reference range and classification."""
    enriched: list[dict[str, Any]] = []
    for item in biomarkers:
        name = item.get("name", "")
        raw_value = float(item.get("value", 0))
        raw_unit = str(item.get("unit", "") or "")
        normalized = normalize_biomarker(name, raw_value, raw_unit)
        value = float(normalized["value"])
        classification = classify_biomarker(name, value)
        display = f"{value:g} {normalized['unit']}".strip()
        if normalized.get("normalization_note"):
            classification["interpretation"] = (
                f"{classification['interpretation']} "
                f"({normalized['normalization_note']})"
            ).strip()
        classification["precaution"] = get_precaution(
            name, classification.get("flag", ""), classification.get("is_abnormal", False)
        )
        classification["category"] = LAB_CATALOG.get(name, {}).get("category", "Other")
        enriched.append(
            {
                **item,
                **classification,
                "value": value,
                "unit": normalized["unit"],
                "raw_value": normalized["raw_value"],
                "raw_unit": normalized["raw_unit"],
                "display_value": display,
            }
        )
    return enriched


def summarize_abnormal_results(biomarkers: list[dict[str, Any]]) -> dict[str, Any]:
    """Return counts and list of abnormal findings for summaries."""
    abnormal = [b for b in biomarkers if b.get("is_abnormal")]
    normal = [b for b in biomarkers if b.get("status") == "normal"]
    return {
        "total": len(biomarkers),
        "abnormal_count": len(abnormal),
        "normal_count": len(normal),
        "abnormal": abnormal,
    }


def _normal(name: str, value: float, unit: str, range_text: str, interpretation: str) -> dict[str, Any]:
    return {
        "status": "normal",
        "flag": "NORMAL",
        "is_abnormal": False,
        "reference_range": range_text,
        "interpretation": interpretation,
        "clinical_note": CLINICAL_NOTES.get(name, ""),
        "precaution": get_precaution(name, "NORMAL", False),
        "display_value": f"{value:g} {unit}".strip(),
    }


def _abnormal(
    name: str,
    value: float,
    unit: str,
    range_text: str,
    flag: str,
    interpretation: str,
) -> dict[str, Any]:
    return {
        "status": "abnormal",
        "flag": flag,
        "is_abnormal": True,
        "reference_range": range_text,
        "interpretation": interpretation,
        "clinical_note": CLINICAL_NOTES.get(name, ""),
        "precaution": get_precaution(name, flag, True),
        "display_value": f"{value:g} {unit}".strip(),
    }
