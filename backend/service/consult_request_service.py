"""Consult request orchestration."""

from __future__ import annotations

import os
import uuid
from typing import Any

from sqlalchemy.orm import Session

from backend.core.base_service import BaseService
from backend.dao.consult_dao import ConsultDao
from backend.dao.encounter_dao import EncounterDao
from backend.model.consult_model import ConsultRequestModel
from backend.model.patient_model import PatientModel
from backend.service.audit_service import AuditService
from backend.utils.exceptions import NotFoundException, ValidationException

DEFAULT_URGENCY = os.getenv("CONSULT_DEFAULT_URGENCY", "within_24h")
TELEHEALTH_URL = os.getenv("TELEHEALTH_BOOKING_URL", "")


class ConsultRequestService(BaseService):
    """Create and list physician consult requests."""

    def __init__(self, session: Session) -> None:
        super().__init__(session)
        self._dao = ConsultDao(session)
        self._encounter_dao = EncounterDao(session)
        self._audit = AuditService(session)

    def create_request(
        self,
        encounter_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        urgency: str | None = None,
        reason: str | None = None,
        external_link_used: bool = False,
    ) -> dict[str, Any]:
        encounter = self._encounter_dao.find_by_id(encounter_id)
        if encounter is None:
            raise NotFoundException("Encounter not found.")

        patient = (
            self._session.query(PatientModel)
            .filter(PatientModel.id == encounter.patient_id)
            .first()
        )
        if patient is None:
            raise ValidationException("Patient not found for encounter.")

        request = ConsultRequestModel(
            encounter_id=encounter_id,
            patient_id=patient.id,
            requested_by_user_id=user_id,
            urgency=urgency or DEFAULT_URGENCY,
            reason=reason,
            status="pending",
            external_link_used=external_link_used,
        )
        self._dao.create(request)
        self._audit.log_action(
            user_id,
            "CONSULT_REQUESTED",
            "consult_request",
            str(request.id),
            {"encounter_id": str(encounter_id), "urgency": request.urgency},
        )
        return self._serialize(request, patient)

    def list_queue(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._dao.list_pending(limit=limit)
        results: list[dict[str, Any]] = []
        for row in rows:
            patient = (
                self._session.query(PatientModel)
                .filter(PatientModel.id == row.patient_id)
                .first()
            )
            results.append(self._serialize(row, patient))
        return results

    def get_config(self) -> dict[str, Any]:
        return self._config_payload()

    @staticmethod
    def get_config_static() -> dict[str, Any]:
        return {
            "telehealth_booking_url": TELEHEALTH_URL or None,
            "default_urgency": DEFAULT_URGENCY,
        }

    def _config_payload(self) -> dict[str, Any]:
        return self.get_config_static()

    def _serialize(
        self, request: ConsultRequestModel, patient: PatientModel | None
    ) -> dict[str, Any]:
        return {
            "id": str(request.id),
            "encounter_id": str(request.encounter_id),
            "patient_id": str(request.patient_id),
            "patient_name": patient.full_name if patient else None,
            "urgency": request.urgency,
            "reason": request.reason,
            "status": request.status,
            "external_link_used": request.external_link_used,
            "created_at": request.created_at.isoformat(),
            "telehealth_booking_url": TELEHEALTH_URL or None,
        }
