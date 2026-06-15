"""Plain-language imaging summaries for review UI."""

from __future__ import annotations

from typing import Any

FINDING_LABELS: dict[str, str] = {
    "pneumothorax": "Pneumothorax",
    "opacity": "Lung opacity",
    "pleural_effusion": "Pleural effusion",
    "nodule": "Lung nodule or mass",
    "cardiomegaly": "Enlarged heart (cardiomegaly)",
}


def format_imaging_summary(imaging: dict[str, Any] | None) -> str:
    """Build a physician-review headline from chest X-ray findings."""
    if not imaging or imaging.get("skipped"):
        return "Chest X-ray uploaded — imaging analysis was not run. Please re-upload as a chest X-ray."

    if imaging.get("proof", {}).get("is_fallback") or str(
        imaging.get("model_version", "")
    ).startswith("fallback"):
        return (
            "Chest X-ray uploaded — AI model is in fallback mode. "
            "No reliable pathology scores are available; radiologist review required."
        )

    findings = imaging.get("findings") or {}
    detected: list[str] = []
    for key, data in findings.items():
        if not isinstance(data, dict) or not data.get("detected"):
            continue
        label = FINDING_LABELS.get(key, key.replace("_", " ").title())
        pct = int(round((data.get("probability") or 0) * 100))
        detected.append(f"{label} ({pct}% confidence)")

    if detected:
        return (
            "Chest X-ray review: "
            + "; ".join(detected[:4])
            + ". Radiologist confirmation required."
        )
    return (
        "Chest X-ray review: no findings exceeded the alert threshold. "
        "A doctor should still review the image."
    )


def imaging_attention_items(imaging: dict[str, Any] | None) -> list[dict[str, str]]:
    """Structured attention items for the findings panel."""
    if not imaging or imaging.get("skipped"):
        return []

    items: list[dict[str, str]] = []
    for key, data in (imaging.get("findings") or {}).items():
        if not isinstance(data, dict) or not data.get("detected"):
            continue
        label = FINDING_LABELS.get(key, key.replace("_", " ").title())
        pct = int(round((data.get("probability") or 0) * 100))
        items.append({
            "test": label,
            "flag": "IMAGE",
            "text": (
                f"AI model estimated {pct}% likelihood. "
                "This is not a diagnosis — correlate with symptoms and imaging review."
            ),
        })
    return items
