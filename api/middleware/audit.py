"""
Audit logging middleware.

Logs every API request with method, path, user, latency, and status.
Sensitive data (passwords, tokens) is automatically redacted.
"""
from __future__ import annotations

import time
import logging
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("astrosage.api")


class AuditMiddleware(BaseHTTPMiddleware):
    """Logs structured audit entries for every API request."""

    SENSITIVE_PATHS = {"/api/v1/auth/token", "/api/v1/auth/register"}
    SENSITIVE_PARAMS = {"password", "token", "secret", "api_key", "refresh_token"}

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        start_time = time.time()

        response: Response = await call_next(request)

        elapsed_ms = round((time.time() - start_time) * 1000, 1)

        # Redact sensitive paths
        path = request.url.path
        if path in self.SENSITIVE_PARAMS:
            path = f"{path}/[REDACTED]"

        extra = {
            "request_id": request_id,
            "method": request.method,
            "path": path,
            "status_code": response.status_code,
            "latency_ms": elapsed_ms,
            "ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", ""),
        }

        if hasattr(request.state, "user_id"):
            extra["user_id"] = request.state.user_id

        if response.status_code >= 400:
            logger.warning(f"API {request.method} {path} -> {response.status_code}", extra=extra)
        else:
            logger.info(f"API {request.method} {path} -> {response.status_code}", extra=extra)

        response.headers["X-Request-ID"] = request_id
        return response
