"""
AstroSage AI — FastAPI Application

Entry point for the AstroSage AI REST API.
Run with: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from api.config import settings
from api.logging import setup_logging
from api.error_handlers import setup_error_handlers
from api.middleware.cors import setup_cors
from api.middleware.audit import AuditMiddleware
from api.middleware.rate_limit import RateLimitMiddleware

logger = logging.getLogger("astrosage.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle — startup and shutdown."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version} ({settings.environment})")
    logger.info(f"Knowledge base: {settings.knowledge_base_path}")
    yield
    logger.info(f"Shutting down {settings.app_name}")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AstroSage AI — Evidence-First Knowledge Operating System",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── Middleware (order matters: first added = outermost) ──
app.add_middleware(AuditMiddleware)
app.add_middleware(RateLimitMiddleware)
setup_cors(app)

# ── Error handlers ──
setup_error_handlers(app)

# ── Routes ──
from api.routes.health import router as health_router
from api.routes.auth import router as auth_router
from api.routes.search import router as search_router
from api.routes.graph import router as graph_router
from api.routes.answer import router as answer_router
from api.routes.chat import router as chat_router

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(search_router)
app.include_router(graph_router)
app.include_router(answer_router)
app.include_router(chat_router)


# ── Root redirect ──
from fastapi.responses import RedirectResponse


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


# ── Prometheus metrics ──
try:
    from prometheus_fastapi_instrumentator import Instrumentator

    Instrumentator().instrument(app).expose(app, endpoint="/api/v1/metrics")
    logger.info("Prometheus metrics enabled at /api/v1/metrics")
except ImportError:
    logger.info("Prometheus metrics not available (install prometheus-fastapi-instrumentator)")


def generate_custom_openapi() -> dict:
    """Generate custom OpenAPI schema with proper security schemes."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.app_name,
        version=settings.app_version,
        description="AstroSage AI — Evidence-First Knowledge Operating System\n\n"
        "## Authentication\n\n"
        "Two authentication methods are supported:\n"
        "1. **Bearer Token** — JWT access token\n"
        "2. **API Key** — Use `X-API-Key` header for programmatic access\n\n"
        "Get your tokens via `POST /api/v1/auth/token`.",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT access token from /api/v1/auth/token",
        },
        "apiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key from /api/v1/auth/api-keys",
        },
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = generate_custom_openapi
