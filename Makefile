# ────────────────────────────────────────────────────────────────
# AstroSage AI — Makefile
# ────────────────────────────────────────────────────────────────

.PHONY: help install dev lint test build run clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install --upgrade pip
	pip install -e ".[dev]"
	pip install fastapi[standard] uvicorn[standard] pydantic-settings \
		python-jose[cryptography] passlib[bcrypt] httpx prometheus-fastapi-instrumentator

dev: ## Start development server with hot reload
	uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

lint: ## Run linters
	ruff check api/
	mypy api/ --ignore-missing-imports || true

test: ## Run tests
	pytest api/tests/ -v --tb=short --cov=api/ --cov-report=term-missing

test-all: ## Run all tests including existing knowledge tests
	pytest tests/ -v --tb=short --ignore=tests/test_phase31.py --ignore=tests/test_phase35.py

build: ## Build Docker image
	docker build -t astrosage/astrosage-api:latest .

run: ## Start with Docker Compose
	docker compose up --build

run-detached: ## Start with Docker Compose (background)
	docker compose up --build -d

stop: ## Stop Docker Compose
	docker compose down

clean: ## Clean Python artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache

health: ## Check API health
	curl -s http://localhost:8000/api/v1/health | python3 -m json.tool

logs: ## View Docker logs
	docker compose logs -f api
