"""Explainability and evidence traceability service."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from backend.client.ml_model_loader import get_ml_model_loader
from backend.core.base_service import BaseService
from backend.enums.model_type import ModelType
from backend.logger import get_logger

logger = get_logger()


class ExplainabilityService(BaseService):
    """Builds explainability payloads for clinical review."""

    def __init__(self, session: Session) -> None:
        """Initialize dependencies."""
        super().__init__(session)
        self._model_loader = get_ml_model_loader()

    def build_explanation(
        self,
        encounter_id: uuid.UUID,
        findings: dict[str, Any],
        heatmap_path: str | None,
    ) -> dict[str, Any]:
        """Return explainability bundle for UI overlays."""
        model = self._model_loader.get_model(ModelType.EXPLAINABILITY)
        logger.info("Building explainability | encounter=%s", encounter_id)
        evidence_traces = []
        for finding_name, finding_data in findings.items():
            evidence_traces.append(
                {
                    "source": "imaging_ai",
                    "finding": finding_name,
                    "confidence": finding_data.get("probability", 0.0),
                    "detected": finding_data.get("detected", False),
                }
            )
        return {
            "encounter_id": str(encounter_id),
            "heatmap_path": heatmap_path,
            "evidence_traces": evidence_traces,
            "model_version": model.get("version", "1.0.0"),
        }
