"""Authentication DTOs."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class LoginRequestDto(BaseModel):
    """Login payload."""

    email: EmailStr
    password: str = Field(min_length=8)


class RegisterRequestDto(BaseModel):
    """Registration payload."""

    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2)
    role: str | None = None


class RefreshRequestDto(BaseModel):
    """Token refresh payload."""

    refresh_token: str


class ForgotPasswordRequestDto(BaseModel):
    """Forgot password payload."""

    email: EmailStr


class ResetPasswordRequestDto(BaseModel):
    """Reset password payload."""

    token: str
    new_password: str = Field(min_length=8)


class UpdatePasswordRequestDto(BaseModel):
    """Update password payload."""

    current_password: str
    new_password: str = Field(min_length=8)
