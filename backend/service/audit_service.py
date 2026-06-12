"""Audit logging service."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from backend.core.base_service import BaseService
from backend.dao.audit_log_dao import AuditLogDao
from backend.model.document_model import AuditLogModel


class AuditService(BaseService):
    """Records immutable audit events."""

    def __init__(self, session: Session) -> None:
        """Initialize with database session."""
        super().__init__(session)
        self._dao = AuditLogDao(session)

    def log_action(
        self,
        user_id: uuid.UUID | None,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Append an audit log entry."""
        entry = AuditLogModel(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_json=metadata or {},
        )
        self._dao.create(entry)
