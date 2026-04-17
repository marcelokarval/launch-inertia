# Launch Inertia

Full-stack Django + Inertia.js + React platform centered on lead capture, identity resolution, landing flows, checkout, billing, and operator-facing dashboards.

## Current Phase

The repository is in a more advanced state than the original bootstrap docs suggested.

Current highlights:

- backend reorganized under `backend/`
- multiple frontends under `frontends/`
- root-level internal docs consolidated under `docs/`
- Docusaurus-style feature docs under `frontends/docusaurus/docs/`
- lead capture flow hardened end-to-end with:
  - anonymous session identity on first visit
  - delayed fingerprint association
  - explicit prelead model (`CaptureIntent`)
  - transactional submit path (`CaptureService.complete_capture()`)
  - guaranteed `CaptureSubmission`
  - durable outbox for external integrations
  - submit idempotency
  - admin visibility, health checks, repair and requeue tooling

## Repository Layout

```text
launch-inertia/
├── backend/                      # Django backend project
│   ├── manage.py
│   ├── pyproject.toml
│   ├── src/
│   │   ├── apps/
│   │   │   ├── identity/
│   │   │   ├── contacts/
│   │   │   ├── landing/
│   │   │   ├── billing/
│   │   │   ├── launches/
│   │   │   ├── ads/
│   │   │   └── notifications/
│   │   ├── config/
│   │   ├── core/
│   │   ├── infrastructure/
│   │   └── tests/
│   ├── templates/
│   ├── static/
│   └── media/
├── frontends/
│   ├── dashboard/               # Operator / private app
│   ├── landing/                 # Public funnel / checkout / content app
│   └── docusaurus/              # Feature-oriented docs source
├── docs/                        # Internal architecture / process / runbooks
├── Makefile
└── README.md
```

## Tech Stack

### Backend
- Django 6.x
- Inertia Django
- PostgreSQL
- Redis
- Celery
- Channels / Daphne
- Stripe / dj-stripe
- django-unfold
- uv

### Frontend
- React 19
- TypeScript
- Vite 7
- Tailwind CSS 4
- HeroUI on dashboard
- Stripe React SDK on landing checkout surfaces

## Core Runtime Concepts

The platform distinguishes account identity from lead identity.

- `identity.User`
  Authenticated internal account for private/operator flows.

- `contacts.identity.Identity`
  Unified person/lead identity for capture and contact resolution.

- `contacts.fingerprint.FingerprintIdentity`
  FingerprintJS Pro `visitorId` record.

- `core.tracking.CaptureEvent`
  Runtime event timeline.

- `core.tracking.CaptureIntent`
  Prelead record created before final submit.

- `ads.CaptureSubmission`
  Fact record for a valid capture.

- `landing.LeadIntegrationOutbox`
  Durable async delivery for `n8n` and `meta_capi`.

## Documentation Surfaces

### Internal project docs
- `docs/README.md`

This area contains:
- architecture notes
- domain notes
- runbooks
- process docs
- archives/history

### Feature-oriented docs
- `frontends/docusaurus/docs/intro.md`

Important lead-capture docs live there, including:
- workflow
- to-be architecture
- identity resolution runtime flow
- identity gap analysis
- rollout notes
- hardening checklist
- ADRs

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+
- `uv`

### Backend setup

```bash
cd backend
uv sync

# preferred local env location
cp ../.env.example .env

# or keep using a root-level .env
# the backend env loader supports backend/.env first,
# then falls back to ../.env

uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver 8844
```

### Frontend setup

From the repository root:

```bash
npm install
```

Dashboard dev server:

```bash
cd frontends/dashboard
npm run dev
```

Landing dev server:

```bash
cd frontends/landing
npm run dev
```

## Common Commands

Use the `Makefile` from the repository root.

```bash
make install         # backend + frontend dependencies
make dev             # backend + dashboard
make dev-full        # backend + dashboard + landing + celery + beat
make test            # backend + frontend tests
make test-back       # backend pytest
make migrate         # Django migrate
make makemigrations  # create migrations
make celery          # worker
make celery-beat     # beat scheduler
```

## Frontend Builds

From the repository root:

```bash
npm run build --workspace=@launch/dashboard
npm run build --workspace=@launch/landing
```

The generated assets are written to:

- `backend/src/static/dashboard/`
- `backend/src/static/landing/`

## Validation Commands

### Backend

```bash
cd backend
uv run python manage.py check
uv run pytest
```

### Focused capture stack regression

```bash
cd backend
uv run pytest \
  src/tests/test_capture.py \
  src/tests/test_checkout.py \
  src/tests/test_launches.py \
  src/tests/test_landing_admin.py \
  src/tests/test_ads.py \
  src/tests/test_tracking.py \
  src/tests/test_meta_capi.py -q
```

## Operational Tooling Added For Lead Capture

These commands are useful once the system is running.

```bash
cd backend

# Sync legacy JSON capture pages into DB-backed CapturePage rows
uv run python manage.py sync_legacy_capture_pages --dry-run
uv run python manage.py sync_legacy_capture_pages

# Check if capture runtime is ready to run without JSON fallback
uv run python manage.py check_capture_page_readiness --strict

# Health check for outbox delivery
uv run python manage.py check_lead_integration_health

# Requeue failed integrations
uv run python manage.py requeue_failed_lead_integrations --dry-run
uv run python manage.py requeue_failed_lead_integrations --integration-type n8n

# Repair incomplete outbox payloads from persisted submission facts
uv run python manage.py repair_lead_integration_payloads --dry-run
```

## Runtime Notes

### Legacy JSON fallback

Capture runtime can still use legacy JSON configs when enabled:

- `LANDING_JSON_FALLBACK_ENABLED=True`

Production should converge to DB-backed `CapturePage` records and disable fallback once readiness passes.

### Outbox SLOs

Defaults:

- `LEAD_OUTBOX_N8N_SLO_MINUTES=10`
- `LEAD_OUTBOX_META_CAPI_SLO_MINUTES=15`

## Project Status Guidance

If you are trying to understand the lead capture domain first, read in this order:

1. `frontends/docusaurus/docs/lead-capture-workflow.md`
2. `frontends/docusaurus/docs/identity-resolution-runtime-flow.md`
3. `frontends/docusaurus/docs/identity-resolution-gap-analysis.md`
4. `frontends/docusaurus/docs/lead-capture-production-hardening.md`
5. `frontends/docusaurus/docs/lead-capture-rollout-no-json-fallback.md`

If you are trying to understand internal architecture and process:

1. `docs/README.md`
2. `docs/architecture/`
3. `docs/process/`

## License

MIT
