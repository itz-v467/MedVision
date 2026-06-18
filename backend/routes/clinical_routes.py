"""Clinical workflow API routes (FastAPI)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Body, Depends, File, Form, Query, UploadFile

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
    patient_external_id: str = Form("AUTO"),
    patient_name: str = Form("Unknown Patient"),
    file_type: str = Form(...),
    patient_age: str = Form(None),
    patient_gender: str = Form(None),
):
    """Upload file and run full AI clinical pipeline."""
    return await _controller.upload(
        current_user,
        file,
        patient_external_id,
        patient_name,
        file_type,
        patient_age,
        patient_gender,
    )


@router.post("/cases")
async def upload_case(
    current_user: CurrentUser = Depends(_auth.require_roles(*_upload_roles)),
    files: list[UploadFile] = File(default=[]),
    file_types: list[str] = Form(default=[]),
    patient_external_id: str = Form("AUTO"),
    patient_name: str = Form("Unknown Patient"),
    patient_age: str = Form(None),
    patient_gender: str = Form(None),
    symptom_transcript: str = Form(None),
):
    """Upload multiple documents as one unified clinical case."""
    return await _controller.upload_case(
        current_user,
        files,
        file_types,
        patient_external_id,
        patient_name,
        patient_age,
        patient_gender,
        symptom_transcript,
    )


@router.post("/triage/converse")
def triage_converse_intake(
    payload: dict = Body(...),
    current_user: CurrentUser = Depends(_auth.require_roles(*_upload_roles)),
):
    """Symptom chat during intake before encounter is created."""
    return _controller.triage_converse_intake(current_user, payload)


@router.get("/triage/roadmap")
def triage_roadmap(_user: CurrentUser = Depends(get_current_user)):
    """Staged advanced triage capabilities."""
    return _controller.triage_roadmap()


@router.post("/encounters/{encounter_id}/triage/session")
def triage_create_session(
    encounter_id: uuid.UUID,
    current_user: CurrentUser = Depends(_auth.require_roles(*_upload_roles)),
):
    """Create or return triage session for encounter."""
    return _controller.triage_create_session(encounter_id, current_user)


@router.get("/encounters/{encounter_id}/triage/session")
def triage_get_session(
    encounter_id: uuid.UUID,
    _user: CurrentUser = Depends(get_current_user),
):
    """Get triage session transcript and assessment."""
    return _controller.triage_get_session(encounter_id)


@router.post("/encounters/{encounter_id}/triage/messages")
def triage_add_message(
    encounter_id: uuid.UUID,
    payload: dict = Body(...),
    current_user: CurrentUser = Depends(_auth.require_roles(*_upload_roles)),
):
    """Send patient symptom message in encounter triage chat."""
    return _controller.triage_add_message(
        encounter_id,
        current_user,
        str(payload.get("message", "")),
    )


@router.post("/encounters/{encounter_id}/triage/finalize")
def triage_finalize(
    encounter_id: uuid.UUID,
    payload: dict = Body(default={}),
    current_user: CurrentUser = Depends(_auth.require_roles(*_review_roles)),
):
    """Finalize triage after physician review."""
    return _controller.triage_finalize(
        encounter_id,
        current_user,
        physician_note=payload.get("physician_note"),
    )


@router.get("/patients/search")
def search_patients(
    q: str = Query(""),
    limit: int = Query(10, ge=1, le=25),
    _user: CurrentUser = Depends(get_current_user),
):
    """Search patients by name, MedVision ID, or semantic similarity."""
    return _controller.search_patients(q, limit=limit)


@router.get("/patients/preview-id")
def preview_patient_id(_user: CurrentUser = Depends(get_current_user)):
    """Preview the next MedVision patient number (assigned formally at upload)."""
    return _controller.preview_patient_id()


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


@router.delete("/encounters/{encounter_id}")
def delete_encounter(
    encounter_id: uuid.UUID,
    current_user: CurrentUser = Depends(_auth.require_roles(*_upload_roles)),
):
    """Remove encounter from queue; activity log is preserved."""
    return _controller.delete_encounter(encounter_id, current_user)


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


@router.get("/consult/config")
def consult_config(_user: CurrentUser = Depends(get_current_user)):
    """Telehealth URL and default consult urgency."""
    return _controller.consult_config()


@router.get("/consult/queue")
def consult_queue(_user: CurrentUser = Depends(_auth.require_roles(*_review_roles))):
    """Pending consult requests for physicians."""
    return _controller.consult_queue(_user)


@router.post("/encounters/{encounter_id}/consult/request")
def request_consult(
    encounter_id: uuid.UUID,
    payload: dict = Body(default={}),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Request in-app physician consultation."""
    return _controller.request_consult(encounter_id, current_user, payload)


@router.get("/encounters/{encounter_id}/care-plan")
def get_care_plan(
    encounter_id: uuid.UUID,
    _user: CurrentUser = Depends(get_current_user),
):
    """Return AI care plan for encounter."""
    return _controller.get_care_plan(encounter_id)


@router.post("/encounters/{encounter_id}/care-plan/approve")
def approve_care_plan(
    encounter_id: uuid.UUID,
    current_user: CurrentUser = Depends(_auth.require_roles(*_review_roles)),
):
    """Physician approves suggested care plan."""
    return _controller.approve_care_plan(encounter_id, current_user)


@router.post("/encounters/{encounter_id}/synthesis/regenerate")
def regenerate_synthesis(
    encounter_id: uuid.UUID,
    current_user: CurrentUser = Depends(_auth.require_roles(*_review_roles)),
):
    """Rebuild global context, correlation, and dual summaries."""
    return _controller.regenerate_synthesis(encounter_id, current_user)


@router.post("/encounters/{encounter_id}/imaging/reanalyze")
def reanalyze_imaging(
    encounter_id: uuid.UUID,
    current_user: CurrentUser = Depends(_auth.require_roles(*_review_roles)),
):
    """Re-run ChestNet inference on the stored chest X-ray."""
    return _controller.reanalyze_imaging(encounter_id, current_user)


@router.get("/encounters/{encounter_id}/heatmap")
def encounter_heatmap(
    encounter_id: uuid.UUID,
    _user: CurrentUser = Depends(get_current_user),
):
    """Explainability heatmap PNG for an encounter."""
    return _controller.get_encounter_heatmap(encounter_id)


@router.get("/encounters/{encounter_id}/image")
def encounter_image(
    encounter_id: uuid.UUID,
    _user: CurrentUser = Depends(get_current_user),
):
    """Source uploaded image (chest X-ray) for an encounter."""
    return _controller.get_encounter_image(encounter_id)
