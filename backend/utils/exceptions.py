"""Application exception hierarchy."""

from __future__ import annotations

from backend.enums.api_errors import ApiErrorCode
from backend.enums.http_status import HttpStatus


class AppException(Exception):
    """Base application exception with HTTP mapping."""

    def __init__(
        self,
        message: str,
        error_code: ApiErrorCode,
        status_code: HttpStatus,
    ) -> None:
        """Initialize exception metadata."""
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code


class ValidationException(AppException):
    """Raised when input validation fails."""

    def __init__(self, message: str) -> None:
        """Initialize validation error."""
        super().__init__(
            message,
            ApiErrorCode.VALIDATION_ERROR,
            HttpStatus.BAD_REQUEST,
        )


class UnauthorizedException(AppException):
    """Raised when authentication fails."""

    def __init__(self, message: str) -> None:
        """Initialize unauthorized error."""
        super().__init__(
            message,
            ApiErrorCode.UNAUTHORIZED,
            HttpStatus.UNAUTHORIZED,
        )


class ForbiddenException(AppException):
    """Raised when authorization fails."""

    def __init__(self, message: str) -> None:
        """Initialize forbidden error."""
        super().__init__(
            message,
            ApiErrorCode.FORBIDDEN,
            HttpStatus.FORBIDDEN,
        )


class NotFoundException(AppException):
    """Raised when a resource is missing."""

    def __init__(self, message: str) -> None:
        """Initialize not found error."""
        super().__init__(
            message,
            ApiErrorCode.NOT_FOUND,
            HttpStatus.NOT_FOUND,
        )


class ConflictException(AppException):
    """Raised on resource conflicts."""

    def __init__(self, message: str) -> None:
        """Initialize conflict error."""
        super().__init__(
            message,
            ApiErrorCode.CONFLICT,
            HttpStatus.CONFLICT,
        )


class AiProcessingException(AppException):
    """Raised when AI pipeline fails."""

    def __init__(self, message: str) -> None:
        """Initialize AI processing error."""
        super().__init__(
            message,
            ApiErrorCode.AI_PROCESSING_FAILED,
            HttpStatus.UNPROCESSABLE_ENTITY,
        )
