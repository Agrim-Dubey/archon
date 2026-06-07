"""Redis sliding window log rate limiter with Lua script and in-memory fallback."""

import time
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.redis import get_redis

# Atomic Sliding Window Log Lua script
SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])

local clearBefore = now - window
redis.call('ZREMRANGEBYSCORE', key, 0, clearBefore)
local currentRequests = redis.call('ZCARD', key)

if currentRequests < limit then
    redis.call('ZADD', key, now, now)
    redis.call('EXPIRE', key, math.ceil(window))
    return 1
else
    return 0
end
"""


class InMemorySlidingWindowLimiter:
    """In-memory rate limiter when Redis is absent."""

    def __init__(self):
        self._history = {}

    def is_allowed(self, key: str, limit: int, window_seconds: float) -> bool:
        now = time.time()
        cutoff = now - window_seconds
        records = [ts for ts in self._history.get(key, []) if ts > cutoff]
        if len(records) < limit:
            records.append(now)
            self._history[key] = records
            return True
        self._history[key] = records
        return False


_in_memory_limiter = InMemorySlidingWindowLimiter()


class RateLimiter:
    """Sliding window log rate limiter."""

    def __init__(self, limit: int = 120, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds

    async def is_allowed(self, identifier: str) -> bool:
        redis_client = await get_redis()
        now = time.time()
        key = f"ratelimit:{identifier}"

        # If real redis client supports eval
        if hasattr(redis_client, "eval"):
            try:
                allowed = await redis_client.eval(
                    SLIDING_WINDOW_LUA,
                    1,
                    key,
                    now,
                    self.window_seconds,
                    self.limit,
                )
                return bool(allowed)
            except Exception:
                pass

        return _in_memory_limiter.is_allowed(
            identifier, self.limit, self.window_seconds
        )


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """FastAPI Middleware to enforce rate limits per IP / User."""

    def __init__(
        self,
        app,
        limit: int = 120,
        window_seconds: int = 60,
        key_func: Optional[Callable[[Request], str]] = None,
    ):
        super().__init__(app)
        self.limiter = RateLimiter(limit=limit, window_seconds=window_seconds)
        self.key_func = key_func or self._default_key_func

    def _default_key_func(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        client = request.client
        return client.host if client else "127.0.0.1"

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in ["/metrics", "/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        key = self.key_func(request)
        allowed = await self.limiter.is_allowed(key)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "Rate limit exceeded. Please wait before making more requests.",
                    "code": "RATE_LIMIT_EXCEEDED",
                },
            )

        return await call_next(request)
