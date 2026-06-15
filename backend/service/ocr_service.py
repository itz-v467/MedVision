"""OCR processing service."""

from __future__ import annotations

import time
import uuid
from typing import Any

from sqlalchemy.orm import Session

from backend.client.ml_model_loader import get_ml_model_loader
from backend.client.document_ocr_client import get_ocr_capabilities
from backend.client.ocr_extractor import (
    extract_text_from_file,
    extraction_warning_for_text,
)
from backend.service.lab_analysis_service import LabAnalysisService
from backend.utils.lab_value_normalizer import clean_ocr_lab_text
from backend.utils.patient_demographics_extractor import extract_patient_demographics
from backend.core.base_service import BaseService
from backend.dao.document_dao import DocumentDao
from backend.enums.ai_status import AiProcessingStatus
from backend.enums.model_type import ModelType
from backend.logger import get_logger
from backend.utils.debug_log import pipeline_debug, pipeline_info, pipeline_warning
from backend.model.document_model import OcrResultModel
from backend.utils.exceptions import AiProcessingException

logger = get_logger()

IMAGE_MIME_TYPES = {"image/png", "image/jpeg"}
EMPTY_LAB_ANALYSIS = {
    "precautions": [],
    "wellness_notes": [],
    "panel_coverage_pct": 0.0,
    "missing_core_tests": [],
    "clinical_summary": "",
    "abnormal_count": 0,
    "normal_count": 0,
    "total_parsed": 0,
    "disclaimer": (
        "Chest X-ray image — blood panel parsing does not apply. "
        "Review imaging AI findings instead."
    ),
    "llm_extraction": {"used": False},
}


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
        pipeline_info("ocr", "OCR started", document_id=str(document_id), mime=document.mime_type)

        raw_text, text_confidence, extraction_method = extract_text_from_file(
            document.storage_path, document.mime_type
        )
        pipeline_debug(
            "ocr",
            "Text extraction finished",
            method=extraction_method,
            chars=len(raw_text),
            confidence=text_confidence,
        )
        if not raw_text.strip():
            pipeline_warning(
                "ocr",
                "No text extracted from document",
                document_id=str(document_id),
                method=extraction_method,
            )

        raw_text = clean_ocr_lab_text(raw_text)
        warning = extraction_warning_for_text(
            raw_text, document.mime_type, extraction_method
        )

        if document.file_type == "xray":
            structured_data = self._build_imaging_ocr_payload(
                raw_text=raw_text,
                text_confidence=text_confidence,
                extraction_method=extraction_method,
                warning=warning,
                model_version=model.get("version", "1.0.0"),
            )
            biomarkers: list[dict[str, Any]] = []
            confidence = text_confidence if raw_text.strip() else 0.25
        else:
            lab_analysis = LabAnalysisService().analyze_text(raw_text)
            pipeline_debug(
                "ocr",
                "Lab analysis finished",
                biomarkers=lab_analysis.get("total_parsed", 0),
                abnormal=lab_analysis.get("abnormal_count", 0),
            )
            biomarkers = lab_analysis["biomarkers"]
            structured_data = {
                "patient_demographics": extract_patient_demographics(raw_text),
                "biomarkers": lab_analysis["biomarkers"],
                "lab_analysis": {
                    "precautions": lab_analysis["precautions"],
                    "wellness_notes": lab_analysis["wellness_notes"],
                    "panel_coverage_pct": lab_analysis["panel_coverage_pct"],
                    "missing_core_tests": lab_analysis["missing_core_tests"],
                    "clinical_summary": lab_analysis["clinical_summary"],
                    "abnormal_count": lab_analysis["abnormal_count"],
                    "normal_count": lab_analysis["normal_count"],
                    "total_parsed": lab_analysis["total_parsed"],
                    "disclaimer": lab_analysis["disclaimer"],
                    "llm_extraction": lab_analysis.get("llm_extraction", {}),
                },
                "raw_text": raw_text,
                "raw_text_preview": raw_text[:2000] if raw_text else "",
                "chars_extracted": len(raw_text),
                "extraction_method": extraction_method,
                "extraction_warning": warning,
                "ocr_engines_available": get_ocr_capabilities(),
                "model_version": model.get("version", "1.0.0"),
            }
            confidence = text_confidence
            if biomarkers:
                confidence = min(confidence + 0.1, 0.95)
            elif warning:
                confidence = min(confidence, 0.35)

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

    def _build_imaging_ocr_payload(
        self,
        *,
        raw_text: str,
        text_confidence: float,
        extraction_method: str,
        warning: str | None,
        model_version: str,
    ) -> dict[str, Any]:
        """Minimal OCR payload for chest X-ray uploads (no blood panel parsing)."""
        imaging_warning = warning
        if not raw_text.strip():
            imaging_warning = (
                "Chest X-ray image uploaded. Text OCR is limited on scans — "
                "review uses ChestNet image analysis instead."
            )
        return {
            "patient_demographics": extract_patient_demographics(raw_text) if raw_text else {},
            "biomarkers": [],
            "lab_analysis": dict(EMPTY_LAB_ANALYSIS),
            "raw_text": raw_text,
            "raw_text_preview": raw_text[:2000] if raw_text else "",
            "chars_extracted": len(raw_text),
            "extraction_method": extraction_method,
            "extraction_warning": imaging_warning,
            "ocr_engines_available": get_ocr_capabilities(),
            "model_version": model_version,
            "document_mode": "xray",
        }
