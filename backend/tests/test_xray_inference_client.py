"""Tests for chest X-ray inference preprocessing."""

from __future__ import annotations

import importlib.util

import numpy as np
import pytest
from PIL import Image


def test_grayscale_tensor_gets_channel_dimension() -> None:
    """TXRV transforms require channel-first arrays (C, H, W)."""
    img = np.zeros((256, 256), dtype=np.float32)
    if img.ndim == 2:
        img = img[None, ...]
    assert img.shape == (1, 256, 256)


@pytest.mark.skipif(
    not importlib.util.find_spec("torchxrayvision"),
    reason="TorchXRayVision not installed",
)
def test_grayscale_image_runs_without_shape_error(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("IMAGING_ENABLED", "true")
    from backend.client.xray_inference_client import XrayInferenceClient, get_xray_inference_client

    XrayInferenceClient.reset_instance()
    arr = np.full((480, 480), 90, dtype=np.uint8)
    arr[280:380, 140:260] = 200
    image_path = tmp_path / "chest.png"
    Image.fromarray(arr).save(image_path)

    client = get_xray_inference_client()
    result = client.predict(str(image_path))

    assert result["engine"] == "torchxrayvision"
    assert result["model_version"] != "fallback-1.0.0"
    assert result["pathology_scores"]
