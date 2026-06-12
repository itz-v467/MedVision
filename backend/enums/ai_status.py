"""AI processing status constants."""

from enum import Enum


class AiProcessingStatus(str, Enum):
    """Pipeline job states."""

    PENDING = "PENDING"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    FINALIZED = "FINALIZED"
