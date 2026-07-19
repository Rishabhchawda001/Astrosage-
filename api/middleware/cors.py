"""CORS middleware configuration."""
from __future__ import annotations

from fastapi.middleware.cors import CORSMiddleware

from api.config import settings


def setup_cors(app) -> None:
    """Configure CORS middleware."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
