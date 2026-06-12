"""RAG indexing and retrieval using PostgreSQL pgvector."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from backend.client.embedding_client import get_embedding_client
from backend.client.vector_store_client import get_vector_store_client
from backend.config import get_settings
from backend.core.base_service import BaseService
from backend.logger import get_logger

logger = get_logger()


class RagIndexingService(BaseService):
    """Indexes clinical artifacts and retrieves grounded context."""

    def __init__(self, session: Session) -> None:
        """Initialize RAG service."""
        super().__init__(session)
        self._vector_store = get_vector_store_client()
        self._embedding = get_embedding_client()
        self._settings = get_settings()

    def index_text(
        self,
        encounter_id: uuid.UUID,
        source_type: str,
        source_id: str,
        text_content: str,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        """Index clinical text for later RAG retrieval."""
        if not self._vector_store.is_enabled:
            return None

        self._vector_store.ensure_extension(self._session)
        embedding = self._embedding.embed(text_content)
        return self._vector_store.upsert_embedding(
            self._session,
            encounter_id,
            source_type,
            source_id,
            text_content,
            embedding,
            metadata,
        )

    def retrieve_context(
        self, encounter_id: uuid.UUID, query_text: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Retrieve similar chunks for summary grounding."""
        if not self._vector_store.is_enabled:
            return []

        query_embedding = self._embedding.embed(query_text)
        return self._vector_store.similarity_search(
            self._session,
            encounter_id,
            query_embedding,
            limit or self._settings.vector_search_limit,
        )
