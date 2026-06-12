"""Dashboard statistics HTTP controller."""

from __future__ import annotations

from fastapi.responses import JSONResponse

from backend.core.base_controller import BaseController
from backend.db import get_database_manager
from backend.service.stats_service import StatsService
from backend.utils.response_builder import ResponseBuilder


class StatsController(BaseController):
    """Handles stats API responses."""

    def __init__(self) -> None:
        """Initialize controller."""
        super().__init__()

    def dashboard(self) -> JSONResponse:
        """Return dashboard overview stats."""
        with get_database_manager().session_scope() as session:
            data = StatsService(session).get_dashboard_stats()
        return ResponseBuilder.success(data)

    def charts(self) -> JSONResponse:
        """Return chart datasets."""
        with get_database_manager().session_scope() as session:
            data = StatsService(session).get_chart_data()
        return ResponseBuilder.success(data)

    def alerts(self) -> JSONResponse:
        """Return alert statistics."""
        with get_database_manager().session_scope() as session:
            data = StatsService(session).get_alerts()
        return ResponseBuilder.success({"alerts": data})

    def patients(self) -> JSONResponse:
        """Return patient statistics."""
        with get_database_manager().session_scope() as session:
            data = StatsService(session).get_patient_stats()
        return ResponseBuilder.success(data)

    def ai_performance(self) -> JSONResponse:
        """Return AI performance metrics."""
        with get_database_manager().session_scope() as session:
            data = StatsService(session).get_ai_performance()
        return ResponseBuilder.success(data)
