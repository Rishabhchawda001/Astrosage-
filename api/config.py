"""
AstroSage configuration via Pydantic Settings.

All configuration originates from environment variables.
No hardcoded secrets, no configuration files with credentials.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Application ──────────────────────────────────────────────
    app_name: str = "AstroSage AI"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "production"  # development, staging, production

    # ── Server ───────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    cors_origins: list[str] = ["http://localhost:3000", "https://astrosage.ai"]

    # ── Authentication ───────────────────────────────────────────
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    # ── Database ─────────────────────────────────────────────────
    database_url: Optional[str] = None  # PostgreSQL connection string

    # ── Redis ────────────────────────────────────────────────────
    redis_url: Optional[str] = None  # redis://localhost:6379/0

    # ── Rate Limiting ────────────────────────────────────────────
    rate_limit_per_minute: int = 100
    rate_limit_burst: int = 20

    # ── Logging ──────────────────────────────────────────────────
    log_level: str = "INFO"
    log_format: str = "json"  # json or plain

    # ── AI Model ─────────────────────────────────────────────────
    local_model: Optional[str] = None  # Path or model name for vLLM
    embedding_model: str = "all-MiniLM-L6-v2"
    max_tokens: int = 4096
    temperature: float = 0.7

    # ── Storage ──────────────────────────────────────────────────
    knowledge_base_path: str = "knowledge/releases/v1.0.0"

    # ── Monitoring ───────────────────────────────────────────────
    sentry_dsn: Optional[str] = None
    otlp_endpoint: Optional[str] = None  # OpenTelemetry collector

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


settings = Settings()


def validate_environment() -> list[str]:
    """Validate critical environment variables. Returns list of warnings."""
    warnings = []

    # Check required secrets
    if settings.secret_key == "change-me-in-production":
        warnings.append(
            "SECRET_KEY is set to the default value. Generate a random 64-character "
            "string with `openssl rand -hex 32` and set it via the SECRET_KEY env var."
        )

    # Check potentially problematic configurations
    if settings.debug and settings.environment == "production":
        warnings.append("DEBUG is enabled in production. Disable via DEBUG=false.")

    if settings.cors_origins == ["*"]:
        warnings.append(
            "CORS allows all origins (*). Restrict to specific domains in production."
        )

    # Check Redis and database config for production
    if settings.environment == "production":
        if not settings.redis_url or settings.redis_url == "":
            warnings.append(
                "REDIS_URL is not set. Rate limiting will use in-memory storage "
                "(not suitable for multi-worker deployments)."
            )
        if not settings.database_url or settings.database_url == "":
            warnings.append(
                "DATABASE_URL is not set. Conversations will use SQLite (development only)."
            )

    return warnings


# Run validation on import
_env_warnings = validate_environment()
if _env_warnings:
    import logging
    _logger = logging.getLogger("astrosage.config")
    for w in _env_warnings:
        _logger.warning(f"Configuration: {w}")

