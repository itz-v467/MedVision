"""Audit log API routes (FastAPI)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.auth.dependencies import AuthDependencies
from backend.controller.audit_controller import AuditController
from backend.core.request_context import CurrentUser
from backend.enums.user_roles import UserRole

router = APIRouter(prefix="/api/audit", tags=["Audit"])
_controller = AuditController()
_auth = AuthDependencies()


@router.get("/logs")
def logs(
    _admin: CurrentUser = Depends(_auth.require_roles(UserRole.ADMIN)),
):
    """Return immutable audit log entries (admin only)."""
    return _controller.list_logs()
