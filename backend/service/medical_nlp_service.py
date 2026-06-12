"""Medical NLP processing service."""

from __future__ import annotations

import time
import uuid
from typing import Any

from sqlalchemy.orm import Session

from backend.client.ml_model_loader import get_ml_model_loader
from backend.client.ocr_extractor import extract_clinical_entities
from backend.core.base_service import BaseService
from backend.dao.document_dao import DocumentDao
from backend.enums.model_type import ModelType
from backend.logger import get_logger
from backend.model.document_model import NlpExtractionModel

logger = get_logger()


class MedicalNlpService(BaseService):
    """Extracts clinical entities and terminology codes."""

    def __init__(self, session: Session) -> None:
        """Initialize dependencies."""
        super().__init__(session)
        self._dao = DocumentDao(session)
        self._model_loader = get_ml_model_loader()

    def process_encounter(self, encounter_id: uuid.UUID, text: str) -> dict[str, Any]:
        """Run NLP extraction for an encounter."""
        start = time.perf_counter()
        model = self._model_loader.get_model(ModelType.NLP)
        logger.info("NLP inference started | encounter=%s", encounter_id)

        extraction_result = extract_clinical_entities(text or "")
        entities = extraction_result["entities"]
        extraction = NlpExtractionModel(
            encounter_id=encounter_id,
            entities=entities,
            snomed_codes=extraction_result["snomed_codes"],
            icd10_codes=extraction_result["icd10_codes"],
            confidence_score=extraction_result["confidence"],
        )
        self._dao.save_nlp_extraction(extraction)
        latency_ms = (time.perf_counter() - start) * 1000
        logger.info("NLP completed | latency_ms=%.2f", latency_ms)
        return {
            "nlp_id": str(extraction.id),
            "entities": entities,
            "confidence": extraction.confidence_score,
            "model_version": model.get("version", "1.0.0"),
            "latency_ms": latency_ms,
        }
