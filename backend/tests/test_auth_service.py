"""Authentication service tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from backend.dto.auth_dto import RegisterRequestDto
from backend.service.auth_service import AuthService
from backend.utils.exceptions import ConflictException


class TestAuthService:
    """Auth service unit tests."""

    def test_register_raises_when_email_exists(self) -> None:
        """Register should fail for duplicate email."""
        session = MagicMock()
        service = AuthService(session)
        service._user_dao.find_by_email = MagicMock(return_value=MagicMock())
        payload = RegisterRequestDto(
            email="dup@test.com",
            password="Password1!",
            full_name="Test User",
        )
        with pytest.raises(ConflictException):
            service.register(payload)
