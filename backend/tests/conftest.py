"""Pytest fixtures using OOP test factory."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

_TEST_DB = Path(__file__).resolve().parents[2] / "test_medvision_pytest.db"
if _TEST_DB.exists():
    _TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{_TEST_DB.as_posix()}"
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["FLASK_ENV"] = "development"
os.environ["IMAGING_ENABLED"] = "false"
os.environ["EMBEDDINGS_ENABLED"] = "false"

from backend.config.settings_manager import SettingsManager
from backend.db.database_manager import DatabaseManager

SettingsManager.reset_instance()
DatabaseManager.reset_instance()

import backend.model  # noqa: F401, E402
from backend.app import ApplicationBootstrap  # noqa: E402
from backend.db import Base, get_database_manager  # noqa: E402


class TestApplicationFactory:
    """Builds FastAPI apps for automated test runs."""

    def __init__(self) -> None:
        """Initialize bootstrap helper."""
        self._bootstrap = ApplicationBootstrap()

    def create(self) -> FastAPI:
        """Create a test-configured FastAPI app."""
        return self._bootstrap.create()


@pytest.fixture(scope="session")
def app() -> FastAPI:
    """Provide FastAPI application per test session."""
    application = TestApplicationFactory().create()
    tables = [
        table
        for table in Base.metadata.sorted_tables
        if table.name not in ("document_embeddings", "patient_embeddings")
    ]
    Base.metadata.create_all(bind=get_database_manager().engine, tables=tables)
    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Provide FastAPI test client."""
    return TestClient(app)
