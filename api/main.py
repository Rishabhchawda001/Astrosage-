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

    # ── Validate knowledge base ────────────────────────────────
    import os
    kb_path = settings.knowledge_base_path
    required_files = [
        os.path.join(kb_path, "retrieval", "bm25_index.json"),
        os.path.join(kb_path, "graph", "graph.json"),
    ]
    missing = [f for f in required_files if not os.path.isfile(f)]
    if missing:
        logger.error(
            f"STARTUP: Knowledge base missing required files: {missing}. "
            f"The API will start but all knowledge operations will fail."
        )
    else:
        logger.info(f"Knowledge base validated: {len(required_files)} files present")
    # ── Log knowledge base size ────────────────────────────────
    import glob
    kb_files = glob.glob(os.path.join(kb_path, "**", "*"), recursive=True)
    total_size = sum(os.path.getsize(f) for f in kb_files if os.path.isfile(f))
    logger.info(f"Knowledge base size: {len(kb_files)} files, {total_size / 1024 / 1024:.1f} MB")

    # ── Security warnings ─────────────────────────────────────
    if settings.secret_key == "change-me-in-production":
        logger.warning(
            "SECURITY: Using default SECRET_KEY. Set a strong random key via "
            "the SECRET_KEY environment variable for production deployments."
        )
    if settings.debug and settings.environment == "production":
        logger.warning("SECURITY: Debug mode enabled in production. Disable for production use.")
    if settings.cors_origins == ["*"]:
        logger.warning("SECURITY: CORS allows all origins (*). Restrict in production.")

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

# ── Security headers ──
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.environment == "production":
            response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# ── Request body size limit (prevents large payload attacks) ──
MAX_BODY_SIZE = 1024 * 512  # 512KB — accommodates long chat histories

class RequestBodySizeMiddleware(BaseHTTPMiddleware):
    """Limits request body size to prevent large payload attacks."""

    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > MAX_BODY_SIZE:
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": {
                            "code": "request_too_large",
                            "message": f"Request body exceeds maximum size of {MAX_BODY_SIZE} bytes",
                            "status_code": 413,
                            "details": {},
                        }
                    },
                )
        return await call_next(request)

app.add_middleware(RequestBodySizeMiddleware)

# ── Error handlers ──
setup_error_handlers(app)

# ── Routes ──
from api.routes.health import router as health_router
from api.routes.auth import router as auth_router
from api.routes.search import router as search_router
from api.routes.graph import router as graph_router
from api.routes.answer import router as answer_router
from api.routes.chat import router as chat_router
from api.routes.conversation import router as conversation_router
from api.routes.cache import router as cache_router

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(search_router)
app.include_router(graph_router)
app.include_router(answer_router)
app.include_router(chat_router)
app.include_router(conversation_router)
app.include_router(cache_router)


# ── Root redirect ──
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
import os


# Mount static files for the web UI
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
async def root():
    index_path = os.path.join(static_dir, "index.html") if os.path.isdir(static_dir) else None
    if index_path and os.path.isfile(index_path):
        return FileResponse(index_path, media_type="text/html")
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
