"""Upload file-type and MIME validation helpers."""

from __future__ import annotations

import re
from pathlib import Path

from backend.utils.exceptions import ValidationException
from backend.utils.image_content_classifier import classify_clinical_image

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

IMAGING_NAME_HINTS = re.compile(
    r"xray|x-?ray|chest|thorax|pneu|pna|lung|radiograph|cxr|scan",
    re.IGNORECASE,
)
LAB_NAME_HINTS = re.compile(
    r"lab|blood|cbc|panel|pathology|metabolic|hemoglobin|glucose",
    re.IGNORECASE,
)

IMAGE_MIME_TYPES = {"image/png", "image/jpeg"}


def normalize_mime_type(mime_type: str, file_name: str) -> str:
    """Resolve MIME type from extension when the browser sends a generic type."""
    if mime_type in ALLOWED_MIME_TYPES:
        return mime_type

    extension = Path(file_name).suffix.lower()
    return EXTENSION_MIME_MAP.get(extension, mime_type)


def suggest_file_type(file_name: str, mime_type: str) -> str | None:
    """Suggest a document type from file name and MIME type."""
    resolved_mime = normalize_mime_type(mime_type, file_name)
    name = file_name or ""

    if resolved_mime == "text/plain":
        return "clinical_note"
    if resolved_mime in {"application/pdf", "text/csv"}:
        return "lab_report"
    if resolved_mime in IMAGE_MIME_TYPES:
        if IMAGING_NAME_HINTS.search(name):
            return "xray"
        if LAB_NAME_HINTS.search(name):
            return "lab_report"
        # Unlabeled clinical images default to chest X-ray workflow.
        return "xray"
    return None


def normalize_file_type(file_type: str) -> str:
    """Normalize and require a supported document type."""
    normalized = (file_type or "").strip().lower()
    if normalized not in FILE_TYPE_MIME_MAP:
        raise ValidationException(
            "Document type is required. Select Clinical Note, Lab Report, or Chest X-Ray."
        )
    return normalized


def resolve_document_type(file_name: str, mime_type: str, selected_type: str) -> str:
    """Resolve final document type without silently changing user selection."""
    return selected_type


def validate_image_content(storage_path: str, selected_type: str) -> None:
    """Reject uploads whose image content conflicts with the selected section."""
    if selected_type not in {"xray", "lab_report"}:
        return

    detected = classify_clinical_image(storage_path)
    if detected == "unknown":
        return

    if selected_type == "xray" and detected == "lab_report":
        raise ValidationException(
            "This image looks like a lab/blood report photo, not a chest X-ray. "
            "Please select 'Lab Report' or upload a chest scan image."
        )

    if selected_type == "lab_report" and detected == "xray":
        raise ValidationException(
            "This image looks like a chest X-ray, not a lab report. "
            "Please select 'Chest X-Ray (PNG/JPG)' for proper analysis."
        )


def validate_type_selection(file_name: str, mime_type: str, selected_type: str) -> None:
    """Reject likely alternate-section uploads with a clear user-facing error."""
    resolved_mime = normalize_mime_type(mime_type, file_name)
    name = file_name or ""
    if resolved_mime not in IMAGE_MIME_TYPES:
        return

    if selected_type == "xray" and LAB_NAME_HINTS.search(name):
        raise ValidationException(
            "This looks like a lab/blood report image, not a chest X-ray. "
            "Please select 'Lab Report' or upload the chest scan."
        )

    if selected_type == "lab_report" and IMAGING_NAME_HINTS.search(name):
        raise ValidationException(
            "This looks like a chest X-ray image, not a lab report. "
            "Please select 'Chest X-Ray (PNG/JPG)' for proper analysis."
        )


def validate_upload(file_name: str, mime_type: str, file_type: str) -> str:
    """Validate and normalize an upload. Returns the resolved MIME type."""
    resolved_mime = normalize_mime_type(mime_type, file_name)

    if resolved_mime not in ALLOWED_MIME_TYPES:
        raise ValidationException(
            "Unsupported file type. Allowed: PDF, PNG, JPG, TXT, CSV."
        )

    allowed_mimes = FILE_TYPE_MIME_MAP[file_type]
    if resolved_mime not in allowed_mimes:
        label = FILE_TYPE_LABELS.get(file_type, file_type)
        raise ValidationException(
            f"File does not match selected document type ({label}). "
            f"Choose the correct type or upload a compatible file."
        )

    return resolved_mime
