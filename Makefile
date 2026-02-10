.PHONY: help dev dev-all dev-back dev-front test test-back test-front lint migrate makemigrations shell celery celery-beat celery-all install

# Default
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Development ──────────────────────────────────────────

dev: ## Run Django + Vite dev servers (parallel)
	@trap 'kill 0' EXIT; \
	$(MAKE) dev-back & \
	$(MAKE) dev-front & \
	wait

dev-all: ## Run Django + Vite + Celery worker + Celery beat (parallel)
	@trap 'kill 0' EXIT; \
	$(MAKE) dev-back & \
	$(MAKE) dev-front & \
	$(MAKE) celery & \
	$(MAKE) celery-beat & \
	wait

dev-back: ## Run Django dev server (port 8844)
	cd src && uv run python ../manage.py runserver 8844

dev-front: ## Run Vite dev server (port 3344)
	cd frontend && npm run dev

# ── Testing ──────────────────────────────────────────────

test: test-back test-front ## Run all tests

test-back: ## Run Django/pytest tests
	cd src && uv run python -m pytest

test-front: ## Run Vitest frontend tests
	cd frontend && npx vitest run

# ── Linting / Type checking ─────────────────────────────

lint: ## Run frontend linting + type check
	cd frontend && npm run lint && npm run typecheck

# ── Database ─────────────────────────────────────────────

migrate: ## Run Django migrations
	uv run python manage.py migrate

makemigrations: ## Create new migrations
	uv run python manage.py makemigrations

# ── Django utilities ─────────────────────────────────────

shell: ## Django shell
	uv run python manage.py shell

createsuperuser: ## Create admin superuser
	uv run python manage.py createsuperuser

collectstatic: ## Collect static files
	uv run python manage.py collectstatic --noinput

# ── Celery ───────────────────────────────────────────────

celery: ## Run Celery worker (all queues)
	cd src && uv run celery -A infrastructure.tasks.celery worker -l info -Q celery,default --concurrency=2

celery-beat: ## Run Celery beat scheduler
	cd src && uv run celery -A infrastructure.tasks.celery beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

celery-all: ## Run Celery worker + beat in parallel
	@trap 'kill 0' EXIT; \
	$(MAKE) celery & \
	$(MAKE) celery-beat & \
	wait

# ── Setup ────────────────────────────────────────────────

install: ## Install all dependencies
	uv pip install -e ".[dev]" && cd frontend && npm install

install-back: ## Install Python dependencies only
	uv pip install -e ".[dev]"

install-front: ## Install Node dependencies only
	cd frontend && npm install
