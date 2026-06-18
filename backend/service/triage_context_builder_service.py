"""Build encounter context for grounded triage responses."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from backend.dao.document_dao import DocumentDao
from backend.dao.encounter_dao import EncounterDao
from backend.model.patient_model import PatientModel
from backend.service.longitudinal_analysis_service import LongitudinalAnalysisService


class TriageContextBuilderService:
    """Assemble patient + encounter context for triage dialogue."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._encounter_dao = EncounterDao(session)
        self._document_dao = DocumentDao(session)
        self._longitudinal = LongitudinalAnalysisService(session)

    def build_intake_context(
        self,
        *,
        patient_name: str | None = None,
        patient_age: str | None = None,
        patient_gender: str | None = None,
    ) -> dict[str, Any]:
        """Context available before an encounter exists."""
        return {
            "patient_name": patient_name or "",
            "patient_age": patient_age or "",
            "patient_gender": patient_gender or "",
            "mode": "intake",
        }

    def build_encounter_context(self, encounter_id: uuid.UUID) -> dict[str, Any]:
        """Pull encounter artifacts for contextual triage."""
        encounter = self._encounter_dao.find_by_id(encounter_id)
        if encounter is None:
            return {}

        patient = (
            self._session.query(PatientModel)
            .filter(PatientModel.id == encounter.patient_id)
            .first()
        )
        ocr = self._document_dao.find_ocr_by_encounter(encounter_id)
        nlp = self._document_dao.find_nlp_by_encounter(encounter_id)
        study, inference = self._document_dao.find_imaging_by_encounter(encounter_id)
        alerts = self._document_dao.find_alerts_by_encounter(encounter_id)
        timeline = self._longitudinal.build_timeline(encounter.patient_id)

        structured = (ocr.structured_data if ocr else {}) or {}
        imaging_findings = inference.findings if inference else {}

        return {
            "mode": "encounter",
            "encounter_id": str(encounter_id),
            "case_type": encounter.case_type,
            "patient_name": patient.full_name if patient else "",
            "patient_age": patient.date_of_birth if patient else "",
            "patient_gender": patient.gender if patient else "",
            "biomarker_count": len(structured.get("biomarkers", [])),
            "nlp_entities": nlp.entities if nlp else {},
            "imaging_findings": imaging_findings,
            "correlation": structured.get("correlation", {}),
            "alert_count": len(alerts),
            "prior_encounters": timeline.get("encounter_count", 0),
        }
