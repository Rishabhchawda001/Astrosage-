# ────────────────────────────────────────────────────────────────
# AstroSage AI — Makefile
# ────────────────────────────────────────────────────────────────

.PHONY: dev api api-dev frontend frontend-dev build test lint clean docker docker-up docker-down

# ── Default ──────────────────────────────────────────────────
help:
	@echo "AstroSage AI Commands"
	@echo "  make api         - Start API server"
	@echo "  make frontend    - Start frontend dev server"
	@echo "  make dev         - Start both API and frontend"
	@echo "  make test        - Run all tests"
	@echo "  make build       - Build frontend"
	@echo "  make docker-up   - Start all Docker services"
	@echo "  make docker-down - Stop all Docker services"

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
