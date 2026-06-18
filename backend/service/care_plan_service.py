"""Care plan generation and physician approval."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from backend.core.base_service import BaseService
from backend.dao.document_dao import DocumentDao
from backend.logger import get_logger
from backend.service.audit_service import AuditService
from backend.utils.exceptions import NotFoundException

logger = get_logger()

CARE_PLAN_DISCLAIMER = (
    "Suggestions only — not a prescription until your doctor approves this care plan."
)


class CarePlanService(BaseService):
    """Manage AI-generated care plans pending physician approval."""

    def __init__(self, session: Session) -> None:
        super().__init__(session)
        self._dao = DocumentDao(session)
        self._audit = AuditService(session)

    def extract_from_synthesis(self, synthesis: dict[str, Any]) -> dict[str, Any]:
        """Normalize care_plan block from clinical synthesis."""
        care = synthesis.get("care_plan") or {}
        if not isinstance(care, dict):
            care = {}
        care.setdefault("status", "pending_physician_approval")
        care.setdefault("medications", [])
        care.setdefault("otc_options", [])
        care.setdefault("recovery", {})
        care.setdefault("monitoring", [])
        care["disclaimer"] = CARE_PLAN_DISCLAIMER
        return care

    def get_care_plan(self, encounter_id: uuid.UUID) -> dict[str, Any]:
        """Return care plan from latest summary evidence."""
        summary = self._dao.find_summary_by_encounter(encounter_id)
        if summary is None:
            raise NotFoundException("No clinical summary found for this encounter.")
        evidence = summary.evidence_sources if isinstance(summary.evidence_sources, dict) else {}
        care = evidence.get("care_plan") or {}
        synthesis = evidence.get("clinical_synthesis") or {}
        if not care and synthesis.get("care_plan"):
            care = self.extract_from_synthesis(synthesis)
        return {
            "encounter_id": str(encounter_id),
            "summary_id": str(summary.id),
            "care_plan": care,
            "consult_recommendation": synthesis.get("consult_recommendation") or {},
            "status": care.get("status", "pending_physician_approval"),
        }

    def approve_care_plan(
        self, encounter_id: uuid.UUID, physician_id: uuid.UUID
    ) -> dict[str, Any]:
        """Mark care plan as physician-approved on the latest summary."""
        summary = self._dao.find_summary_by_encounter(encounter_id)
        if summary is None:
            raise NotFoundException("No clinical summary found for this encounter.")

        evidence = dict(summary.evidence_sources or {})
        care = evidence.get("care_plan") or {}
        if not care:
            synthesis = evidence.get("clinical_synthesis") or {}
            care = self.extract_from_synthesis(synthesis)
        care["status"] = "approved"
        care["approved_by"] = str(physician_id)
        evidence["care_plan"] = care
        summary.evidence_sources = evidence
        self._dao.save_summary(summary)

        self._audit.log_action(
            physician_id,
            "CARE_PLAN_APPROVED",
            "clinical_summary",
            str(summary.id),
            {"encounter_id": str(encounter_id)},
        )
        logger.info("Care plan approved | encounter=%s", encounter_id)
        return {
            "encounter_id": str(encounter_id),
            "summary_id": str(summary.id),
            "care_plan": care,
            "message": "Care plan approved by physician.",
        }
