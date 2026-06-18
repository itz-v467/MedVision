"""Resolve uploaded clinical files to absolute paths inside storage root."""

from __future__ import annotations

from pathlib import Path

from backend.config import get_settings
from backend.logger import get_logger
from backend.utils.exceptions import NotFoundException

logger = get_logger()


def _path_candidates(raw: Path, storage_root: Path) -> list[Path]:
    """Build likely absolute paths for a stored upload reference."""
    candidates: list[Path] = []
    if raw.is_absolute():
        candidates.append(raw.resolve())
    else:
        candidates.append((Path.cwd() / raw).resolve())
        candidates.append((storage_root / raw.name).resolve())
        # Handle values already relative to storage root (e.g. ./data/uploads/file.pdf)
        if raw.parent != Path("."):
            candidates.append((storage_root / raw.name).resolve())
    deduped: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key not in seen:
            seen.add(key)
            deduped.append(candidate)
    return deduped


def resolve_storage_file(file_path: str) -> Path:
    """Return an absolute, validated path inside the configured storage root."""
    storage_root = Path(get_settings().storage_path).resolve()
    raw = Path(file_path)

    for path in _path_candidates(raw, storage_root):
        if not path.is_file():
            continue
        try:
            path.relative_to(storage_root)
            return path
        except ValueError:
            # Legacy relative paths may resolve outside strict join logic but still
            # point at the configured uploads directory on disk.
            if path.parent.resolve() == storage_root:
                return path

    raise NotFoundException(f"File not found on server: {raw.name}")


def resolve_storage_file_optional(file_path: str) -> Path | None:
    """Best-effort storage path resolution without raising."""
    try:
        return resolve_storage_file(file_path)
    except Exception as exc:
        logger.warning("Storage path resolution failed for %s: %s", file_path, exc)
        return None
