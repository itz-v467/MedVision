"""Singleton application settings manager."""

from __future__ import annotations

import os

from dotenv import load_dotenv

from backend.core.singleton import SingletonMixin


class SettingsManager(SingletonMixin):
    """Loads and exposes environment-backed configuration."""

    def __init__(self) -> None:
        """Load environment variables once."""
        if self._initialized:
            return
        load_dotenv()
        self.flask_env: str = os.getenv("FLASK_ENV", "development")
        self.secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key")
        self.database_url: str = os.getenv(
            "DATABASE_URL",
            "postgresql://medvision:medvision@localhost:5432/medvision",
        )
        self.redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
        self.jwt_access_expires_minutes: int = int(
            os.getenv("JWT_ACCESS_EXPIRES_MINUTES", "15")
        )
        self.jwt_refresh_expires_days: int = int(
            os.getenv("JWT_REFRESH_EXPIRES_DAYS", "7")
        )
        self.ml_inference_base_url: str = os.getenv(
            "ML_INFERENCE_BASE_URL", "http://localhost:8001"
        )
        self.storage_path: str = os.getenv("STORAGE_PATH", "./data/uploads")
        self.embedding_dimensions: int = int(os.getenv("EMBEDDING_DIMENSIONS", "384"))
        self.vector_search_limit: int = int(os.getenv("VECTOR_SEARCH_LIMIT", "5"))
        self.imaging_model_name: str = os.getenv(
            "IMAGING_MODEL_NAME", "densenet121-res224-all"
        )
        self.imaging_weights_dir: str = os.getenv(
            "IMAGING_WEIGHTS_DIR", "./models/imaging"
        )
        self.imaging_device: str = os.getenv("IMAGING_DEVICE", "cpu")
        self.imaging_detection_threshold: float = float(
            os.getenv("IMAGING_DETECTION_THRESHOLD", "0.5")
        )
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        self.openai_llm_model: str = os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini")
        self.openai_embedding_model: str = os.getenv(
            "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
        )
        self.openai_lab_extraction_enabled: bool = os.getenv(
            "OPENAI_LAB_EXTRACTION_ENABLED", "true"
        ).lower() in ("1", "true", "yes")
        self.embedding_model_name: str = os.getenv(
            "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
        )
        cors_raw = os.getenv("CORS_ORIGINS", "http://localhost:5173")
        self.cors_origins: list[str] = [
            origin.strip() for origin in cors_raw.split(",") if origin.strip()
        ]
        self._initialized = True

    @property
    def is_production(self) -> bool:
        """Return True when running in production."""
        return self.flask_env == "production"

    @property
    def use_pgvector(self) -> bool:
        """Return True when PostgreSQL pgvector should be used."""
        return self.database_url.startswith("postgresql")

    @property
    def openai_enabled(self) -> bool:
        """Return True when OpenAI API key is configured."""
        return bool(self.openai_api_key.strip())


def get_settings() -> SettingsManager:
    """Return the settings singleton."""
    return SettingsManager()
