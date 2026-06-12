"""Clinical data ingestion and AI workflow orchestration."""

from __future__ import annotations

import uuid
from typing import Any, BinaryIO

from sqlalchemy.orm import Session

from backend.client.storage_client import StorageClient
from backend.core.base_service import BaseService
from backend.dao.document_dao import DocumentDao
from backend.dao.encounter_dao import EncounterDao
from backend.enums.ai_status import AiProcessingStatus
from backend.enums.messages import Messages
from backend.logger import get_logger
from backend.model.document_model import DocumentModel
from backend.model.encounter_model import EncounterModel
from backend.model.patient_model import PatientModel
from backend.service.alert_engine_service import AlertEngineService
from backend.service.audit_service import AuditService
from backend.service.clinical_summary_service import ClinicalSummaryService
from backend.service.explainability_service import ExplainabilityService
from backend.service.imaging_ai_service import ImagingAiService
from backend.service.longitudinal_analysis_service import LongitudinalAnalysisService
from backend.service.medical_nlp_service import MedicalNlpService
from backend.service.multimodal_correlation_service import MultimodalCorrelationService
from backend.service.ocr_service import OcrService
from backend.utils.exceptions import NotFoundException, ValidationException

logger = get_logger()

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "text/plain",
    "text/csv",
}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024


class IngestionService(BaseService):
    """Orchestrates upload and full AI clinical workflow."""

    def __init__(self, session: Session) -> None:
        """Initialize collaborators."""
        super().__init__(session)
        self._encounter_dao = EncounterDao(session)
        self._document_dao = DocumentDao(session)
        self._storage = StorageClient()
        self._ocr = OcrService(session)
        self._nlp = MedicalNlpService(session)
        self._imaging = ImagingAiService(session)
        self._correlation = MultimodalCorrelationService(session)
        self._summary = ClinicalSummaryService(session)
        self._explainability = ExplainabilityService(session)
        self._alerts = AlertEngineService(session)
        self._audit = AuditService(session)
        self._longitudinal = LongitudinalAnalysisService(session)

    def upload_and_process(
        self,
        user_id: uuid.UUID,
        patient_external_id: str,
        patient_name: str,
        file_stream: BinaryIO,
        file_name: str,
        mime_type: str,
        file_type: str,
    ) -> dict[str, Any]:
        """Upload file and execute AI pipeline."""
        if mime_type not in ALLOWED_MIME_TYPES:
            raise ValidationException("Unsupported file type.")

        file_stream.seek(0, 2)
        size = file_stream.tell()
        file_stream.seek(0)
        if size > MAX_FILE_SIZE_BYTES:
            raise ValidationException("File exceeds maximum allowed size.")

        patient = (
            self._session.query(PatientModel)
            .filter(PatientModel.external_id == patient_external_id)
            .first()
        )
        if patient is None:
            patient = PatientModel(
                external_id=patient_external_id,
                full_name=patient_name,
            )
            self._session.add(patient)
            self._session.flush()

        encounter = EncounterModel(
            patient_id=patient.id,
            assigned_user_id=user_id,
            status=AiProcessingStatus.PROCESSING.value,
        )
        self._encounter_dao.create(encounter)

        storage_path = self._storage.save_file(file_stream, file_name)
        document = DocumentModel(
            encounter_id=encounter.id,
            file_name=file_name,
            mime_type=mime_type,
            storage_path=storage_path,
            file_type=file_type,
            status=AiProcessingStatus.PROCESSING.value,
        )
        self._document_dao.create_document(document)
        self._audit.log_action(user_id, "FILE_UPLOAD", "document", str(document.id))

        ocr_result = self._ocr.process_document(document.id)
        nlp_text = ocr_result.get("raw_text") or ""
        nlp_result = self._nlp.process_encounter(encounter.id, nlp_text)
        imaging_result = self._imaging.analyze_study(
            encounter.id, storage_path, mime_type, file_type
        )
        correlation = self._correlation.correlate(
            encounter.id,
            {
                "imaging_confidence": imaging_result["confidence"],
                "ocr_confidence": ocr_result["confidence"],
                "nlp_confidence": nlp_result["confidence"],
            },
        )
        explanation = self._explainability.build_explanation(
            encounter.id,
            imaging_result.get("findings") or {},
            imaging_result.get("heatmap_path"),
        )
        summary = self._summary.generate_summary(
            encounter.id,
            {
                "ocr": ocr_result,
                "nlp": nlp_result,
                "imaging": imaging_result,
                "correlation": correlation,
            },
        )
        findings = imaging_result.get("findings") or {}
        alerts = self._alerts.evaluate_findings(encounter.id, findings)

        encounter.status = AiProcessingStatus.REVIEW_REQUIRED.value
        self._encounter_dao.update(encounter)
        logger.info("Workflow completed | encounter=%s", encounter.id)

        return {
            "encounter_id": str(encounter.id),
            "document_id": str(document.id),
            "ocr": ocr_result,
            "nlp": nlp_result,
            "imaging": imaging_result,
            "correlation": correlation,
            "explainability": explanation,
            "summary": summary,
            "alerts": alerts,
            "message": Messages.AI_PROCESSING_COMPLETE.value,
        }

    def list_encounters(self) -> list[dict[str, Any]]:
        """Return encounter triage queue."""
        encounters = self._encounter_dao.list_recent()
        return [
            {
                "id": str(encounter.id),
                "patient_id": str(encounter.patient_id),
                "status": encounter.status,
                "chief_complaint": encounter.chief_complaint,
                "created_at": encounter.created_at.isoformat(),
            }
            for encounter in encounters
        ]

    def get_encounter_detail(self, encounter_id: uuid.UUID) -> dict[str, Any]:
        """Return full encounter detail for physician review."""
        encounter = self._encounter_dao.find_by_id(encounter_id)
        if encounter is None:
            raise NotFoundException("Encounter not found.")

        patient = (
            self._session.query(PatientModel)
            .filter(PatientModel.id == encounter.patient_id)
            .first()
        )
        summary = self._document_dao.find_summary_by_encounter(encounter_id)
        ocr = self._document_dao.find_ocr_by_encounter(encounter_id)
        nlp = self._document_dao.find_nlp_by_encounter(encounter_id)
        study, inference = self._document_dao.find_imaging_by_encounter(encounter_id)
        alerts = self._document_dao.find_alerts_by_encounter(encounter_id)
        documents = self._document_dao.find_documents_by_encounter(encounter_id)
        timeline = self._longitudinal.build_timeline(encounter.patient_id)
        imaging = self._serialize_imaging(study, inference, encounter_id)

        return {
            "encounter": {
                "id": str(encounter.id),
                "patient_id": str(encounter.patient_id),
                "status": encounter.status,
                "chief_complaint": encounter.chief_complaint,
                "created_at": encounter.created_at.isoformat(),
            },
            "patient": {
                "id": str(patient.id) if patient else None,
                "external_id": patient.external_id if patient else None,
                "full_name": patient.full_name if patient else None,
            },
            "documents": [
                {
                    "id": str(doc.id),
                    "file_name": doc.file_name,
                    "file_type": doc.file_type,
                    "mime_type": doc.mime_type,
                    "status": doc.status,
                }
                for doc in documents
            ],
            "ocr": self._serialize_ocr(ocr),
            "nlp": self._serialize_nlp(nlp),
            "imaging": imaging,
            "summary": self._serialize_summary(summary),
            "timeline": timeline,
            "alerts": [
                {
                    "id": str(alert.id),
                    "title": alert.title,
                    "message": alert.message,
                    "priority": alert.priority,
                    "is_acknowledged": alert.is_acknowledged,
                    "created_at": alert.created_at.isoformat(),
                }
                for alert in alerts
            ],
        }

    def acknowledge_alert(
        self, alert_id: uuid.UUID, user_id: uuid.UUID
    ) -> dict[str, Any]:
        """Acknowledge a clinical alert."""
        alert = self._alerts.acknowledge_alert(alert_id)
        self._audit.log_action(
            user_id,
            "ALERT_ACKNOWLEDGED",
            "alert",
            str(alert.id),
            {"encounter_id": str(alert.encounter_id)},
        )
        return {
            "alert_id": str(alert.id),
            "is_acknowledged": alert.is_acknowledged,
            "message": "Alert acknowledged.",
        }

    def get_heatmap_path(self, encounter_id: uuid.UUID) -> str:
        """Return validated heatmap file path for an encounter."""
        from pathlib import Path

        from backend.config import get_settings

        encounter = self._encounter_dao.find_by_id(encounter_id)
        if encounter is None:
            raise NotFoundException("Encounter not found.")

        _, inference = self._document_dao.find_imaging_by_encounter(encounter_id)
        if inference is None or not inference.heatmap_path:
            raise NotFoundException("Heatmap not available for this encounter.")

        heatmap_path = Path(inference.heatmap_path).resolve()
        storage_root = Path(get_settings().storage_path).resolve()
        try:
            heatmap_path.relative_to(storage_root)
        except ValueError as exc:
            raise NotFoundException("Heatmap path is invalid.") from exc

        if not heatmap_path.is_file():
            raise NotFoundException("Heatmap file not found.")

        return str(heatmap_path)

    def get_patient_timeline(self, patient_id: uuid.UUID) -> dict[str, Any]:
        """Return longitudinal timeline for a patient."""
        patient = (
            self._session.query(PatientModel)
            .filter(PatientModel.id == patient_id)
            .first()
        )
        if patient is None:
            raise NotFoundException("Patient not found.")
        return self._longitudinal.build_timeline(patient_id)

    def finalize_summary(
        self,
        summary_id: uuid.UUID,
        reviewer_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Finalize summary and update encounter status."""
        summary = self._summary.finalize_summary(summary_id, reviewer_id)
        encounter = self._encounter_dao.find_by_id(summary.encounter_id)
        if encounter is not None:
            encounter.status = AiProcessingStatus.FINALIZED.value
            self._encounter_dao.update(encounter)
        self._audit.log_action(
            reviewer_id,
            "SUMMARY_FINALIZED",
            "clinical_summary",
            str(summary.id),
            {"encounter_id": str(summary.encounter_id)},
        )
        return {
            "summary_id": str(summary.id),
            "encounter_id": str(summary.encounter_id),
            "status": summary.status,
            "message": "Summary finalized.",
        }

    def _serialize_ocr(self, ocr: Any) -> dict[str, Any] | None:
        """Serialize OCR ORM row."""
        if ocr is None:
            return None
        return {
            "id": str(ocr.id),
            "structured_data": ocr.structured_data,
            "confidence": ocr.confidence_score,
        }

    def _serialize_nlp(self, nlp: Any) -> dict[str, Any] | None:
        """Serialize NLP ORM row."""
        if nlp is None:
            return None
        return {
            "id": str(nlp.id),
            "entities": nlp.entities,
            "snomed_codes": nlp.snomed_codes,
            "icd10_codes": nlp.icd10_codes,
            "confidence": nlp.confidence_score,
        }

    def _serialize_imaging(
        self, study: Any, inference: Any, encounter_id: uuid.UUID | None = None
    ) -> dict[str, Any] | None:
        """Serialize imaging ORM rows."""
        if study is None:
            return None
        payload: dict[str, Any] = {
            "study_id": str(study.id),
            "storage_path": study.storage_path,
            "status": study.status,
        }
        if inference is not None:
            heatmap_url = None
            if inference.heatmap_path and encounter_id is not None:
                heatmap_url = f"/api/clinical/encounters/{encounter_id}/heatmap"
            payload.update(
                {
                    "inference_id": str(inference.id),
                    "findings": inference.findings,
                    "heatmap_path": inference.heatmap_path,
                    "heatmap_url": heatmap_url,
                    "confidence": inference.confidence_score,
                    "model_version": inference.model_version,
                }
            )
        return payload

    def _serialize_summary(self, summary: Any) -> dict[str, Any] | None:
        """Serialize summary ORM row."""
        if summary is None:
            return None
        return {
            "id": str(summary.id),
            "summary_text": summary.summary_text,
            "status": summary.status,
            "reviewed_by": str(summary.reviewed_by) if summary.reviewed_by else None,
            "evidence_sources": summary.evidence_sources,
        }
