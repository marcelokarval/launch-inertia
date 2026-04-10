.PHONY: help dev dev-all dev-back dev-dashboard dev-landing test test-back test-front lint migrate makemigrations shell celery celery-beat celery-all install

# Default
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Development ──────────────────────────────────────────

dev: ## Run Django + Dashboard Vite dev servers (parallel)
	@trap 'kill 0' EXIT; \
	$(MAKE) dev-back & \
	$(MAKE) dev-dashboard & \
	wait

dev-all: ## Run Django + Dashboard + Celery worker + Celery beat (parallel)
	@trap 'kill 0' EXIT; \
	$(MAKE) dev-back & \
	$(MAKE) dev-dashboard & \
	$(MAKE) celery & \
	$(MAKE) celery-beat & \
	wait

dev-full: ## Run Django + Dashboard + Landing + Celery (parallel)
	@trap 'kill 0' EXIT; \
	$(MAKE) dev-back & \
	$(MAKE) dev-dashboard & \
	$(MAKE) dev-landing & \
	$(MAKE) celery & \
	$(MAKE) celery-beat & \
	wait

dev-back: ## Run Django dev server (port 8844)
	cd backend && uv run python manage.py runserver 8844

dev-dashboard: ## Run Dashboard Vite dev server (port 3344)
	cd frontends/dashboard && npm run dev

dev-landing: ## Run Landing Vite dev server (port 3345)
	cd frontends/landing && npm run dev

# ── Testing ──────────────────────────────────────────────

test: test-back test-front ## Run all tests

test-back: ## Run Django/pytest tests
	cd backend && uv run python -m pytest

test-front: ## Run Dashboard Vitest frontend tests
	cd frontends/dashboard && npx vitest run

# ── Linting / Type checking ─────────────────────────────

lint: ## Run frontend linting + type check
	cd frontends/dashboard && npm run lint && npm run typecheck

# ── Database ─────────────────────────────────────────────

migrate: ## Run Django migrations
	cd backend && uv run python manage.py migrate

makemigrations: ## Create new migrations
	cd backend && uv run python manage.py makemigrations

# ── Django utilities ─────────────────────────────────────

shell: ## Django shell
	cd backend && uv run python manage.py shell

createsuperuser: ## Create admin superuser
	cd backend && uv run python manage.py createsuperuser

collectstatic: ## Collect static files
	cd backend && uv run python manage.py collectstatic --noinput

# ── Celery ───────────────────────────────────────────────

celery: ## Run Celery worker (all queues)
	cd backend && uv run celery -A infrastructure.tasks.celery worker -l info -Q celery,default --concurrency=2

celery-beat: ## Run Celery beat scheduler
	cd backend && uv run celery -A infrastructure.tasks.celery beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

celery-all: ## Run Celery worker + beat in parallel
	@trap 'kill 0' EXIT; \
	$(MAKE) celery & \
	$(MAKE) celery-beat & \
	wait

# ── Setup ────────────────────────────────────────────────

install: ## Install all dependencies (Python + Node workspaces)
	cd backend && uv pip install -e ".[dev]" && cd .. && npm install

install-back: ## Install Python dependencies only
	cd backend && uv pip install -e ".[dev]"

install-front: ## Install Node dependencies only (all workspaces)
	npm install
