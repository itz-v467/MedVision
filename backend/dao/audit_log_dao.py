"""Audit log data access object."""

from __future__ import annotations

from backend.core.base_dao import BaseDao
from backend.model.document_model import AuditLogModel


class AuditLogDao(BaseDao):
    """Append-only audit log persistence."""

    def create(self, log_entry: AuditLogModel) -> AuditLogModel:
        """Persist an audit log entry."""
        self._session.add(log_entry)
        self._session.flush()
        return log_entry

    def list_recent(self, limit: int = 100) -> list[AuditLogModel]:
        """Return recent audit entries."""
        return (
            self._session.query(AuditLogModel)
            .order_by(AuditLogModel.created_at.desc())
            .limit(limit)
            .all()
        )
