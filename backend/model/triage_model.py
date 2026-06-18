"""Symptom triage session and message ORM entities."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.db import Base


class TriageSessionModel(Base):
    """Encounter-linked symptom triage conversation."""

    __tablename__ = "triage_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    encounter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("encounters.id"), index=True
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), index=True
    )
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)
    risk_level: Mapped[str] = mapped_column(String(20), default="low")
    recommended_disposition: Mapped[str | None] = mapped_column(Text, nullable=True)
    assessment: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    finalized_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class TriageMessageModel(Base):
    """Single turn in a triage session."""

    __tablename__ = "triage_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("triage_sessions.id"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))
    message_text: Mapped[str] = mapped_column(Text)
    structured_symptoms: Mapped[dict] = mapped_column(JSON, default=dict)
    safety_flags: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
