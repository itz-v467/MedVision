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
