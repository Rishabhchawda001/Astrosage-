"""
Authentication routes — register, login, token refresh, API key management.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Header, Security
from fastapi.security import HTTPAuthorizationCredentials

from api.dependencies import get_current_user, bearer_scheme
from api.exceptions import AuthenticationError, ValidationError
from api.models.user import (
    UserCreate,
    UserResponse,
    TokenRequest,
    TokenResponse,
    TokenRefreshRequest,
    APIKeyCreateResponse,
)
from api.services import auth as auth_service
from api.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(body: UserCreate):
    """Register a new user account."""
    try:
        user = auth_service.create_user(body.username, body.password)
        api_key = auth_service.create_api_key(body.username)
        return UserResponse(
            username=user["username"],
            scopes=user["scopes"],
            created_at=user["created_at"],
            api_key=api_key,
        )
    except ValueError as e:
        raise ValidationError(message=str(e))


@router.post("/token", response_model=TokenResponse)
async def login(body: TokenRequest):
    """Authenticate and receive JWT tokens."""
    user = auth_service.authenticate_user(body.username, body.password)
    if not user:
        raise AuthenticationError(message="Invalid username or password")

    access_token = auth_service.create_access_token(
        data={"sub": user["username"], "scopes": user["scopes"]}
    )
    refresh_token = auth_service.create_refresh_token(
        data={"sub": user["username"]}
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: TokenRefreshRequest):
    """Refresh an expired access token using a refresh token."""
    from api.services.auth import decode_access_token

    payload = decode_access_token(body.refresh_token)
    if payload is None:
        raise AuthenticationError(message="Invalid or expired refresh token")

    username = payload.get("sub")
    if not username:
        raise AuthenticationError(message="Invalid token payload")

    access_token = auth_service.create_access_token(
        data={"sub": username, "scopes": payload.get("scopes", ["read"])}
    )
    new_refresh_token = auth_service.create_refresh_token(data={"sub": username})

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
):
    """Get information about the currently authenticated user."""
    return UserResponse(
        username=current_user.get("sub", "unknown"),
        scopes=current_user.get("scopes", []),
        created_at="",
    )


@router.post("/api-keys", response_model=APIKeyCreateResponse)
async def create_api_key(
    current_user: dict = Depends(get_current_user),
):
    """Create a new API key for programmatic access."""
    username = current_user.get("sub", "unknown")
    api_key = auth_service.create_api_key(username)
    return APIKeyCreateResponse(api_key=api_key)
