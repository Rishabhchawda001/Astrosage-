"""
AstroSage API exception hierarchy.

Every exception produces a structured JSON error response
with consistent format across all endpoints.
"""
from __future__ import annotations


class AstroSageError(Exception):
    """Base exception for all AstroSage API errors."""

    status_code: int = 500
    code: str = "internal_error"
    message: str = "An unexpected error occurred"

    def __init__(
        self,
        message: str | None = None,
        status_code: int | None = None,
        code: str | None = None,
        details: dict | None = None,
    ):
        if message:
            self.message = message
        if status_code:
            self.status_code = status_code
        if code:
            self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "status_code": self.status_code,
                "details": self.details,
            }
        }


class AuthenticationError(AstroSageError):
    status_code = 401
    code = "authentication_error"
    message = "Authentication failed"


class AuthorizationError(AstroSageError):
    status_code = 403
    code = "authorization_error"
    message = "Insufficient permissions"


class NotFoundError(AstroSageError):
    status_code = 404
    code = "not_found"
    message = "Resource not found"


class ValidationError(AstroSageError):
    status_code = 422
    code = "validation_error"
    message = "Invalid request parameters"


class RateLimitError(AstroSageError):
    status_code = 429
    code = "rate_limit_exceeded"
    message = "Too many requests. Please slow down."


class KnowledgeNotFoundError(NotFoundError):
    code = "knowledge_not_found"
    message = "No knowledge found matching the query"


class ServiceUnavailableError(AstroSageError):
    status_code = 503
    code = "service_unavailable"
    message = "Service temporarily unavailable"
