"""Reusable singleton pattern for infrastructure components."""

from __future__ import annotations

from typing import Any, ClassVar, TypeVar

T = TypeVar("T", bound="SingletonMixin")


class SingletonMixin:
    """Ensure only one instance exists per concrete class."""

    _instances: ClassVar[dict[type, Any]] = {}

    def __new__(cls: type[T], *args: Any, **kwargs: Any) -> T:
        """Return the existing instance or create a new one."""
        if cls not in cls._instances:
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instances[cls] = instance
        return cls._instances[cls]

    @classmethod
    def reset_instance(cls) -> None:
        """Clear singleton instance (used in tests)."""
        cls._instances.pop(cls, None)
