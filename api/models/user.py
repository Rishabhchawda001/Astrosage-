"""User and authentication models."""
from __future__ import annotations

from datetime import datetime, timezone
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Request model for user registration."""
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=8, max_length=128)


class UserResponse(BaseModel):
    """Response model for user data (no password hash)."""
    username: str
    scopes: list[str]
    created_at: str
    api_key: str | None = None


class TokenRequest(BaseModel):
    """Request model for token generation."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Response model for authentication tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefreshRequest(BaseModel):
    """Request model for token refresh."""
    refresh_token: str


class APIKeyCreateResponse(BaseModel):
    """Response model for API key creation."""
    api_key: str
    message: str = "Save this API key — it will not be shown again."
