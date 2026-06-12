"""Clinical workflow API routes (FastAPI)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile

from backend.auth.dependencies import AuthDependencies, get_current_user
from backend.controller.clinical_controller import ClinicalController
from backend.core.request_context import CurrentUser
from backend.enums.user_roles import UserRole

router = APIRouter(prefix="/api/clinical", tags=["Clinical AI"])
_controller = ClinicalController()
_auth = AuthDependencies()

_upload_roles = (
    UserRole.ADMIN,
    UserRole.RADIOLOGIST,
    UserRole.PHYSICIAN,
    UserRole.TECHNICIAN,
)

_review_roles = (
    UserRole.ADMIN,
    UserRole.RADIOLOGIST,
    UserRole.PHYSICIAN,
)


@router.post("/upload")
async def upload(
    current_user: CurrentUser = Depends(_auth.require_roles(*_upload_roles)),
    file: UploadFile = File(...),
    patient_external_id: str = Form("P-UNKNOWN"),
    patient_name: str = Form("Unknown Patient"),
    file_type: str = Form("lab_report"),
):
    """Upload file and run full AI clinical pipeline."""
    return await _controller.upload(
        current_user,
        file,
        patient_external_id,
        patient_name,
        file_type,
    )


@router.get("/encounters")
def encounters(_user: CurrentUser = Depends(get_current_user)):
    """Encounter triage queue."""
    return _controller.list_encounters()


@router.get("/encounters/{encounter_id}")
def encounter_detail(
    encounter_id: uuid.UUID,
    _user: CurrentUser = Depends(get_current_user),
):
    """Full encounter detail for physician review."""
    return _controller.get_encounter(encounter_id)


@router.post("/summaries/{summary_id}/finalize")
def finalize_summary(
    summary_id: uuid.UUID,
    current_user: CurrentUser = Depends(_auth.require_roles(*_review_roles)),
):
    """Finalize AI summary after physician review."""
    return _controller.finalize_summary(summary_id, current_user)


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Acknowledge a clinical alert."""
    return _controller.acknowledge_alert(alert_id, current_user)


@router.get("/patients/{patient_id}/timeline")
def patient_timeline(
    patient_id: uuid.UUID,
    _user: CurrentUser = Depends(get_current_user),
):
    """Longitudinal timeline for a patient."""
    return _controller.get_patient_timeline(patient_id)


@router.get("/encounters/{encounter_id}/heatmap")
def encounter_heatmap(
    encounter_id: uuid.UUID,
    _user: CurrentUser = Depends(get_current_user),
):
    """Explainability heatmap PNG for an encounter."""
    return _controller.get_encounter_heatmap(encounter_id)
