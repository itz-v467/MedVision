"""Dashboard statistics service."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.core.base_service import BaseService
from backend.dao.stats_dao import StatsDao


class StatsService(BaseService):
    """Aggregates live dashboard metrics."""

    def __init__(self, session: Session) -> None:
        """Initialize DAO."""
        super().__init__(session)
        self._dao = StatsDao(session)

    def get_dashboard_stats(self) -> dict[str, Any]:
        """Return dashboard overview metrics."""
        return self._dao.get_dashboard_counts()

    def get_chart_data(self) -> dict[str, Any]:
        """Return all chart datasets."""
        return {
            "daily_predictions": self._dao.get_daily_predictions(),
            "weekly_analysis_volume": self._dao.get_weekly_analysis_volume(),
            "abnormality_distribution": self._dao.get_abnormality_distribution(),
            "model_confidence_scatter": self._dao.get_confidence_scatter(),
        }

    def get_alerts(self) -> list[dict[str, Any]]:
        """Return alert feed for dashboard."""
        alerts = self._dao.get_recent_alerts()
        return [
            {
                "id": str(alert.id),
                "encounter_id": str(alert.encounter_id),
                "title": alert.title,
                "message": alert.message,
                "priority": alert.priority,
                "is_acknowledged": alert.is_acknowledged,
                "created_at": alert.created_at.isoformat(),
            }
            for alert in alerts
        ]

    def get_patient_stats(self) -> dict[str, int]:
        """Return patient-related counters."""
        counts = self._dao.get_dashboard_counts()
        return {"total_patients": counts["patients"]}

    def get_ai_performance(self) -> dict[str, float]:
        """Return AI performance KPIs."""
        return self._dao.get_ai_performance()
