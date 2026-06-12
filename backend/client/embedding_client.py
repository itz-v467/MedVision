"""Embedding generation for RAG retrieval."""

from __future__ import annotations

import hashlib
import importlib.util
import os
from typing import Any

from backend.config import get_settings
from backend.core.singleton import SingletonMixin
from backend.logger import get_logger

logger = get_logger()


class EmbeddingClient(SingletonMixin):
    """Generates dense vectors for pgvector similarity search."""

    def __init__(self) -> None:
        """Initialize embedding backend."""
        if self._initialized:
            return
        self._settings = get_settings()
        self._model: Any = None
        self._available = self._probe_availability()
        self._initialized = True
        if self._available:
            logger.info(
                "EmbeddingClient ready | model=%s", self._settings.embedding_model_name
            )
        else:
            logger.warning("sentence-transformers unavailable; using hash fallback")

    @property
    def is_available(self) -> bool:
        """Return True when real embedding model is loaded."""
        return self._available

    def _probe_availability(self) -> bool:
        """Check optional dependency availability."""
        if os.getenv("EMBEDDINGS_ENABLED", "true").lower() == "false":
            return False
        return importlib.util.find_spec("sentence_transformers") is not None

    def _ensure_model(self) -> None:
        """Lazy-load sentence-transformers model."""
        if self._model is not None:
            return
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(self._settings.embedding_model_name)

    def embed(self, text_content: str) -> list[float]:
        """Return embedding vector for input text."""
        if not text_content.strip():
            return self._hash_embedding("empty")

        if self._available:
            try:
                self._ensure_model()
                vector = self._model.encode(text_content, normalize_embeddings=True)
                embedding = [float(value) for value in vector.tolist()]
                return self._fit_dimensions(embedding)
            except Exception as exc:
                logger.warning("Embedding inference failed: %s", exc)

        return self._hash_embedding(text_content)

    def _fit_dimensions(self, embedding: list[float]) -> list[float]:
        """Pad or truncate vector to configured pgvector dimensions."""
        dimensions = self._settings.embedding_dimensions
        if len(embedding) == dimensions:
            return embedding
        if len(embedding) > dimensions:
            return embedding[:dimensions]
        return embedding + [0.0] * (dimensions - len(embedding))

    def _hash_embedding(self, text_content: str) -> list[float]:
        """Build deterministic placeholder vector."""
        dimensions = self._settings.embedding_dimensions
        digest = hashlib.sha256(text_content.encode("utf-8")).digest()
        values: list[float] = []
        while len(values) < dimensions:
            for byte in digest:
                values.append((byte / 255.0) * 2.0 - 1.0)
                if len(values) >= dimensions:
                    break
            digest = hashlib.sha256(digest).digest()
        return values[:dimensions]


def get_embedding_client() -> EmbeddingClient:
    """Return embedding client singleton."""
    return EmbeddingClient()
