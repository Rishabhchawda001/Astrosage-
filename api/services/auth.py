"""
Authentication service — JWT token creation, validation, user management.

Uses python-jose for JWT and passlib + bcrypt for password hashing.
Designed for upgrade to database-backed storage in Phase 3.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
import bcrypt

from api.config import settings

# Password hashing — direct bcrypt


# ── In-Memory User Store (temporary, will be replaced by PostgreSQL) ──

_users: dict[str, dict] = {
    "admin": {
        "username": "admin",
        "password_hash": bcrypt.hashpw(b"astrosage-admin", bcrypt.gensalt()).decode('utf-8'),  # CHANGE IN PRODUCTION
        "scopes": ["read", "write", "admin"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
}
_api_keys: dict[str, str] = {}  # api_key -> username


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_user(username: str, password: str, scopes: list[str] | None = None) -> dict:
    """Create a new user. Will be replaced by database-backed storage."""
    if username in _users:
        raise ValueError(f"User '{username}' already exists")
    if len(password) > 72:
        raise ValueError("Password too long (max 72 characters)")
    user = {
        "username": username,
        "password_hash": hash_password(password),
        "scopes": scopes or ["read"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _users[username] = user
    return {k: v for k, v in user.items() if k != "password_hash"}


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate a user by username and password."""
    user = _users.get(username)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return {k: v for k, v in user.items() if k != "password_hash"}


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token with longer expiry."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def generate_api_key() -> str:
    """Generate a new API key."""
    return f"ast-{secrets.token_hex(32)}"


def create_api_key(username: str) -> str:
    """Create an API key for a user."""
    api_key = generate_api_key()
    _api_keys[api_key] = username
    return api_key


def validate_api_key(api_key: str) -> Optional[str]:
    """Validate an API key and return the associated username."""
    return _api_keys.get(api_key)
