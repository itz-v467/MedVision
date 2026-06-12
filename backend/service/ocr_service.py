"""OCR processing service."""

from __future__ import annotations

import time
import uuid
from typing import Any

from sqlalchemy.orm import Session

from backend.client.ml_model_loader import get_ml_model_loader
from backend.client.ocr_extractor import extract_text_from_file, parse_biomarkers
from backend.core.base_service import BaseService
from backend.dao.document_dao import DocumentDao
from backend.enums.ai_status import AiProcessingStatus
from backend.enums.model_type import ModelType
from backend.logger import get_logger
from backend.model.document_model import OcrResultModel
from backend.utils.exceptions import AiProcessingException

logger = get_logger()


class OcrService(BaseService):
    """Extracts structured data from lab and report documents."""

    def __init__(self, session: Session) -> None:
        """Initialize dependencies."""
        super().__init__(session)
        self._dao = DocumentDao(session)
        self._model_loader = get_ml_model_loader()

    def process_document(self, document_id: uuid.UUID) -> dict[str, Any]:
        """Run OCR pipeline on a document."""
        document = self._dao.find_document(document_id)
        if document is None:
            raise AiProcessingException("Document not found for OCR.")

        start = time.perf_counter()
        model = self._model_loader.get_model(ModelType.OCR)
        logger.info("OCR inference started | document=%s", document_id)

        raw_text, text_confidence = extract_text_from_file(
            document.storage_path, document.mime_type
        )
        biomarkers = parse_biomarkers(raw_text)
        structured_data = {
            "patient_demographics": {},
            "biomarkers": biomarkers,
            "raw_text": raw_text,
            "model_version": model.get("version", "1.0.0"),
        }
        confidence = text_confidence
        if biomarkers:
            confidence = min(confidence + 0.05, 0.95)

        latency_ms = (time.perf_counter() - start) * 1000

        result = OcrResultModel(
            document_id=document_id,
            structured_data=structured_data,
            confidence_score=confidence,
        )
        self._dao.save_ocr_result(result)
        document.status = AiProcessingStatus.COMPLETED.value
        logger.info("OCR completed | latency_ms=%.2f", latency_ms)
        return {
            "ocr_result_id": str(result.id),
            "confidence": confidence,
            "structured_data": structured_data,
            "raw_text": raw_text,
            "latency_ms": latency_ms,
        }
