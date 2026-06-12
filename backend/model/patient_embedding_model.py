"""Patient profile embeddings for semantic search (pgvector)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.db import Base

try:
    from pgvector.sqlalchemy import Vector

    _VECTOR_TYPE = Vector(384)
except ImportError:
    _VECTOR_TYPE = None


class PatientEmbeddingModel(Base):
    """Searchable patient profile vector — one row per patient."""

    __tablename__ = "patient_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id"),
        unique=True,
        index=True,
        nullable=False,
    )
    search_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    if _VECTOR_TYPE is not None:
        embedding: Mapped[list[float]] = mapped_column(_VECTOR_TYPE, nullable=False)
