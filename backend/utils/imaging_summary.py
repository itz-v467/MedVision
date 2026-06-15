"""Plain-language imaging summaries for review UI."""

from __future__ import annotations

from typing import Any

FINDING_LABELS: dict[str, str] = {
    "pneumothorax": "Pneumothorax",
    "opacity": "Lung opacity / pneumonia pattern",
    "pleural_effusion": "Pleural effusion",
    "nodule": "Lung nodule or mass",
    "cardiomegaly": "Enlarged heart (cardiomegaly)",
}


def format_imaging_summary(imaging: dict[str, Any] | None) -> str:
    """Build a physician-review headline from chest X-ray findings."""
    if not imaging or imaging.get("skipped"):
        return "Chest X-ray uploaded — imaging analysis was not run. Please re-upload as a chest X-ray."

    findings = imaging.get("findings") or {}
    detected: list[str] = []
    for key, data in findings.items():
        if not isinstance(data, dict):
            continue
        label = FINDING_LABELS.get(key, key.replace("_", " ").title())
        pct = int(round((data.get("probability") or 0) * 100))
        if data.get("detected"):
            detected.append(f"{label} ({pct}% confidence)")
        elif pct >= 40:
            detected.append(f"Possible {label.lower()} ({pct}% confidence)")

    if detected:
        return (
            "Chest X-ray review: "
            + "; ".join(detected[:4])
            + ". Radiologist confirmation required."
        )
    return (
        "Chest X-ray review: no findings exceeded the automatic alert threshold. "
        "A doctor should still review the image."
    )


def imaging_attention_items(imaging: dict[str, Any] | None) -> list[dict[str, str]]:
    """Structured attention items for the findings panel."""
    if not imaging or imaging.get("skipped"):
        return []

    items: list[dict[str, str]] = []
    for key, data in (imaging.get("findings") or {}).items():
        if not isinstance(data, dict):
            continue
        if not data.get("detected") and (data.get("probability") or 0) < 0.4:
            continue
        label = FINDING_LABELS.get(key, key.replace("_", " ").title())
        pct = int(round((data.get("probability") or 0) * 100))
        items.append({
            "test": label,
            "flag": "IMAGE" if data.get("detected") else "WATCH",
            "text": (
                f"AI model estimated {pct}% likelihood. "
                "This is not a diagnosis — correlate with symptoms and imaging review."
            ),
        })
    return items
