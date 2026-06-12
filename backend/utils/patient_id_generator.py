"""MedVision patient number (external ID) generation."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from backend.model.patient_model import PatientModel

AUTO_ID_SENTINELS = frozenset({"", "P-UNKNOWN", "AUTO", "UNKNOWN", "NEW"})


def should_auto_generate_patient_id(external_id: str | None) -> bool:
    """Return True when the system should assign a new MedVision patient number."""
    if external_id is None:
        return True
    normalized = external_id.strip().upper()
    return normalized in AUTO_ID_SENTINELS


def generate_patient_external_id(session: Session) -> str:
    """Generate a unique, human-readable ID: MV-YYYYMMDD-0001."""
    day = datetime.now(UTC).strftime("%Y%m%d")
    prefix = f"MV-{day}-"

    existing = (
        session.query(PatientModel.external_id)
        .filter(PatientModel.external_id.like(f"{prefix}%"))
        .all()
    )

    max_seq = 0
    for (external_id,) in existing:
        suffix = external_id.rsplit("-", 1)[-1]
        try:
            max_seq = max(max_seq, int(suffix))
        except ValueError:
            continue

    return f"{prefix}{max_seq + 1:04d}"


def resolve_patient_external_id(session: Session, provided: str | None) -> str:
    """Use provided hospital ID or assign a new MedVision patient number."""
    if should_auto_generate_patient_id(provided):
        return generate_patient_external_id(session)
    return provided.strip()
