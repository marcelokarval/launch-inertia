# Implementation Plan — Launch Inertia

> Gerado em: 2026-02-13
> Status: Proposta para aprovação
> Referência: `FRONTEND_ARCHITECTURE_ANALYSIS.md`, `CONTACTS_ANALYSIS.md`

---

## Visão geral

O sistema é um **monolito modular Django** que serve duas interfaces web via Inertia.js:

1. **Dashboard** (`/app/*`) — gestão interna de lançamentos, identities, billing
2. **Landing** (`/*`) — páginas públicas de captura, checkout, obrigado, CPL, suporte

Cada frontend é um build Vite separado, servido como estático pelo Django em produção.
Em dev, cada um roda seu próprio Vite dev server (HMR).

---

## Estado atual (2026-02-13)

### O que JÁ existe e funciona

| Item | Status | Evidência |
|------|--------|-----------|
| Django backend (`src/`) com 5 apps | Funcionando | 284 testes passando |
| Dashboard frontend (`frontend/`) | Funcionando | 36 testes, build limpo |
| Identity sub-apps (email, phone, fingerprint, identity) | Funcionando | Services, models, signals, tasks |
| LifecycleService + expand-on-demand | Funcionando | 43 testes dedicados |
| HeroUI v3 max compliance | Concluído | Commit `27a400c` |
| GAPs 1, 2, 4, 6, 9, 10 aplicados no código | Aplicado | Verificado em auditoria |

### O que NÃO existe ainda

| Item | Razão |
|------|-------|
| Diretório `frontends/` | Renomeação ainda não feita |
| `frontends/landing/` | Frontend de landing pages não criado |
| `frontends/shared/` | Código compartilhado não extraído |
| `package.json` raiz (workspaces) | Depende da renomeação |
| `src/apps/landing/` (views Django) | App de landing não existe |
| Build em `src/static/dashboard/` | Vite config aponta para lá mas build não rodou |
| Build antigo `src/static/dist/` | Ainda existe, precisa ser removido |
| Prefixo `/app/` nas URLs do dashboard | URLs atuais são na raiz (`/dashboard/`, `/identities/`, etc.) |

---

## Plano de implementação

### Lógica de sequenciamento

```
Fase A: Infraestrutura (preparar o terreno)
  → Mover pastas, criar workspaces, validar build
  → SEM mudança funcional — tudo continua funcionando igual

Fase B: Dashboard sob /app/ (migrar URLs)
  → Mover todas as URLs do dashboard para /app/*
  → Simplificar middleware guards
  → Dashboard fica "isolado" e pronto para coexistir

Fase C: Landing — esqueleto (criar o frontend vazio)
  → Novo Vite app, entry point, primeira página Inertia
  → Provar que Django serve dois frontends simultaneamente

Fase D: Landing — captura (o que gera dinheiro primeiro)
  → Migrar CaptureForm, PhoneInput, FingerprintProvider
  → Django view que recebe form e proxia para N8N
  → UMA landing page funcionando end-to-end

Fase E: Landing — checkout (receita direta)
  → Stripe checkout absorvido no Django (sem FastAPI externo)
  → Migrar checkout-wh como referência

Fase F: Landing — thank-you + CPL + suporte
  → Páginas de pós-conversão e conteúdo
  → Menor urgência, menor risco

Fase G: Identities + Launch models (o coração do negócio)
  → Retomar as Phases 2-6 do CONTACTS_ANALYSIS.md
  → FingerprintJS webhook, Launch, LaunchParticipant
```

Cada fase produz um sistema funcional. Nenhuma fase quebra o que já existe.

---

## Fase A — Infraestrutura de diretórios

**Objetivo**: Reorganizar pastas sem quebrar funcionalidade.

**Esforço**: 1 dia
**Risco**: Baixo (renomeação + ajuste de paths)

### Mapa de operações de diretório (visão geral de TODAS as fases)

| Diretório destino | Operação | Quando | Como |
|-------------------|----------|--------|------|
| `frontends/dashboard/` | **Mover** `frontend/` existente | Fase A | `git mv frontend frontends/dashboard` (preserva histórico) |
| `frontends/landing/` | **Criar do zero** como novo Vite+Inertia app | Fase C | Scaffold novo, componentes portados manualmente do legado |
| `frontends/shared/` | **Criar do zero** quando duplicação real surgir | Fase H | Extrair código compartilhado (cn(), types, validators) |
| `frontend-landing-pages/` | **Manter como referência** → **deletar** após migração | Deletar na Fase F | NÃO mover para frontends/, é blueprint de consulta |

> **IMPORTANTE**: `frontends/landing/` NÃO é um "mover" do `frontend-landing-pages/`.
> O legado é Next.js — não funciona com Inertia. O novo landing é criado do zero com
> Vite+Inertia, usando o legado apenas como referência para portar componentes e lógica.

### A.1 — Mover `frontend/` → `frontends/dashboard/` (git mv)

```bash
mkdir -p frontends
git mv frontend frontends/dashboard
```

Atualizar referências em:
- `Makefile` — todos os `cd frontend` → `cd frontends/dashboard`
- `frontends/dashboard/vite.config.ts` — `outDir` path relativo (agora `../../src/static/dashboard`)
- `frontends/dashboard/tsconfig.json` — verificar paths
- `.gitignore` — atualizar se necessário
- `CLAUDE.md` — atualizar referências de paths

### A.2 — Criar `package.json` raiz com npm workspaces

```json
{
  "private": true,
  "workspaces": ["frontends/*"],
  "scripts": {
    "dev:dashboard": "npm -w @launch/dashboard run dev",
    "dev:landing": "npm -w @launch/landing run dev",
    "build": "npm -w @launch/dashboard run build",
    "test": "npm -w @launch/dashboard run test"
  }
}
```

Renomear `frontends/dashboard/package.json` name para `@launch/dashboard`.

### A.3 — Rodar build e validar

```bash
rm -rf src/static/dist/        # Remover build antigo
cd frontends/dashboard && npm run build
# Confirmar output em src/static/dashboard/
# Rodar testes backend + frontend
```

### A.4 — Atualizar Makefile

```makefile
dev:           make dev-back & make dev-dashboard & wait
dev-back:      cd src && uv run python ../manage.py runserver 8844
dev-dashboard: cd frontends/dashboard && npm run dev
dev-landing:   cd frontends/landing && npm run dev   # (futuro)
install:       uv pip install -e ".[dev]" && npm install
test:          make test-back && make test-front
test-back:     cd src && uv run python -m pytest
test-front:    cd frontends/dashboard && npx vitest run
```

### A.5 — Commit

```
feat(infra): reorganize to multi-frontend workspace structure

- Rename frontend/ → frontends/dashboard/
- Create root package.json with npm workspaces
- Update Makefile, vite.config.ts paths
- Remove stale build from src/static/dist/
- Build output now at src/static/dashboard/
```

**Critério de saída**: `make dev` funciona, `make test` passa, build limpo.

---

## Fase B — Dashboard sob `/app/`

**Objetivo**: Isolar URLs do dashboard sob prefixo `/app/` para que a raiz fique livre para landing pages.

**Esforço**: 1 dia
**Risco**: Médio (precisa atualizar URLs no frontend e backend)

### B.1 — Backend: Mover URLs para `/app/`

```python
# config/urls.py
urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("stripe/", include("djstripe.urls", namespace="djstripe")),

    # Dashboard (autenticado) — tudo sob /app/
    path("app/", include("apps.identity.dashboard_urls")),
    path("app/identities/", include("apps.contacts.urls")),
    path("app/billing/", include("apps.billing.urls")),
    path("app/notifications/", include("apps.notifications.urls")),

    # Landing (público) — raiz, adicionado na Fase C
    # path("", include("apps.landing.urls")),
]
```

### B.2 — Frontend: Atualizar todas as rotas no React

Buscar/substituir em todos os arquivos de `frontends/dashboard/src/`:
- `/dashboard/` → `/app/`
- `/identities/` → `/app/identities/`
- `/billing/` → `/app/billing/`
- `/notifications/` → `/app/notifications/`
- `/settings/` → `/app/settings/`
- `/delinquent/` → `/app/delinquent/`

Incluindo: `router.visit()`, `router.get()`, `router.post()`, `<Link href>`, `post()` URLs.

### B.3 — Simplificar middleware guards

```python
# Remover prefixos temporários, manter apenas /app/
DASHBOARD_PREFIXES = ("/app/",)
```

### B.4 — Backend: Auth views (login/register/reset) ficam em `/auth/`

```python
# Estas NÃO vão sob /app/ porque o user ainda não está logado
path("auth/", include("apps.identity.auth_urls")),
path("onboarding/", include("apps.identity.onboarding_urls")),
```

### B.5 — Commit

```
refactor(urls): move dashboard routes under /app/ prefix

- All dashboard routes now under /app/*
- Auth routes under /auth/* (pre-login)
- Onboarding routes under /onboarding/*
- Simplify middleware guards to single /app/ prefix
- Update all frontend router.visit/Link/post URLs
```

**Critério de saída**: Dashboard funciona em `/app/`, login em `/auth/`, testes passam.

---

## Fase C — Landing: Esqueleto do frontend

**Objetivo**: Criar `frontends/landing/` como Vite app funcional e provar que Django serve dois frontends.

**Esforço**: 1 dia
**Risco**: Baixo

> **NOTA**: Este frontend é **criado do zero** — NÃO é uma cópia ou move do `frontend-landing-pages/` (Next.js legado). O legado serve como referência de consulta para portar componentes nas Fases D-F.

### C.1 — Scaffold do frontend landing

```
frontends/landing/
├── src/
│   ├── main.tsx              # createInertiaApp com glob de ./pages/**/*.tsx
│   ├── styles/globals.css    # Tailwind v4 base (tokens do legado)
│   ├── pages/
│   │   └── Home/Index.tsx    # Página placeholder
│   ├── layouts/
│   │   └── LandingLayout.tsx # Layout base (sem sidebar, sem auth)
│   └── types/
│       └── index.ts
├── public/
├── package.json              # name: "@launch/landing"
├── vite.config.ts            # port 3345, outDir → ../../src/static/landing
├── tsconfig.json
└── tsconfig.build.json
```

### C.2 — Django view de smoke test

```python
# src/apps/landing/__init__.py, apps.py, urls.py
# Uma view simples:
from core.inertia.helpers import inertia_render

def home(request):
    return inertia_render(request, "Home/Index", {}, app="landing")
```

```python
# config/urls.py — adicionar no final
path("", include("apps.landing.urls")),
```

### C.3 — Validar dual-frontend

1. `make dev-back` + `make dev-dashboard` + `make dev-landing`
2. `http://localhost:8844/app/` → dashboard (Inertia via `dashboard.html`)
3. `http://localhost:8844/` → landing page placeholder (Inertia via `landing.html`)
4. HMR funciona em ambos independentemente

### C.4 — Commit

```
feat(landing): scaffold landing frontend with dual Inertia entry points

- Create frontends/landing/ with Vite on port 3345
- Create src/apps/landing/ with smoke test view
- Prove Django serves dashboard + landing simultaneously
- Both Vite dev servers work with independent HMR
```

**Critério de saída**: Duas URLs, dois frontends, dois Vite servers, tudo funcionando.

---

## Fase D — Landing: Captura de leads (o que gera dinheiro)

**Objetivo**: Migrar o fluxo de captura do legado Next.js para Inertia. Uma landing page real funcionando end-to-end.

**Esforço**: 3-5 dias
**Risco**: Médio (integração N8N + FingerprintJS)

### D.1 — Backend: Views e services de captura

```
src/apps/landing/
├── views/
│   ├── capture.py         # GET: serve landing page com config como props
│   │                      # POST: recebe form, cria Identity, proxia N8N
│   └── fingerprint.py     # POST: recebe dados fingerprint, cria FingerprintEvent
├── services/
│   ├── capture.py         # Lógica: validar, criar Identity/Email/Phone, disparar N8N
│   └── n8n_proxy.py       # Proxy HTTP para webhooks N8N (com retry)
└── urls.py
```

**Fluxo Inertia:**
```
GET /inscrever/wh-rc-v3/
  → capture_view(request, campaign="wh-rc-v3")
  → inertia_render(request, "Capture/Index", {
      campaign: config_from_db_or_json,
      fingerprint_api_key: settings.FINGERPRINT_API_KEY,
    }, app="landing")

POST /inscrever/wh-rc-v3/
  → CaptureService.process_lead(request.data)
    → Criar/resolver Identity (usa ResolutionService existente!)
    → Criar ContactEmail + ContactPhone
    → Trigger LifecycleService.recalculate()
    → POST para N8N webhook (async via Celery)
  → redirect para /obrigado/wh-rc-v3/
```

**Ponto chave**: O `ResolutionService` e `IdentityService` que já existem em `contacts/identity/services/` fazem exatamente o que o legado faz via N8N. Agora a resolução de identidade acontece no Django ANTES de ir para o N8N.

### D.2 — Frontend: Portar componentes do legado

Portar componentes de `frontend-landing-pages/` (Next.js legado, referência) para `frontends/landing/src/`:

> **Processo de portagem**: Ler o componente original, entender a lógica, reescrever para
> Vite+Inertia. Remover `'use client'`, `next/script`, `next/image`, `next/navigation`.
> Substituir `fetch()` + `react-hook-form` por Inertia `useForm().post()`.
> Não é copy-paste — é reescrita informada.

| Componente | Referência no legado | Destino em landing | Mudanças |
|-----------|---------------------|-------------------|----------|
| `CaptureForm` | `components/capture-form.tsx` (758 linhas) | `components/CaptureForm.tsx` | `fetch()` → `useForm().post()`. Remove `react-hook-form`. Server valida. |
| `PhoneInput` | `components/phone-input.tsx` (161 linhas) | `components/PhoneInput.tsx` | Porta direta. Manter `react-international-phone`. |
| `FingerprintProvider` | `components/fingerprint/FingerprintProvider.tsx` | `components/FingerprintProvider.tsx` | Porta direta. API key vem das props Inertia (não hardcoded). |
| `PageLayout` | `components/page-layout-v2.tsx` | `layouts/CaptureLayout.tsx` | Adaptar para Inertia layout pattern. |
| UI primitives | `components/ui/` (shadcn) | `components/ui/` | Manter separados do dashboard (que usa HeroUI). Landing pode usar seus próprios Button/Input. |

### D.3 — Página Inertia: Capture/Index.tsx

```tsx
// frontends/landing/src/pages/Capture/Index.tsx
export default function CaptureIndex({ campaign, fingerprint_api_key }) {
  const { data, setData, post, processing, errors } = useForm({
    email: '',
    phone: '',
    fingerprint_visitor_id: '',
    utm_source: '',
    utm_medium: '',
    utm_campaign: '',
  });

  // ... FingerprintProvider, CaptureForm, PhoneInput
  // POST para mesma URL (Django view cuida do redirect)
}
```

### D.4 — Configuração de campanha

O legado usa arquivos `page.json` por landing page. Opções para Inertia:

1. **JSON fixtures no repo** — Django lê o JSON e passa como props (simples, funciona agora)
2. **Django model** — `CampaignConfig` model no admin (melhor longo prazo, editável sem deploy)

**Recomendação**: Começar com (1), migrar para (2) depois.

### D.5 — Testes

- Teste de integração: POST para `/inscrever/wh-rc-v3/` com dados válidos → Identity criada + N8N chamado
- Teste de validação: email inválido retorna erros Inertia
- Teste de fingerprint: endpoint recebe dados e cria FingerprintEvent

### D.6 — Commit

```
feat(landing): implement lead capture flow with identity resolution

- Django views: capture GET/POST with campaign config as props
- CaptureService: validate, resolve identity, create email/phone, proxy N8N
- Migrate CaptureForm, PhoneInput, FingerprintProvider from Next.js legacy
- Landing page renders via Inertia with independent Vite build
- Integration with existing ResolutionService for cross-launch identity
```

**Critério de saída**: `GET /inscrever/wh-rc-v3/` mostra landing page, form submete, Identity criada no DB, N8N recebe webhook.

---

## Fase E — Landing: Checkout Stripe

**Objetivo**: Absorver o FastAPI Stripe server no Django e migrar o checkout.

**Esforço**: 3-5 dias
**Risco**: Alto (dinheiro real, Stripe em produção)
**Dependência**: Fase D concluída

### E.1 — Backend: Absorver Stripe no Django

O legado tem um `server.py` FastAPI com 4 endpoints. Todos viram views Django usando o `BillingService` existente:

| FastAPI endpoint | Django view | Serviço |
|-----------------|-------------|---------|
| `POST /create-checkout-session/` | `apps/landing/views/checkout.py` | `BillingService.create_checkout_session()` |
| `POST /create-payment-intent/` | mesma view, método diferente | `BillingService.create_payment_intent()` |
| `POST /create-customer/` | `apps/landing/views/checkout.py` | `BillingService.get_or_create_customer()` |
| `POST /create-subscription/` | mesma view | `BillingService.create_subscription()` |

dj-stripe já está configurado para webhooks. O Stripe publishable key vai como props Inertia (não hardcoded no frontend).

### E.2 — Frontend: Checkout page

Migrar `checkout-wh` como referência. O componente usa Stripe Embedded Checkout (não Elements):

```tsx
// frontends/landing/src/pages/Checkout/Index.tsx
export default function CheckoutIndex({ stripe_publishable_key, checkout_config }) {
  // Stripe.js carrega via <script> ou import
  // Embedded Checkout monta no DOM
  // Session criada via fetch() para Django JSON endpoint
}
```

**Nota**: Checkout NÃO usa `useForm` porque não é um POST Inertia — é uma chamada Stripe JS → Django JSON API → Stripe API. O frontend precisa de `fetch()` com CSRF token para criar a session.

### E.3 — Config de preços

O legado busca preços de MinIO S3 (scripts JS dinâmicos). Opções:

1. **Django model** — `Product`, `Price` via dj-stripe (já existe) + view JSON que retorna configuração
2. **Cache Redis** — Django busca do Stripe e cacheia

**Recomendação**: Usar dados do dj-stripe diretamente. O admin já mostra Products/Prices.

### E.4 — Commit

```
feat(landing): implement Stripe checkout replacing FastAPI server

- Absorb server.py endpoints into Django BillingService
- Create checkout page with Stripe Embedded Checkout
- Price config from dj-stripe models (no more MinIO scripts)
- CSRF-protected JSON endpoints for Stripe session creation
```

**Critério de saída**: Checkout funciona em staging com Stripe test mode. Payment completa. Webhook dj-stripe recebe confirmação.

---

## Fase F — Landing: Thank-you, CPL, suporte

**Objetivo**: Completar as páginas de pós-conversão.

**Esforço**: 2-3 dias
**Risco**: Baixo (pages estáticas com pouca lógica)

### F.1 — Thank-you pages

```
GET /obrigado/wh-rc-v3/
  → thankyou_view(request, campaign="wh-rc-v3")
  → inertia_render com WhatsApp group link, video embed, tracking pixel
```

Componentes: `WhatsAppCTA`, `CountdownTimer`, `UrgencyBanner` — portar do legado.

### F.2 — CPL / AgreliFlix

Aulas YouTube públicas. View simples que passa config de episódio como props.
Componentes complexos do legado (achievement badges, episode unlock) portar progressivamente.

### F.3 — Sales page (recado-importante)

Long-form sales page com 22 seções. Portar como Inertia page com componentes por seção.
Pode ser feito incrementalmente — começar com estrutura e conteúdo, refinar design depois.

### F.4 — Suporte pré-compra

Chatwoot embed + FAQ panel. Portar `ChatwootProvider` (617 linhas, React puro).

### F.5 — Legal (terms, privacy)

Páginas estáticas de texto. Trivial.

### F.6 — Remover legado

Quando todas as landing pages estiverem funcionando via Inertia:

```bash
rm -rf frontend-landing-pages/    # Remover o Next.js legado da raiz
# Atualizar .gitignore se necessário
```

> O legado já serviu seu propósito como referência. Todo código útil foi portado para `frontends/landing/`.

### F.7 — Commit(s)

```
feat(landing): add thank-you pages with WhatsApp CTA and conversion tracking
feat(landing): add CPL/AgreliFlix video lesson pages
feat(landing): add sales page, support, and legal pages
```

**Critério de saída**: Funil completo funciona — captura → obrigado → WhatsApp. Checkout → obrigado.

---

## Fase G — Retomar Phases do negócio

**Objetivo**: Voltar ao roadmap de negócio agora que a infraestrutura dual-frontend está pronta.

**Esforço**: Timeline original do CONTACTS_ANALYSIS.md
**Dependência**: Fase D concluída (captura funcionando = FingerprintJS integrado)

### G.1 — Phase 2: Webhook FingerprintJS + Capture (2-3 dias)

Já parcialmente coberto pela Fase D. Completar:
- Endpoint webhook que FingerprintJS Pro envia server-side
- `FingerprintEvent` para `page_view`, `form_submit`
- `Attribution` para UTMs
- Integration tests

### G.2 — Phase 3: Launch Models (3-5 dias)

Criar os modelos de lançamento:
- `Launch` (root tag, phases, dates)
- `Product` (main + bumps + upsells + downsells, each with tag)
- `LaunchPhase` (CPL1, CPL2, Cart Open, Cart Close)
- `LaunchPage` (capture, sales, checkout — linked to Django views)

### G.3 — Phase 4: LaunchParticipant (3-5 dias)

O elo entre Identity e Launch:
- `LaunchParticipant` (lifecycle por lançamento)
- `LaunchProductParticipant` (status por produto)
- Entry count tracking, UTM cost tracking

### G.4 — Phase 5: Capture Pages dinâmicas (3-5 dias)

Com os Launch models existindo:
- Landing pages puxam configuração do Launch model (não mais JSON fixtures)
- A/B testing via Launch model
- Métricas de conversão por página

### G.5 — Phase 6: Analytics Dashboard + Materialized Views (2-3 dias)

Dashboard de métricas no `frontends/dashboard/`:
- Identities por lançamento
- Conversão por fase
- Revenue por produto
- Materialized views para performance

---

## Fase H — Shared code e polimento

**Objetivo**: Extrair código compartilhado e criar `frontends/shared/`.

**Esforço**: 1-2 dias
**Dependência**: Fases D-F concluídas (saber o que é realmente compartilhado)

**Nota**: Fazer isso DEPOIS, não antes. O código compartilhado real entre dashboard (HeroUI) e landing (UI própria) é mínimo:
- `cn()` utility
- Email validation helpers
- TypeScript types compartilhados (Identity, Tag)
- Possivelmente formatadores (phone, date)

Não extrair prematuramente — esperar que a duplicação real apareça.

---

## Resumo visual

```
                    Fase A          Fase B         Fase C
                    Infra           /app/          Esqueleto
                    1 dia           1 dia          1 dia
                    ──────────────►──────────────►──────────────►
                                                       │
                              ┌─────────────────────────┘
                              │
                              ▼
                         Fase D              Fase E           Fase F
                         Captura             Checkout         Thank-you/CPL
                         3-5 dias            3-5 dias         2-3 dias
                         ──────────────────►────────────────►──────────────►
                              │
                              │ (FingerprintJS integrado)
                              ▼
                         Fase G.1            G.2              G.3-G.5
                         FP Webhook          Launch Models    Participant+Analytics
                         2-3 dias            3-5 dias         8-13 dias
                         ──────────────────►────────────────►──────────────────────►
                                                                    │
                                                                    ▼
                                                               Fase H
                                                               Shared code
                                                               1-2 dias
```

### Timeline estimada

| Fase | Duração | Acumulado |
|------|---------|-----------|
| A — Infra | 1 dia | 1 dia |
| B — `/app/` | 1 dia | 2 dias |
| C — Esqueleto landing | 1 dia | 3 dias |
| D — Captura | 3-5 dias | 6-8 dias |
| E — Checkout | 3-5 dias | 9-13 dias |
| F — Thank-you/CPL | 2-3 dias | 11-16 dias |
| G.1 — FP Webhook | 2-3 dias | 13-19 dias |
| G.2 — Launch Models | 3-5 dias | 16-24 dias |
| G.3-G.5 — Participant+Analytics | 8-13 dias | 24-37 dias |
| H — Shared code | 1-2 dias | 25-39 dias |

**Total: ~5-8 semanas** (considerando ritmo real com revisões e ajustes)
**Target: Fim de Q2 2026 (junho)**

---

## Regras para todas as fases

1. **Cada fase produz commits testáveis** — nunca deixar o sistema quebrado
2. **Backend tests obrigatórios** — toda view/service tem teste
3. **Build limpo obrigatório** — `npm run build` passa sem erros em cada commit
4. **Landing pages mantêm seus próprios componentes UI** — não forçar HeroUI nas landings
5. **N8N continua como orquestrador externo** — Django faz proxy, não reimplementa
6. **Stripe via dj-stripe** — não recriar o FastAPI server
7. **Configuração de campanha começa como JSON fixtures** — migra para Django models quando os Launch models existirem (Fase G.2)
8. **`frontends/shared/` só na Fase H** — não extrair prematuramente
9. **`frontend-landing-pages/` é referência, não fonte** — componentes são portados (reescritos para Inertia), não copiados. O diretório legado é deletado na Fase F.
10. **`frontends/dashboard/` é mover, `frontends/landing/` é criar** — não confundir as duas operações. Dashboard preserva histórico git via `git mv`. Landing é app novo.

---

*Plano criado em 2026-02-13. Pendente aprovação para iniciar Fase A.*
