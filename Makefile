# ────────────────────────────────────────────────────────────────
# AstroSage AI — Makefile
# ────────────────────────────────────────────────────────────────

.PHONY: help dev api frontend test test-all build lint clean docker-up docker-down docker-prod

help:
	@echo "AstroSage AI Commands"
	@echo "  make dev          - Start API + Frontend (development)"
	@echo "  make api           - Start API server"
	@echo "  make frontend      - Start frontend dev server"
	@echo "  make test          - Run API tests"
	@echo "  make build         - Build frontend"
	@echo "  make lint          - Lint all code"
	@echo "  make docker-up     - Start all Docker services"
	@echo "  make docker-prod   - Start production stack"
	@echo "  make docker-down   - Stop all services"
	@echo "  make clean         - Clean build artifacts"

# ── API ──────────────────────────────────────────────────────
api:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

api-dev:
	APP_ENVIRONMENT=development uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# ── Frontend ─────────────────────────────────────────────────
frontend:
	cd frontend && npm run dev

frontend-dev:
	cd frontend && NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev

frontend-build:
	cd frontend && npm run build

# ── Dev ──────────────────────────────────────────────────────
dev:
	@echo "Starting AstroSage AI..."
	@echo "  API:      http://localhost:8000"
	@echo "  Frontend: http://localhost:3000"
	@trap 'kill 0' EXIT; \
		APP_ENVIRONMENT=development uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 & \
		cd frontend && npm run dev

# ── Tests ────────────────────────────────────────────────────
test:
	APP_ENVIRONMENT=development python3 -m pytest api/tests/ -v --tb=short -q

test-all:
	APP_ENVIRONMENT=development python3 -m pytest api/tests/ tests/ -v --tb=short -q

test-eval:
	APP_ENVIRONMENT=development python3 -m evaluation.real_pipeline_eval

# ── Lint ─────────────────────────────────────────────────────
lint:
	cd frontend && npm run lint
	ruff check api/ --output-format=github || true

# ── Docker ───────────────────────────────────────────────────
docker-up:
	docker compose up --build -d
	@echo "API:      http://localhost:8000"
	@echo "Frontend: http://localhost:3000"

docker-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
	@echo "API:      http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "Nginx:    http://localhost:80"

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

# ── Clean ────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .next -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/node_modules frontend/.next
