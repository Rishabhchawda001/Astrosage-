"""
FastAPI dependency injection for shared services.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from api.config import settings
from api.exceptions import AuthenticationError

# Security scheme for Swagger UI
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    """
    Dependency that validates JWT token and returns user info.
    Currently validates token format; auth is fully implemented in Phase 0.2.
    """
    from api.services.auth import decode_access_token

    if settings.environment == "development" and not credentials:
        # Dev mode: return anonymous user
        return {"sub": "anonymous", "scopes": ["read", "write", "admin"]}

    if not credentials:
        raise AuthenticationError(message="Missing authentication token")

    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise AuthenticationError(message="Invalid or expired token")

    return payload


async def optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict | None:
    """Optional auth — returns None if no token provided."""
    if not credentials:
        return None
    from api.services.auth import decode_access_token
    payload = decode_access_token(credentials.credentials)
    return payload
