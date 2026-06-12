"""Authentication and authorization business logic."""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from backend.auth import PasswordHasher, get_jwt_manager
from backend.config import get_settings
from backend.core.base_service import BaseService
from backend.dao.refresh_token_dao import RefreshTokenDao
from backend.dao.user_dao import UserDao
from backend.dto.auth_dto import (
    ForgotPasswordRequestDto,
    LoginRequestDto,
    RefreshRequestDto,
    RegisterRequestDto,
    ResetPasswordRequestDto,
    UpdatePasswordRequestDto,
)
from backend.enums.messages import Messages
from backend.enums.user_roles import UserRole
from backend.model.refresh_token_model import RefreshTokenModel
from backend.model.user_model import UserModel
from backend.service.audit_service import AuditService
from backend.utils.exceptions import (
    ConflictException,
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)


class AuthService(BaseService):
    """Handles user authentication workflows."""

    def __init__(self, session: Session) -> None:
        """Initialize DAOs and helpers."""
        super().__init__(session)
        self._user_dao = UserDao(session)
        self._token_dao = RefreshTokenDao(session)
        self._hasher = PasswordHasher()
        self._jwt = get_jwt_manager()
        self._audit = AuditService(session)

    def register(self, payload: RegisterRequestDto) -> dict[str, Any]:
        """Register a new user account."""
        existing = self._user_dao.find_by_email(payload.email)
        if existing is not None:
            raise ConflictException("Email already registered.")

        role = UserRole.VIEWER
        if payload.role is not None:
            role = UserRole(payload.role)

        user = UserModel(
            email=payload.email.lower(),
            password_hash=self._hasher.hash_password(payload.password),
            full_name=payload.full_name,
            role=role.value,
            is_verified=False,
        )
        self._user_dao.create(user)
        self._audit.log_action(user.id, "USER_REGISTER", "user", str(user.id))
        return {"user_id": str(user.id), "message": Messages.REGISTER_SUCCESS.value}

    def login(self, payload: LoginRequestDto) -> dict[str, Any]:
        """Authenticate user and issue tokens."""
        user = self._user_dao.find_by_email(payload.email)
        if user is None:
            raise UnauthorizedException(Messages.INVALID_CREDENTIALS.value)

        if not user.is_active:
            raise UnauthorizedException(Messages.UNAUTHORIZED.value)

        if not self._hasher.verify_password(payload.password, user.password_hash):
            raise UnauthorizedException(Messages.INVALID_CREDENTIALS.value)

        return self._issue_tokens(user)

    def refresh(self, payload: RefreshRequestDto) -> dict[str, Any]:
        """Refresh access token using refresh token."""
        try:
            decoded = self._jwt.decode_token(payload.refresh_token)
        except Exception as exc:
            raise UnauthorizedException(Messages.UNAUTHORIZED.value) from exc

        if decoded.get("type") != "refresh":
            raise UnauthorizedException(Messages.UNAUTHORIZED.value)

        jti = decoded.get("jti")
        token_row = self._token_dao.find_by_jti(jti)
        if token_row is None or token_row.is_revoked:
            raise UnauthorizedException(Messages.UNAUTHORIZED.value)

        if token_row.expires_at < datetime.now(UTC):
            raise UnauthorizedException(Messages.UNAUTHORIZED.value)

        user = self._user_dao.find_by_id(uuid.UUID(decoded["sub"]))
        if user is None:
            raise NotFoundException(Messages.USER_NOT_FOUND.value)

        access_token = self._jwt.create_access_token(
            str(user.id), user.email, UserRole(user.role)
        )
        return {
            "access_token": access_token,
            "message": Messages.TOKEN_REFRESHED.value,
        }

    def logout(self, user_id: uuid.UUID) -> dict[str, str]:
        """Revoke refresh tokens for user."""
        self._token_dao.revoke_by_user_id(user_id)
        self._audit.log_action(user_id, "USER_LOGOUT", "user", str(user_id))
        return {"message": Messages.LOGOUT_SUCCESS.value}

    def forgot_password(self, payload: ForgotPasswordRequestDto) -> dict[str, str]:
        """Initiate password reset flow."""
        user = self._user_dao.find_by_email(payload.email)
        if user is None:
            return {"message": Messages.PASSWORD_RESET_SENT.value}

        user.reset_token = secrets.token_urlsafe(32)
        user.reset_token_expires_at = datetime.now(UTC) + timedelta(hours=1)
        self._user_dao.update(user)
        self._audit.log_action(user.id, "PASSWORD_RESET_REQUEST", "user", str(user.id))
        return {"message": Messages.PASSWORD_RESET_SENT.value}

    def reset_password(self, payload: ResetPasswordRequestDto) -> dict[str, str]:
        """Reset password using token."""
        user = (
            self._session.query(UserModel)
            .filter(UserModel.reset_token == payload.token)
            .first()
        )
        if user is None:
            raise ValidationException("Invalid or expired reset token.")

        if (
            user.reset_token_expires_at is None
            or user.reset_token_expires_at < datetime.now(UTC)
        ):
            raise ValidationException("Invalid or expired reset token.")

        user.password_hash = self._hasher.hash_password(payload.new_password)
        user.reset_token = None
        user.reset_token_expires_at = None
        self._user_dao.update(user)
        self._token_dao.revoke_by_user_id(user.id)
        self._audit.log_action(user.id, "PASSWORD_RESET", "user", str(user.id))
        return {"message": Messages.PASSWORD_UPDATED.value}

    def update_password(
        self, user_id: uuid.UUID, payload: UpdatePasswordRequestDto
    ) -> dict[str, str]:
        """Update password for authenticated user."""
        user = self._user_dao.find_by_id(user_id)
        if user is None:
            raise NotFoundException(Messages.USER_NOT_FOUND.value)

        if not self._hasher.verify_password(
            payload.current_password, user.password_hash
        ):
            raise UnauthorizedException(Messages.INVALID_CREDENTIALS.value)

        user.password_hash = self._hasher.hash_password(payload.new_password)
        self._user_dao.update(user)
        self._audit.log_action(user_id, "PASSWORD_UPDATE", "user", str(user_id))
        return {"message": Messages.PASSWORD_UPDATED.value}

    def _issue_tokens(self, user: UserModel) -> dict[str, Any]:
        """Create access and refresh tokens."""
        access = self._jwt.create_access_token(
            str(user.id), user.email, UserRole(user.role)
        )
        refresh, jti = self._jwt.create_refresh_token(str(user.id))
        expires = datetime.now(UTC) + timedelta(
            days=get_settings().jwt_refresh_expires_days
        )
        token_row = RefreshTokenModel(
            user_id=user.id,
            jti=jti,
            expires_at=expires,
        )
        self._token_dao.create(token_row)
        self._audit.log_action(user.id, "USER_LOGIN", "user", str(user.id))
        return {
            "access_token": access,
            "refresh_token": refresh,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
            },
            "message": Messages.LOGIN_SUCCESS.value,
        }
