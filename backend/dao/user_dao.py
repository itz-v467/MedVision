"""User data access object."""

from __future__ import annotations

import uuid

from backend.core.base_dao import BaseDao
from backend.model.user_model import UserModel


class UserDao(BaseDao):
    """Database operations for users."""

    def find_by_email(self, email: str) -> UserModel | None:
        """Return a user by email or None."""
        return (
            self._session.query(UserModel)
            .filter(UserModel.email == email.lower())
            .first()
        )

    def find_by_id(self, user_id: uuid.UUID) -> UserModel | None:
        """Return a user by primary key or None."""
        return self._session.query(UserModel).filter(UserModel.id == user_id).first()

    def create(self, user: UserModel) -> UserModel:
        """Persist a new user."""
        self._session.add(user)
        self._session.flush()
        return user

    def update(self, user: UserModel) -> UserModel:
        """Persist user changes."""
        self._session.add(user)
        self._session.flush()
        return user
