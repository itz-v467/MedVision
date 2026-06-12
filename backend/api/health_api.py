"""Health check API surface."""

from __future__ import annotations

from backend.client.document_ocr_client import get_ocr_capabilities
from backend.utils.response_builder import ResponseBuilder


class HealthApi:
    """Provides service health endpoints."""

    def health(self):
        """Return service health status."""
        return ResponseBuilder.success(
            {"status": "healthy", "service": "medvision-api"}
        )

    def ocr_status(self):
        """Return OCR engine availability for operator diagnostics."""
        caps = get_ocr_capabilities()
        ready = caps.get("tesseract") or caps.get("easyocr") or caps.get("paddleocr")
        return ResponseBuilder.success(
            {
                "ocr_ready": ready,
                "engines": caps,
                "hint": (
                    "Install easyocr: pip install easyocr"
                    if not ready
                    else "At least one OCR engine is available."
                ),
            }
        )
