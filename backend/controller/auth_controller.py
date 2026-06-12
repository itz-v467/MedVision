"""Authentication HTTP controller."""

from __future__ import annotations

from fastapi.responses import JSONResponse

from backend.core.base_controller import BaseController
from backend.core.request_context import CurrentUser
from backend.db import get_database_manager
from backend.dto.auth_dto import (
    ForgotPasswordRequestDto,
    LoginRequestDto,
    RefreshRequestDto,
    RegisterRequestDto,
    ResetPasswordRequestDto,
    UpdatePasswordRequestDto,
)
from backend.enums.http_status import HttpStatus
from backend.service.auth_service import AuthService
from backend.utils.response_builder import ResponseBuilder


class AuthController(BaseController):
    """Handles auth HTTP request/response mapping."""

    def __init__(self) -> None:
        """Initialize controller."""
        super().__init__()

    def register(self, payload: RegisterRequestDto) -> JSONResponse:
        """Register a new user."""
        with get_database_manager().session_scope() as session:
            result = AuthService(session).register(payload)
        return ResponseBuilder.success(result, status=HttpStatus.CREATED)

    def login(self, payload: LoginRequestDto) -> JSONResponse:
        """Authenticate user."""
        with get_database_manager().session_scope() as session:
            result = AuthService(session).login(payload)
        return ResponseBuilder.success(result)

    def refresh(self, payload: RefreshRequestDto) -> JSONResponse:
        """Refresh access token."""
        with get_database_manager().session_scope() as session:
            result = AuthService(session).refresh(payload)
        return ResponseBuilder.success(result)

    def logout(self, current_user: CurrentUser) -> JSONResponse:
        """Logout current user."""
        with get_database_manager().session_scope() as session:
            result = AuthService(session).logout(current_user.user_id)
        return ResponseBuilder.success(result)

    def forgot_password(self, payload: ForgotPasswordRequestDto) -> JSONResponse:
        """Request password reset."""
        with get_database_manager().session_scope() as session:
            result = AuthService(session).forgot_password(payload)
        return ResponseBuilder.success(result)

    def reset_password(self, payload: ResetPasswordRequestDto) -> JSONResponse:
        """Reset password with token."""
        with get_database_manager().session_scope() as session:
            result = AuthService(session).reset_password(payload)
        return ResponseBuilder.success(result)

    def update_password(
        self, current_user: CurrentUser, payload: UpdatePasswordRequestDto
    ) -> JSONResponse:
        """Update password for logged-in user."""
        with get_database_manager().session_scope() as session:
            result = AuthService(session).update_password(current_user.user_id, payload)
        return ResponseBuilder.success(result)
