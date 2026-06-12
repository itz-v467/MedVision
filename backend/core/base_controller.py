"""Base controller for HTTP request/response mapping."""

from __future__ import annotations


class BaseController:
    """Parent class for HTTP controllers (no business logic)."""

    def __init__(self) -> None:
        """Initialize controller dependencies."""
        self._initialized = True
