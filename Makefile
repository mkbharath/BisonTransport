.PHONY: up down logs seed test lint format agents test-email clean

# --- Docker Compose ---
up:
	docker compose up -d
	@echo "Services starting... MinIO: http://localhost:9001 | MailHog: http://localhost:8025 | API: http://localhost:8000 | Frontend: http://localhost:5173"

down:
	docker compose down

logs:
	docker compose logs -f

logs-agents:
	docker compose logs -f agents

logs-api:
	docker compose logs -f api

# --- Database ---
migrate:
	docker compose exec api alembic upgrade head

seed:
	docker compose exec api python -m scripts.seed_local

reset-db:
	docker compose down -v
	docker compose up -d postgres
	@sleep 3
	$(MAKE) migrate
	$(MAKE) seed

# --- Agents ---
agents:
	docker compose up -d agents

test-email:
	@if [ -z "$(FILE)" ]; then echo "Usage: make test-email FILE=path/to/email.eml"; exit 1; fi
	cp $(FILE) test-emails/inbox/

# --- Testing ---
test:
	cd packages/shared/python && python -m pytest
	cd packages/agents && python -m pytest
	cd packages/api && python -m pytest

test-shared:
	cd packages/shared/python && python -m pytest -v

test-agents:
	cd packages/agents && python -m pytest -v

test-api:
	cd packages/api && python -m pytest -v

test-frontend:
	cd packages/frontend && npm run test

# --- Linting & Formatting ---
lint:
	cd packages/shared/python && ruff check . && mypy order_shared
	cd packages/agents && ruff check . && mypy src/order_agents
	cd packages/api && ruff check . && mypy src/order_api
	cd packages/frontend && npm run lint

format:
	cd packages/shared/python && black . && isort .
	cd packages/agents && black . && isort .
	cd packages/api && black . && isort .

# --- Demo ---
demo:
	./scripts/run_demo.sh

# --- Cleanup ---
clean:
	docker compose down -v --remove-orphans
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
