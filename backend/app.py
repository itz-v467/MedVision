"""MedVision FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI

from backend.core.app_factory import AppFactory


class ApplicationBootstrap:
    """Bootstraps the ASGI application via AppFactory."""

    def __init__(self) -> None:
        """Initialize bootstrap."""
        self._factory = AppFactory()

    def create(self) -> FastAPI:
        """Build FastAPI application.

        Returns:
            Configured FastAPI app.
        """
        return self._factory.build()


def create_app() -> FastAPI:
    """ASGI entrypoint for Uvicorn and tests.

    Returns:
        Configured FastAPI application.
    """
    return ApplicationBootstrap().create()


if __name__ == "__main__":
    AppFactory().run_dev_server()
