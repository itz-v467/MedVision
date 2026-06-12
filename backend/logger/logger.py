"""Centralized logging configuration with singleton guard."""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler


class LoggerSetup:
    """Configures application loggers exactly once."""

    _configured: bool = False
    _logger: logging.Logger | None = None

    @classmethod
    def setup_logging(cls) -> logging.Logger:
        """Configure rotating file handlers and console output."""
        if cls._configured and cls._logger is not None:
            return cls._logger

        log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
        os.makedirs(log_dir, exist_ok=True)

        app_log_path = os.path.join(log_dir, "app.log")
        error_log_path = os.path.join(log_dir, "error.log")

        logger = logging.getLogger("medvision")
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        app_handler = RotatingFileHandler(
            app_log_path, maxBytes=5_000_000, backupCount=5
        )
        app_handler.setLevel(logging.INFO)
        app_handler.setFormatter(formatter)

        error_handler = RotatingFileHandler(
            error_log_path, maxBytes=5_000_000, backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        logger.addHandler(app_handler)
        logger.addHandler(error_handler)
        logger.addHandler(console_handler)

        cls._logger = logger
        cls._configured = True
        return logger


def get_logger() -> logging.Logger:
    """Return the configured application logger."""
    return LoggerSetup.setup_logging()
