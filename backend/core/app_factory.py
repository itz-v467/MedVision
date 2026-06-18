"""FastAPI application factory."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.health_api import HealthApi
from backend.config import get_settings
from backend.db import Base, get_database_manager
from backend.logger import get_logger
from backend.middleware import ErrorHandlerRegistry, RequestMiddleware
from backend.routes.route_registry import RouteRegistry

logger = get_logger()


class AppFactory:
    """Builds and configures the MedVision FastAPI application."""

    def __init__(self) -> None:
        """Initialize factory state."""
        self._app: FastAPI | None = None

    def build(self) -> FastAPI:
        """Create a fully configured FastAPI application.

        Returns:
            Configured FastAPI app instance.
        """
        if self._app is not None:
            return self._app

        settings = get_settings()
        self._app = FastAPI(
            title="MedVision Clinical AI API",
            description="Enterprise multimodal clinical decision support platform",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
        )
        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        RequestMiddleware(self._app)
        ErrorHandlerRegistry(self._app)
        RouteRegistry().register_all(self._app)
        self._register_health()
        self._run_migrations()
        self._ensure_database()
        return self._app

    def _register_health(self) -> None:
        """Register health probe endpoint."""
        assert self._app is not None
        health_api = HealthApi()

        @self._app.get("/health", tags=["Health"])
        def health():
            """Service health check."""
            return health_api.health()

        @self._app.get("/health/ocr", tags=["Health"])
        def ocr_health():
            """OCR engine availability check."""
            return health_api.ocr_status()

        @self._app.get("/health/imaging", tags=["Health"])
        def imaging_health():
            """Chest X-ray AI stack availability check."""
            return health_api.imaging_status()

    def _run_migrations(self) -> None:
        """Apply schema updates for existing PostgreSQL databases."""
        if not get_settings().database_url.startswith("postgresql"):
            return

        from sqlalchemy import inspect, text

        engine = get_database_manager().engine
        inspector = inspect(engine)
        if "encounters" not in inspector.get_table_names():
            return

        encounter_cols = {col["name"] for col in inspector.get_columns("encounters")}
        imaging_cols = {col["name"] for col in inspector.get_columns("imaging_studies")}

        statements: list[str] = []
        if "case_type" not in encounter_cols:
            statements.extend(
                [
                    "ALTER TABLE encounters ADD COLUMN IF NOT EXISTS case_type VARCHAR(50)",
                    "CREATE INDEX IF NOT EXISTS ix_encounters_case_type ON encounters (case_type)",
                ]
            )
        if "source_document_id" not in imaging_cols:
            statements.extend(
                [
                    "ALTER TABLE imaging_studies "
                    "ADD COLUMN IF NOT EXISTS source_document_id UUID",
                    "CREATE INDEX IF NOT EXISTS ix_imaging_studies_source_document_id "
                    "ON imaging_studies (source_document_id)",
                    """
                    DO $$
                    BEGIN
                        ALTER TABLE imaging_studies
                        ADD CONSTRAINT fk_imaging_studies_source_document_id
                        FOREIGN KEY (source_document_id) REFERENCES documents(id);
                    EXCEPTION
                        WHEN duplicate_object THEN NULL;
                    END $$;
                    """,
                ]
            )

        table_names = set(inspector.get_table_names())
        if "triage_sessions" not in table_names:
            statements.extend(
                [
                    """
                    CREATE TABLE IF NOT EXISTS triage_sessions (
                        id UUID PRIMARY KEY,
                        encounter_id UUID NOT NULL REFERENCES encounters(id),
                        patient_id UUID NOT NULL REFERENCES patients(id),
                        status VARCHAR(30) NOT NULL DEFAULT 'active',
                        risk_level VARCHAR(20) NOT NULL DEFAULT 'low',
                        recommended_disposition TEXT,
                        assessment JSONB NOT NULL DEFAULT '{}',
                        created_by UUID REFERENCES users(id),
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        finalized_at TIMESTAMPTZ
                    )
                    """,
                    "CREATE INDEX IF NOT EXISTS ix_triage_sessions_encounter_id "
                    "ON triage_sessions (encounter_id)",
                    "CREATE INDEX IF NOT EXISTS ix_triage_sessions_patient_id "
                    "ON triage_sessions (patient_id)",
                    "CREATE INDEX IF NOT EXISTS ix_triage_sessions_status "
                    "ON triage_sessions (status)",
                    """
                    CREATE TABLE IF NOT EXISTS triage_messages (
                        id UUID PRIMARY KEY,
                        session_id UUID NOT NULL REFERENCES triage_sessions(id),
                        role VARCHAR(20) NOT NULL,
                        message_text TEXT NOT NULL,
                        structured_symptoms JSONB NOT NULL DEFAULT '{}',
                        safety_flags JSONB NOT NULL DEFAULT '{}',
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """,
                    "CREATE INDEX IF NOT EXISTS ix_triage_messages_session_id "
                    "ON triage_messages (session_id)",
                ]
            )

        if "consult_requests" not in table_names:
            statements.extend(
                [
                    """
                    CREATE TABLE IF NOT EXISTS consult_requests (
                        id UUID PRIMARY KEY,
                        encounter_id UUID NOT NULL REFERENCES encounters(id),
                        patient_id UUID NOT NULL REFERENCES patients(id),
                        requested_by_user_id UUID NOT NULL REFERENCES users(id),
                        urgency VARCHAR(30) NOT NULL DEFAULT 'within_24h',
                        reason TEXT,
                        status VARCHAR(30) NOT NULL DEFAULT 'pending',
                        external_link_used BOOLEAN NOT NULL DEFAULT FALSE,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """,
                    "CREATE INDEX IF NOT EXISTS ix_consult_requests_encounter_id "
                    "ON consult_requests (encounter_id)",
                    "CREATE INDEX IF NOT EXISTS ix_consult_requests_status "
                    "ON consult_requests (status)",
                ]
            )

        if not statements:
            return

        with engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement))
        logger.info("Applied unified-case schema patch (%d statement(s))", len(statements))

        stamp_revision = (
            "005_consult_requests"
            if "consult_requests" not in table_names
            else "004_triage_tables"
            if "triage_sessions" not in table_names
            else "003_unified_case_columns"
        )
        try:
            from pathlib import Path

            from alembic import command
            from alembic.config import Config

            ini_path = Path(__file__).resolve().parents[1] / "migrations" / "alembic.ini"
            alembic_cfg = Config(str(ini_path))
            command.stamp(alembic_cfg, stamp_revision)
        except Exception as exc:
            logger.warning("Could not stamp Alembic revision: %s", exc)

    def _ensure_database(self) -> None:
        """Create tables for non-production environments."""
        if get_settings().is_production:
            return
        tables = self._tables_for_bind(get_database_manager().engine)
        with get_database_manager().engine.begin() as connection:
            Base.metadata.create_all(bind=connection, tables=tables)
        logger.info("Database tables ensured")

    def _tables_for_bind(self, engine) -> list:
        """Return ORM tables appropriate for the database dialect."""
        if get_settings().use_pgvector:
            return list(Base.metadata.sorted_tables)
        return [
            table
            for table in Base.metadata.sorted_tables
            if table.name not in ("document_embeddings", "patient_embeddings")
        ]

    def run_dev_server(self) -> None:
        """Run development server with uvicorn."""
        import uvicorn

        port = int(os.getenv("PORT", "5000"))
        uvicorn.run(
            "backend.app:create_app",
            factory=True,
            host="0.0.0.0",
            port=port,
            reload=not get_settings().is_production,
        )
