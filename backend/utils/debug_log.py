"""Structured debug logging for clinical pipeline troubleshooting."""

from __future__ import annotations

import logging
from typing import Any

from backend.logger import get_logger

_pipeline_logger = logging.getLogger("medvision.pipeline")


def pipeline_debug(step: str, message: str, **context: Any) -> None:
    """Write a DEBUG pipeline event with optional structured context."""
    if context:
        details = " | ".join(f"{key}={value}" for key, value in context.items())
        _pipeline_logger.debug("[%s] %s | %s", step, message, details)
    else:
        _pipeline_logger.debug("[%s] %s", step, message)


def pipeline_info(step: str, message: str, **context: Any) -> None:
    """Write an INFO pipeline event."""
    logger = get_logger()
    if context:
        details = " | ".join(f"{key}={value}" for key, value in context.items())
        logger.info("[%s] %s | %s", step, message, details)
    else:
        logger.info("[%s] %s", step, message)


def pipeline_warning(step: str, message: str, **context: Any) -> None:
    """Write a WARNING pipeline event."""
    logger = get_logger()
    if context:
        details = " | ".join(f"{key}={value}" for key, value in context.items())
        logger.warning("[%s] %s | %s", step, message, details)
    else:
        logger.warning("[%s] %s", step, message)
