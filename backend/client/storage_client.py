"""Local and cloud object storage client."""

from __future__ import annotations

import os
import uuid
from typing import BinaryIO

from backend.config import get_settings
from backend.logger import get_logger

logger = get_logger()


class StorageClient:
    """Persists uploaded clinical files."""

    def __init__(self) -> None:
        """Ensure storage directory exists."""
        settings = get_settings()
        self._base_path = settings.storage_path
        os.makedirs(self._base_path, exist_ok=True)

    def save_file(self, file_stream: BinaryIO, file_name: str) -> str:
        """Save a file and return its storage path."""
        safe_name = f"{uuid.uuid4()}_{file_name}"
        destination = os.path.join(self._base_path, safe_name)
        with open(destination, "wb") as output_file:
            output_file.write(file_stream.read())
        logger.info("Stored file at %s", destination)
        return destination
