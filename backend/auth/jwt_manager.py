"""Singleton JWT creation and validation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt

from backend.config import get_settings
from backend.core.singleton import SingletonMixin
from backend.enums.user_roles import UserRole
from backend.logger import get_logger

logger = get_logger()


class JwtManager(SingletonMixin):
    """Handles access and refresh token lifecycle."""

    _algorithm: str = "HS256"

    def __init__(self) -> None:
        """Load signing configuration once."""
        if self._initialized:
            return
        self._settings = get_settings()
        self._initialized = True
        logger.info("JWT manager initialized")

    def create_access_token(self, user_id: str, email: str, role: UserRole) -> str:
        """Create a short-lived access token."""
        now = datetime.now(UTC)
        expires = now + timedelta(minutes=self._settings.jwt_access_expires_minutes)
        payload = {
            "sub": user_id,
            "email": email,
            "role": role.value,
            "type": "access",
            "iat": now,
            "exp": expires,
        }
        return jwt.encode(
            payload, self._settings.jwt_secret_key, algorithm=self._algorithm
        )

    def create_refresh_token(self, user_id: str) -> tuple[str, str]:
        """Create a refresh token and return token plus jti."""
        now = datetime.now(UTC)
        expires = now + timedelta(days=self._settings.jwt_refresh_expires_days)
        jti = str(uuid4())
        payload = {
            "sub": user_id,
            "type": "refresh",
            "jti": jti,
            "iat": now,
            "exp": expires,
        }
        token = jwt.encode(
            payload, self._settings.jwt_secret_key, algorithm=self._algorithm
        )
        return token, jti

    def decode_token(self, token: str) -> dict[str, Any]:
        """Decode and validate a JWT."""
        return jwt.decode(
            token,
            self._settings.jwt_secret_key,
            algorithms=[self._algorithm],
        )


def get_jwt_manager() -> JwtManager:
    """Return the JWT singleton."""
    return JwtManager()
