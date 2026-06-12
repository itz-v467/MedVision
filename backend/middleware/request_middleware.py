"""Request timing and tracing middleware for FastAPI."""

from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from backend.core.request_context import RequestContext
from backend.logger import get_logger

logger = get_logger()


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Adds request ID and latency logging."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request with tracing metadata."""
        request_id = str(uuid.uuid4())
        start = time.perf_counter()
        logger.debug(
            "Request started | id=%s | method=%s | path=%s",
            request_id,
            request.method,
            request.url.path,
        )
        try:
            response = await call_next(request)
        finally:
            RequestContext.clear()
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "Request completed | id=%s | status=%s | duration_ms=%.2f",
            request_id,
            response.status_code,
            duration_ms,
        )
        response.headers["X-Request-Id"] = request_id
        return response


class RequestMiddleware:
    """Registers request middleware on FastAPI."""

    def __init__(self, app: FastAPI) -> None:
        """Add middleware stack."""
        app.add_middleware(RequestTracingMiddleware)
