"""Base DAO with shared session handling."""

from __future__ import annotations

from sqlalchemy.orm import Session


class BaseDao:
    """Parent class for all data-access objects."""

    def __init__(self, session: Session) -> None:
        """Attach the active SQLAlchemy session.

        Args:
            session: Unit-of-work session for the current request.
        """
        self._session = session

    @property
    def session(self) -> Session:
        """Return the bound SQLAlchemy session."""
        return self._session
