"""
In-memory rate limiting middleware.

Uses a sliding window counter per IP or per user.
Designed to be swapped for Redis-based limiting in production.
"""
from __future__ import annotations

import time
import logging
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from api.config import settings

logger = logging.getLogger("astrosage.ratelimit")


class InMemoryRateLimiter:
    """Sliding window rate limiter."""

    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._windows: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> tuple[bool, int]:
        now = time.time()
        window_start = now - self.window_seconds
        timestamps = self._windows[key]
        # Prune old entries
        self._windows[key] = [t for t in timestamps if t > window_start]
        count = len(self._windows[key])
        if count >= self.max_requests:
            return False, count
        self._windows[key].append(now)
        return True, count

    def remaining(self, key: str) -> int:
        now = time.time()
        window_start = now - self.window_seconds
        timestamps = [t for t in self._windows.get(key, []) if t > window_start]
        return max(0, self.max_requests - len(timestamps))


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limits by IP address. Redis version will replace this."""

    def __init__(self, app):
        super().__init__(app)
        self._limiter = InMemoryRateLimiter(max_requests=settings.rate_limit_per_minute)

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path == "/api/v1/health":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        allowed, count = self._limiter.check(client_ip)

        if not allowed:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "rate_limit_exceeded",
                        "message": "Too many requests. Please slow down.",
                        "status_code": 429,
                        "details": {"retry_after_seconds": 60},
                    }
                },
                headers={
                    "X-RateLimit-Limit": str(settings.rate_limit_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": "60",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(self._limiter.remaining(client_ip))
        return response
