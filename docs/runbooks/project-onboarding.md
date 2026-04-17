# Project Onboarding

This is the fastest path to understand the current repository without relying on historical assumptions.

## 1. Start Here

Read in this order:

1. `README.md`
2. `docs/README.md`
3. `frontends/docusaurus/docs/intro.md`

This gives you:

- current repository layout
- where internal docs live
- where feature/flow docs live

## 2. Understand The Repository Shape

Current high-level layout:

```text
launch-inertia/
├── backend/      # Django project, tests, templates, static, media
├── frontends/    # dashboard, landing, docusaurus
├── docs/         # internal architecture/process/runbooks/archive
├── README.md
└── CHANGELOG.md
```

## 3. Understand The Lead Capture Domain

Read these docs in sequence:

1. `frontends/docusaurus/docs/lead-capture-workflow.md`
2. `frontends/docusaurus/docs/identity-resolution-runtime-flow.md`
3. `frontends/docusaurus/docs/identity-resolution-gap-analysis.md`
4. `frontends/docusaurus/docs/lead-capture-production-hardening.md`
5. `frontends/docusaurus/docs/lead-capture-rollout-no-json-fallback.md`

These cover:

- visitor/session/fingerprint lifecycle
- identity resolution and merge
- capture submission and outbox delivery
- remaining operational gaps and rollout posture

## 4. Understand Internal Architecture

Recommended internal docs:

1. `docs/architecture/frontend-architecture-analysis.md`
2. `docs/architecture/contacts-analysis.md`
3. `docs/domain/session-fingerprint-explained.md`
4. `docs/process/accelerate-multi-agent-team-os.md`

## 5. Run The Project

Backend:

```bash
cd backend
uv sync
uv run python manage.py migrate
uv run python manage.py runserver 8844
```

Frontends from repo root:

```bash
npm install
cd frontends/dashboard && npm run dev
cd frontends/landing && npm run dev
```

Or use:

```bash
make dev
make dev-full
```

## 6. Validate Safely

Backend:

```bash
cd backend
uv run python manage.py check
uv run pytest
```

Focused capture regression:

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

Frontend builds from repo root:

```bash
npm run build --workspace=@launch/dashboard
npm run build --workspace=@launch/landing
```

## 7. Operational Commands Worth Knowing

```bash
cd backend

uv run python manage.py sync_legacy_capture_pages --dry-run
uv run python manage.py check_capture_page_readiness --strict
uv run python manage.py check_lead_integration_health
uv run python manage.py requeue_failed_lead_integrations --dry-run
uv run python manage.py repair_lead_integration_payloads --dry-run
```

## 8. Repo Hygiene Rules

- generated frontend static output under `backend/src/static/**` is not tracked
- `docs/` is for internal project docs
- `frontends/docusaurus/docs/` is for navigable feature docs
- treat archived docs as historical context, not current source of truth

## 9. Commit Trail To Understand The Recent Evolution

Read `CHANGELOG.md` first, then inspect the recent commits if needed.
