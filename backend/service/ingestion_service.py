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
from backend.utils.debug_log import pipeline_debug, pipeline_info, pipeline_warning
from backend.utils.exceptions import NotFoundException, ValidationException
from backend.utils.patient_name_matcher import compare_patient_names
from backend.utils.pipeline_tracker import (
    PipelineTracker,
    plain_step_label,
    summarize_pipeline_step,
)
from backend.service.patient_search_service import PatientSearchService
from backend.utils.patient_id_generator import resolve_patient_external_id
from backend.utils.upload_validation import validate_upload

logger = get_logger()

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
        patient_age: str | None = None,
        patient_gender: str | None = None,
    ) -> dict[str, Any]:
        """Upload file and execute AI pipeline."""
        mime_type = validate_upload(file_name, mime_type, file_type)

        file_stream.seek(0, 2)
        size = file_stream.tell()
        file_stream.seek(0)
        if size > MAX_FILE_SIZE_BYTES:
            raise ValidationException("File exceeds maximum allowed size.")

        patient_external_id = resolve_patient_external_id(
            self._session, patient_external_id
        )

        patient = (
            self._session.query(PatientModel)
            .filter(PatientModel.external_id == patient_external_id)
            .first()
        )
        if patient is None:
            patient = PatientModel(
                external_id=patient_external_id,
                full_name=patient_name,
                date_of_birth=patient_age,
                gender=patient_gender,
            )
            self._session.add(patient)
            self._session.flush()
        else:
            if patient_name and patient_name.strip().lower() not in {"unknown patient", "unknown"}:
                patient.full_name = patient_name
            if patient_age:
                patient.date_of_birth = patient_age
            if patient_gender:
                patient.gender = patient_gender

        PatientSearchService(self._session).index_patient(patient)

        if not patient_name or not patient_name.strip():
            raise ValidationException("Please enter the patient's full name.")

        pipeline_info(
            "upload",
            "Starting clinical upload",
            patient=patient_name,
            file_type=file_type,
            file_name=file_name,
        )

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

        tracker = PipelineTracker()

        ocr_label, ocr_detail = plain_step_label("ocr")
        with tracker.run_step("ocr", ocr_label, ocr_detail) as ocr_record:
            ocr_result = self._ocr.process_document(document.id)
            pipeline_debug(
                "ocr",
                "OCR finished",
                confidence=ocr_result.get("confidence"),
                chars=len(ocr_result.get("raw_text", "")),
                biomarkers=len(
                    ocr_result.get("structured_data", {}).get("biomarkers", [])
                ),
            )
            demographics = ocr_result.get("structured_data", {}).get(
                "patient_demographics", {}
            )
            extracted_name = demographics.get("full_name", "")
            name_validation = compare_patient_names(patient_name, extracted_name)
            if not name_validation["matched"]:
                pipeline_warning(
                    "identity",
                    "Name check warning — continuing processing",
                    entered=patient_name,
                    extracted=extracted_name,
                )

            structured = dict(ocr_result.get("structured_data", {}))
            structured["name_validation"] = name_validation
            ocr_result["structured_data"] = structured
            self._persist_ocr_structured_data(document.id, structured)
            ocr_record["summary"] = summarize_pipeline_step("ocr", ocr_result, file_type)

        nlp_text = ocr_result.get("raw_text") or ""
        nlp_label, nlp_detail = plain_step_label("nlp")
        with tracker.run_step("nlp", nlp_label, nlp_detail) as nlp_record:
            nlp_result = self._nlp.process_encounter(encounter.id, nlp_text)
            nlp_record["summary"] = summarize_pipeline_step("nlp", nlp_result, file_type)

        img_label, img_detail = plain_step_label("imaging")
        with tracker.run_step("imaging", img_label, img_detail) as imaging_record:
            imaging_result = self._imaging.analyze_study(
                encounter.id, storage_path, mime_type, file_type
            )
            if imaging_result.get("skipped"):
                imaging_record["status"] = "skipped"
            imaging_record["summary"] = summarize_pipeline_step(
                "imaging", imaging_result, file_type
            )

        corr_label, corr_detail = plain_step_label("correlation")
        with tracker.run_step("correlation", corr_label, corr_detail) as correlation_record:
            correlation = self._correlation.correlate(
                encounter.id,
                {
                    "imaging_confidence": imaging_result["confidence"],
                    "ocr_confidence": ocr_result["confidence"],
                    "nlp_confidence": nlp_result["confidence"],
                    "imaging_skipped": imaging_result.get("skipped", False),
                    "file_type": file_type,
                },
            )
            correlation_record["summary"] = summarize_pipeline_step(
                "correlation", correlation, file_type
            )

        explanation = self._explainability.build_explanation(
            encounter.id,
            imaging_result.get("findings") or {},
            imaging_result.get("heatmap_path"),
        )

        rag_label, rag_detail = plain_step_label("rag")
        with tracker.run_step("rag", rag_label, rag_detail) as rag_record:
            rag_record["summary"] = "Preparing multimodal context"

        sum_label, sum_detail = plain_step_label("summary")
        with tracker.run_step("summary", sum_label, sum_detail) as summary_record:
            summary = self._summary.generate_summary(
                encounter.id,
                {
                    "file_type": file_type,
                    "ocr": ocr_result,
                    "nlp": nlp_result,
                    "imaging": imaging_result,
                    "correlation": correlation,
                },
            )
            summary_record["summary"] = summarize_pipeline_step(
                "summary", summary, file_type
            )
            evidence = summary.get("evidence_sources", {})
            rag_chunks = evidence.get("rag_chunks") if isinstance(evidence, dict) else []
            if isinstance(rag_chunks, list) and rag_chunks:
                for step in tracker.steps:
                    if step["id"] == "rag":
                        step["summary"] = f"{len(rag_chunks)} evidence chunks retrieved"
                        break

        findings = imaging_result.get("findings") or {}
        alert_label, alert_detail = plain_step_label("alerts")
        with tracker.run_step("alerts", alert_label, alert_detail) as alerts_record:
            alerts = self._alerts.evaluate_findings(encounter.id, findings)
            alerts_record["summary"] = summarize_pipeline_step("alerts", alerts, file_type)

        pipeline_run = tracker.as_dict()
        structured["pipeline_run"] = pipeline_run
        self._persist_ocr_structured_data(document.id, structured)

        encounter.status = AiProcessingStatus.REVIEW_REQUIRED.value
        self._encounter_dao.update(encounter)
        logger.info("Workflow completed | encounter=%s", encounter.id)

        lab_analysis = structured.get("lab_analysis", {})
        return {
            "encounter_id": str(encounter.id),
            "document_id": str(document.id),
            "patient_external_id": patient.external_id,
            "patient_id": str(patient.id),
            "name_validation": name_validation,
            "pipeline": pipeline_run,
            "results_overview": self._build_results_overview(
                file_type=file_type,
                ocr_result=ocr_result,
                lab_analysis=lab_analysis,
                summary=summary,
                alerts=alerts,
                name_validation=name_validation,
            ),
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
        """Return encounter triage queue (excludes soft-deleted)."""
        rows = self._encounter_dao.list_recent_with_patient()
        return [
            {
                "id": str(encounter.id),
                "patient_id": str(encounter.patient_id),
                "patient_name": patient.full_name if patient else None,
                "patient_external_id": patient.external_id if patient else None,
                "status": encounter.status,
                "chief_complaint": encounter.chief_complaint,
                "created_at": encounter.created_at.isoformat(),
            }
            for encounter, patient in rows
        ]

    def delete_encounter(
        self, encounter_id: uuid.UUID, user_id: uuid.UUID
    ) -> dict[str, Any]:
        """Soft-delete an encounter while preserving an audit log snapshot."""
        encounter = self._encounter_dao.find_by_id(encounter_id)
        if encounter is None or encounter.status == AiProcessingStatus.DELETED.value:
            raise NotFoundException("Record not found or already removed.")

        snapshot = self.get_encounter_detail(encounter_id)
        encounter.status = AiProcessingStatus.DELETED.value
        self._encounter_dao.update(encounter)

        self._audit.log_action(
            user_id,
            "ENCOUNTER_DELETED",
            "encounter",
            str(encounter_id),
            metadata={
                "patient_id": str(encounter.patient_id),
                "snapshot": snapshot,
                "reason": "user_requested_delete",
            },
        )
        pipeline_info(
            "delete",
            "Encounter soft-deleted",
            encounter_id=str(encounter_id),
            user_id=str(user_id),
        )
        return {
            "encounter_id": str(encounter_id),
            "status": encounter.status,
            "message": "Record removed. A secure activity log has been saved.",
        }

    def get_encounter_detail(self, encounter_id: uuid.UUID) -> dict[str, Any]:
        """Return full encounter detail for physician review."""
        encounter = self._encounter_dao.find_by_id(encounter_id)
        if encounter is None or encounter.status == AiProcessingStatus.DELETED.value:
            raise NotFoundException("This record was removed or does not exist.")

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
        ocr_payload = self._serialize_ocr(ocr)
        structured = (ocr_payload or {}).get("structured_data", {})
        name_validation = structured.get("name_validation")
        pipeline_run = structured.get("pipeline_run")
        lab_analysis = structured.get("lab_analysis", {})
        results_overview = None
        if structured:
            results_overview = self._build_results_overview(
                file_type=documents[0].file_type if documents else "clinical_note",
                ocr_result={"structured_data": structured},
                lab_analysis=lab_analysis,
                summary=self._serialize_summary(summary) or {},
                alerts=alerts,
                name_validation=name_validation or {},
            )

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
                "date_of_birth": patient.date_of_birth if patient else None,
                "gender": patient.gender if patient else None,
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
            "ocr": ocr_payload,
            "nlp": self._serialize_nlp(nlp),
            "imaging": imaging,
            "summary": self._serialize_summary(summary),
            "name_validation": name_validation,
            "pipeline": pipeline_run,
            "results_overview": results_overview,
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

    def _persist_ocr_structured_data(
        self, document_id: uuid.UUID, structured: dict[str, Any]
    ) -> None:
        """Update stored OCR structured payload."""
        ocr = self._document_dao.find_ocr_by_document(document_id)
        if ocr is not None:
            ocr.structured_data = structured
            self._document_dao.save_ocr_result(ocr)

    def _build_results_overview(
        self,
        *,
        file_type: str,
        ocr_result: dict[str, Any],
        lab_analysis: dict[str, Any],
        summary: dict[str, Any],
        alerts: list[Any],
        name_validation: dict[str, Any],
    ) -> dict[str, Any]:
        """Structured high-level results for the review UI."""
        biomarkers = ocr_result.get("structured_data", {}).get("biomarkers", [])
        abnormal = lab_analysis.get("abnormal_count", 0)
        normal = lab_analysis.get("normal_count", 0)
        return {
            "document_type": file_type,
            "identity_verified": name_validation.get("matched", False),
            "extracted_patient_name": name_validation.get("extracted_name", ""),
            "entered_patient_name": name_validation.get("entered_name", ""),
            "lab_tests_parsed": len(biomarkers),
            "lab_abnormal_count": abnormal,
            "lab_normal_count": normal,
            "panel_coverage_pct": lab_analysis.get("panel_coverage_pct"),
            "summary_status": summary.get("status"),
            "alert_count": len(alerts) if isinstance(alerts, list) else 0,
            "headline": self._results_headline(file_type, abnormal, normal, alerts),
        }

    def _results_headline(
        self,
        file_type: str,
        abnormal: int,
        normal: int,
        alerts: list[Any],
    ) -> str:
        """One-line clinical headline for the results overview."""
        if file_type == "lab_report":
            if abnormal > 0:
                return f"{abnormal} test result(s) are outside the usual healthy range — please show your doctor."
            if normal > 0:
                return f"Good news: {normal} test result(s) look healthy based on standard ranges."
            return "Report uploaded — please ask your doctor to review the extracted values."
        alert_count = len(alerts) if isinstance(alerts, list) else 0
        if alert_count:
            return f"{alert_count} reminder(s) added — please review with your doctor."
        return "Analysis complete — your doctor should review this before any decisions."

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
