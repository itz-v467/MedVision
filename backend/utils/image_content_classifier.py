"""Heuristic classification of uploaded clinical images (X-ray vs lab photo)."""

from __future__ import annotations

import statistics
from pathlib import Path

from PIL import Image


def _sample_pixels(storage_path: str) -> list[tuple[int, int, int]]:
    """Downsample image pixels for fast heuristics."""
    with Image.open(storage_path) as img:
        rgb = img.convert("RGB")
        width, height = rgb.size
        thumb = rgb.resize((min(256, width), min(256, height)))
        return list(thumb.getdata())


def classify_clinical_image(storage_path: str) -> str:
    """Return ``xray``, ``lab_report``, or ``unknown`` from image content."""
    path = Path(storage_path)
    if not path.is_file():
        return "unknown"

    try:
        pixels = _sample_pixels(str(path))
    except Exception:
        return "unknown"

    if not pixels:
        return "unknown"

    chroma: list[float] = []
    luminance: list[float] = []
    for red, green, blue in pixels:
        chroma.append(float(max(red, green, blue) - min(red, green, blue)))
        luminance.append(0.299 * red + 0.587 * green + 0.114 * blue)

    avg_chroma = statistics.mean(chroma)
    lum_std = statistics.pstdev(luminance) if len(luminance) > 1 else 0.0
    white_ratio = sum(1 for value in luminance if value > 235) / len(luminance)
    mid_ratio = sum(1 for value in luminance if 40 < value < 200) / len(luminance)
    color_ratio = sum(1 for value in chroma if value > 28) / len(chroma)

    # Lab report photos: bright paper background, visible color ink or charts.
    if white_ratio > 0.5:
        return "lab_report"
    if white_ratio > 0.28 and (avg_chroma > 12 or color_ratio > 0.08):
        return "lab_report"

    # Chest X-rays: mostly grayscale with spread mid-tones.
    if avg_chroma < 22 and mid_ratio > 0.22 and lum_std > 22:
        return "xray"

    if avg_chroma < 14 and white_ratio < 0.2:
        return "xray"

    return "unknown"
