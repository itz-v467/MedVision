"""User role constants."""

from enum import Enum


class UserRole(str, Enum):
    """RBAC role identifiers."""

    ADMIN = "ADMIN"
    RADIOLOGIST = "RADIOLOGIST"
    PHYSICIAN = "PHYSICIAN"
    ANALYST = "ANALYST"
    TECHNICIAN = "TECHNICIAN"
    VIEWER = "VIEWER"
