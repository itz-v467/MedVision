"""TorchXRayVision chest X-ray inference client."""

from __future__ import annotations

import importlib.util
import os
from typing import Any

from backend.config import get_settings
from backend.core.singleton import SingletonMixin
from backend.logger import get_logger
from backend.utils.imaging_regions import derive_anomaly_regions

logger = get_logger()

# Map FRD finding keys to TorchXRayVision pathology labels
PATHOLOGY_MAP: dict[str, list[str]] = {
    "pneumothorax": ["Pneumothorax"],
    "opacity": ["Lung Opacity", "Consolidation", "Infiltration", "Pneumonia"],
    "pleural_effusion": ["Effusion"],
    "nodule": ["Nodule", "Mass"],
    "cardiomegaly": ["Cardiomegaly"],
}


class XrayInferenceClient(SingletonMixin):
    """Runs chest X-ray pathology inference via TorchXRayVision."""

    def __init__(self) -> None:
        """Initialize lazy model handles."""
        if self._initialized:
            return
        self._settings = get_settings()
        self._model = None
        self._transform = None
        self._torch = None
        self._xrv = None
        self._available = self._probe_availability()
        self._initialized = True
        if self._available:
            logger.info(
                "XrayInferenceClient ready | device=%s", self._settings.imaging_device
            )
        else:
            logger.warning(
                "TorchXRayVision unavailable; imaging will use fallback scores"
            )

    @property
    def is_available(self) -> bool:
        """Return True when TorchXRayVision can run inference."""
        return self._available

    def _probe_availability(self) -> bool:
        """Check whether optional ML dependencies are installed."""
        if os.getenv("IMAGING_ENABLED", "true").lower() == "false":
            return False
        return (
            importlib.util.find_spec("torch") is not None
            and importlib.util.find_spec("torchxrayvision") is not None
        )

    def _ensure_model(self) -> None:
        """Lazy-load DenseNet weights."""
        if self._model is not None:
            return

        import torch
        import torchvision
        import torchxrayvision as xrv

        os.makedirs(self._settings.imaging_weights_dir, exist_ok=True)
        weights = self._settings.imaging_model_name
        self._model = xrv.models.DenseNet(weights=weights)
        self._model.eval()
        device = self._settings.imaging_device
        if device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA requested but unavailable; falling back to CPU")
            device = "cpu"
        self._model = self._model.to(device)
        self._device = device
        self._torch = torch
        self._xrv = xrv
        self._transform = torchvision.transforms.Compose(
            [
                xrv.datasets.XRayCenterCrop(),
                xrv.datasets.XRayResizer(224),
            ]
        )

    def predict(self, image_path: str) -> dict[str, Any]:
        """Run inference on a chest X-ray image file.

        Args:
            image_path: Path to PNG/JPEG image.

        Returns:
            Findings dict, confidence, model version, and optional heatmap path.
        """
        if not self._available:
            return self._fallback_prediction(image_path)

        try:
            return self._run_inference(image_path)
        except Exception as exc:
            logger.exception("Imaging inference failed | path=%s", image_path)
            result = self._fallback_prediction(image_path)
            result["error"] = str(exc)
            return result

    def _run_inference(self, image_path: str) -> dict[str, Any]:
        """Execute TorchXRayVision forward pass."""
        import skimage.io

        self._ensure_model()
        assert self._model is not None
        assert self._transform is not None
        assert self._torch is not None

        img = skimage.io.imread(image_path)
        if img.ndim == 3:
            img = img.mean(axis=2)
        img = self._xrv.datasets.normalize(img, 255)
        # TXRV transforms expect channel-first tensors (C, H, W).
        if img.ndim == 2:
            img = img[None, ...]
        img = self._transform(img)
        tensor = self._torch.from_numpy(img).unsqueeze(0).to(self._device)

        with self._torch.no_grad():
            outputs = self._model(tensor)[0].cpu().numpy()

        pathology_scores = {
            label: float(outputs[index])
            for index, label in enumerate(self._model.pathologies)
        }
        threshold = self._settings.imaging_detection_threshold
        findings = self._map_findings(pathology_scores, threshold)
        confidence = max(finding["probability"] for finding in findings.values())
        heatmap_path = self._save_intensity_heatmap(image_path, img)
        flagged = any(item.get("detected") for item in findings.values())
        regions = derive_anomaly_regions(image_path, findings) if flagged else []

        return {
            "findings": findings,
            "confidence": round(confidence, 4),
            "model_version": self._settings.imaging_model_name,
            "heatmap_path": heatmap_path,
            "pathology_scores": pathology_scores,
            "engine": "torchxrayvision",
            "regions": regions,
        }

    def _map_findings(
        self, pathology_scores: dict[str, float], threshold: float
    ) -> dict[str, dict[str, Any]]:
        """Map TXRV labels to FRD finding keys with conservative detection."""
        mapped: dict[str, float] = {}
        for finding_key, labels in PATHOLOGY_MAP.items():
            mapped[finding_key] = max(
                pathology_scores.get(label, 0.0) for label in labels
            )

        top_score = max(mapped.values(), default=0.0)
        findings: dict[str, dict[str, Any]] = {}
        for finding_key, probability in mapped.items():
            rounded = round(probability, 4)
            detected = (
                top_score >= threshold
                and rounded >= threshold
                and rounded >= top_score * 0.92
            )
            findings[finding_key] = {
                "probability": rounded,
                "detected": detected,
            }
        return findings

    def _fallback_prediction(self, image_path: str) -> dict[str, Any]:
        """Neutral fallback when ML stack is unavailable — never invent pathology."""
        findings = {
            key: {"probability": 0.12, "detected": False}
            for key in PATHOLOGY_MAP
        }
        heatmap_path = self._save_simple_heatmap(image_path)
        regions: list[dict[str, Any]] = []
        return {
            "findings": findings,
            "confidence": 0.12,
            "model_version": "fallback-1.0.0",
            "heatmap_path": heatmap_path,
            "pathology_scores": {},
            "engine": "fallback",
            "regions": regions,
            "fallback_notice": (
                "TorchXRayVision is not active in this environment. "
                "Scores are placeholders only — do not use for clinical decisions."
            ),
        }

    def _save_intensity_heatmap(self, image_path: str, normalized_img: Any) -> str:
        """Save a grayscale intensity overlay as explainability artifact."""
        try:
            import numpy as np
            from PIL import Image

            heatmap = normalized_img
            if hasattr(heatmap, "numpy"):
                heatmap = heatmap.numpy()
            heatmap = np.asarray(heatmap, dtype=np.float32)
            if heatmap.ndim == 3:
                heatmap = heatmap.mean(axis=0)
            heatmap = heatmap - heatmap.min()
            if heatmap.max() > 0:
                heatmap = heatmap / heatmap.max()
            heatmap_uint8 = (heatmap * 255).astype(np.uint8)
            output_path = f"{image_path}.heatmap.png"
            Image.fromarray(heatmap_uint8).save(output_path)
            return output_path
        except Exception as exc:
            logger.warning("Heatmap generation failed: %s", exc)
            return f"{image_path}.heatmap.png"

    def _save_simple_heatmap(self, image_path: str) -> str | None:
        """Build a grayscale intensity map without TorchXRayVision."""
        try:
            from PIL import Image
            import numpy as np

            img = Image.open(image_path).convert("L")
            arr = np.asarray(img, dtype=np.float32)
            arr = arr - arr.min()
            if arr.max() > 0:
                arr = arr / arr.max()
            output_path = f"{image_path}.heatmap.png"
            Image.fromarray((arr * 255).astype(np.uint8)).save(output_path)
            return output_path
        except Exception as exc:
            logger.warning("Fallback heatmap generation failed: %s", exc)
            return None


def get_xray_inference_client() -> XrayInferenceClient:
    """Return X-ray inference singleton."""
    return XrayInferenceClient()
