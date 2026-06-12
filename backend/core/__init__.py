"""Core abstractions for OOP layering and singleton lifecycle."""

from backend.core.base_controller import BaseController
from backend.core.base_dao import BaseDao
from backend.core.base_service import BaseService
from backend.core.singleton import SingletonMixin

__all__ = [
    "BaseController",
    "BaseDao",
    "BaseService",
    "SingletonMixin",
]
