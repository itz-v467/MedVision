"""Singleton ML model loader for inference pipelines."""

from __future__ import annotations

from typing import Any

from backend.client.embedding_client import get_embedding_client
from backend.client.xray_inference_client import get_xray_inference_client
from backend.config import get_settings
from backend.core.singleton import SingletonMixin
from backend.enums.model_type import ModelType
from backend.logger import get_logger

logger = get_logger()


class MlModelLoader(SingletonMixin):
    """Lazy-loads and caches ML model handles by type."""

    def __init__(self) -> None:
        """Initialize model registry cache."""
        if self._initialized:
            return
        self._models: dict[ModelType, Any] = {}
        self._settings = get_settings()
        self._initialized = True
        logger.info("ML model loader initialized")

    def get_model(self, model_type: ModelType) -> Any:
        """Return a loaded model for the given type."""
        if model_type in self._models:
            return self._models[model_type]

        model_handle = self._load_model(model_type)
        self._models[model_type] = model_handle
        logger.info("Loaded model type=%s", model_type.value)
        return model_handle

    def _load_model(self, model_type: ModelType) -> dict[str, Any]:
        """Load model weights or remote endpoint configuration."""
        if model_type == ModelType.IMAGING:
            xray = get_xray_inference_client()
            return {
                "type": model_type.value,
                "version": (
                    self._settings.imaging_model_name
                    if xray.is_available
                    else "fallback-1.0.0"
                ),
                "ready": True,
                "client": xray,
            }
        if model_type == ModelType.RAG:
            embedding = get_embedding_client()
            return {
                "type": model_type.value,
                "version": (
                    self._settings.embedding_model_name
                    if embedding.is_available
                    else "hash-fallback-1.0.0"
                ),
                "ready": True,
            }
        return {
            "type": model_type.value,
            "version": "1.0.0",
            "ready": True,
        }


def get_ml_model_loader() -> MlModelLoader:
    """Return the ML model loader singleton."""
    return MlModelLoader()
