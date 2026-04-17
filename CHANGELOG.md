# Changelog

All notable changes to this repository should be tracked here.

## 2026-04 - Repository Reorganization And Lead Capture Hardening

### Added
- `backend/` as the dedicated backend root
- `docs/` as the internal project documentation root
- feature-oriented lead capture docs under `frontends/docusaurus/docs/`
- `CaptureIntent` prelead model
- `LeadIntegrationOutbox` durable delivery model
- `LeadCaptureIdempotencyKey` for submit replay safety
- admin visibility for outbox and idempotency records
- operational commands for:
  - syncing legacy capture pages
  - readiness checks
  - outbox health checks
  - failed integration requeue
  - incomplete payload repair

### Changed
- capture submit flow consolidated under `CaptureService.complete_capture()`
- valid capture now guarantees `CaptureSubmission`
- `capture-intent` no longer creates final contact channels on blur
- `n8n` and `meta_capi` delivery moved behind outbox workers
- runtime JSON fallback is now controlled by `LANDING_JSON_FALLBACK_ENABLED`
- root docs moved into categorized `docs/`
- generated frontend static assets are no longer tracked in git

### Refactored
- removed legacy private onboarding flow from `identity` / dashboard paths
- formalized special public content flows in landing
- clarified documentation surfaces:
  - `docs/` for internal architecture/process/runbooks
  - `frontends/docusaurus/docs/` for navigable feature docs

### Operational Defaults
- outbox SLO targets:
  - `n8n`: 10 minutes
  - `meta_capi`: 15 minutes

### Validation
- focused backend capture suite passing
- Django system checks passing
- dashboard and landing builds passing during the hardening/reorg work
