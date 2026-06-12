"""Encounter data access object."""

from __future__ import annotations

import uuid

from backend.core.base_dao import BaseDao
from backend.enums.ai_status import AiProcessingStatus
from backend.model.encounter_model import EncounterModel
from backend.model.patient_model import PatientModel


class EncounterDao(BaseDao):
    """Database operations for encounters."""

    def find_by_id(self, encounter_id: uuid.UUID) -> EncounterModel | None:
        """Return an encounter by ID."""
        return (
            self._session.query(EncounterModel)
            .filter(EncounterModel.id == encounter_id)
            .first()
        )

    def list_recent(self, limit: int = 50) -> list[EncounterModel]:
        """Return recent encounters for triage queue."""
        return (
            self._session.query(EncounterModel)
            .filter(EncounterModel.status != AiProcessingStatus.DELETED.value)
            .order_by(EncounterModel.created_at.desc())
            .limit(limit)
            .all()
        )

    def list_recent_with_patient(
        self, limit: int = 50
    ) -> list[tuple[EncounterModel, PatientModel | None]]:
        """Return recent encounters joined with patient details."""
        return (
            self._session.query(EncounterModel, PatientModel)
            .outerjoin(PatientModel, EncounterModel.patient_id == PatientModel.id)
            .filter(EncounterModel.status != AiProcessingStatus.DELETED.value)
            .order_by(EncounterModel.created_at.desc())
            .limit(limit)
            .all()
        )

    def list_by_patient(
        self, patient_id: uuid.UUID, limit: int = 50
    ) -> list[EncounterModel]:
        """Return encounters for a patient ordered by recency."""
        return (
            self._session.query(EncounterModel)
            .filter(EncounterModel.patient_id == patient_id)
            .order_by(EncounterModel.created_at.desc())
            .limit(limit)
            .all()
        )

    def create(self, encounter: EncounterModel) -> EncounterModel:
        """Persist a new encounter."""
        self._session.add(encounter)
        self._session.flush()
        return encounter

    def update(self, encounter: EncounterModel) -> EncounterModel:
        """Persist encounter updates."""
        self._session.add(encounter)
        self._session.flush()
        return encounter
