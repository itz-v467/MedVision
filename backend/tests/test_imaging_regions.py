"""Tests for chest X-ray anomaly region detection."""

from __future__ import annotations

from PIL import Image
import numpy as np

from backend.utils.imaging_regions import derive_anomaly_regions


class TestImagingRegions:
    def test_detects_synthetic_opacity_patch(self, tmp_path) -> None:
        width, height = 512, 512
        arr = np.full((height, width), 70, dtype=np.uint8)
        arr[300:410, 120:250] = 175
        Image.fromarray(arr).save(tmp_path / "opacity.png")

        regions = derive_anomaly_regions(
            str(tmp_path / "opacity.png"),
            {"opacity": {"probability": 0.82, "detected": True}},
        )

        assert len(regions) == 1
        region = regions[0]
        assert region["width"] > 0.05
        assert region["height"] > 0.05
        assert region["y"] > 0.35
        assert "opacity" in region["label"].lower() or "lung" in region["label"].lower()

    def test_returns_heuristic_when_no_pixels(self, tmp_path) -> None:
        arr = np.full((256, 256), 120, dtype=np.uint8)
        Image.fromarray(arr).save(tmp_path / "flat.png")

        regions = derive_anomaly_regions(
            str(tmp_path / "flat.png"),
            {"opacity": {"probability": 0.7, "detected": True}},
        )

        assert len(regions) == 1
        assert regions[0]["width"] > 0
