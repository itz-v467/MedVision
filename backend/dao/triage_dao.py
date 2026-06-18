"""Database access for symptom triage sessions."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from backend.core.base_dao import BaseDao
from backend.model.triage_model import TriageMessageModel, TriageSessionModel


class TriageDao(BaseDao):
    """CRUD for triage sessions and messages."""

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def create_session(self, row: TriageSessionModel) -> TriageSessionModel:
        self._session.add(row)
        self._session.flush()
        return row

    def find_session_by_encounter(self, encounter_id: uuid.UUID) -> TriageSessionModel | None:
        return (
            self._session.query(TriageSessionModel)
            .filter(TriageSessionModel.encounter_id == encounter_id)
            .order_by(TriageSessionModel.created_at.desc())
            .first()
        )

    def find_session_by_id(self, session_id: uuid.UUID) -> TriageSessionModel | None:
        return (
            self._session.query(TriageSessionModel)
            .filter(TriageSessionModel.id == session_id)
            .first()
        )

    def save_message(self, message: TriageMessageModel) -> TriageMessageModel:
        self._session.add(message)
        self._session.flush()
        return message

    def list_messages(self, session_id: uuid.UUID) -> list[TriageMessageModel]:
        return (
            self._session.query(TriageMessageModel)
            .filter(TriageMessageModel.session_id == session_id)
            .order_by(TriageMessageModel.created_at.asc())
            .all()
        )

    def update_session(self, row: TriageSessionModel) -> TriageSessionModel:
        self._session.add(row)
        self._session.flush()
        return row
