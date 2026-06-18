"""Consult request data access."""

from __future__ import annotations

import uuid

from backend.core.base_dao import BaseDao
from backend.model.consult_model import ConsultRequestModel


class ConsultDao(BaseDao):
    """Database operations for consult requests."""

    def create(self, request: ConsultRequestModel) -> ConsultRequestModel:
        self._session.add(request)
        self._session.flush()
        return request

    def list_pending(self, limit: int = 50) -> list[ConsultRequestModel]:
        return (
            self._session.query(ConsultRequestModel)
            .filter(ConsultRequestModel.status == "pending")
            .order_by(ConsultRequestModel.created_at.desc())
            .limit(limit)
            .all()
        )

    def find_by_encounter(
        self, encounter_id: uuid.UUID
    ) -> ConsultRequestModel | None:
        return (
            self._session.query(ConsultRequestModel)
            .filter(ConsultRequestModel.encounter_id == encounter_id)
            .order_by(ConsultRequestModel.created_at.desc())
            .first()
        )

    def update(self, request: ConsultRequestModel) -> ConsultRequestModel:
        self._session.flush()
        return request
