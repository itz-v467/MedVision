"""Clinical alert engine service."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from backend.core.base_service import BaseService
from backend.dao.document_dao import DocumentDao
from backend.enums.alert_priority import AlertPriority
from backend.logger import get_logger
from backend.model.document_model import AlertModel
from backend.utils.exceptions import NotFoundException

logger = get_logger()


class AlertEngineService(BaseService):
    """Creates and manages clinical alerts."""

    def __init__(self, session: Session) -> None:
        """Initialize dependencies."""
        super().__init__(session)
        self._document_dao = DocumentDao(session)

    def evaluate_findings(
        self, encounter_id: uuid.UUID, findings: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate alerts from AI findings."""
        alerts_created: list[dict[str, Any]] = []
        for finding_name, finding_data in findings.items():
            probability = float(finding_data.get("probability", 0.0))
            detected = bool(finding_data.get("detected", False))
            if not detected or probability < 0.7:
                continue
            priority = AlertPriority.HIGH
            if probability >= 0.85:
                priority = AlertPriority.CRITICAL
            alert = AlertModel(
                encounter_id=encounter_id,
                title=f"Critical finding: {finding_name}",
                message=f"{finding_name} detected with probability {probability:.2f}",
                priority=priority.value,
            )
            self._session.add(alert)
            self._session.flush()
            alerts_created.append(
                {
                    "id": str(alert.id),
                    "title": alert.title,
                    "priority": alert.priority,
                    "message": alert.message,
                }
            )
        logger.info("Alerts created | count=%s", len(alerts_created))
        return alerts_created

    def evaluate_lab_abnormalities(
        self,
        encounter_id: uuid.UUID,
        biomarkers: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Create alerts for abnormal lab values."""
        alerts_created: list[dict[str, Any]] = []
        for marker in biomarkers:
            if not marker.get("is_abnormal") and str(marker.get("flag", "")).upper() in {
                "",
                "NORMAL",
                "N",
            }:
                continue
            name = marker.get("display_name") or marker.get("name") or "Lab test"
            value = marker.get("display_value") or marker.get("value") or ""
            alert = AlertModel(
                encounter_id=encounter_id,
                title=f"Abnormal lab: {name}",
                message=f"{name} {value} is outside the usual reference range.",
                priority=AlertPriority.MEDIUM.value,
            )
            self._session.add(alert)
            self._session.flush()
            alerts_created.append(
                {
                    "id": str(alert.id),
                    "title": alert.title,
                    "priority": alert.priority,
                    "message": alert.message,
                }
            )
        return alerts_created

    def acknowledge_alert(self, alert_id: uuid.UUID) -> AlertModel:
        """Mark an alert as acknowledged."""
        alert = self._document_dao.find_alert_by_id(alert_id)
        if alert is None:
            raise NotFoundException("Alert not found.")
        alert.is_acknowledged = True
        self._session.add(alert)
        self._session.flush()
        logger.info("Alert acknowledged | id=%s", alert_id)
        return alert
