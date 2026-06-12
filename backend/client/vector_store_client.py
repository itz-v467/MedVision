"""PostgreSQL pgvector client for RAG retrieval."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.core.singleton import SingletonMixin
from backend.logger import get_logger
from backend.model.embedding_model import DocumentEmbeddingModel

logger = get_logger()


class VectorStoreClient(SingletonMixin):
    """Indexes and searches clinical embeddings via pgvector."""

    def __init__(self) -> None:
        """Initialize vector store client."""
        if self._initialized:
            return
        self._settings = get_settings()
        self._initialized = True
        logger.info("Vector store client initialized")

    @property
    def is_enabled(self) -> bool:
        """Return True when PostgreSQL pgvector is available."""
        return self._settings.use_pgvector

    def ensure_extension(self, session: Session) -> None:
        """Enable pgvector extension on PostgreSQL."""
        if not self.is_enabled:
            return
        session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        session.flush()
        logger.info("pgvector extension ensured")

    def upsert_embedding(
        self,
        session: Session,
        encounter_id: uuid.UUID,
        source_type: str,
        source_id: str,
        chunk_text: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store a document chunk and its embedding.

        Args:
            session: Active SQLAlchemy session.
            encounter_id: Related clinical encounter.
            source_type: Origin module (ocr, nlp, imaging, summary).
            source_id: Source record identifier.
            chunk_text: Text used for RAG grounding.
            embedding: Dense vector (must match EMBEDDING_DIMENSIONS).
            metadata: Optional trace metadata.

        Returns:
            Stored embedding row id as string.
        """
        if not self.is_enabled:
            logger.warning("Vector store disabled; skipping upsert")
            return ""

        row = DocumentEmbeddingModel(
            encounter_id=encounter_id,
            source_type=source_type,
            source_id=source_id,
            chunk_text=chunk_text,
            embedding=embedding,
            metadata_json=metadata or {},
        )
        session.add(row)
        session.flush()
        return str(row.id)

    def similarity_search(
        self,
        session: Session,
        encounter_id: uuid.UUID,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Retrieve top similar chunks for an encounter.

        Args:
            session: Active SQLAlchemy session.
            encounter_id: Encounter scope for retrieval.
            query_embedding: Query vector.
            limit: Maximum results.

        Returns:
            Ranked chunks with similarity scores.
        """
        if not self.is_enabled:
            return []

        dimensions = self._settings.embedding_dimensions
        vector_literal = "[" + ",".join(str(value) for value in query_embedding) + "]"
        sql = text(
            """
            SELECT id, chunk_text, source_type, source_id, metadata_json,
                   1 - (embedding <=> CAST(:query_vec AS vector)) AS similarity
            FROM document_embeddings
            WHERE encounter_id = CAST(:encounter_id AS uuid)
            ORDER BY embedding <=> CAST(:query_vec AS vector)
            LIMIT :result_limit
            """
        )
        rows = session.execute(
            sql,
            {
                "query_vec": vector_literal,
                "encounter_id": str(encounter_id),
                "result_limit": limit,
            },
        ).fetchall()

        results: list[dict[str, Any]] = []
        for row in rows:
            results.append(
                {
                    "id": str(row.id),
                    "chunk_text": row.chunk_text,
                    "source_type": row.source_type,
                    "source_id": row.source_id,
                    "metadata": row.metadata_json,
                    "similarity": float(row.similarity),
                    "dimensions": dimensions,
                }
            )
        return results


def get_vector_store_client() -> VectorStoreClient:
    """Return vector store singleton."""
    return VectorStoreClient()
