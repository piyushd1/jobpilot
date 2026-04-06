.PHONY: dev test migrate lint format typecheck clean setup

# --- Development ---
dev:
	docker compose up -d postgres redis qdrant minio temporal temporal-ui
	@echo "Waiting for services..."
	@sleep 5
	uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

dev-all:
	docker compose up --build

dev-down:
	docker compose down

dev-reset:
	docker compose down -v
	docker compose up -d

# --- Database ---
migrate:
	alembic upgrade head

migrate-new:
	@read -p "Migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

migrate-down:
	alembic downgrade -1

# --- Testing ---
test:
	pytest tests/unit -v --tb=short -m unit

test-all:
	pytest -v --tb=short

test-cov:
	pytest tests/unit -v --tb=short --cov=src --cov-report=term-missing

# --- Code Quality ---
lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

typecheck:
	mypy src/

# --- Setup ---
setup:
	pip install -e ".[dev]"
	pre-commit install
	cp -n .env.example .env || true
	@echo "Setup complete. Edit .env with your API keys."

# --- Worker ---
worker:
	python -m src.worker

# --- Clean ---
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
