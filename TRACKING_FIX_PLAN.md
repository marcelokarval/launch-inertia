# TRACKING FIX PLAN — Data Flow + Dashboard + Identity

> Created: 2026-02-20
> Status: IN PROGRESS
> Commits: (will be updated as we go)

## Context

The tracking system has solid architecture (26 models, middleware chain, identity resolution)
but data does NOT flow to persistent entities. The database has 6 anonymous Identities with
zero ContactEmails, zero ContactPhones, zero FingerprintIdentities, zero CaptureSubmissions.

Root causes:
1. `capture-intent` saves hints ONLY in Django session (cache-backed Redis, volatile)
2. Without `form_success`, identity resolution pipeline never runs
3. FingerprintJS Pro not creating FingerprintIdentity records in DB
4. Session engine is cache-only — Redis restart loses ALL sessions
5. CaptureEvents for intents record `identity=None` and wrong `page_path`

## Phases

### P0 — Critical Bugs (quick fixes)

- [x] P0.1: Fix `{{total}}` i18n mismatch in Identity Index (`count` → `total`)
- [x] P0.2: Fix DailyTrendChart tooltip invisible in dark mode (add `color` to contentStyle)
- [x] P0.3: Fix capture_intent view — use Referer for page_path, link identity from middleware

### P1 — Data Persistence (make data flow)

- [x] P1.1: Migrate SESSION_ENGINE from `cache` to `cached_db` (cache + DB fallback)
- [x] P1.2: capture-intent creates ContactEmail/ContactPhone with lifecycle_status=pending
- [x] P1.3: capture-intent runs bind_events_to_identity retroactively
- [x] P1.4: Fix use-capture-intent.ts — separate debounce timers per field, send both hints together
- [x] P1.5: Debug FingerprintJS — verified code is correct, issue is FINGERPRINT_API_KEY not set in .env

### P2 — Dashboard Analytics Enhancements

- [x] P2.1: Add unique_visitors to get_overview_stats() (StatCards: show total + unique views)
- [x] P2.2: Add unique_visitors to get_daily_trend() (DailyTrendChart: 3rd line)
- [x] P2.3: Add unique_visitors to get_top_capture_pages() (TopPagesTable: new column)
- [x] P2.4: Update TypeScript types for new analytics fields
- [x] P2.5: Update frontend components (StatCards, DailyTrendChart, TopPagesTable)

### P3 — Identity Detail Improvements

- [ ] P3.1: Add "Overview" tab as default in Identity Show with stats + hints + activity
- [ ] P3.2: Timeline includes CaptureEvents for the identity (not just FingerprintEvents)
- [ ] P3.3: Show intent hints (email_domain, phone_prefix) when identity has no contacts
- [ ] P3.4: Fix N+1 queries in Identity Index (annotate + prefetch_related)
- [ ] P3.5: Move display_name, operator_notes, tags into Identity.to_dict()

### P4 — Session-Identity Binding

- [ ] P4.1: Evaluate django-user-sessions vs current IdentitySessionMiddleware approach
- [ ] P4.2: Implement session history tracking on Identity (store visit count, pages visited)

## Verification Checklist

After each phase:
- [x] `npx tsc --noEmit` (non-test): 0 errors
- [x] `uv run npx pyright src/`: 0/0/0
- [x] `uv run pytest src/tests/ --no-migrations -x -q`: 605 passed, 2 skipped, 0 failed
- [ ] Manual test: visit capture page, fill form, check dashboard + identity detail
