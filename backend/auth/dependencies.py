"""FastAPI dependency injection for authentication and RBAC."""

from __future__ import annotations

from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.auth.jwt_manager import get_jwt_manager
from backend.core.request_context import CurrentUser, RequestContext
from backend.enums.messages import Messages
from backend.enums.user_roles import UserRole
from backend.utils.exceptions import ForbiddenException, UnauthorizedException

_bearer_scheme = HTTPBearer(auto_error=False)


class AuthDependencies:
    """FastAPI auth dependency providers."""

    def __init__(self) -> None:
        """Initialize JWT manager."""
        self._jwt_manager = get_jwt_manager()

    def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    ) -> CurrentUser:
        """Validate bearer token and return current user.

        Args:
            credentials: Authorization header bearer token.

        Returns:
            Authenticated user context.
        """
        if credentials is None or not credentials.credentials:
            raise UnauthorizedException(Messages.UNAUTHORIZED.value)

        token = credentials.credentials
        try:
            payload = self._jwt_manager.decode_token(token)
        except jwt.PyJWTError as exc:
            raise UnauthorizedException(Messages.UNAUTHORIZED.value) from exc

        if payload.get("type") != "access":
            raise UnauthorizedException(Messages.UNAUTHORIZED.value)

        user = CurrentUser(
            user_id=UUID(payload["sub"]),
            email=str(payload.get("email", "")),
            role=UserRole(payload.get("role")),
        )
        RequestContext.set_user(user)
        return user

    def require_roles(self, *roles: UserRole):
        """Build a dependency that enforces role membership.

        Args:
            roles: Allowed roles.

        Returns:
            FastAPI dependency callable.
        """
        allowed = roles

        def role_checker(
            user: CurrentUser = Depends(self.get_current_user),
        ) -> CurrentUser:
            if user.role not in allowed:
                raise ForbiddenException(Messages.FORBIDDEN.value)
            return user

        return role_checker


_auth_dependencies = AuthDependencies()
get_current_user = _auth_dependencies.get_current_user
