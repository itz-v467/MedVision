"""Resolve uploaded clinical files to absolute paths inside storage root."""

from __future__ import annotations

from pathlib import Path

from backend.config import get_settings
from backend.logger import get_logger
from backend.utils.exceptions import NotFoundException

logger = get_logger()


def resolve_storage_file(file_path: str) -> Path:
    """Return an absolute, validated path inside the configured storage root."""
    storage_root = Path(get_settings().storage_path).resolve()
    path = Path(file_path)
    if not path.is_absolute():
        path = (storage_root / path).resolve()
    else:
        path = path.resolve()
    try:
        path.relative_to(storage_root)
    except ValueError as exc:
        raise NotFoundException("File path is invalid.") from exc
    if not path.is_file():
        raise NotFoundException(f"File not found on server: {path.name}")
    return path


def resolve_storage_file_optional(file_path: str) -> Path | None:
    """Best-effort storage path resolution without raising."""
    try:
        return resolve_storage_file(file_path)
    except Exception as exc:
        logger.warning("Storage path resolution failed for %s: %s", file_path, exc)
        return None
