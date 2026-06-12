"""Application factory tests."""

from __future__ import annotations

from fastapi import FastAPI

from backend.core.app_factory import AppFactory
from backend.tests.base_test_case import BaseTestCase


class TestApplicationFactory(BaseTestCase):
    """Validates OOP application bootstrap."""

    def test_factory_returns_fastapi_app(self) -> None:
        """AppFactory should produce a FastAPI instance."""
        app = AppFactory().build()
        self.assertIsInstance(app, FastAPI)
