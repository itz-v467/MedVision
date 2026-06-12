"""Authentication API routes (FastAPI)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.auth.dependencies import get_current_user
from backend.controller.auth_controller import AuthController
from backend.core.request_context import CurrentUser
from backend.dto.auth_dto import (
    ForgotPasswordRequestDto,
    LoginRequestDto,
    RefreshRequestDto,
    RegisterRequestDto,
    ResetPasswordRequestDto,
    UpdatePasswordRequestDto,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
_controller = AuthController()


@router.post("/register", status_code=201)
def register(payload: RegisterRequestDto):
    """Register a new user account."""
    return _controller.register(payload)


@router.post("/login")
def login(payload: LoginRequestDto):
    """Authenticate and receive tokens."""
    return _controller.login(payload)


@router.post("/refresh")
def refresh(payload: RefreshRequestDto):
    """Refresh access token."""
    return _controller.refresh(payload)


@router.post("/logout")
def logout(current_user: CurrentUser = Depends(get_current_user)):
    """Revoke refresh tokens."""
    return _controller.logout(current_user)


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequestDto):
    """Initiate password reset."""
    return _controller.forgot_password(payload)


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequestDto):
    """Complete password reset."""
    return _controller.reset_password(payload)


@router.put("/update-password")
def update_password(
    payload: UpdatePasswordRequestDto,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update password for authenticated user."""
    return _controller.update_password(current_user, payload)
