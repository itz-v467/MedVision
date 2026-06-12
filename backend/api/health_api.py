"""Health check API surface."""

from __future__ import annotations

from backend.utils.response_builder import ResponseBuilder


class HealthApi:
    """Provides service health endpoints."""

    def health(self):
        """Return service health status."""
        return ResponseBuilder.success(
            {"status": "healthy", "service": "medvision-api"}
        )
