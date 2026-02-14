# Frontend Architecture Analysis — Multi-Frontend Organization

> Gerado em: 2026-02-13
> Status: **DECIDIDO** — Nomenclatura definida, gaps mapeados

---

## Decisao final

```
src/           → Django backend (mantém)
frontends/     → NOVO parent directory
  dashboard/   → MOVER de frontend/ via git mv (dashboard operacional)
  landing/     → CRIAR DO ZERO como novo Vite+Inertia app (páginas públicas)
  shared/      → CRIAR DO ZERO na Fase H (código compartilhado entre frontends)
templates/     → 2 base templates (dashboard.html + landing.html)
```

### Operações de diretório (IMPORTANTE — evitar confusão)

| Diretório destino | Operação | Origem |
|-------------------|----------|--------|
| `frontends/dashboard/` | **`git mv frontend frontends/dashboard`** | O `frontend/` atual, que já funciona com Vite+Inertia. Preserva histórico git. |
| `frontends/landing/` | **Criar do zero** | Novo Vite+Inertia app. Componentes portados manualmente do legado `frontend-landing-pages/` como referência. NÃO é um "mover" — é reescrita para Inertia. |
| `frontends/shared/` | **Criar do zero na Fase H** | Só quando duplicação real entre dashboard e landing aparecer. Não extrair prematuramente. |
| `frontend-landing-pages/` | **Manter como referência de consulta** | Projeto Next.js legado. Fica na raiz como blueprint durante a migração. Removido quando Fase F estiver concluída. |

---

## O que temos hoje

| Pasta | O que é | Problema |
|-------|---------|----------|
| `src/` | Django backend | OK |
| `frontend/` | Dashboard administrativo (React+Vite+Inertia) | "frontend" é genérico — frontend de quem? |
| `frontend-landing-pages/` | Landing pages de captura (Next.js legado) | Precisa migrar para Vite+Inertia |
| `templates/base.html` | Template único Inertia | Precisa virar 2 templates |

---

## O cenário real

Temos **3 interfaces distintas**, cada uma com audiência, autenticação e propósito diferentes:

| Interface | Audiência | Auth | Propósito |
|-----------|-----------|------|-----------|
| Django Admin (unfold) | Devs/staff | Staff login | Gerenciamento de dados |
| Dashboard operacional | Equipe interna Agrelli | User login + setup flow | Gestão de lançamentos, identities, billing |
| Páginas públicas | Leads/visitantes | Nenhuma (fingerprint) | Captura, checkout, obrigado, vendas, CPL, suporte pré-compra |

Cada frontend é um **container Docker** potencial com réplicas independentes.

---

## Estrutura aprovada

```
launch-inertia/
├── src/                              # Django backend
│   ├── apps/
│   │   ├── identity/                 # Auth, users, profiles
│   │   ├── contacts/                 # CRM (identities)
│   │   ├── billing/                  # Stripe via dj-stripe
│   │   └── notifications/            # In-app alerts
│   ├── config/
│   │   └── settings/
│   │       └── base.py               # DJANGO_VITE com 2 keys: "dashboard" + "landing"
│   ├── core/
│   ├── infrastructure/
│   └── static/
│       ├── dashboard/                 # Build output do frontends/dashboard/
│       │   └── .vite/manifest.json
│       └── landing/                   # Build output do frontends/landing/
│           └── .vite/manifest.json
│
├── frontends/                         # Pai de TODOS os frontends React
│   ├── dashboard/                     # Interface do operador (atual frontend/)
│   │   ├── src/
│   │   │   ├── pages/
│   │   │   ├── layouts/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── types/
│   │   │   └── main.tsx               # Entry point → createInertiaApp
│   │   ├── public/locales/
│   │   ├── package.json               # name: "@launch/dashboard"
│   │   ├── vite.config.ts             # port 3344, outDir → src/static/dashboard/
│   │   └── tsconfig.json
│   │
│   ├── landing/                       # Interface pública (migração do Next.js)
│   │   ├── src/
│   │   │   ├── pages/                 # Capture, Checkout, ThankYou, Sales, CPL
│   │   │   ├── layouts/               # LandingLayout, CheckoutLayout
│   │   │   ├── components/            # CaptureForm, PhoneInput, StripeCheckout
│   │   │   ├── hooks/                 # useFingerprint, useCaptureForm
│   │   │   ├── types/
│   │   │   └── main.tsx               # Entry point → createInertiaApp (resolve separado)
│   │   ├── public/
│   │   ├── package.json               # name: "@launch/landing"
│   │   ├── vite.config.ts             # port 3345, outDir → src/static/landing/
│   │   └── tsconfig.json
│   │
│   └── shared/                        # Código compartilhado entre frontends
│       ├── src/
│       │   ├── components/ui/         # Design system base (HeroUI wrappers)
│       │   ├── hooks/                 # useTheme, formatters
│       │   ├── utils/                 # Validators, helpers
│       │   └── types/                 # Tipos TypeScript compartilhados
│       ├── package.json               # name: "@launch/shared"
│       └── tsconfig.json
│
├── templates/
│   ├── dashboard.html                 # {% vite_asset 'src/main.tsx' app="dashboard" %}
│   ├── landing.html                   # {% vite_asset 'src/main.tsx' app="landing" %}
│   └── emails/                        # Email templates (mantém)
│
├── package.json                       # Workspace root: ["frontends/*"]
├── docker-compose.yml
├── Makefile
├── pyproject.toml
└── manage.py
```

---

## Por que estes nomes

| Nome | Razão |
|------|-------|
| **`frontends/`** (plural) | Indica claramente que há múltiplos. Escala para `frontends/partner/`, `frontends/courses/` no futuro. Sem ambiguidade em PT-BR (diferente de `clients/` que confunde com "cliente da empresa") |
| **`dashboard/`** | Universalmente entendido como "interface de gestão logada". Não colide com Django admin (`/admin/`) |
| **`landing/`** | "Onde os leads aterram" — cobre captura, checkout, obrigado, vendas, CPL, suporte pré-compra. Tudo público, sem conceito de pessoa logada |
| **`shared/`** | Código compartilhado: design system, hooks, types, utils. Evita duplicação entre dashboard e landing |

---

## Por que NÃO outros nomes

| Rejeitado | Problema |
|-----------|---------|
| `frontend/` (singular) | Ambíguo quando há múltiplos |
| `frontend-admin/` | "admin" colide com Django admin. Prefixo repetitivo |
| `clients/` | Em PT-BR "cliente" remete a cliente da empresa, não client application |
| `web/` | O prop4you usa `interfaces/web/` para views Django, não JS |
| `portal/` | Implica login obrigatório — não encaixa nas landing pages |
| `site/` | Vago, pode confundir com `django.contrib.sites` |
| `public/` | Colide com `public/` dentro de cada projeto React |
| `capture/` | Muito específico — as landing pages também têm checkout, sales page, CPL |

---

## Consistência cross-layer

O mesmo nome aparece em **todas** as camadas:

| Camada | Dashboard | Landing |
|--------|-----------|---------|
| Client code | `frontends/dashboard/` | `frontends/landing/` |
| Vite config key | `DJANGO_VITE["dashboard"]` | `DJANGO_VITE["landing"]` |
| Django template | `templates/dashboard.html` | `templates/landing.html` |
| INERTIA_LAYOUT | `"dashboard.html"` | `"landing.html"` |
| Static build | `src/static/dashboard/` | `src/static/landing/` |
| Vite dev port | 3344 | 3345 |
| Docker service | `vite-dashboard` | `vite-landing` |
| npm package | `@launch/dashboard` | `@launch/landing` |
| Makefile target | `dev-dashboard` | `dev-landing` |
| URL prefix | `/app/*` (autenticado) | `/*` (público) |

---

## Configuração Django-Vite (multi-app)

```python
# src/config/settings/base.py

_VITE_DEV_HOST = "localhost"

def _detect_vite_dev_mode(port: int) -> bool:
    """Auto-detect se o Vite dev server está rodando na porta especificada."""
    explicit = os.getenv("DJANGO_VITE_DEV_MODE", "").lower()
    if explicit in ("true", "1", "yes"):
        return True
    if explicit in ("false", "0", "no"):
        return False
    if not is_development():
        return False
    import socket
    try:
        with socket.create_connection((_VITE_DEV_HOST, port), timeout=0.1):
            return True
    except (ConnectionRefusedError, OSError, TimeoutError):
        return False

DJANGO_VITE = {
    "dashboard": {
        "dev_mode": _detect_vite_dev_mode(port=3344),
        "dev_server_protocol": "http",
        "dev_server_host": _VITE_DEV_HOST,
        "dev_server_port": 3344,
        "static_url_prefix": "dashboard",
        "manifest_path": SRC_DIR / "static" / "dashboard" / ".vite" / "manifest.json",
    },
    "landing": {
        "dev_mode": _detect_vite_dev_mode(port=3345),
        "dev_server_protocol": "http",
        "dev_server_host": _VITE_DEV_HOST,
        "dev_server_port": 3345,
        "static_url_prefix": "landing",
        "manifest_path": SRC_DIR / "static" / "landing" / ".vite" / "manifest.json",
    },
}
```

---

## Configuração Inertia (multi-layout)

```python
# O INERTIA_LAYOUT padrão é usado pelo dashboard.
# As views de landing precisam especificar template_name explicitamente.
INERTIA_LAYOUT = "dashboard.html"

# Nas views de landing:
# from inertia import render as inertia_render
# return inertia_render(request, "Capture/Index", props={...}, template_name="landing.html")
```

**Alternativa**: Usar middleware que detecta o URL prefix e seta o layout automaticamente:

```python
class InertiaLayoutMiddleware:
    """Auto-set INERTIA_LAYOUT based on URL prefix."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/app/'):
            request.inertia_layout = 'dashboard.html'
        else:
            request.inertia_layout = 'landing.html'
        return self.get_response(request)
```

---

## Templates

### dashboard.html
```html
{% load django_vite %}
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title inertia>{% block title %}Launch{% endblock %}</title>

    {# Theme initialization #}
    <script>
    (function(){
      try {
        var t = localStorage.getItem('launch-theme');
        var isDark = t === 'dark' || (t !== 'light' && window.matchMedia('(prefers-color-scheme: dark)').matches);
        if (isDark) document.documentElement.classList.add('dark');
      } catch(e) {}
    })();
    </script>

    {% load static %}
    <link rel="icon" type="image/svg+xml" href="{% static 'favicon.svg' %}">
    <link rel="preconnect" href="https://fonts.bunny.net">
    <link href="https://fonts.bunny.net/css?family=inter:400,500,600,700&display=swap" rel="stylesheet" />

    {% vite_hmr_client app="dashboard" %}
    {% vite_react_refresh app="dashboard" %}
    {% vite_asset "src/main.tsx" app="dashboard" %}

    {% block inertia_head %}{% endblock %}
</head>
<body class="min-h-screen bg-background font-sans antialiased">
    {% block inertia %}{% endblock %}
</body>
</html>
```

### landing.html
```html
{% load django_vite %}
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title inertia>{% block title %}Arthur Agrelli{% endblock %}</title>

    {% load static %}
    <link rel="icon" type="image/png" href="{% static 'favicon.png' %}">

    {# Fonts otimizadas para landing #}
    <link rel="preconnect" href="https://fonts.bunny.net">
    <link href="https://fonts.bunny.net/css?family=inter:400,500,600,700,800&display=swap" rel="stylesheet" />

    {% vite_hmr_client app="landing" %}
    {% vite_react_refresh app="landing" %}
    {% vite_asset "src/main.tsx" app="landing" %}

    {# Analytics (landing only) #}
    {% block analytics %}{% endblock %}
    {% block inertia_head %}{% endblock %}
</head>
<body>
    {% block inertia %}{% endblock %}

    {# Tracking scripts (landing only) #}
    {% block tracking %}{% endblock %}
</body>
</html>
```

---

## Mapeamento de URLs Django

```python
# config/urls.py
urlpatterns = [
    # Django Admin (unfold)
    path("admin/", admin.site.urls),

    # Landing pages públicas — raiz do domínio
    path("", include("apps.landing.urls")),

    # Dashboard operacional — prefixo /app/
    path("app/", include("apps.identity.urls")),
    path("app/identities/", include("apps.contacts.urls")),
    path("app/billing/", include("apps.billing.urls")),
    path("app/notifications/", include("apps.notifications.urls")),

    # External integrations
    path("accounts/", include("allauth.urls")),
    path("stripe/", include("djstripe.urls", namespace="djstripe")),
]
```

**Nota**: O prefixo `/app/` separa claramente rotas autenticadas das públicas. Middleware de auth pode targetar `/app/*` com precisão.

---

## Docker

```yaml
services:
  django:           # Serve ambos os frontends (builds estáticos em prod)
    ports: ["8844:8844"]

  vite-dashboard:   # Dev only — HMR port 3344
    command: npm run dev
    working_dir: /app/frontends/dashboard
    ports: ["3344:3344"]

  vite-landing:     # Dev only — HMR port 3345
    command: npm run dev
    working_dir: /app/frontends/landing
    ports: ["3345:3345"]

  postgres:
    ports: ["5432:5432"]

  redis:
    ports: ["6379:6379"]

  celery-worker:
  celery-beat:
```

---

## Makefile

```makefile
dev:            ## Django + Dashboard + Landing (parallel)
	@trap 'kill 0' EXIT; \
	$(MAKE) dev-back & \
	$(MAKE) dev-dashboard & \
	$(MAKE) dev-landing & \
	wait

dev-back:       ## Django dev server (port 8844)
	cd src && uv run python ../manage.py runserver 8844

dev-dashboard:  ## Dashboard Vite dev server (port 3344)
	cd frontends/dashboard && npm run dev

dev-landing:    ## Landing Vite dev server (port 3345)
	cd frontends/landing && npm run dev

install:        ## Install all dependencies
	uv pip install -e ".[dev]" && npm install

install-front:  ## Install all frontend dependencies
	npm install

build:          ## Build all frontends for production
	npm -w @launch/shared run build && npm -ws run build

test:           ## Run all tests
	$(MAKE) test-back && $(MAKE) test-front

test-back:
	cd src && uv run python -m pytest

test-front:
	npm -ws run test -- --run
```

---

## npm workspaces (root package.json)

```json
{
  "private": true,
  "workspaces": [
    "frontends/*"
  ],
  "scripts": {
    "dev:dashboard": "npm -w @launch/dashboard run dev",
    "dev:landing": "npm -w @launch/landing run dev",
    "build": "npm -w @launch/shared run build && npm -w @launch/dashboard run build && npm -w @launch/landing run build",
    "build:dashboard": "npm -w @launch/dashboard run build",
    "build:landing": "npm -w @launch/landing run build"
  }
}
```

---

## CORS (atualizar em base.py)

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8844",
    "http://127.0.0.1:8844",
    "http://localhost:3344",   # Dashboard Vite
    "http://127.0.0.1:3344",
    "http://localhost:3345",   # Landing Vite
    "http://127.0.0.1:3345",
]
```

---

## Gaps identificados e resoluções

### GAP 1: `vite_dev_mode` hardcoded como `is_development()`

**Atual** ([flags.py:180-181](src/config/settings/flags.py#L180-L181)):
```python
@property
def vite_dev_mode(self) -> bool:
    return is_development()
```

**Problema**: Se estiver em dev mas sem Vite rodando, Django tenta conectar ao Vite e a página fica em branco. O doc global `django-vite-patterns.md` proíbe este padrão.

**Resolução**: Substituir por auto-detecção TCP (já documentado acima em `_detect_vite_dev_mode`). A nova config usa detecção por porta, uma para cada frontend.

---

### GAP 2: `INERTIA_LAYOUT` é singleton

**Atual** ([base.py:271](src/config/settings/base.py#L271)):
```python
INERTIA_LAYOUT = "base.html"
```

**Problema**: Com dois frontends, cada um precisa de um template diferente. A lib `inertia-django` usa `INERTIA_LAYOUT` como default global.

**Resolução**: Opções (em ordem de preferência):
1. **`template_name` por view**: Cada view de landing passa `template_name="landing.html"` explicitamente. Dashboard usa o default.
2. **Middleware de layout**: Middleware que detecta URL prefix e seta o layout automaticamente (documentado acima).
3. **Helper wrapper**: Modificar `inertia_render()` em [helpers.py](src/core/inertia/helpers.py) para aceitar um parâmetro `app` que resolve o template.

---

### GAP 3: `STATICFILES_DIRS` aponta para diretório único

**Atual** ([base.py:246](src/config/settings/base.py#L246)):
```python
STATICFILES_DIRS = [
    SRC_DIR / "static",
]
```

**Problema**: Funciona porque o build output vai para `src/static/dashboard/` e `src/static/landing/` que são subdiretórios de `src/static/`. O Django já coleta tudo recursivamente.

**Resolução**: Nenhuma ação necessária. O diretório pai já engloba os dois. Mas garantir que cada `vite.config.ts` escreva no subdiretório correto (`outDir: '../../src/static/dashboard'` e `outDir: '../../src/static/landing'`).

---

### GAP 4: `base` do Vite precisa de `static_url_prefix`

**Atual** ([vite.config.ts:16](frontend/vite.config.ts#L16)):
```typescript
base: '/static/',
```

**Problema**: Com dois frontends, os assets de ambos teriam colisão no namespace `/static/`. O `static_url_prefix` no Django-Vite resolve isso.

**Resolução**: Cada `vite.config.ts` deve ter `base: '/static/dashboard/'` e `base: '/static/landing/'` respectivamente. E o `DJANGO_VITE` config precisa do `static_url_prefix` correspondente (já documentado acima).

---

### GAP 5: Sem `package.json` raiz (npm workspaces)

**Atual**: Não existe `package.json` na raiz do projeto. O único está em `frontend/package.json`.

**Problema**: Sem npm workspaces, cada frontend precisa de `npm install` separado. `@launch/shared` não pode ser importado por path resolution.

**Resolução**: Criar `package.json` raiz com workspaces (documentado acima). Isso permite:
- `npm install` na raiz instala tudo
- `@launch/shared` é resolvido automaticamente
- Scripts podem rodar em todos os workspaces com `npm -ws`

---

### GAP 6: CSRF trusted origins faltando porta 3345

**Atual** ([flags.py:57-63](src/config/settings/flags.py#L57-L63)):
```python
return [
    "http://localhost:8844",
    "http://127.0.0.1:8844",
    "http://localhost:3344",
    "http://127.0.0.1:3344",
]
```

**Problema**: Não inclui a porta 3345 do landing Vite dev server.

**Resolução**: Adicionar `http://localhost:3345` e `http://127.0.0.1:3345`.

---

### GAP 7: Views de landing não existem no Django

**Atual**: Não existe `apps.landing` nem nenhuma view para servir as landing pages via Inertia.

**Problema**: O legado roda como Next.js standalone. Para migrar para Inertia, precisamos de views Django que façam `inertia_render(request, "Capture/Index", props={...})`.

**Resolução**: Criar nova app Django para as views de landing:
```
src/apps/landing/
├── __init__.py
├── apps.py
├── urls.py              # Rotas públicas
├── views/
│   ├── __init__.py
│   ├── capture.py       # Landing pages de captura
│   ├── checkout.py      # Checkout Stripe
│   ├── thankyou.py      # Páginas de obrigado
│   └── content.py       # CPL, suporte pré-compra, legal
└── services/
    ├── __init__.py
    ├── capture.py       # Lógica de lead capture (webhook N8N)
    ├── checkout.py      # Integração Stripe (payment intents)
    └── fingerprint.py   # FingerprintJS integration
```

**Nota**: As API routes do Next.js (`/api/track`, `/api/payment-intent`, etc.) viram views Django regulares dentro desta app. A lógica de Stripe que hoje está num FastAPI separado (`stripe.arthuragrelli.com`) pode ser absorvida pelo Django usando dj-stripe.

---

### GAP 8: Integrações externas do legado precisam de absorção

| Serviço legado | O que faz | Absorção no Django |
|----------------|-----------|-------------------|
| FastAPI Stripe (`stripe.arthuragrelli.com`) | Payment intents, checkout sessions | Absorver em `apps.landing.services.checkout` usando dj-stripe |
| N8N webhooks | Lead tracking, fingerprint analytics | Django view proxy ou Celery task que posta no N8N |
| MinIO (S3) configs | Checkout configs dinâmicos | Django model ou cache Redis |
| FingerprintJS Pro | Browser fingerprinting | Frontend SDK + Django view para receber dados |
| Redis cache | Cache de scripts | Django cache framework (já configurado) |

**Nota**: N8N e Mautic continuam externos — Django apenas faz proxy/webhook.

---

### GAP 9: `entryFileNames` sem hash em prod

**Atual** ([vite.config.ts:52](frontend/vite.config.ts#L52)):
```typescript
entryFileNames: 'assets/[name].js',
```

**Problema**: Entry files sem hash podem causar cache stale em produção. Chunks e assets já têm hash, mas o entry point não.

**Resolução**: Considerar usar `'assets/[name]-[hash].js'` para o entry point também. O django-vite resolve via manifest.json independente do nome.

---

### GAP 10: Middleware guards (SetupStatus, Delinquent) aplicam em tudo

**Atual** ([base.py:130-131](src/config/settings/base.py#L130-L131)):
```python
"core.inertia.middleware.SetupStatusMiddleware",
"core.inertia.middleware.DelinquentMiddleware",
```

**Problema**: Estes middleware rodam em TODAS as requests. Landing pages públicas não devem ser bloqueadas por onboarding/billing status.

**Resolução**: Os middleware precisam ser atualizados para excluir rotas que NÃO começam com `/app/`:
```python
class SetupStatusMiddleware:
    def __call__(self, request):
        # Skip non-dashboard routes
        if not request.path.startswith('/app/'):
            return self.get_response(request)
        # ... existing logic
```

---

## Contexto: O que existe no legado (frontend-landing-pages/)

O projeto legado em Next.js contém **49 páginas** organizadas em:

### Categorias de páginas

| Categoria | Exemplos | Quantidade |
|-----------|----------|-----------|
| **Captura** (`inscrever-*`) | `inscrever-wh-rc-v1`, `inscrever-bf-v1` | ~10 variantes A/B |
| **Checkout** (`checkout-*`) | `checkout-wh`, `checkout-bf`, upsells/downsells | ~13 variantes |
| **Obrigado** (`obrigado-*`) | `obrigado-us`, `obrigado-bf`, `obrigado-new` | ~5 variantes |
| **CPL/Conteúdo** | `agrelliflix-aula-1` a `aula-4`, `recado-importante` | ~6 páginas |
| **Suporte** | `suporte`, `suporte-launch`, `onboarding` | ~3 páginas |
| **Utilitário** | `status`, `urls`, `privacy-policy`, `terms-of-service` | ~4 páginas |
| **Admin interno** | `admin`, `admin/editor`, `admin/checkout` | ~5 páginas |

**Nota sobre agrelliflix**: São aulas públicas no YouTube, NÃO um sistema de cursos. Um sistema de cursos real será implementado futuramente como feature separada (possivelmente terceiro frontend `frontends/courses/` ou via app Django da comunidade).

### Componentes-chave para migrar

| Componente | O que faz |
|-----------|-----------|
| `capture-form.tsx` | Form de captura (email + phone + tracking hidden fields) |
| `phone-input.tsx` | Input telefone internacional (libphonenumber-js) |
| `checkout-page.tsx` | Wrapper Stripe Embedded Checkout |
| `checkout-form.tsx` | Form com Stripe Elements |
| `FingerprintProvider.tsx` | FingerprintJS Pro provider |
| `youtube-player-advanced.tsx` | Player YouTube avançado |
| `whatsapp-button.tsx` | Botão flutuante WhatsApp |

### Integrações externas no legado

| Serviço | URL | Propósito |
|---------|-----|-----------|
| **FastAPI Stripe Server** | `stripe.arthuragrelli.com` | Stripe secret key ops |
| **N8N** | `n8n.arthuragrelli.com` | Webhooks: lead forms, fingerprint, checkout tracking |
| **MinIO (S3)** | `s3.arthuragrelli.com` | Configs de checkout dinâmicos |
| **Mautic** | `mkt.arthuragrelli.com` | Marketing automation |
| **FingerprintJS Pro** | `finger.arthuragrelli.com` | Browser fingerprinting |
| **Chatwoot** | via SDK | Live chat suporte pré-compra |
| **Redis** | `redis_landing:6379` | Cache de scripts com TTL 5min |

### Data flow do legado

```
Lead Capture:
  Visitante → Landing Page → CaptureForm → N8N Webhook → CRM/Mautic
                                         → FingerprintJS analytics
                                         → Thank-You Page → WhatsApp Group

Checkout:
  Visitante → Checkout Page → /api/minio-script/ → Redis/S3 (preços)
                            → /api/customer (Stripe customer)
                            → /api/subscription ou /api/checkout-session
                            → FastAPI Stripe Backend → Stripe API
                            → /api/track → N8N (tracking)
                            → Onboarding Page
```

---

## Resumo de gaps e prioridade

| # | Gap | Severidade | Esforço | Status |
|---|-----|-----------|---------|--------|
| 1 | `vite_dev_mode` hardcoded | P1 | Baixo | **APLICADO** |
| 2 | `INERTIA_LAYOUT` singleton | P1 | Baixo | **APLICADO** |
| 3 | `STATICFILES_DIRS` | OK | Nenhum | N/A |
| 4 | Vite `base` + `static_url_prefix` | P1 | Baixo | **APLICADO** |
| 5 | Sem `package.json` raiz | P2 | Baixo | Pendente |
| 6 | CSRF faltando porta 3345 | P2 | Trivial | **APLICADO** (junto com GAP 1) |
| 7 | Views de landing inexistentes | P1 | Alto | Pendente |
| 8 | Absorção de integrações externas | P2 | Médio | Pendente |
| 9 | Entry files sem hash | P3 | Trivial | **APLICADO** (junto com GAP 4) |
| 10 | Middleware guards em rotas públicas | P1 | Baixo | **APLICADO** |

---

## Correções já aplicadas (2026-02-13)

> **IMPORTANTE para sessões futuras**: Os gaps P1 abaixo JÁ FORAM aplicados no código.
> NÃO reimplemente — apenas valide que as alterações persistem.

### GAP 1 — APLICADO: Auto-detecção TCP para `vite_dev_mode`

**Arquivos alterados:**
- `src/config/settings/flags.py` — Removida property `vite_dev_mode` (era `return is_development()`)
- `src/config/settings/base.py` — Adicionada função `_detect_vite_dev_mode(port: int) -> bool` com TCP socket check (<100ms timeout). `DJANGO_VITE` agora usa duas keys (`"dashboard"` e `"landing"`) cada uma com detecção independente por porta
- `src/config/settings/flags.py` — CSRF trusted origins agora inclui portas 3344 E 3345
- `src/config/settings/base.py` — CORS allowed origins agora inclui portas 3344 E 3345

**Estado atual do `DJANGO_VITE`:**
```python
DJANGO_VITE = {
    "dashboard": {
        "dev_mode": _detect_vite_dev_mode(port=3344),
        "dev_server_port": 3344,
        "static_url_prefix": "dashboard",
        "manifest_path": SRC_DIR / "static" / "dashboard" / ".vite" / "manifest.json",
    },
    "landing": {
        "dev_mode": _detect_vite_dev_mode(port=3345),
        "dev_server_port": 3345,
        "static_url_prefix": "landing",
        "manifest_path": SRC_DIR / "static" / "landing" / ".vite" / "manifest.json",
    },
}
```

### GAP 2 — APLICADO: Multi-layout Inertia

**Arquivos alterados:**
- `src/config/settings/base.py` — `INERTIA_LAYOUT = "dashboard.html"` + novo dict `INERTIA_LAYOUTS = {"dashboard": "dashboard.html", "landing": "landing.html"}`
- `src/core/inertia/helpers.py` — `inertia_render()` agora aceita keyword argument `app: str = "dashboard"` que resolve o template via `INERTIA_LAYOUTS`
- `templates/base.html` — **RENOMEADO** para `templates/dashboard.html`, tags vite atualizadas para `app="dashboard"`
- `templates/landing.html` — **CRIADO** com tags `app="landing"`, título "Arthur Agrelli", blocos `{% block analytics %}` e `{% block tracking %}`

**API do helper:**
```python
# Dashboard (default)
return inertia_render(request, "Dashboard/Index", {"stats": data})

# Landing (explicitar app="landing")
return inertia_render(request, "Capture/Index", {"campaign": "wh-rc-v1"}, app="landing")
```

### GAP 4 — APLICADO: Vite base path namespaced

**Arquivos alterados:**
- `frontend/vite.config.ts`:
  - `base`: `'/static/'` → `'/static/dashboard/'`
  - `outDir`: `'../src/static/dist'` → `'../src/static/dashboard'`
  - `entryFileNames`: `'assets/[name].js'` → `'assets/[name]-[hash].js'` (GAP 9 corrigido junto)

**ATENÇÃO**: O build antigo em `src/static/dist/` NÃO é mais usado. O novo output vai para `src/static/dashboard/`. Ao rodar `npm run build` pela primeira vez após esta mudança, o diretório `src/static/dist/` pode ser removido manualmente.

### GAP 10 — APLICADO: Middleware guards scoped ao dashboard

**Arquivos alterados:**
- `src/core/inertia/middleware.py`:
  - **Criada** classe base `_DashboardOnlyMiddleware` com `DASHBOARD_PREFIXES` e método `_is_dashboard_route(path)`
  - `SetupStatusMiddleware` agora herda de `_DashboardOnlyMiddleware` — faz skip automático em rotas que NÃO são dashboard
  - `DelinquentMiddleware` agora herda de `_DashboardOnlyMiddleware` — landing pages nunca são bloqueadas

**`DASHBOARD_PREFIXES` atuais** (inclui rotas temporárias pré-migração para `/app/`):
```python
DASHBOARD_PREFIXES = (
    "/app/",           # Futuro: todas as rotas dashboard
    "/dashboard/",     # Temporário: rota atual
    "/identities/",    # Temporário: rota atual
    "/billing/",       # Temporário: rota atual
    "/notifications/", # Temporário: rota atual
    "/settings/",      # Temporário: rota atual
    "/delinquent/",    # Temporário: rota atual
)
```

> Quando as URLs migrarem para o prefixo `/app/`, remover os prefixos temporários e manter apenas `"/app/"`.

---

## Próximos passos (pendentes)

| # | O que | Operação | Esforço | Dependência |
|---|-------|----------|---------|-------------|
| 5 | Criar `package.json` raiz com npm workspaces | Criar novo | Baixo | `git mv frontend frontends/dashboard` concluído |
| — | Mover `frontend/` → `frontends/dashboard/` | `git mv` (preserva histórico) | Baixo | Nenhuma |
| — | Criar `frontends/landing/` (novo Vite app) | Criar do zero (NÃO mover legado) | Médio | GAP 7 (views Django existirem) |
| 7 | Criar `src/apps/landing/` (views, urls, services) | Criar novo no Django | Alto | Definir quais páginas migram primeiro |
| 8 | Absorver FastAPI Stripe → `apps.landing.services.checkout` | Reescrever no Django | Médio | GAP 7 concluído |
| — | Criar `frontends/shared/` (`@launch/shared`) | Criar do zero na Fase H | Médio | Duplicação real identificada entre dashboard e landing |
| — | Migrar URLs existentes para prefixo `/app/` | Refactor backend + frontend | Médio | Dashboard ajustado |
| — | Remover `frontend-landing-pages/` | Deletar quando Fase F concluída | Trivial | Todas as landing pages migradas |

### Sobre `frontend-landing-pages/` (legado Next.js)

> **NÃO mover para dentro de `frontends/`.** Este diretório é um projeto Next.js standalone
> que serve como **referência de consulta** para portar componentes, lógica e integrações.
> O novo `frontends/landing/` será um Vite+Inertia app criado do zero, com componentes
> portados manualmente do legado. Quando a migração estiver completa (Fase F), o diretório
> legado será removido do repositório.

---

*Decisão final em 2026-02-13. P1s aplicados em 2026-02-13. Operações de diretório clarificadas em 2026-02-14. Plano detalhado em `IMPLEMENTATION_PLAN.md`.*
