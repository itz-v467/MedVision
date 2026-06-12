"""Request-scoped user context (replaces Flask g)."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from uuid import UUID

from backend.enums.user_roles import UserRole

_current_user: ContextVar[CurrentUser | None] = ContextVar("current_user", default=None)


@dataclass(frozen=True)
class CurrentUser:
    """Authenticated user attached to the current request."""

    user_id: UUID
    email: str
    role: UserRole


class RequestContext:
    """Get/set current user for the active request."""

    @staticmethod
    def set_user(user: CurrentUser) -> None:
        """Attach user to request context."""
        _current_user.set(user)

    @staticmethod
    def get_user() -> CurrentUser:
        """Return current user or raise if missing."""
        user = _current_user.get()
        if user is None:
            from backend.enums.messages import Messages
            from backend.utils.exceptions import UnauthorizedException

            raise UnauthorizedException(Messages.UNAUTHORIZED.value)
        return user

    @staticmethod
    def clear() -> None:
        """Clear context after request completes."""
        _current_user.set(None)
