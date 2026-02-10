# CLAUDE.md - Launch Inertia Project

## Project Overview

Full-stack Django + Inertia.js + React application for launch management platform.

### Tech Stack

- **Backend**: Django 6.0.2+, PostgreSQL, Redis, Celery
- **Frontend**: React 19, Vite 7.3+, TypeScript, HeroUI v3 beta.6+, Tailwind CSS v4
- **Bridge**: Inertia.js v2 (inertia-django)
- **Auth**: Custom services (login/register) + django-allauth (Google OAuth only)
- **Billing**: Stripe via dj-stripe
- **Admin**: django-unfold
- **i18n**: i18next (pt/en/es), PT default

### Ports

- Django dev: **8844**
- Vite dev: **3344**

---

## Critical Knowledge

### Inertia.js + Django Integration

**SEMPRE consulte a skill antes de implementar**: `.claude/skills/inertia-django/SKILL.md`

#### Regras OBRIGATÓRIAS

1. **Form Submission**: SEMPRE use `forceFormData: true`
   ```typescript
   post('/url/', { forceFormData: true })
   ```

2. **Login Form**: Use campo `username` (não `email`)
   ```typescript
   useForm({ username: '', password: '' })
   ```

3. **CSRF**: Cookie = `XSRF-TOKEN`, Header = `X-XSRF-TOKEN`, `HTTPONLY=False`. Inertia.js v2 (Axios) lê o cookie e envia automaticamente.

4. **useAppForm hook**: Wrapper around `useForm` that auto-applies `forceFormData: true`

5. **request.data (NÃO request.POST)**: Todas as views DEVEM usar `request.data` para ler dados do request. `InertiaJsonParserMiddleware` unifica JSON e form-encoded em `request.data`. NUNCA use `request.POST` diretamente.
   ```python
   # CORRETO
   name = request.data.get("name", "")
   form = MyForm(request.data)
   
   # PROIBIDO
   name = request.POST.get("name", "")  # NÃO!
   ```

---

## Project Structure

```
launch-inertia/
├── src/                         # Django backend
│   ├── apps/
│   │   ├── identity/            # Auth, users, profiles
│   │   │   ├── models.py        # User, Profile
│   │   │   ├── models/          # UserToken, EmailVerificationToken
│   │   │   ├── services/        # AuthService, RegistrationService, TokenService, SetupStatusService
│   │   │   ├── views.py         # Auth + onboarding views
│   │   │   ├── tasks.py         # Email tasks (Celery)
│   │   │   └── signals.py       # user_registered, email_verified
│   │   ├── contacts/            # CRM
│   │   │   ├── services/        # ContactService(BaseService[Contact])
│   │   │   └── views.py
│   │   ├── billing/             # Stripe (no custom models, uses djstripe)
│   │   │   ├── services/        # BillingService (classmethods)
│   │   │   ├── signals/         # Webhook signal receivers
│   │   │   └── views.py
│   │   └── notifications/       # In-app alerts
│   │       ├── services/        # NotificationService(BaseService[Notification])
│   │       └── tasks.py         # cleanup_old_notifications
│   ├── config/
│   │   ├── environment.py       # Env loading helpers
│   │   └── settings/
│   │       ├── base.py          # Main settings (FeatureFlags)
│   │       ├── flags.py         # FeatureFlags class
│   │       ├── development.py
│   │       ├── production.py
│   │       └── test_memory.py   # SQLite in-memory for tests
│   ├── core/
│   │   ├── inertia/             # InertiaJsonParserMiddleware, InertiaShareMiddleware, SetupStatusMiddleware, DelinquentMiddleware
│   │   ├── security/            # @require_ownership, SecurityEventDetector, SecurityHeaders, RateLimit
│   │   └── shared/
│   │       ├── models/          # BaseModel, mixins (PublicID, SoftDelete, Metadata, Timestamp)
│   │       └── services/        # BaseService[T] generic
│   ├── infrastructure/
│   │   ├── email/               # EmailService + EmailTemplate definitions
│   │   └── tasks/               # Celery app config
│   └── tests/                   # pytest test suite
│       ├── conftest.py -> ../conftest.py
│       ├── factories.py         # User, Profile, Contact, Tag, Notification factories
│       ├── test_identity_services.py
│       ├── test_contacts_service.py
│       ├── test_middleware.py
│       └── test_security.py
├── frontend/
│   └── src/
│       ├── components/ui/       # Button, InputField, PasswordInput, Card, FormErrorBanner, ThemeToggle, LanguageSelector
│       ├── hooks/               # useAppForm, useTheme
│       ├── layouts/             # AuthLayout, DashboardLayout, OnboardingLayout
│       ├── lib/                 # i18n config
│       ├── pages/
│       │   ├── Auth/            # Login, Register, ResetPassword
│       │   ├── Onboarding/      # VerifyEmail, Legal, ProfileCompletion, PlanSelection
│       │   ├── Dashboard/       # Index
│       │   ├── Contacts/        # Index, Show, Create, Edit, Delete
│       │   ├── Billing/         # Index
│       │   ├── Notifications/   # Index
│       │   ├── Settings/        # Index, Profile, Security
│       │   └── Delinquent.tsx
│       ├── tests/               # Vitest component tests
│       │   ├── setup.ts
│       │   ├── Button.test.tsx
│       │   ├── FormErrorBanner.test.tsx
│       │   └── InputField.test.tsx
│       └── types/               # TypeScript types (single source of truth)
│           ├── index.ts
│           └── inertia.d.ts
├── templates/
│   ├── base.html                # Inertia layout (django-vite)
│   └── emails/                  # Django email templates
│       ├── email_verification.{txt,html}
│       ├── password_reset.{txt,html}
│       └── welcome.{txt,html}
├── Makefile                     # Dev commands
├── .env.example                 # All env vars documented
├── pyproject.toml               # Python deps + pytest config
└── manage.py
```

---

## Development Commands

```bash
# Both servers in parallel
make dev

# Backend only (Django on port 8844)
make dev-back

# Frontend only (Vite on port 3344)
make dev-front

# Run all tests
make test

# Run backend tests only
make test-back

# Run frontend tests only
make test-front

# Database
make migrate
make makemigrations

# Celery
make celery
make celery-beat

# Install all deps
make install
```

---

## Architecture Decisions

### Service Layer

All business logic lives in services, views are thin HTTP dispatchers.

| App | Service | Pattern |
|-----|---------|---------|
| identity | AuthService | classmethod |
| identity | RegistrationService | classmethod |
| identity | TokenService | classmethod |
| identity | SetupStatusService | classmethod |
| contacts | ContactService | BaseService[Contact] instance |
| notifications | NotificationService | BaseService[Notification] instance |
| billing | BillingService | classmethod (Stripe wrapper) |

### User Model

Does NOT inherit BaseModel. Uses `PublicIDMixin + SoftDeleteMixin + MetadataMixin + AbstractUser` directly with its own `UserManager`.

### Billing

No custom models. Relies entirely on djstripe's `Customer`, `Subscription`, `Invoice`. Webhook signals in `billing/signals/`.

### Onboarding

4-step flow enforced by `SetupStatusMiddleware`:
1. Email verification
2. Legal (terms acceptance)
3. Profile completion
4. Plan selection

### Security

- `@require_ownership` decorator for IDOR prevention
- `SecurityEventDetector` for audit logging
- `SecurityHeadersMiddleware` + `RateLimitMiddleware` in MIDDLEWARE

### Frontend Types

`frontend/src/types/index.ts` is the **single source of truth**. Pages should never define local interfaces for backend data.

---

## Key Files

| File | Purpose |
|------|---------|
| `src/config/settings/base.py` | Django settings + FeatureFlags |
| `src/config/settings/flags.py` | FeatureFlags class (env-aware) |
| `src/core/inertia/middleware.py` | InertiaJsonParserMiddleware + shared data + guards |
| `src/core/security/decorators/ownership.py` | @require_ownership |
| `src/core/shared/services/base.py` | BaseService[T] generic |
| `src/apps/identity/services/` | Auth, Registration, Token services |
| `src/apps/identity/views.py` | Auth + onboarding views |
| `src/infrastructure/email/service.py` | EmailService (SES/console) |
| `frontend/src/main.tsx` | React entry point + i18n |
| `frontend/src/hooks/useAppForm.ts` | Form wrapper (forceFormData) |
| `frontend/src/types/index.ts` | All TypeScript types |

---

## Known Issues & Solutions

### 1. Form data not received by Django
**Cause**: Inertia sends JSON, Django expects form-encoded
**Solution**: Use `request.data` in views (provided by `InertiaJsonParserMiddleware`). Frontend uses `useAppForm` hook which applies `forceFormData: true`.

### 2. CSRF token errors
**Cause**: Misconfigured CSRF cookie/header names or origins
**Solution**: `CSRF_COOKIE_NAME="XSRF-TOKEN"`, `CSRF_HEADER_NAME="HTTP_X_XSRF_TOKEN"`, `CSRF_COOKIE_HTTPONLY=False`. Also ensure `CSRF_TRUSTED_ORIGINS` includes Django and Vite ports.

### 3. Login field validation error
**Cause**: AuthenticationForm expects `username` field
**Solution**: Frontend form must use `username` (not `email`)

### 4. LSP type errors in models
**Known pre-existing**: Django Meta/Manager typing incompatibilities in `identity/models.py`, `shared/models/base.py`, `notifications/consumers.py`, `billing/views.py`. They work at runtime. Do NOT fix.

---

## Skills

| Skill | Descrição |
|-------|-----------|
| `inertia-django` | Guia oficial Inertia.js + Django |

Location: `.claude/skills/inertia-django/SKILL.md`

---

*Last updated: 2026-02*
