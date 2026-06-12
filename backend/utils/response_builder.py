"""HTTP response helpers for FastAPI."""

from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse

from backend.enums.http_status import HttpStatus


class ResponseBuilder:
    """Build consistent JSON API responses."""

    @staticmethod
    def success(
        data: dict[str, Any] | None = None,
        message: str = "",
        status: HttpStatus = HttpStatus.OK,
    ) -> JSONResponse:
        """Return a success JSON response."""
        payload: dict[str, Any] = {"success": True, "message": message}
        if data is not None:
            payload["data"] = data
        return JSONResponse(content=payload, status_code=int(status))

    @staticmethod
    def error(
        message: str,
        error_code: str,
        status: HttpStatus,
        details: dict[str, Any] | None = None,
    ) -> JSONResponse:
        """Return an error JSON response."""
        payload: dict[str, Any] = {
            "success": False,
            "message": message,
            "error_code": error_code,
        }
        if details is not None:
            payload["details"] = details
        return JSONResponse(content=payload, status_code=int(status))
