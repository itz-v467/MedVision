"""Legacy decorator facade — prefer backend.auth.dependencies for FastAPI."""

from __future__ import annotations

from backend.auth.dependencies import AuthDependencies, get_current_user
from backend.enums.user_roles import UserRole

_auth = AuthDependencies()


class AuthDecorators:
    """Backward-compatible names; use FastAPI Depends in new code."""

    get_current_user = staticmethod(get_current_user)

    @staticmethod
    def roles_required(*roles: UserRole):
        """Return FastAPI role dependency."""
        return _auth.require_roles(*roles)


login_required = get_current_user
roles_required = AuthDecorators.roles_required
