"""FastAPI exception handlers."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.enums.api_errors import ApiErrorCode
from backend.enums.http_status import HttpStatus
from backend.logger import get_logger
from backend.utils.exceptions import AppException
from backend.utils.response_builder import ResponseBuilder

logger = get_logger()


class ErrorHandlerRegistry:
    """Registers global exception handlers on the FastAPI app."""

    def __init__(self, app: FastAPI) -> None:
        """Attach handlers to the application."""
        self._app = app
        self._register()

    def _register(self) -> None:
        """Register exception handlers."""

        @self._app.exception_handler(AppException)
        async def handle_app_exception(
            _request: Request, exc: AppException
        ) -> JSONResponse:
            logger.warning("Handled application error: %s", exc.message)
            return ResponseBuilder.error(
                exc.message,
                exc.error_code.value,
                exc.status_code,
            )

        @self._app.exception_handler(Exception)
        async def handle_unexpected_exception(
            _request: Request, exc: Exception
        ) -> JSONResponse:
            logger.error("Unhandled exception: %s", exc, exc_info=True)
            return ResponseBuilder.error(
                "An unexpected error occurred.",
                ApiErrorCode.INTERNAL_ERROR.value,
                HttpStatus.INTERNAL_SERVER_ERROR,
            )
