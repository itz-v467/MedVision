"""Central registry for FastAPI routers."""

from __future__ import annotations

from fastapi import FastAPI

from backend.routes import audit_routes, auth_routes, clinical_routes, stats_routes


class RouteRegistry:
    """Registers all domain routers on the FastAPI application."""

    def __init__(self) -> None:
        """Initialize router list."""
        self._routers = [
            auth_routes.router,
            stats_routes.router,
            clinical_routes.router,
            audit_routes.router,
        ]

    def register_all(self, app: FastAPI) -> None:
        """Include every domain router.

        Args:
            app: FastAPI application instance.
        """
        for router in self._routers:
            app.include_router(router)
