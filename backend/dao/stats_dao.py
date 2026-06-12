"""Dashboard statistics data access object."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func

from backend.core.base_dao import BaseDao
from backend.model.document_model import (
    AiMetricModel,
    AlertModel,
    InferenceResultModel,
)
from backend.model.encounter_model import EncounterModel
from backend.model.patient_model import PatientModel


class StatsDao(BaseDao):
    """Aggregated queries for dashboard analytics."""

    def get_dashboard_counts(self) -> dict[str, int]:
        """Return high-level dashboard counters."""
        patient_count = self._session.query(func.count(PatientModel.id)).scalar() or 0
        encounter_count = (
            self._session.query(func.count(EncounterModel.id)).scalar() or 0
        )
        alert_count = (
            self._session.query(func.count(AlertModel.id))
            .filter(AlertModel.is_acknowledged.is_(False))
            .scalar()
            or 0
        )
        inference_count = (
            self._session.query(func.count(InferenceResultModel.id)).scalar() or 0
        )
        return {
            "patients": int(patient_count),
            "encounters": int(encounter_count),
            "active_alerts": int(alert_count),
            "ai_analyses": int(inference_count),
        }

    def get_daily_predictions(self, days: int = 14) -> list[dict[str, Any]]:
        """Return daily prediction counts for line chart."""
        metrics = (
            self._session.query(AiMetricModel)
            .order_by(AiMetricModel.metric_date.desc())
            .limit(days)
            .all()
        )
        metrics.reverse()
        return [
            {"date": metric.metric_date, "count": metric.predictions_count}
            for metric in metrics
        ]

    def get_weekly_analysis_volume(self) -> list[dict[str, Any]]:
        """Return weekly analysis volume for bar chart."""
        week_ago = datetime.now(UTC) - timedelta(days=7)
        rows = (
            self._session.query(
                func.date(EncounterModel.created_at).label("day"),
                func.count(EncounterModel.id).label("volume"),
            )
            .filter(EncounterModel.created_at >= week_ago)
            .group_by(func.date(EncounterModel.created_at))
            .all()
        )
        return [{"day": str(row.day), "volume": int(row.volume)} for row in rows]

    def get_abnormality_distribution(self) -> dict[str, int]:
        """Return abnormality counts for doughnut chart."""
        latest_metric = (
            self._session.query(AiMetricModel)
            .order_by(AiMetricModel.metric_date.desc())
            .first()
        )
        if latest_metric is None:
            return {}
        return dict(latest_metric.abnormality_counts or {})

    def get_confidence_scatter(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return confidence scatter plot data."""
        results = (
            self._session.query(InferenceResultModel)
            .order_by(InferenceResultModel.created_at.desc())
            .limit(limit)
            .all()
        )
        scatter: list[dict[str, Any]] = []
        for index, result in enumerate(results):
            scatter.append(
                {
                    "x": index + 1,
                    "y": float(result.confidence_score),
                    "label": result.model_version,
                }
            )
        return scatter

    def get_recent_alerts(self, limit: int = 20) -> list[AlertModel]:
        """Return recent clinical alerts."""
        return (
            self._session.query(AlertModel)
            .order_by(AlertModel.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_ai_performance(self) -> dict[str, float]:
        """Return aggregate AI performance metrics."""
        avg_confidence = (
            self._session.query(
                func.avg(InferenceResultModel.confidence_score)
            ).scalar()
            or 0.0
        )
        avg_latency = (
            self._session.query(func.avg(AiMetricModel.avg_latency_ms)).scalar() or 0.0
        )
        return {
            "avg_confidence": float(avg_confidence),
            "avg_latency_ms": float(avg_latency),
        }
