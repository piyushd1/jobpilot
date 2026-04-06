"""Redis client wrapper with basic get/set/expire helpers."""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis

from src.config.settings import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class RedisCache:
    """Async Redis client with JSON serialization helpers."""

    def __init__(self) -> None:
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        """Initialize the Redis connection."""
        self._client = redis.from_url(settings.redis_url, decode_responses=True)
        logger.info("Connected to Redis", url=settings.redis_url)

    async def close(self) -> None:
        """Close the Redis connection."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            raise RuntimeError("RedisCache not connected. Call connect() first.")
        return self._client

    async def get(self, key: str) -> str | None:
        """Get a string value."""
        return await self.client.get(key)

    async def get_json(self, key: str) -> Any | None:
        """Get and deserialize a JSON value."""
        raw = await self.client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set(self, key: str, value: str, expire_seconds: int | None = None) -> None:
        """Set a string value with optional TTL."""
        if expire_seconds:
            await self.client.setex(key, expire_seconds, value)
        else:
            await self.client.set(key, value)

    async def set_json(
        self, key: str, value: Any, expire_seconds: int | None = None
    ) -> None:
        """Serialize and set a JSON value with optional TTL."""
        await self.set(key, json.dumps(value, default=str), expire_seconds)

    async def delete(self, key: str) -> None:
        """Delete a key."""
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        return bool(await self.client.exists(key))

    async def expire(self, key: str, seconds: int) -> None:
        """Set TTL on an existing key."""
        await self.client.expire(key, seconds)

    async def incr(self, key: str) -> int:
        """Increment a counter."""
        return await self.client.incr(key)


# Singleton
cache = RedisCache()
