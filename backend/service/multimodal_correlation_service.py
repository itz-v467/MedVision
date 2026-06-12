"""Multimodal evidence correlation service."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from backend.core.base_service import BaseService
from backend.logger import get_logger

logger = get_logger()


class MultimodalCorrelationService(BaseService):
    """Correlates imaging, labs, and NLP outputs."""

    def __init__(self, session: Session) -> None:
        """Initialize dependencies."""
        super().__init__(session)

    def correlate(
        self, encounter_id: uuid.UUID, modalities: dict[str, Any]
    ) -> dict[str, Any]:
        """Produce weighted evidence scores across modalities."""
        logger.info("Correlation started | encounter=%s", encounter_id)
        imaging_score = modalities.get("imaging_confidence", 0.0)
        ocr_score = modalities.get("ocr_confidence", 0.0)
        nlp_score = modalities.get("nlp_confidence", 0.0)
        imaging_skipped = modalities.get("imaging_skipped", False)
        file_type = modalities.get("file_type", "")

        if imaging_skipped or file_type in {"lab_report", "clinical_note"}:
            weighted_score = (ocr_score * 0.65) + (nlp_score * 0.35)
            correlations = []
            if ocr_score > 0:
                correlations.append(
                    {
                        "type": "lab_ocr",
                        "description": "Lab values and report text extracted via OCR",
                        "weight": round(ocr_score, 2),
                    }
                )
            if nlp_score > 0:
                correlations.append(
                    {
                        "type": "clinical_nlp",
                        "description": "Clinical entities mapped from report text",
                        "weight": round(nlp_score, 2),
                    }
                )
        else:
            weighted_score = (imaging_score * 0.5) + (ocr_score * 0.25) + (nlp_score * 0.25)
            correlations = [
                {
                    "type": "imaging_lab",
                    "description": "Imaging findings correlated with available clinical data",
                    "weight": round(weighted_score, 2),
                }
            ]

        return {
            "encounter_id": str(encounter_id),
            "weighted_evidence_score": round(weighted_score, 4),
            "correlations": correlations,
        }
