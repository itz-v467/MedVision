"""Optional OpenAI extraction for lab values missed by regex/OCR parsing."""

from __future__ import annotations

import json
import re
from typing import Any

from backend.client.openai_client import get_openai_client
from backend.config import get_settings
from backend.logger import get_logger
from backend.utils.lab_catalog import LAB_CATALOG

logger = get_logger()

LAB_EXTRACTION_SYSTEM = (
    "You extract structured blood test results from OCR text of laboratory reports. "
    "Return ONLY valid JSON. Never invent values not present in the text. "
    "Map synonyms to canonical test names (e.g. SGPT->ALT, SGOT->AST, BUN->Urea, PCV->Hematocrit). "
    "Use plain numbers without commas (226000 not 2,26,000). "
    "Physician review is required; this is decision support only."
)


def resolve_canonical_name(raw_name: str) -> str | None:
    """Map OCR/LLM label to a catalog test name."""
    token = raw_name.strip().lower()
    if not token:
        return None
    for name, cfg in LAB_CATALOG.items():
        if name.lower() == token:
            return name
        for alias in cfg.get("aliases", []):
            if alias.lower() == token:
                return name
    return None


def merge_biomarker_lists(
    primary: list[dict[str, Any]],
    secondary: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Merge regex-parsed results with LLM extras. Primary wins on name conflicts."""
    merged: dict[str, dict[str, Any]] = {}
    for item in primary:
        name = item.get("name")
        if name:
            merged[name] = dict(item)

    added: list[str] = []
    for item in secondary:
        name = resolve_canonical_name(str(item.get("name", "")))
        if not name or name in merged:
            continue
        try:
            value = float(item["value"])
        except (KeyError, TypeError, ValueError):
            continue
        merged[name] = {
            "name": name,
            "value": value,
            "unit": str(item.get("unit", "") or ""),
            "extraction_source": "openai",
        }
        added.append(name)

    return sorted(merged.values(), key=lambda row: row["name"]), added


def extract_biomarkers_with_llm(raw_text: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Call OpenAI to extract biomarkers from OCR text. Returns (biomarkers, metadata)."""
    settings = get_settings()
    meta: dict[str, Any] = {
        "used": False,
        "added_tests": [],
        "model": settings.openai_llm_model,
        "error": None,
    }
    if not settings.openai_enabled or not settings.openai_lab_extraction_enabled:
        return [], meta
    if not raw_text.strip():
        return [], meta

    client = get_openai_client()
    canonical_names = ", ".join(sorted(LAB_CATALOG.keys()))
    user_prompt = (
        f"Extract all blood test results from this OCR lab report text.\n\n"
        f"Use ONLY these canonical names: {canonical_names}\n\n"
        f'Return JSON: {{"biomarkers": [{{"name": "...", "value": 0.0, "unit": "..."}}]}}\n\n'
        f"OCR TEXT:\n{raw_text[:12000]}"
    )

    try:
        payload = client.extract_structured_json(
            system_prompt=LAB_EXTRACTION_SYSTEM,
            user_prompt=user_prompt,
            max_tokens=2000,
        )
        meta["used"] = True
        biomarkers = _parse_llm_payload(payload)
        meta["raw_count"] = len(biomarkers)
        return biomarkers, meta
    except Exception as exc:
        logger.warning("OpenAI lab extraction failed: %s", exc)
        meta["error"] = str(exc)
        return [], meta


def _parse_llm_payload(payload: Any) -> list[dict[str, Any]]:
    """Normalize LLM JSON into raw biomarker dicts."""
    if isinstance(payload, str):
        payload = _load_json_from_text(payload)
    if not isinstance(payload, dict):
        return []

    rows = payload.get("biomarkers", payload.get("tests", []))
    if not isinstance(rows, list):
        return []

    parsed: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = resolve_canonical_name(str(row.get("name", "")))
        if not name:
            continue
        value = _coerce_number(row.get("value"))
        if value is None:
            continue
        parsed.append(
            {
                "name": name,
                "value": value,
                "unit": str(row.get("unit", "") or LAB_CATALOG[name].get("unit", "")),
            }
        )
    return parsed


def _coerce_number(value: Any) -> float | None:
    """Parse numeric lab values from LLM output."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace(",", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _load_json_from_text(text: str) -> Any:
    """Parse JSON, tolerating markdown code fences."""
    stripped = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, re.DOTALL)
    if fence:
        stripped = fence.group(1)
    return json.loads(stripped)
