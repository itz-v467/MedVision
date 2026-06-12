"""Singleton Redis client for caching and token storage."""

from __future__ import annotations

import redis

from backend.config import get_settings
from backend.core.singleton import SingletonMixin
from backend.logger import get_logger

logger = get_logger()


class RedisClient(SingletonMixin):
    """Wraps Redis connection with singleton lifecycle."""

    def __init__(self) -> None:
        """Connect to Redis once."""
        if self._initialized:
            return
        settings = get_settings()
        self._client = redis.from_url(settings.redis_url, decode_responses=True)
        self._initialized = True
        logger.info("Redis client initialized")

    @property
    def client(self) -> redis.Redis:
        """Return the underlying Redis client."""
        return self._client

    def set_value(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        """Store a string value with optional TTL."""
        if ttl_seconds is not None:
            self._client.setex(key, ttl_seconds, value)
            return
        self._client.set(key, value)

    def get_value(self, key: str) -> str | None:
        """Retrieve a string value."""
        return self._client.get(key)

    def delete_key(self, key: str) -> None:
        """Remove a key."""
        self._client.delete(key)


def get_redis_client() -> RedisClient:
    """Return the Redis singleton."""
    return RedisClient()
