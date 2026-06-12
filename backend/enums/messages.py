"""Application message constants."""

from enum import Enum


class Messages(str, Enum):
    """User-facing and internal message strings."""

    SUCCESS = "Operation completed successfully."
    LOGIN_SUCCESS = "Login successful."
    LOGOUT_SUCCESS = "Logout successful."
    REGISTER_SUCCESS = "Registration successful."
    PASSWORD_RESET_SENT = "Password reset instructions sent."
    PASSWORD_UPDATED = "Password updated successfully."
    TOKEN_REFRESHED = "Token refreshed successfully."
    UNAUTHORIZED = "Authentication required."
    FORBIDDEN = "You do not have permission for this action."
    USER_NOT_FOUND = "User not found."
    INVALID_CREDENTIALS = "Invalid email or password."
    VALIDATION_FAILED = "Validation failed."
    RESOURCE_NOT_FOUND = "Resource not found."
    FILE_UPLOAD_SUCCESS = "File uploaded successfully."
    AI_PROCESSING_STARTED = "AI processing started."
    AI_PROCESSING_COMPLETE = "AI processing completed."
    SUMMARY_PENDING_REVIEW = "Summary pending physician review."
