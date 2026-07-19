"""
Global exception handlers for FastAPI.

Returns structured JSON errors with consistent format for all exception types.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.exceptions import AstroSageError

logger = logging.getLogger("astrosage.api")


def setup_error_handlers(app: FastAPI) -> None:
    """Register global exception handlers."""

    @app.exception_handler(AstroSageError)
    async def astrosage_error_handler(request: Request, exc: AstroSageError):
        logger.warning(
            f"AstroSageError: {exc.code} — {exc.message}",
            extra={"request_id": getattr(request.state, "request_id", None)},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error.get("loc", [])),
                "message": error.get("msg", ""),
                "type": error.get("type", ""),
            })
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed",
                    "status_code": 422,
                    "details": {"errors": errors},
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        logger.exception(
            f"Unhandled exception: {exc}",
            extra={"request_id": getattr(request.state, "request_id", None)},
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred",
                    "status_code": 500,
                    "details": {},
                }
            },
        )
