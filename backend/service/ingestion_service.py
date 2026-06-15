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
from backend.service.clinical_correlation_engine import ClinicalCorrelationEngine
from backend.service.clinical_summary_service import ClinicalSummaryService
from backend.service.encounter_fusion_service import EncounterFusionService
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
from backend.utils.case_type import infer_case_type
from backend.utils.imaging_summary import format_imaging_summary, imaging_attention_items
from backend.utils.imaging_regions import compute_imaging_status, derive_anomaly_regions
from backend.utils.patient_id_generator import resolve_patient_external_id
from backend.utils.storage_paths import resolve_storage_file
from backend.utils.upload_validation import (
    IMAGE_MIME_TYPES,
    normalize_file_type,
    resolve_document_type,
    validate_image_content,
    validate_type_selection,
    validate_upload,
)

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
        self._fusion = EncounterFusionService()
        self._clinical_correlation = ClinicalCorrelationEngine()

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
        """Upload a single file (backward-compatible wrapper)."""
        return self.upload_case(
            user_id=user_id,
            patient_external_id=patient_external_id,
            patient_name=patient_name,
            documents=[
                {
                    "file_stream": file_stream,
                    "file_name": file_name,
                    "mime_type": mime_type,
                    "file_type": file_type,
                }
            ],
            patient_age=patient_age,
            patient_gender=patient_gender,
        )

    def upload_case(
        self,
        user_id: uuid.UUID,
        patient_external_id: str,
        patient_name: str,
        documents: list[dict[str, Any]],
        patient_age: str | None = None,
        patient_gender: str | None = None,
    ) -> dict[str, Any]:
        """Upload one or more documents into a single encounter and run unified AI pipeline."""
        if not documents:
            raise ValidationException("At least one clinical document is required.")

        validated_docs: list[dict[str, Any]] = []
        for doc in documents:
            file_type = normalize_file_type(str(doc.get("file_type", "")))
            file_name = doc.get("file_name") or "upload.bin"
            mime_type = validate_upload(file_name, doc.get("mime_type") or "", file_type)
            validate_type_selection(file_name, mime_type, file_type)
            file_type = resolve_document_type(file_name, mime_type, file_type)
            stream: BinaryIO = doc["file_stream"]
            stream.seek(0, 2)
            size = stream.tell()
            stream.seek(0)
            if size > MAX_FILE_SIZE_BYTES:
                raise ValidationException(f"File {file_name} exceeds maximum allowed size.")
            validated_docs.append(
                {
                    "file_stream": stream,
                    "file_name": file_name,
                    "mime_type": mime_type,
                    "file_type": file_type,
                }
            )

        case_type = infer_case_type(d["file_type"] for d in validated_docs)
        patient_external_id = resolve_patient_external_id(self._session, patient_external_id)
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
            "Starting clinical case upload",
            patient=patient_name,
            case_type=case_type,
            document_count=len(validated_docs),
        )

        encounter = EncounterModel(
            patient_id=patient.id,
            assigned_user_id=user_id,
            status=AiProcessingStatus.PROCESSING.value,
            case_type=case_type,
        )
        self._encounter_dao.create(encounter)
        tracker = PipelineTracker()

        document_results: list[dict[str, Any]] = []
        name_validation: dict[str, Any] = {}
        xray_doc = None

        ocr_label, ocr_detail = plain_step_label("ocr")
        with tracker.run_step("ocr", ocr_label, ocr_detail) as ocr_record:
            total_biomarkers = 0
            for doc in validated_docs:
                storage_path = self._storage.save_file(doc["file_stream"], doc["file_name"])
                if doc["mime_type"] in IMAGE_MIME_TYPES:
                    validate_image_content(storage_path, doc["file_type"])
                document = DocumentModel(
                    encounter_id=encounter.id,
                    file_name=doc["file_name"],
                    mime_type=doc["mime_type"],
                    storage_path=storage_path,
                    file_type=doc["file_type"],
                    status=AiProcessingStatus.PROCESSING.value,
                )
                self._document_dao.create_document(document)
                self._audit.log_action(user_id, "FILE_UPLOAD", "document", str(document.id))

                ocr_result = self._ocr.process_document(document.id)
                structured = dict(ocr_result.get("structured_data", {}))
                demographics = structured.get("patient_demographics", {})
                extracted_name = demographics.get("full_name", "")
                doc_name_validation = compare_patient_names(patient_name, extracted_name)
                structured["name_validation"] = doc_name_validation
                ocr_result["structured_data"] = structured
                self._persist_ocr_structured_data(document.id, structured)

                if not name_validation:
                    name_validation = doc_name_validation
                total_biomarkers += len(structured.get("biomarkers", []))
                document_results.append({"document": document, "ocr": ocr_result})
                if doc["file_type"] == "xray":
                    xray_doc = document

            ocr_record["summary"] = (
                f"{len(document_results)} document(s) · {total_biomarkers} lab value(s) extracted"
            )

        imaging_result: dict[str, Any] = {"skipped": True, "findings": {}, "confidence": 0.0}
        img_label, img_detail = plain_step_label("imaging")
        with tracker.run_step("imaging", img_label, img_detail) as imaging_record:
            if xray_doc is not None:
                imaging_result = self._imaging.analyze_study(
                    encounter.id,
                    xray_doc.storage_path,
                    xray_doc.mime_type,
                    "xray",
                    source_document_id=xray_doc.id,
                )
            if imaging_result.get("skipped"):
                imaging_record["status"] = "skipped"
            imaging_record["summary"] = summarize_pipeline_step(
                "imaging", imaging_result, case_type
            )

        fused = self._fusion.fuse(
            document_results=document_results,
            imaging_result=imaging_result,
            case_type=case_type,
        )
        merged_text = fused.get("merged_text") or ""

        nlp_label, nlp_detail = plain_step_label("nlp")
        with tracker.run_step("nlp", nlp_label, nlp_detail) as nlp_record:
            nlp_result = self._nlp.process_encounter(encounter.id, merged_text)
            nlp_record["summary"] = summarize_pipeline_step("nlp", nlp_result, case_type)

        fused["nlp_confidence"] = nlp_result.get("confidence", 0)

        corr_label, corr_detail = plain_step_label("correlation")
        with tracker.run_step("correlation", corr_label, corr_detail) as correlation_record:
            correlation = self._clinical_correlation.correlate(fused)
            correlation_record["summary"] = summarize_pipeline_step(
                "correlation", correlation, case_type
            )

        primary_doc = document_results[0]["document"]
        primary_ocr = document_results[0]["ocr"]
        structured = dict(fused.get("structured_data", {}))
        structured["name_validation"] = name_validation
        structured["correlation"] = correlation
        structured["case_type"] = case_type
        primary_ocr["structured_data"] = structured
        self._persist_ocr_structured_data(primary_doc.id, structured)

        if case_type == "single_xray" and not imaging_result.get("skipped"):
            imaging_summary = format_imaging_summary(imaging_result)
            lab_analysis = dict(structured.get("lab_analysis", {}))
            lab_analysis["clinical_summary"] = imaging_summary
            lab_analysis["precautions"] = [
                {
                    "test": item["test"],
                    "flag": item["flag"],
                    "value": "",
                    "reference_range": "",
                    "precaution": item["text"],
                    "severity": "high" if item["flag"] == "IMAGE" else "moderate",
                }
                for item in imaging_attention_items(imaging_result)
            ]
            structured["lab_analysis"] = lab_analysis
            structured["imaging_summary"] = imaging_summary
            primary_ocr["structured_data"] = structured
            self._persist_ocr_structured_data(primary_doc.id, structured)

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
                    "file_type": fused.get("file_type", case_type),
                    "case_type": case_type,
                    "document_manifest": fused.get("document_manifest", []),
                    "ocr": primary_ocr,
                    "nlp": nlp_result,
                    "imaging": imaging_result,
                    "correlation": correlation,
                    "fused": fused,
                },
            )
            summary_record["summary"] = summarize_pipeline_step("summary", summary, case_type)
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
            alerts.extend(
                self._alerts.evaluate_lab_abnormalities(
                    encounter.id, fused.get("biomarkers", [])
                )
            )
            alerts_record["summary"] = summarize_pipeline_step("alerts", alerts, case_type)

        pipeline_run = tracker.as_dict()
        structured["pipeline_run"] = pipeline_run
        self._persist_ocr_structured_data(primary_doc.id, structured)

        encounter.status = AiProcessingStatus.REVIEW_REQUIRED.value
        self._encounter_dao.update(encounter)
        logger.info("Workflow completed | encounter=%s case_type=%s", encounter.id, case_type)

        lab_analysis = structured.get("lab_analysis", {})
        return {
            "encounter_id": str(encounter.id),
            "document_id": str(primary_doc.id),
            "document_ids": [str(item["document"].id) for item in document_results],
            "patient_external_id": patient.external_id,
            "patient_id": str(patient.id),
            "case_type": case_type,
            "name_validation": name_validation,
            "pipeline": pipeline_run,
            "results_overview": self._build_results_overview(
                file_type=fused.get("file_type", case_type),
                case_type=case_type,
                ocr_result=primary_ocr,
                lab_analysis=lab_analysis,
                summary=summary,
                alerts=alerts,
                name_validation=name_validation,
                imaging_result=imaging_result,
                correlation=correlation,
            ),
            "ocr": primary_ocr,
            "nlp": nlp_result,
            "imaging": imaging_result,
            "correlation": correlation,
            "explainability": explanation,
            "summary": summary,
            "alerts": alerts,
            "documents": [
                {
                    "id": str(item["document"].id),
                    "file_name": item["document"].file_name,
                    "file_type": item["document"].file_type,
                }
                for item in document_results
            ],
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
        ocr = self._resolve_fused_ocr(encounter_id)
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
        correlation = structured.get("correlation", {})
        case_type = encounter.case_type or structured.get("case_type") or infer_case_type(
            doc.file_type for doc in documents
        )
        file_type = case_type if case_type == "multimodal" else (
            documents[0].file_type if documents else "clinical_note"
        )
        results_overview = None
        if structured:
            results_overview = self._build_results_overview(
                file_type=file_type,
                case_type=case_type,
                ocr_result={"structured_data": structured},
                lab_analysis=lab_analysis,
                summary=self._serialize_summary(summary) or {},
                alerts=alerts,
                name_validation=name_validation or {},
                imaging_result=imaging,
                correlation=correlation,
            )

        return {
            "encounter": {
                "id": str(encounter.id),
                "patient_id": str(encounter.patient_id),
                "status": encounter.status,
                "chief_complaint": encounter.chief_complaint,
                "case_type": case_type,
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
            "correlation": correlation,
            "document_manifest": structured.get("document_manifest", []),
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
        encounter = self._encounter_dao.find_by_id(encounter_id)
        if encounter is None:
            raise NotFoundException("Encounter not found.")

        _, inference = self._document_dao.find_imaging_by_encounter(encounter_id)
        if inference is None or not inference.heatmap_path:
            raise NotFoundException("Heatmap not available for this encounter.")

        return str(self._validate_storage_file(inference.heatmap_path))

    def get_source_image_path(self, encounter_id: uuid.UUID) -> tuple[str, str]:
        """Return validated source image path and MIME type for an encounter."""
        from backend.service.imaging_ai_service import IMAGE_MIME_TYPES

        encounter = self._encounter_dao.find_by_id(encounter_id)
        if encounter is None:
            raise NotFoundException("Encounter not found.")

        documents = self._document_dao.find_documents_by_encounter(encounter_id)
        if not documents:
            raise NotFoundException("No document found for this encounter.")

        document = next(
            (doc for doc in documents if doc.file_type == "xray"),
            next((doc for doc in documents if doc.mime_type in IMAGE_MIME_TYPES), documents[0]),
        )
        if document.mime_type not in IMAGE_MIME_TYPES:
            raise NotFoundException("Source file is not an image.")

        return str(resolve_storage_file(document.storage_path)), document.mime_type

    def _validate_storage_file(self, file_path: str):
        """Ensure a file path is inside the configured storage root."""
        return resolve_storage_file(file_path)

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
        imaging_result: dict[str, Any] | None = None,
        case_type: str | None = None,
        correlation: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Structured high-level results for the review UI."""
        biomarkers = ocr_result.get("structured_data", {}).get("biomarkers", [])
        abnormal = lab_analysis.get("abnormal_count", 0)
        normal = lab_analysis.get("normal_count", 0)
        resolved_case_type = case_type or file_type
        return {
            "document_type": file_type,
            "case_type": resolved_case_type,
            "identity_verified": name_validation.get("matched", False),
            "extracted_patient_name": name_validation.get("extracted_name", ""),
            "entered_patient_name": name_validation.get("entered_name", ""),
            "lab_tests_parsed": len(biomarkers),
            "lab_abnormal_count": abnormal,
            "lab_normal_count": normal,
            "panel_coverage_pct": lab_analysis.get("panel_coverage_pct"),
            "summary_status": summary.get("status"),
            "alert_count": len(alerts) if isinstance(alerts, list) else 0,
            "correlation_score": (correlation or {}).get("weighted_evidence_score"),
            "headline": self._results_headline(
                file_type,
                abnormal,
                normal,
                alerts,
                imaging_result,
                case_type=resolved_case_type,
                lab_analysis=lab_analysis,
            ),
        }

    def _results_headline(
        self,
        file_type: str,
        abnormal: int,
        normal: int,
        alerts: list[Any],
        imaging_result: dict[str, Any] | None = None,
        *,
        case_type: str | None = None,
        lab_analysis: dict[str, Any] | None = None,
    ) -> str:
        """One-line clinical headline for the results overview."""
        if case_type == "multimodal":
            custom = (lab_analysis or {}).get("clinical_summary", "")
            if custom:
                return custom.split(".")[0] + " — unified case review required"
            return "Multimodal case: review lab and imaging findings together."
        if file_type == "lab_report":
            if abnormal > 0:
                return f"{abnormal} test result(s) are outside the usual healthy range — please show your doctor."
            if normal > 0:
                return f"Good news: {normal} test result(s) look healthy based on standard ranges."
            return "Report uploaded — please ask your doctor to review the extracted values."
        if file_type == "xray":
            return format_imaging_summary(imaging_result or {"skipped": True})
        alert_count = len(alerts) if isinstance(alerts, list) else 0
        if alert_count:
            return f"{alert_count} reminder(s) added — please review with your doctor."
        return "Analysis complete — your doctor should review this before any decisions."

    def _resolve_fused_ocr(self, encounter_id: uuid.UUID) -> Any:
        """Return OCR row carrying fused encounter structured data when present."""
        rows = self._document_dao.find_all_ocr_by_encounter(encounter_id)
        if not rows:
            return None
        for row in rows:
            structured = row.structured_data or {}
            if structured.get("document_manifest") or structured.get("correlation"):
                return row
        return rows[-1]

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
        from pathlib import Path

        from backend.client.xray_inference_client import get_xray_inference_client

        if study is None:
            return None
        payload: dict[str, Any] = {
            "study_id": str(study.id),
            "storage_path": study.storage_path,
            "status": study.status,
        }
        if encounter_id is not None:
            payload["image_url"] = f"/api/clinical/encounters/{encounter_id}/image"
        if inference is not None:
            heatmap_url = None
            heatmap_exists = False
            if inference.heatmap_path:
                heatmap_exists = Path(inference.heatmap_path).is_file()
                if heatmap_exists and encounter_id is not None:
                    heatmap_url = f"/api/clinical/encounters/{encounter_id}/heatmap"

            proof = {}
            regions: list[dict[str, Any]] = []
            if isinstance(inference.bounding_boxes, dict):
                proof = inference.bounding_boxes.get("analysis_proof", {})
                raw_regions = inference.bounding_boxes.get("regions", [])
                if not raw_regions and isinstance(proof, dict):
                    raw_regions = proof.get("regions", [])
                if isinstance(raw_regions, list):
                    regions = raw_regions

            if not regions and study.storage_path:
                try:
                    image_path = str(resolve_storage_file(study.storage_path))
                    regions = derive_anomaly_regions(
                        image_path, inference.findings if inference else {}
                    )
                    if regions and isinstance(inference.bounding_boxes, dict):
                        inference.bounding_boxes["regions"] = regions
                        if isinstance(inference.bounding_boxes.get("analysis_proof"), dict):
                            inference.bounding_boxes["analysis_proof"]["regions"] = regions
                        self._document_dao.save_inference(inference)
                except Exception as exc:
                    logger.warning("Region re-derive failed: %s", exc)
                    regions = derive_anomaly_regions(
                        study.storage_path, inference.findings if inference else {}
                    )

            txrv = get_xray_inference_client()
            engine = proof.get("engine") or (
                "torchxrayvision"
                if not str(inference.model_version).startswith("fallback")
                else "fallback"
            )
            imaging_status = compute_imaging_status(
                study=study,
                inference=inference,
                regions=regions,
            )
            payload.update(
                {
                    "inference_id": str(inference.id),
                    "findings": inference.findings,
                    "heatmap_path": inference.heatmap_path,
                    "heatmap_url": heatmap_url,
                    "confidence": inference.confidence_score,
                    "model_version": inference.model_version,
                    "regions": regions,
                    "imaging_status": imaging_status,
                    "proof": {
                        "engine": engine,
                        "txrv_installed": txrv.is_available,
                        "model_version": inference.model_version,
                        "heatmap_available": heatmap_exists,
                        "study_status": study.status,
                        "imaging_status": imaging_status,
                        "pathology_scores": proof.get("pathology_scores") or {},
                        "is_fallback": engine == "fallback"
                        or str(inference.model_version).startswith("fallback"),
                    },
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
