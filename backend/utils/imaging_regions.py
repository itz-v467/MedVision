"""Derive clinician-facing anomaly boxes on chest X-rays."""

from __future__ import annotations

from pathlib import Path
from typing import Any

FINDING_LABELS = {
    "pneumothorax": "Pneumothorax",
    "opacity": "Lung opacity / pneumonia",
    "pleural_effusion": "Pleural effusion",
    "nodule": "Lung nodule",
    "cardiomegaly": "Cardiomegaly",
}


def _primary_finding_key(findings: dict[str, dict[str, Any]] | None) -> str | None:
    if not findings:
        return None
    ranked = sorted(
        findings.items(),
        key=lambda item: item[1].get("probability", 0),
        reverse=True,
    )
    for key, data in ranked:
        if data.get("detected") or (data.get("probability", 0) >= 0.35):
            return key
    return ranked[0][0] if ranked else None


def _top_finding_label(findings: dict[str, dict[str, Any]] | None) -> str:
    key = _primary_finding_key(findings)
    if not key:
        return "Area to review"
    return FINDING_LABELS.get(key, key.replace("_", " ").title())


def _normalize_box(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    width: int,
    height: int,
    *,
    label: str,
    finding_key: str | None,
) -> dict[str, Any]:
    pad_x = max(int((x1 - x0) * 0.12), 6)
    pad_y = max(int((y1 - y0) * 0.12), 6)
    left = max(int(x0) - pad_x, 0)
    top = max(int(y0) - pad_y, 0)
    right = min(int(x1) + pad_x, width - 1)
    bottom = min(int(y1) + pad_y, height - 1)
    box_w = max(right - left, int(width * 0.08))
    box_h = max(bottom - top, int(height * 0.08))
    if right - left < box_w:
        center_x = (left + right) / 2
        left = max(int(center_x - box_w / 2), 0)
        right = min(left + box_w, width - 1)
    if bottom - top < box_h:
        center_y = (top + bottom) / 2
        top = max(int(center_y - box_h / 2), 0)
        bottom = min(top + box_h, height - 1)
    return {
        "label": f"{label} — review this area",
        "finding_key": finding_key,
        "x": round(left / width, 4),
        "y": round(top / height, 4),
        "width": round((right - left) / width, 4),
        "height": round((bottom - top) / height, 4),
    }


def derive_anomaly_regions(
    image_path: str,
    findings: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Locate consolidation-style opacities inside the lung fields."""
    path = Path(image_path)
    if not path.is_file():
        return []

    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        return []

    try:
        arr = np.asarray(Image.open(path).convert("L"), dtype=np.float32)
    except Exception:
        return []

    if arr.size == 0:
        return []

    arr = arr - arr.min()
    if arr.max() > 0:
        arr = arr / arr.max()

    height, width = arr.shape
    margin_x = int(width * 0.08)
    margin_y_top = int(height * 0.08)
    margin_y_bottom = int(height * 0.05)
    lung = arr[margin_y_top : height - margin_y_bottom, margin_x : width - margin_x]

    lung_median = float(np.median(lung))
    lung_p75 = float(np.percentile(lung, 75))
    bone_cutoff = float(np.percentile(arr, 96))

    threshold = lung_median + (lung_p75 - lung_median) * 0.5
    threshold = max(threshold, lung_median + 0.05)

    lung_mask = (lung >= threshold) & (lung < bone_cutoff)
    if int(lung_mask.sum()) < 40:
        threshold = max(lung_median + 0.035, float(np.percentile(lung, 82)))
        lung_mask = (lung >= threshold) & (lung < bone_cutoff)

    # Drop edge noise from shoulders and collarbones.
    edge = max(int(min(lung.shape) * 0.08), 4)
    lung_mask[:edge, :] = False
    lung_mask[-edge:, :] = False
    lung_mask[:, :edge] = False
    lung_mask[:, -edge:] = False

    global_mask = np.zeros((height, width), dtype=bool)
    global_mask[
        margin_y_top : height - margin_y_bottom,
        margin_x : width - margin_x,
    ] = lung_mask

    ys, xs = np.where(global_mask)
    label = _top_finding_label(findings)
    finding_key = _primary_finding_key(findings)

    if xs.size < 25:
        return _heuristic_region_for_finding(findings, width, height, label, finding_key)

    x0, x1 = np.percentile(xs, [3, 97])
    y0, y1 = np.percentile(ys, [3, 97])
    return [_normalize_box(x0, y0, x1, y1, width, height, label=label, finding_key=finding_key)]


def _heuristic_region_for_finding(
    findings: dict[str, dict[str, Any]] | None,
    width: int,
    height: int,
    label: str,
    finding_key: str | None,
) -> list[dict[str, Any]]:
    """Place a clinically plausible default box when pixel clustering fails."""
    key = finding_key or "opacity"
    presets: dict[str, tuple[float, float, float, float]] = {
        "opacity": (0.18, 0.48, 0.52, 0.78),
        "pleural_effusion": (0.12, 0.55, 0.45, 0.88),
        "pneumothorax": (0.55, 0.12, 0.88, 0.45),
        "nodule": (0.28, 0.28, 0.58, 0.52),
        "cardiomegaly": (0.34, 0.42, 0.66, 0.82),
    }
    x0, y0, x1, y1 = presets.get(key, presets["opacity"])
    return [
        _normalize_box(
            x0 * width,
            y0 * height,
            x1 * width,
            y1 * height,
            width,
            height,
            label=label,
            finding_key=finding_key,
        )
    ]
