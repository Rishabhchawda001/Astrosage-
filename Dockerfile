# ────────────────────────────────────────────────────────────────
# AstroSage AI — Multi-stage Docker Build
# ────────────────────────────────────────────────────────────────

# ── Stage 1: Build ─────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir . && \
    pip install --no-cache-dir "fastapi[standard]" uvicorn[standard] pydantic-settings \
        python-jose[cryptography] passlib[bcrypt] httpx prometheus-fastapi-instrumentator

# ── Stage 2: Runtime ───────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY api/ api/
COPY pyproject.toml .

# Copy knowledge base (or mount as volume in production)
COPY knowledge/releases/v1.0.0/graph/graph.json /app/knowledge/releases/v1.0.0/graph/graph.json
COPY knowledge/releases/v1.0.0/retrieval/ /app/knowledge/releases/v1.0.0/retrieval/

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Non-root user
RUN useradd -m -u 1000 astrosage && chown -R astrosage:astrosage /app
USER astrosage

EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
