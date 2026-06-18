"""Symptom triage chatbot orchestration."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.client.triage_llm_client import get_triage_llm_client
from backend.config.triage_roadmap import roadmap_as_dict
from backend.constants.triage_policy import TRIAGE_DISCLAIMER
from backend.core.base_service import BaseService
from backend.dao.encounter_dao import EncounterDao
from backend.dao.triage_dao import TriageDao
from backend.enums.alert_priority import AlertPriority
from backend.model.document_model import AlertModel
from backend.model.patient_model import PatientModel
from backend.model.triage_model import TriageMessageModel, TriageSessionModel
from backend.service.audit_service import AuditService
from backend.service.clinical_factor_extractor_service import ClinicalFactorExtractorService
from backend.service.triage_context_builder_service import TriageContextBuilderService
from backend.service.triage_risk_scoring_service import TriageRiskScoringService
from backend.utils.exceptions import NotFoundException, ValidationException


class SymptomTriageService(BaseService):
    """Manage symptom triage sessions, messages, and assessments."""

    def __init__(self, session: Session) -> None:
        super().__init__(session)
        self._dao = TriageDao(session)
        self._encounter_dao = EncounterDao(session)
        self._risk = TriageRiskScoringService()
        self._context = TriageContextBuilderService(session)
        self._llm = get_triage_llm_client()
        self._audit = AuditService(session)

    def converse_intake(
        self,
        *,
        user_id: uuid.UUID,
        message: str,
        history: list[dict[str, Any]] | None = None,
        patient_name: str | None = None,
        patient_age: str | None = None,
        patient_gender: str | None = None,
    ) -> dict[str, Any]:
        """Stateless intake-time chat before an encounter exists."""
        message = (message or "").strip()
        if not message:
            raise ValidationException("Please describe your symptoms.")

        history = list(history or [])
        history.append({"role": "patient", "message_text": message})
        context = self._context.build_intake_context(
            patient_name=patient_name,
            patient_age=patient_age,
            patient_gender=patient_gender,
        )
        assessment = self._risk.score_conversation(history, patient_age=patient_age)
        factors = ClinicalFactorExtractorService().extract(
            patient={"age": patient_age, "gender": patient_gender},
            triage_data={"messages": history},
        )
        assessment["clinical_factors"] = factors
        assessment["data_completeness"] = factors.get("data_completeness")
        assessment["missing_factors"] = factors.get("missing_factors", [])
        reply, assistant_mode = self._llm.generate_reply(history, context, assessment)
        history.append({"role": "assistant", "message_text": reply})

        return {
            "messages": history,
            "assessment": assessment,
            "assistant_mode": assistant_mode,
            "llm_configured": assistant_mode in {"openai", "gemini"},
            "disclaimer": TRIAGE_DISCLAIMER,
            "roadmap_preview": roadmap_as_dict()[:3],
            "clinical_factors": factors,
            "missing_factors": factors.get("missing_factors", []),
            "data_completeness": factors.get("data_completeness"),
        }

    def create_session(
        self,
        encounter_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Create or return active triage session for an encounter."""
        encounter = self._encounter_dao.find_by_id(encounter_id)
        if encounter is None:
            raise NotFoundException("Encounter not found.")

        existing = self._dao.find_session_by_encounter(encounter_id)
        if existing is not None:
            return self.get_session(encounter_id)

        session = TriageSessionModel(
            encounter_id=encounter_id,
            patient_id=encounter.patient_id,
            created_by=user_id,
            status="active",
        )
        self._dao.create_session(session)
        welcome = TriageMessageModel(
            session_id=session.id,
            role="assistant",
            message_text=(
                "Hello — I'm here to help collect your symptoms before your doctor reviews your case. "
                "What symptoms are you experiencing today, and when did they start?"
            ),
            structured_symptoms={},
            safety_flags={},
        )
        self._dao.save_message(welcome)
        self._audit.log_action(
            user_id, "TRIAGE_SESSION_CREATED", "triage_session", str(session.id)
        )
        return self.get_session(encounter_id)

    def add_message(
        self,
        encounter_id: uuid.UUID,
        user_id: uuid.UUID,
        message: str,
    ) -> dict[str, Any]:
        """Add patient message and generate assistant triage reply."""
        message = (message or "").strip()
        if not message:
            raise ValidationException("Message cannot be empty.")

        session_row = self._ensure_session(encounter_id, user_id)
        patient = (
            self._session.query(PatientModel)
            .filter(PatientModel.id == session_row.patient_id)
            .first()
        )

        user_msg = TriageMessageModel(
            session_id=session_row.id,
            role="patient",
            message_text=message,
            structured_symptoms={"keywords": self._risk.extract_symptom_keywords(message)},
            safety_flags={},
        )
        self._dao.save_message(user_msg)

        transcript = self._message_dicts(session_row.id)
        context = self._context.build_encounter_context(encounter_id)
        assessment = self._risk.score_conversation(
            transcript,
            patient_age=patient.date_of_birth if patient else None,
        )
        factors = ClinicalFactorExtractorService().extract(
            patient={
                "date_of_birth": patient.date_of_birth if patient else None,
                "gender": patient.gender if patient else None,
            },
            triage_data={"messages": transcript, "session": {"assessment": assessment}},
        )
        assessment["clinical_factors"] = factors
        assessment["data_completeness"] = factors.get("data_completeness")
        assessment["missing_factors"] = factors.get("missing_factors", [])
        reply_text, _assistant_mode = self._llm.generate_reply(transcript, context, assessment)

        assistant_msg = TriageMessageModel(
            session_id=session_row.id,
            role="assistant",
            message_text=reply_text,
            structured_symptoms={},
            safety_flags=assessment,
        )
        self._dao.save_message(assistant_msg)

        user_msg.structured_symptoms = {
            "keywords": self._risk.extract_symptom_keywords(message),
            "clinical_factors": factors,
        }
        self._session.flush()

        session_row.risk_level = assessment["risk_level"]
        session_row.recommended_disposition = assessment["recommended_disposition"]
        session_row.assessment = assessment
        self._dao.update_session(session_row)

        if assessment.get("escalation_required"):
            self._create_escalation_alert(encounter_id, assessment)

        self._audit.log_action(
            user_id,
            "TRIAGE_MESSAGE",
            "triage_session",
            str(session_row.id),
            metadata={"risk_level": assessment["risk_level"]},
        )

        return self.get_session(encounter_id)

    def import_transcript(
        self,
        encounter_id: uuid.UUID,
        user_id: uuid.UUID,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Import intake-time transcript after case upload."""
        if not messages:
            return {}

        session_row = self._ensure_session(encounter_id, user_id)
        existing = self._dao.list_messages(session_row.id)
        if len(existing) > 1:
            return self.get_session(encounter_id)

        for item in messages:
            role = item.get("role", "patient")
            if role == "user":
                role = "patient"
            text = item.get("message_text") or item.get("content") or ""
            if not text.strip():
                continue
            self._dao.save_message(
                TriageMessageModel(
                    session_id=session_row.id,
                    role=role,
                    message_text=text.strip(),
                    structured_symptoms=(
                        {"keywords": self._risk.extract_symptom_keywords(text)}
                        if role == "patient"
                        else {}
                    ),
                    safety_flags={},
                )
            )

        transcript = self._message_dicts(session_row.id)
        patient = (
            self._session.query(PatientModel)
            .filter(PatientModel.id == session_row.patient_id)
            .first()
        )
        assessment = self._risk.score_conversation(
            transcript,
            patient_age=patient.date_of_birth if patient else None,
        )
        session_row.risk_level = assessment["risk_level"]
        session_row.recommended_disposition = assessment["recommended_disposition"]
        session_row.assessment = assessment
        self._dao.update_session(session_row)

        if assessment.get("escalation_required"):
            self._create_escalation_alert(encounter_id, assessment)

        self._audit.log_action(
            user_id,
            "TRIAGE_TRANSCRIPT_IMPORTED",
            "triage_session",
            str(session_row.id),
        )
        return self.get_session(encounter_id)

    def finalize_session(
        self,
        encounter_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        physician_note: str | None = None,
    ) -> dict[str, Any]:
        """Finalize triage for physician review."""
        session_row = self._dao.find_session_by_encounter(encounter_id)
        if session_row is None:
            raise NotFoundException("No triage session for this encounter.")

        session_row.status = "finalized"
        session_row.finalized_at = datetime.now(UTC)
        if physician_note:
            assessment = dict(session_row.assessment or {})
            assessment["physician_note"] = physician_note
            session_row.assessment = assessment
        self._dao.update_session(session_row)
        self._audit.log_action(
            user_id, "TRIAGE_FINALIZED", "triage_session", str(session_row.id)
        )
        return self.get_session(encounter_id)

    def get_session(self, encounter_id: uuid.UUID) -> dict[str, Any]:
        """Return triage session with messages and assessment."""
        session_row = self._dao.find_session_by_encounter(encounter_id)
        if session_row is None:
            return {"session": None, "messages": [], "roadmap": roadmap_as_dict()}

        messages = self._dao.list_messages(session_row.id)
        return {
            "session": {
                "id": str(session_row.id),
                "encounter_id": str(session_row.encounter_id),
                "status": session_row.status,
                "risk_level": session_row.risk_level,
                "recommended_disposition": session_row.recommended_disposition,
                "assessment": session_row.assessment or {},
                "created_at": session_row.created_at.isoformat(),
                "finalized_at": (
                    session_row.finalized_at.isoformat()
                    if session_row.finalized_at
                    else None
                ),
            },
            "messages": [
                {
                    "id": str(msg.id),
                    "role": msg.role,
                    "message_text": msg.message_text,
                    "structured_symptoms": msg.structured_symptoms,
                    "safety_flags": msg.safety_flags,
                    "created_at": msg.created_at.isoformat(),
                }
                for msg in messages
            ],
            "disclaimer": TRIAGE_DISCLAIMER,
            "roadmap": roadmap_as_dict(),
        }

    def get_roadmap(self) -> list[dict[str, str]]:
        """Return staged advanced use-case roadmap."""
        return roadmap_as_dict()

    def _ensure_session(
        self, encounter_id: uuid.UUID, user_id: uuid.UUID
    ) -> TriageSessionModel:
        session_row = self._dao.find_session_by_encounter(encounter_id)
        if session_row is None:
            self.create_session(encounter_id, user_id)
            session_row = self._dao.find_session_by_encounter(encounter_id)
        if session_row is None:
            raise NotFoundException("Could not create triage session.")
        return session_row

    def _message_dicts(self, session_id: uuid.UUID) -> list[dict[str, Any]]:
        return [
            {"role": msg.role, "message_text": msg.message_text}
            for msg in self._dao.list_messages(session_id)
        ]

    def _create_escalation_alert(
        self, encounter_id: uuid.UUID, assessment: dict[str, Any]
    ) -> None:
        priority = (
            AlertPriority.CRITICAL
            if assessment.get("risk_level") == "emergency"
            else AlertPriority.HIGH
        )
        alert = AlertModel(
            encounter_id=encounter_id,
            title=f"Triage escalation: {assessment.get('risk_level', 'high')}",
            message=assessment.get("recommended_disposition", "Urgent evaluation advised."),
            priority=priority.value,
        )
        self._session.add(alert)
        self._session.flush()
