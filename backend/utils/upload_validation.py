"""Upload file-type and MIME validation helpers."""

from __future__ import annotations

from pathlib import Path

from backend.utils.exceptions import ValidationException

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "text/plain",
    "text/csv",
}

FILE_TYPE_MIME_MAP: dict[str, set[str]] = {
    "clinical_note": {"text/plain"},
    "lab_report": {"application/pdf", "text/csv", "image/png", "image/jpeg"},
    "xray": {"image/png", "image/jpeg"},
}

EXTENSION_MIME_MAP: dict[str, str] = {
    ".txt": "text/plain",
    ".csv": "text/csv",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}

FILE_TYPE_LABELS: dict[str, str] = {
    "clinical_note": "Clinical Note (TXT)",
    "lab_report": "Lab Report (PDF / CSV / Photo)",
    "xray": "Chest X-Ray (PNG / JPG)",
}


def normalize_mime_type(mime_type: str, file_name: str) -> str:
    """Resolve MIME type from extension when the browser sends a generic type."""
    if mime_type in ALLOWED_MIME_TYPES:
        return mime_type

    extension = Path(file_name).suffix.lower()
    return EXTENSION_MIME_MAP.get(extension, mime_type)


def validate_upload(file_name: str, mime_type: str, file_type: str) -> str:
    """Validate and normalize an upload. Returns the resolved MIME type."""
    resolved_mime = normalize_mime_type(mime_type, file_name)

    if resolved_mime not in ALLOWED_MIME_TYPES:
        raise ValidationException(
            "Unsupported file type. Allowed: PDF, PNG, JPG, TXT, CSV."
        )

    allowed_mimes = FILE_TYPE_MIME_MAP.get(file_type)
    if allowed_mimes and resolved_mime not in allowed_mimes:
        label = FILE_TYPE_LABELS.get(file_type, file_type)
        raise ValidationException(
            f"File does not match selected document type ({label}). "
            f"Choose the correct type or upload a compatible file."
        )

    return resolved_mime


def suggest_file_type(file_name: str, mime_type: str) -> str | None:
    """Suggest a document type from file name and MIME type."""
    resolved_mime = normalize_mime_type(mime_type, file_name)
    for file_type, mimes in FILE_TYPE_MIME_MAP.items():
        if resolved_mime in mimes:
            return file_type
    return None
