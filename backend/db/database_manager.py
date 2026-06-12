"""Singleton database connection and session management."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from backend.config import get_settings
from backend.core.singleton import SingletonMixin
from backend.logger import get_logger

logger = get_logger()
Base = declarative_base()


class DatabaseManager(SingletonMixin):
    """Provides pooled SQLAlchemy engine and session factory."""

    def __init__(self) -> None:
        """Initialize engine and session maker once."""
        if self._initialized:
            return
        settings = get_settings()
        engine_kwargs: dict = {"pool_pre_ping": True}
        if settings.database_url.startswith("postgresql"):
            engine_kwargs["pool_size"] = 10
            engine_kwargs["max_overflow"] = 20
        self._engine = create_engine(settings.database_url, **engine_kwargs)
        self._session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
        self._initialized = True
        logger.info("Database manager initialized")

    @property
    def engine(self):
        """Return the SQLAlchemy engine."""
        return self._engine

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Yield a transactional session with automatic rollback on error."""
        session: Session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as exc:
            session.rollback()
            logger.error("Database transaction failed: %s", exc)
            raise
        finally:
            session.close()

    def get_session(self) -> Session:
        """Return a new session (caller must close)."""
        return self._session_factory()


def get_database_manager() -> DatabaseManager:
    """Return the database singleton."""
    return DatabaseManager()
