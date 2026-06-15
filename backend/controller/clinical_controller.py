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
