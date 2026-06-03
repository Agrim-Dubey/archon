"""Redis asynchronous client with in-memory fallback for local testing."""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)


class InMemoryRedisFallback:
    """In-memory key-value store simulating Redis for environments without Redis."""

    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._lists: Dict[str, List[str]] = {}
        self._expiries: Dict[str, float] = {}

    def _is_expired(self, key: str) -> bool:
        exp = self._expiries.get(key)
        if exp and time.time() > exp:
            self._store.pop(key, None)
            self._lists.pop(key, None)
            self._expiries.pop(key, None)
            return True
        return False

    async def ping(self) -> bool:
        return True

    async def get(self, key: str) -> Optional[str]:
        if self._is_expired(key):
            return None
        val = self._store.get(key)
        return str(val) if val is not None else None

    async def set(
        self, key: str, value: Any, ex: Optional[int] = None
    ) -> bool:
        self._store[key] = value
        if ex:
            self._expiries[key] = time.time() + ex
        else:
            self._expiries.pop(key, None)
        return True

    async def delete(self, *keys: str) -> int:
        count = 0
        for k in keys:
            if k in self._store or k in self._lists:
                self._store.pop(k, None)
                self._lists.pop(k, None)
                self._expiries.pop(k, None)
                count += 1
        return count

    async def rpush(self, key: str, *values: str) -> int:
        if key not in self._lists:
            self._lists[key] = []
        for v in values:
            self._lists[key].append(v)
        return len(self._lists[key])

    async def lrange(self, key: str, start: int, end: int) -> List[str]:
        if self._is_expired(key) or key not in self._lists:
            return []
        items = self._lists[key]
        if end == -1:
            return items[start:]
        return items[start : end + 1]

    async def incr(self, key: str) -> int:
        if self._is_expired(key):
            self._store[key] = 0
        val = int(self._store.get(key, 0)) + 1
        self._store[key] = val
        return val

    async def expire(self, key: str, seconds: int) -> bool:
        if key in self._store or key in self._lists:
            self._expiries[key] = time.time() + seconds
            return True
        return False

    async def close(self) -> None:
        pass


_redis_instance = None
_in_memory_instance = None


async def get_redis():
    """Retrieve async Redis client or in-memory fallback."""
    global _redis_instance, _in_memory_instance
    if _redis_instance is not None:
        return _redis_instance

    try:
        client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=1.0,
            socket_connect_timeout=1.0,
        )
        await client.ping()
        _redis_instance = client
        logger.info("Connected to real Redis at %s", settings.REDIS_URL)
        return _redis_instance
    except Exception as e:
        logger.warning(
            "Redis connection failed (%s). Falling back to InMemoryRedis.", e
        )
        if _in_memory_instance is None:
            _in_memory_instance = InMemoryRedisFallback()
        return _in_memory_instance
