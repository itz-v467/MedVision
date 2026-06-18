"""Clinical workflow HTTP controller."""

from __future__ import annotations

import io
import uuid

from fastapi import UploadFile
from fastapi.responses import FileResponse, JSONResponse

from backend.core.base_controller import BaseController
from backend.core.request_context import CurrentUser
from backend.db import get_database_manager
from backend.service.ingestion_service import IngestionService
from backend.service.patient_search_service import PatientSearchService
from backend.service.symptom_triage_service import SymptomTriageService
from backend.utils.patient_id_generator import generate_patient_external_id
from backend.utils.exceptions import ValidationException
from backend.utils.upload_validation import normalize_file_type
from backend.utils.response_builder import ResponseBuilder


class ClinicalController(BaseController):
    """Handles clinical upload and encounter endpoints."""

    def __init__(self) -> None:
        """Initialize controller."""
        super().__init__()

    async def upload(
        self,
        current_user: CurrentUser,
        file: UploadFile,
        patient_external_id: str,
        patient_name: str,
        file_type: str,
        patient_age: str | None = None,
        patient_gender: str | None = None,
    ) -> JSONResponse:
        """Upload and process clinical files."""
        if file is None:
            raise ValidationException("File is required.")

        content = await file.read()
        file_stream = io.BytesIO(content)
        mime_type = file.content_type or "application/octet-stream"
        file_type = normalize_file_type(file_type)

        with get_database_manager().session_scope() as session:
            result = IngestionService(session).upload_and_process(
                user_id=current_user.user_id,
                patient_external_id=patient_external_id,
                patient_name=patient_name,
                file_stream=file_stream,
                file_name=file.filename or "upload.bin",
                mime_type=mime_type,
                file_type=file_type,
                patient_age=patient_age,
                patient_gender=patient_gender,
            )
        return ResponseBuilder.success(result)

    async def upload_case(
        self,
        current_user: CurrentUser,
        files: list[UploadFile],
        file_types: list[str],
        patient_external_id: str,
        patient_name: str,
        patient_age: str | None = None,
        patient_gender: str | None = None,
        symptom_transcript: str | None = None,
    ) -> JSONResponse:
        """Upload multiple documents into one unified clinical case."""
        if not files and not symptom_transcript:
            raise ValidationException(
                "Add at least one document or complete the symptom assistant chat."
            )
        if files and len(files) != len(file_types):
            raise ValidationException("Each file must have a matching document type.")

        documents = []
        for upload, doc_type in zip(files, file_types, strict=True):
            content = await upload.read()
            documents.append(
                {
                    "file_stream": io.BytesIO(content),
                    "file_name": upload.filename or "upload.bin",
                    "mime_type": upload.content_type or "application/octet-stream",
                    "file_type": normalize_file_type(doc_type),
                }
            )

        symptom_messages = None
        if symptom_transcript:
            import json

            try:
                symptom_messages = json.loads(symptom_transcript)
            except json.JSONDecodeError as exc:
                raise ValidationException("Invalid symptom transcript payload.") from exc

        with get_database_manager().session_scope() as session:
            result = IngestionService(session).upload_case(
                user_id=current_user.user_id,
                patient_external_id=patient_external_id,
                patient_name=patient_name,
                documents=documents,
                patient_age=patient_age,
                patient_gender=patient_gender,
                symptom_messages=symptom_messages,
            )
        return ResponseBuilder.success(result)

    def search_patients(self, query: str, limit: int = 10) -> JSONResponse:
        """Semantic + keyword patient search."""
        with get_database_manager().session_scope() as session:
            results = PatientSearchService(session).search(query, limit=limit)
        return ResponseBuilder.success({"patients": results, "query": query})

    def preview_patient_id(self) -> JSONResponse:
        """Preview the next auto-generated MedVision patient number."""
        with get_database_manager().session_scope() as session:
            external_id = generate_patient_external_id(session)
        return ResponseBuilder.success(
            {"patient_external_id": external_id, "auto_generated": True}
        )

    def list_encounters(self) -> JSONResponse:
        """Return encounter triage queue."""
        with get_database_manager().session_scope() as session:
            data = IngestionService(session).list_encounters()
        return ResponseBuilder.success({"encounters": data})

    def get_encounter(self, encounter_id: uuid.UUID) -> JSONResponse:
        """Return encounter detail for review."""
        with get_database_manager().session_scope() as session:
            data = IngestionService(session).get_encounter_detail(encounter_id)
        return ResponseBuilder.success(data)

    def delete_encounter(
        self, encounter_id: uuid.UUID, current_user: CurrentUser
    ) -> JSONResponse:
        """Soft-delete encounter; audit log retains a full snapshot."""
        with get_database_manager().session_scope() as session:
            result = IngestionService(session).delete_encounter(
                encounter_id, current_user.user_id
            )
        return ResponseBuilder.success(result)

    def finalize_summary(
        self, summary_id: uuid.UUID, current_user: CurrentUser
    ) -> JSONResponse:
        """Mark clinical summary as physician-reviewed."""
        with get_database_manager().session_scope() as session:
            result = IngestionService(session).finalize_summary(
                summary_id, current_user.user_id
            )
        return ResponseBuilder.success(result)

    def acknowledge_alert(
        self, alert_id: uuid.UUID, current_user: CurrentUser
    ) -> JSONResponse:
        """Acknowledge a clinical alert."""
        with get_database_manager().session_scope() as session:
            result = IngestionService(session).acknowledge_alert(
                alert_id, current_user.user_id
            )
        return ResponseBuilder.success(result)

    def get_patient_timeline(self, patient_id: uuid.UUID) -> JSONResponse:
        """Return longitudinal patient timeline."""
        with get_database_manager().session_scope() as session:
            data = IngestionService(session).get_patient_timeline(patient_id)
        return ResponseBuilder.success(data)

    def get_encounter_heatmap(self, encounter_id: uuid.UUID) -> FileResponse:
        """Return explainability heatmap image for an encounter."""
        with get_database_manager().session_scope() as session:
            path = IngestionService(session).get_heatmap_path(encounter_id)
        return FileResponse(path, media_type="image/png")

    def get_encounter_image(self, encounter_id: uuid.UUID) -> FileResponse:
        """Return source uploaded image for an encounter."""
        with get_database_manager().session_scope() as session:
            path, media_type = IngestionService(session).get_source_image_path(
                encounter_id
            )
        return FileResponse(path, media_type=media_type)

    def reanalyze_imaging(
        self, encounter_id: uuid.UUID, current_user: CurrentUser
    ) -> JSONResponse:
        """Re-run chest X-ray inference for an existing encounter."""
        with get_database_manager().session_scope() as session:
            data = IngestionService(session).reanalyze_imaging(
                encounter_id, current_user.user_id
            )
        return ResponseBuilder.success(data)

    def regenerate_synthesis(
        self, encounter_id: uuid.UUID, current_user: CurrentUser
    ) -> JSONResponse:
        """Rebuild doctor-style synthesis from all encounter inputs."""
        with get_database_manager().session_scope() as session:
            data = IngestionService(session).regenerate_synthesis(
                encounter_id, current_user.user_id
            )
        return ResponseBuilder.success(data)

    def get_care_plan(self, encounter_id: uuid.UUID) -> JSONResponse:
        with get_database_manager().session_scope() as session:
            from backend.service.care_plan_service import CarePlanService

            data = CarePlanService(session).get_care_plan(encounter_id)
        return ResponseBuilder.success(data)

    def approve_care_plan(
        self, encounter_id: uuid.UUID, current_user: CurrentUser
    ) -> JSONResponse:
        with get_database_manager().session_scope() as session:
            from backend.service.care_plan_service import CarePlanService

            data = CarePlanService(session).approve_care_plan(
                encounter_id, current_user.user_id
            )
        return ResponseBuilder.success(data)

    def request_consult(
        self,
        encounter_id: uuid.UUID,
        current_user: CurrentUser,
        payload: dict,
    ) -> JSONResponse:
        with get_database_manager().session_scope() as session:
            from backend.service.consult_request_service import ConsultRequestService

            data = ConsultRequestService(session).create_request(
                encounter_id,
                current_user.user_id,
                urgency=payload.get("urgency"),
                reason=payload.get("reason"),
                external_link_used=bool(payload.get("external_link_used")),
            )
        return ResponseBuilder.success(data)

    def consult_queue(self, _user: CurrentUser) -> JSONResponse:
        with get_database_manager().session_scope() as session:
            from backend.service.consult_request_service import ConsultRequestService

            data = ConsultRequestService(session).list_queue()
        return ResponseBuilder.success({"requests": data})

    def consult_config(self) -> JSONResponse:
        from backend.service.consult_request_service import ConsultRequestService

        return ResponseBuilder.success(ConsultRequestService.get_config_static())

    def triage_converse_intake(
        self,
        current_user: CurrentUser,
        payload: dict,
    ) -> JSONResponse:
        """Intake-time symptom chat (before encounter creation)."""
        with get_database_manager().session_scope() as session:
            data = SymptomTriageService(session).converse_intake(
                user_id=current_user.user_id,
                message=str(payload.get("message", "")),
                history=payload.get("messages") or [],
                patient_name=payload.get("patient_name"),
                patient_age=payload.get("patient_age"),
                patient_gender=payload.get("patient_gender"),
            )
        return ResponseBuilder.success(data)

    def triage_get_session(self, encounter_id: uuid.UUID) -> JSONResponse:
        """Return triage session for an encounter."""
        with get_database_manager().session_scope() as session:
            data = SymptomTriageService(session).get_session(encounter_id)
        return ResponseBuilder.success(data)

    def triage_create_session(
        self, encounter_id: uuid.UUID, current_user: CurrentUser
    ) -> JSONResponse:
        """Create triage session for encounter."""
        with get_database_manager().session_scope() as session:
            data = SymptomTriageService(session).create_session(
                encounter_id, current_user.user_id
            )
        return ResponseBuilder.success(data)

    def triage_add_message(
        self,
        encounter_id: uuid.UUID,
        current_user: CurrentUser,
        message: str,
    ) -> JSONResponse:
        """Add message to encounter triage session."""
        with get_database_manager().session_scope() as session:
            data = SymptomTriageService(session).add_message(
                encounter_id, current_user.user_id, message
            )
        return ResponseBuilder.success(data)

    def triage_finalize(
        self,
        encounter_id: uuid.UUID,
        current_user: CurrentUser,
        physician_note: str | None = None,
    ) -> JSONResponse:
        """Finalize triage session after physician review."""
        with get_database_manager().session_scope() as session:
            data = SymptomTriageService(session).finalize_session(
                encounter_id,
                current_user.user_id,
                physician_note=physician_note,
            )
        return ResponseBuilder.success(data)

    def triage_roadmap(self) -> JSONResponse:
        """Return staged advanced triage capabilities."""
        with get_database_manager().session_scope() as session:
            data = SymptomTriageService(session).get_roadmap()
        return ResponseBuilder.success({"roadmap": data})

    def get_task_status(self, task_id: str) -> JSONResponse:
        """Return status of a celery background task."""
        from backend.workers.celery_app import celery_app
        res = celery_app.AsyncResult(task_id)
        return ResponseBuilder.success({
            "task_id": task_id,
            "status": res.status,
            "result": res.result if res.ready() else None
        })

    def get_citation(self, citation_id: str) -> JSONResponse:
        """Return citation details for explainability."""
        from backend.ai.explainability.citation_engine import citation_engine
        data = citation_engine.get_citation(citation_id)
        if not data:
            from backend.enums.api_errors import ApiErrorCode
            from backend.enums.http_status import HttpStatus

            return ResponseBuilder.error(
                "Citation not found",
                ApiErrorCode.NOT_FOUND.value,
                HttpStatus.NOT_FOUND,
            )
        return ResponseBuilder.success(data)
