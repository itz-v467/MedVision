"""Audit log HTTP controller."""

from __future__ import annotations

from fastapi.responses import JSONResponse

from backend.core.base_controller import BaseController
from backend.dao.audit_log_dao import AuditLogDao
from backend.db import get_database_manager
from backend.utils.response_builder import ResponseBuilder


class AuditController(BaseController):
    """Handles audit log API responses."""

    def __init__(self) -> None:
        """Initialize controller."""
        super().__init__()

    def list_logs(self) -> JSONResponse:
        """Return recent audit logs."""
        with get_database_manager().session_scope() as session:
            logs = AuditLogDao(session).list_recent()
        payload = [
            {
                "id": str(log.id),
                "user_id": str(log.user_id) if log.user_id else None,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "metadata": log.metadata_json,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ]
        return ResponseBuilder.success({"logs": payload})
