"""Refresh token data access object."""

from __future__ import annotations

import uuid

from backend.core.base_dao import BaseDao
from backend.model.refresh_token_model import RefreshTokenModel


class RefreshTokenDao(BaseDao):
    """Database operations for refresh tokens."""

    def create(self, token: RefreshTokenModel) -> RefreshTokenModel:
        """Persist a refresh token."""
        self._session.add(token)
        self._session.flush()
        return token

    def find_by_jti(self, jti: str) -> RefreshTokenModel | None:
        """Return a token by JTI."""
        return (
            self._session.query(RefreshTokenModel)
            .filter(RefreshTokenModel.jti == jti)
            .first()
        )

    def revoke_by_user_id(self, user_id: uuid.UUID) -> None:
        """Revoke all active tokens for a user."""
        tokens = (
            self._session.query(RefreshTokenModel)
            .filter(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.is_revoked.is_(False),
            )
            .all()
        )
        for token in tokens:
            token.is_revoked = True
        self._session.flush()

    def update(self, token: RefreshTokenModel) -> RefreshTokenModel:
        """Persist token changes."""
        self._session.add(token)
        self._session.flush()
        return token
