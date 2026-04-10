# Kilo Code Ecosystem Suggestions

Este documento contém sugestões de **Custom Modes** e **Rules** para cobrir completamente o ecossistema tecnológico dos projetos Django + Inertia + React.

## Tech Stack Identificado

### Backend (Python/Django)
- Django 6.0.2+
- PostgreSQL (psycopg3)
- Celery + Redis (background tasks)
- django-allauth + PyJWT + pyotp (auth)
- Stripe + dj-stripe (payments)
- django-ses (email via AWS SES)
- django-storages + S3 (file storage)
- django-unfold (admin)
- django-structlog + Sentry (observability)
- facebook-business (Meta CAPI)
- Channels + Daphne (WebSockets)

### Frontend (TypeScript/React)
- React 19
- HeroUI v3 beta (compound components)
- Tailwind CSS v4
- Inertia.js 2.x
- i18next (pt/en/es)
- FingerprintJS Pro
- Stripe React SDK

### DevOps
- Docker + Docker Compose
- uv (Python package manager)
- npm (Node package manager)
- pytest + factory_boy
- vitest + testing-library

---

## Modos Existentes (5)

| Slug | Nome | Foco |
|------|------|------|
| `django-backend` | Django Backend | Django services, models, views, tasks |
| `react-frontend` | React Frontend | React components, hooks, pages |
| `security-review` | Security Reviewer | OWASP audits, vulnerabilities |
| `test-engineer` | Test Engineer | pytest, vitest, TDD |
| `docs-writer` | Doc Writer | Documentation, READMEs |

---

## Modos Sugeridos para Adicionar

### 1. `stripe-billing` - Stripe/Billing Expert
**Quando usar**: Implementação de checkout, subscriptions, webhooks, dunning flows, portal de billing.

```yaml
- slug: stripe-billing
  name: "Stripe Billing"
  roleDefinition: >-
    You are a Stripe integration expert specializing in dj-stripe, Stripe
    Checkout, Subscriptions, Customer Portal, and webhook handling. You
    understand PCI compliance, idempotency, and proper error handling for
    payment flows. You know the dj-stripe sync patterns and how to use
    Stripe models as source of truth.
  whenToUse: >-
    Use for Stripe Checkout integration, subscription management, webhook
    handlers, billing portal, dunning flows, or any payment-related code.
  customInstructions: |
    - dj-stripe is source of truth for subscription data
    - Use stripe.Customer, stripe.Subscription from dj-stripe models
    - Webhooks must be idempotent (check stripe event IDs)
    - Test with Stripe CLI: stripe listen --forward-to localhost:8000
    - Handle CustomerPortal returns with proper redirect URLs
    - Use Stripe test mode keys for development
    - Financial operations need select_for_update()
  groups:
    - read
    - edit
    - command
    - mcp
```

### 2. `celery-tasks` - Celery Task Expert
**Quando usar**: Background tasks, scheduled jobs, task chains, error handling.

```yaml
- slug: celery-tasks
  name: "Celery Tasks"
  roleDefinition: >-
    You are a Celery expert specializing in Django-Celery integration,
    task design, retry strategies, task chains/groups, and monitoring.
    You understand Redis as broker/backend and django-celery-beat for
    scheduled tasks. You know how to handle task failures gracefully.
  whenToUse: >-
    Use for creating background tasks, scheduled jobs, task chains,
    retry logic, or debugging Celery issues.
  customInstructions: |
    - Pass PKs to tasks, not model instances (serialization)
    - Use @shared_task(bind=True) for retry access
    - Set max_retries and default_retry_delay
    - Use exponential backoff for external API calls
    - Group related tasks in domains/*/tasks/ directories
    - Monitor with flower: celery -A config flower
    - Test tasks with CELERY_TASK_ALWAYS_EAGER=True
  groups:
    - read
    - edit
    - command
```

### 3. `i18n-localization` - Internationalization Expert
**Quando usar**: Tradução, locales, i18next, Django gettext.

```yaml
- slug: i18n-localization
  name: "i18n Expert"
  roleDefinition: >-
    You are an internationalization expert for Django + React apps.
    You know django.utils.translation for backend, i18next for frontend,
    and how to manage JSON translation files. You understand locale
    detection, plural forms, and interpolation patterns.
  whenToUse: >-
    Use for adding translations, managing locale files, fixing i18n issues,
    or auditing missing translations.
  customInstructions: |
    - Frontend: all strings via useTranslation hook
    - Backend: all user-facing strings via err(key, message)
    - Translation files: public/locales/{lang}/translation.json
    - Use t('namespace:key') pattern
    - Check for hardcoded strings: grep for plain English in components
    - Support pt, en, es locales minimum
    - Use {{count}} for pluralization
  groups:
    - read
    - edit
```

### 4. `devops-infra` - DevOps/Infrastructure Expert
**Quando usar**: Docker, deploy, CI/CD, environment setup.

```yaml
- slug: devops-infra
  name: "DevOps Infra"
  roleDefinition: >-
    You are a DevOps engineer specializing in Docker, docker-compose,
    deployment pipelines, and infrastructure management. You understand
    Django deployment patterns, Nginx/Caddy configuration, and
    environment variable management.
  whenToUse: >-
    Use for Docker configuration, deployment scripts, CI/CD pipelines,
    environment setup, or infrastructure debugging.
  customInstructions: |
    - Use docker-compose for local development
    - Environment vars via .env (never commit secrets)
    - Use multi-stage Docker builds for smaller images
    - Configure ALLOWED_HOSTS, CSRF, CORS properly
    - Use WhiteNoise for static files in production
    - Set up health check endpoints
    - Configure proper logging for production
  groups:
    - read
    - edit
    - command
```

### 5. `observability` - Monitoring/Observability Expert
**Quando usar**: Logs, Sentry, métricas, debugging em produção.

```yaml
- slug: observability
  name: "Observability"
  roleDefinition: >-
    You are an observability expert specializing in structured logging
    (structlog), error tracking (Sentry), and monitoring. You know how
    to add meaningful context to logs, set up Sentry integrations, and
    debug production issues.
  whenToUse: >-
    Use for setting up logging, Sentry integration, debugging production
    issues, or improving observability.
  customInstructions: |
    - Use structlog for structured JSON logs
    - Add context with structlog.contextvars
    - Sentry: capture_exception() for errors, capture_message() for info
    - Tag Sentry events with user context
    - Use log levels appropriately (debug/info/warning/error)
    - Don't log sensitive data (passwords, tokens, PII)
    - Add request_id to all logs for tracing
  groups:
    - read
    - edit
    - command
```

### 6. `meta-capi` - Meta Conversions API Expert
**Quando usar**: Tracking de conversões, Facebook Pixel, Meta CAPI.

```yaml
- slug: meta-capi
  name: "Meta CAPI"
  roleDefinition: >-
    You are a Meta Conversions API expert specializing in server-side
    event tracking for Facebook/Meta advertising. You understand the
    facebook-business SDK, event deduplication, and privacy compliance
    (LGPD/GDPR) for tracking.
  whenToUse: >-
    Use for implementing Meta CAPI events, conversion tracking, or
    debugging Facebook Pixel integration.
  customInstructions: |
    - Use facebook-business SDK for server-side events
    - Always deduplicate with event_id (match browser pixel)
    - Hash user data (email, phone) with SHA256
    - Required fields: event_name, event_time, action_source
    - Test with Meta Events Manager Test Events
    - Respect user consent preferences (LGPD/GDPR)
    - Send events async via Celery tasks
  groups:
    - read
    - edit
```

### 7. `fingerprint-tracking` - FingerprintJS Expert
**Quando usar**: Device fingerprinting, fraud detection, visitor tracking.

```yaml
- slug: fingerprint-tracking
  name: "Fingerprint Expert"
  roleDefinition: >-
    You are a FingerprintJS Pro expert specializing in device identification,
    visitor tracking, and fraud detection. You understand the FingerprintJS
    Pro SDK, confidence scores, and privacy-respecting implementation.
  whenToUse: >-
    Use for FingerprintJS integration, device tracking, visitor
    identification, or fraud detection features.
  customInstructions: |
    - Use @fingerprintjs/fingerprintjs-pro SDK
    - Store visitorId and requestId on backend
    - Check confidence score for reliability
    - Link fingerprints to user accounts on login
    - Use for device attribution, not PII replacement
    - Handle Pro API rate limits appropriately
    - Store fingerprint data with proper consent
  groups:
    - read
    - edit
    - command
```

---

## Rules Existentes (6 globais + 4 mode-specific)

### Globais (rules/)
1. `code-style.md` — Python/TypeScript formatting
2. `django-inertia-stack.md` — 5-Level Soft-DDD architecture
3. `django-vite-patterns.md` — Asset pipeline
4. `heroui-react-patterns.md` — HeroUI v3 components
5. `infrastructure-patterns.md` — Celery, Redis, Stripe
6. `security-patterns.md` — IDOR, CSRF, timing attacks

### Mode-specific
- `rules-architect/` — architecture-rules.md
- `rules-code/` — backend-rules.md, frontend-rules.md
- `rules-debug/` — debug-rules.md
- `rules-security-review/` — security-rules.md

---

## Rules Sugeridas para Adicionar

### 1. `rules/stripe-patterns.md` - Stripe Best Practices

```markdown
# Stripe Integration Patterns

## dj-stripe as Source of Truth
- NEVER duplicate Stripe data in custom models
- Use dj-stripe models (Customer, Subscription, Price)
- Sync happens via webhooks automatically

## Webhook Handling
- Verify webhook signatures (DJSTRIPE_WEBHOOK_SECRET)
- Idempotent handlers (check stripe_event_id)
- Process webhooks async when possible

## Checkout Flow
- Create Checkout Session server-side
- Redirect to session.url
- Handle success/cancel URLs with proper state

## Customer Portal
- Use Stripe.BillingPortal.create() for customer self-service
- Configure allowed actions in Stripe Dashboard

## Testing
- Use Stripe CLI: stripe listen --forward-to
- Test cards: 4242... (success), 4000... (decline)
```

### 2. `rules/celery-patterns.md` - Celery Best Practices

```markdown
# Celery Task Patterns

## Task Design
- Pass PKs, not model instances
- Use @shared_task(bind=True) for retry access
- Set max_retries and default_retry_delay

## Retry Strategies
- Use exponential backoff for external APIs
- Set reasonable max_retries (3-5)
- Handle permanent failures gracefully

## Task Organization
- Group in domains/*/tasks/
- One task per file when complex
- Name descriptively: send_welcome_email

## Monitoring
- Use flower for real-time monitoring
- Log task start/complete/fail
- Set up Sentry for task errors

## Testing
- CELERY_TASK_ALWAYS_EAGER=True in tests
- Mock external services
- Test retry behavior
```

### 3. `rules/i18n-patterns.md` - Internationalization Patterns

```markdown
# Internationalization Patterns

## Frontend (i18next)
- All user-facing strings via useTranslation hook
- Use t('namespace:key') pattern
- Interpolation: t('key', { count: 5 })
- Files: public/locales/{lang}/translation.json

## Backend (Django)
- User-facing errors via err(key, message)
- backendErrors.* namespace for error keys
- Interpolation via **params

## Translation Files
- Keep keys hierarchical (auth.login.title)
- Use descriptive key names
- Include all 3 locales: pt, en, es

## Auditing
- grep for hardcoded strings in components
- Check for missing keys in all locales
- Test with each locale active
```

### 4. `rules/meta-capi-patterns.md` - Meta CAPI Patterns

```markdown
# Meta Conversions API Patterns

## Event Structure
- event_name: PageView, Lead, Purchase, etc.
- event_time: Unix timestamp
- action_source: website (server-side)
- event_id: for deduplication with Pixel

## User Data Hashing
- SHA256 hash all PII before sending
- Fields: email, phone, first_name, last_name
- Normalize before hashing (lowercase, trim)

## Privacy Compliance
- Only send events with user consent
- Respect LGPD/GDPR preferences
- Allow users to opt out

## Implementation
- Send events via Celery tasks (async)
- Use facebook-business SDK
- Test with Meta Events Manager
```

### 5. `rules/observability-patterns.md` - Observability Patterns

```markdown
# Observability Patterns

## Structured Logging (structlog)
- Use structlog.get_logger()
- Add context: user_id, request_id
- JSON format for production

## Log Levels
- DEBUG: Development details
- INFO: Normal operations
- WARNING: Recoverable issues
- ERROR: Failures needing attention

## Sentry Integration
- capture_exception() in except blocks
- Add user context: set_user()
- Tag events for filtering

## Request Tracing
- Add request_id middleware
- Include in all logs
- Pass to downstream services
```

### 6. `rules/fingerprint-patterns.md` - FingerprintJS Patterns

```markdown
# FingerprintJS Pro Patterns

## Client-Side
- Initialize with FingerprintJS.load()
- Get visitorId and requestId
- Send to backend with form submissions

## Server-Side
- Store visitorId in capture events
- Link to user on authentication
- Query by visitorId for attribution

## Confidence Handling
- confidence.score > 0.9 = high confidence
- Lower scores may be VPN/proxy users
- Don't rely solely on fingerprint for auth

## Privacy
- Inform users about fingerprinting
- Store with proper consent
- Allow deletion on request
```

---

## Skills Existentes Relevantes

Já disponíveis em `~/.kilocode/skills/`:

| Skill | Propósito |
|-------|-----------|
| `billing-automation` | Billing system automation |
| `billing-delinquent-pattern` | Delinquent user handling |
| `heroui-v3` | HeroUI v3 patterns |
| `planning-with-files` | Manus-style planning |
| `workflow-orchestration-patterns` | Temporal/saga patterns |
| `docker-expert` | Docker best practices |
| `prisma-expert` | Prisma ORM (not used here) |

---

## Skills Sugeridas para Criar

1. **`django-service-layer`** — Deep dive no padrão de service layer
2. **`inertia-forms`** — Patterns específicos de useForm + server validation
3. **`stripe-webhooks`** — Webhook handling best practices
4. **`celery-monitoring`** — Flower, monitoring, debugging
5. **`meta-capi-events`** — Full Meta CAPI implementation guide

---

## Resumo de Ações

### Implementar Agora (High Priority)
1. [ ] Adicionar mode `stripe-billing`
2. [ ] Adicionar mode `celery-tasks`
3. [ ] Criar rule `stripe-patterns.md`
4. [ ] Criar rule `celery-patterns.md`

### Implementar Depois (Medium Priority)
5. [ ] Adicionar mode `i18n-localization`
6. [ ] Adicionar mode `observability`
7. [ ] Criar rule `i18n-patterns.md`
8. [ ] Criar rule `observability-patterns.md`

### Nice to Have (Low Priority)
9. [ ] Adicionar mode `devops-infra`
10. [ ] Adicionar mode `meta-capi`
11. [ ] Adicionar mode `fingerprint-tracking`
12. [ ] Criar rules adicionais

---

*Documento gerado em 2026-02-23 para o projeto launch-inertia*
