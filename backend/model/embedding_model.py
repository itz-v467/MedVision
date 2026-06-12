"""Clinical document embeddings for RAG (PostgreSQL + pgvector)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.db import Base

try:
    from pgvector.sqlalchemy import Vector

    _VECTOR_TYPE = Vector(384)
except ImportError:
    _VECTOR_TYPE = None


class DocumentEmbeddingModel(Base):
    """Chunked clinical text with vector embedding for similarity search."""

    __tablename__ = "document_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    encounter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), index=True, nullable=False
    )
    source_type: Mapped[str] = mapped_column(String(50), index=True)
    source_id: Mapped[str] = mapped_column(String(100), index=True)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    if _VECTOR_TYPE is not None:
        embedding: Mapped[list[float]] = mapped_column(_VECTOR_TYPE, nullable=False)
