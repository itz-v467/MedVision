"""Clinical summary generation service."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

from sqlalchemy.orm import Session

from backend.client.ml_model_loader import get_ml_model_loader
from backend.client.openai_client import get_openai_client
from backend.core.base_service import BaseService
from backend.dao.document_dao import DocumentDao
from backend.enums.ai_status import AiProcessingStatus
from backend.enums.messages import Messages
from backend.enums.model_type import ModelType
from backend.logger import get_logger
from backend.model.document_model import ClinicalSummaryModel
from backend.service.rag_indexing_service import RagIndexingService
from backend.utils.exceptions import NotFoundException

logger = get_logger()


class ClinicalSummaryService(BaseService):
    """Generates RAG-grounded clinical summaries."""

    def __init__(self, session: Session) -> None:
        """Initialize dependencies."""
        super().__init__(session)
        self._dao = DocumentDao(session)
        self._model_loader = get_ml_model_loader()
        self._rag = RagIndexingService(session)
        self._openai = get_openai_client()

    def generate_summary(
        self, encounter_id: uuid.UUID, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate AI summary requiring physician review."""
        start = time.perf_counter()
        model = self._model_loader.get_model(ModelType.RAG)
        logger.info("Summary generation started | encounter=%s", encounter_id)

        context_text = json.dumps(context, default=str)
        self._rag.index_text(
            encounter_id,
            "workflow",
            str(encounter_id),
            context_text,
            {"type": "multimodal_context"},
        )

        ocr_text = context.get("ocr", {}).get("raw_text", "")
        if ocr_text:
            self._rag.index_text(
                encounter_id,
                "ocr",
                context.get("ocr", {}).get("ocr_result_id", "ocr"),
                ocr_text,
                {"type": "ocr_text"},
            )

        grounded_chunks = self._rag.retrieve_context(
            encounter_id,
            "clinical summary evidence imaging labs symptoms",
        )

        from backend.ai.rag.orchestrator import rag_orchestrator
        
        query_text = f"Generate clinical summary. Context: {json.dumps(context, default=str)}"
        summary_result = rag_orchestrator.run(query=query_text, patient_id=str(encounter_id))
        
        summary_text = summary_result.get("summary", "Summary generation failed.")
        
        evidence = {**context, "rag_chunks": grounded_chunks, "structured_summary": summary_result}
        summary = ClinicalSummaryModel(
            encounter_id=encounter_id,
            summary_text=summary_text,
            evidence_sources=evidence,
            status=AiProcessingStatus.REVIEW_REQUIRED.value,
        )
        self._dao.save_summary(summary)
        latency_ms = (time.perf_counter() - start) * 1000
        logger.info("Summary generated | latency_ms=%.2f", latency_ms)
        return {
            "summary_id": str(summary.id),
            "summary_text": summary_text,
            "status": summary.status,
            "message": Messages.SUMMARY_PENDING_REVIEW.value,
            "model_version": model.get("version", "1.0.0"),
            "latency_ms": latency_ms,
        }

    def finalize_summary(
        self, summary_id: uuid.UUID, reviewer_id: uuid.UUID
    ) -> ClinicalSummaryModel:
        """Mark summary as physician-reviewed."""
        summary = self._dao.find_summary_by_id(summary_id)
        if summary is None:
            raise NotFoundException("Summary not found.")
        summary.status = AiProcessingStatus.FINALIZED.value
        summary.reviewed_by = reviewer_id
        self._dao.save_summary(summary)
        return summary
