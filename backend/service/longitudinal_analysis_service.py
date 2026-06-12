"""Longitudinal patient intelligence service."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from backend.core.base_service import BaseService
from backend.dao.document_dao import DocumentDao
from backend.dao.encounter_dao import EncounterDao
from backend.logger import get_logger

logger = get_logger()


class LongitudinalAnalysisService(BaseService):
    """Analyzes patient history across encounters."""

    def __init__(self, session: Session) -> None:
        """Initialize dependencies."""
        super().__init__(session)
        self._encounter_dao = EncounterDao(session)
        self._document_dao = DocumentDao(session)

    def build_timeline(self, patient_id: uuid.UUID) -> dict[str, Any]:
        """Return longitudinal timeline from stored encounters."""
        logger.info("Building timeline | patient=%s", patient_id)
        encounters = self._encounter_dao.list_by_patient(patient_id)
        timeline: list[dict[str, Any]] = []

        for encounter in reversed(encounters):
            documents = self._document_dao.find_documents_by_encounter(encounter.id)
            file_types = sorted({doc.file_type for doc in documents})
            label = ", ".join(file_types) if file_types else "Clinical encounter"
            _, inference = self._document_dao.find_imaging_by_encounter(encounter.id)
            if inference and inference.findings:
                detected = [
                    name
                    for name, data in inference.findings.items()
                    if isinstance(data, dict) and data.get("detected")
                ]
                if detected:
                    label = f"Imaging: {', '.join(detected)}"

            timeline.append(
                {
                    "encounter_id": str(encounter.id),
                    "date": encounter.created_at.date().isoformat(),
                    "event": label,
                    "status": encounter.status,
                }
            )

        return {
            "patient_id": str(patient_id),
            "encounter_count": len(encounters),
            "timeline": timeline,
        }
