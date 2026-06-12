"""Radiology imaging AI service."""

from __future__ import annotations

import time
import uuid
from typing import Any

from sqlalchemy.orm import Session

from backend.client.ml_model_loader import get_ml_model_loader
from backend.client.xray_inference_client import get_xray_inference_client
from backend.core.base_service import BaseService
from backend.dao.document_dao import DocumentDao
from backend.enums.ai_status import AiProcessingStatus
from backend.enums.model_type import ModelType
from backend.logger import get_logger
from backend.model.document_model import ImagingStudyModel, InferenceResultModel

logger = get_logger()

IMAGE_MIME_TYPES = {"image/png", "image/jpeg"}


class ImagingAiService(BaseService):
    """Runs chest X-ray inference and explainability artifacts."""

    def __init__(self, session: Session) -> None:
        """Initialize dependencies."""
        super().__init__(session)
        self._dao = DocumentDao(session)
        self._model_loader = get_ml_model_loader()
        self._xray = get_xray_inference_client()

    def analyze_study(
        self,
        encounter_id: uuid.UUID,
        storage_path: str,
        mime_type: str = "image/jpeg",
        file_type: str = "xray",
    ) -> dict[str, Any]:
        """Run imaging inference pipeline."""
        start = time.perf_counter()
        model = self._model_loader.get_model(ModelType.IMAGING)
        logger.info("Imaging inference started | encounter=%s", encounter_id)

        if not self._should_run_imaging(mime_type, file_type):
            return self._skipped_result(start)

        study = ImagingStudyModel(
            encounter_id=encounter_id,
            storage_path=storage_path,
            status=AiProcessingStatus.PROCESSING.value,
        )
        self._dao.create_imaging_study(study)

        prediction = self._xray.predict(storage_path)
        findings = prediction["findings"]
        confidence = prediction["confidence"]
        heatmap_path = prediction.get("heatmap_path")

        inference = InferenceResultModel(
            imaging_study_id=study.id,
            findings=findings,
            bounding_boxes={},
            heatmap_path=heatmap_path,
            confidence_score=confidence,
            model_version=prediction.get(
                "model_version", model.get("version", "1.0.0")
            ),
        )
        self._dao.save_inference(inference)
        study.status = AiProcessingStatus.COMPLETED.value
        latency_ms = (time.perf_counter() - start) * 1000
        logger.info("Imaging inference completed | latency_ms=%.2f", latency_ms)
        return {
            "study_id": str(study.id),
            "inference_id": str(inference.id),
            "findings": findings,
            "heatmap_path": heatmap_path,
            "confidence": confidence,
            "skipped": False,
            "latency_ms": latency_ms,
        }

    def _should_run_imaging(self, mime_type: str, file_type: str) -> bool:
        """Return True when upload is an explicit chest X-ray case."""
        if mime_type not in IMAGE_MIME_TYPES:
            return False
        return file_type in {"xray", "chest_xray", "imaging"}

    def _skipped_result(self, start: float) -> dict[str, Any]:
        """Return neutral result when imaging is not applicable."""
        latency_ms = (time.perf_counter() - start) * 1000
        return {
            "study_id": None,
            "inference_id": None,
            "findings": {},
            "heatmap_path": None,
            "confidence": 0.0,
            "skipped": True,
            "latency_ms": latency_ms,
        }
