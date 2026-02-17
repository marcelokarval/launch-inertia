# Workflow: Acesso a /inscrever-* (Capture Pages)

---

## Frontmatter

| Campo | Valor |
|-------|-------|
| **Documento** | CAPTURE_WORKFLOW.md |
| **Tipo** | Documento de controle — base para discussao e planejamento |
| **Versao** | 3.1 |
| **Criado em** | 2026-02-15 |
| **Atualizado em** | 2026-02-15 |
| **Autor** | Claude (assistente) + Marcelo (owner) |
| **Status** | PLANO APROVADO — pronto para implementacao (Phase G) |
| **Fase do projeto** | Pos-Phase F / Pre-Phase G |

### Objetivo

Documentar o fluxo completo de requisicao das paginas de captura (`/inscrever-*`), servindo como:
1. **Referencia tecnica** — Como o sistema atual funciona (5 cenarios)
2. **Base de comparacao** — Legado (Next.js) vs novo (Inertia+Django)
3. **Registro de gaps** — Funcionalidades ausentes identificadas no scan
4. **Registro de decisoes** — O que manter, adaptar, descartar ou criar novo
5. **Input para o plano** — Alimenta o plan mode com tasks priorizadas

### Escopo

| Dentro do escopo | Fora do escopo |
|------------------|----------------|
| Fluxo GET/POST das capture pages | Checkout/pagamento (Phase E — ja implementado) |
| Validacao de formulario | Thank-you page (Phase F.1 — ja implementado) |
| Identity resolution + attribution | Support page (Phase F.4 — ja implementado) |
| Envio async para N8N | Visual parity (V1-V7 — ja implementado) |
| Features funcionais do legado | Modelos de Launch (Phase G.2 — futuro) |
| Config-driven campaigns | Docker/deploy (Phase H — futuro) |

### Historico de alteracoes

| Versao | Data | Descricao |
|--------|------|-----------|
| 1.0 | 2026-02-15 | Documento inicial com 5 cenarios + mapa de decisao |
| 1.1 | 2026-02-15 | Frontmatter estruturado como documento de controle |
| 2.0 | 2026-02-15 | Analise funcional completa com contexto de paradigma Django+Inertia. 15 gaps documentados, decisoes com owner, tabela de prioridades revisada |
| 3.0 | 2026-02-15 | Diagnostico profundo do estado atual. Modelo CaptureEvent detalhado com ORM chain. Pesquisa FPJS Pro (React SDK v3 + Python SDK + webhooks). Plano G.1-G.8 com 10 sessoes. 14 temas adicionais (cookie fpjs_vid, VisitorMiddleware, capture_token, deferred props, views materializadas, capture session Redis, FPJS open→Pro migration) |
| 3.1 | 2026-02-16 | REVISAO ARQUITETURAL: (R1) FPJS Pro chamado no PAGE LOAD nao no submit — cookie como persistencia primaria, Django complementa com suas proprias libs de deteccao. (R2) CaptureEvent redesenhado como tracker UNIVERSAL de todas as paginas, nao apenas captura. (R3) DeviceProfile dimension table (padrao Matomo star schema) com hash-based dedup para normalizar browser/OS/device. (R4) Stack de identificacao Django: device-detector + django-ipware + geoip2 + Client Hints. (R5) VisitorMiddleware expandido com device profiling e GeoIP |

### Status da analise

| Etapa | Status | Notas |
|-------|--------|-------|
| Documentar fluxo atual (5 cenarios) | CONCLUIDO | Cenarios 1-5 completos |
| Listar arquivos envolvidos | CONCLUIDO | 16 arquivos mapeados |
| Scan funcional do legado | CONCLUIDO | ~2.800 linhas analisadas: capture-form.tsx, capture-config.js, 8x page.json, utils, hooks, layouts |
| Comparacao legado vs novo | CONCLUIDO | 15 gaps identificados (F1-F15) com contexto de paradigma |
| Registro de gaps | CONCLUIDO | Secao "Analise Funcional" com decisao por gap |
| Registro de decisoes | CONCLUIDO | Tabela D1-D15 com decisao, local de execucao e justificativa |
| Plano de melhorias (tasks) | PENDENTE | Sera gerado em plan mode apos aprovacao final do owner |

### Decisoes ja tomadas (pre-documento)

| Decisao | Justificativa | Data |
|---------|---------------|------|
| Config-driven (1 template + N configs JSON) | Elimina duplicacao de 10+ paginas hardcoded | Phase D |
| Rotas `/inscrever-{slug}/` (hifen, sem barra interna) | Compatibilidade com URLs legadas ja indexadas | Phase D (corrigido) |
| Identity resolution no Django (nao no N8N) | Controle centralizado, dedup no banco proprio | Phase D |
| N8N como proxy async via Celery | Nao bloqueia response, retry automatico | Phase D |
| FingerprintJS Pro no frontend | Resolucao de identidade cross-device | Phase D |
| HeroUI NAO usado no landing | Performance — landing precisa ser leve (< 100KB JS) | Phase C |
| Chatwoot SDK global (nao por pagina) | Evita reload do SDK em navegacao SPA | ac80c62 |

### Decisoes tomadas nesta sessao (v2.0)

> Todas as decisoes abaixo foram discutidas e aprovadas com o owner. Ver secao "Tabela de decisoes atualizada" no final do documento para detalhes completos.

| # | Tema | Decisao | Onde executa |
|---|------|---------|--------------|
| D1 | Validacao email avancada (F1) | IMPLEMENTAR | Frontend + Backend |
| D2 | Auto-fill + fingerprint (F2) | IMPLEMENTAR + EXPANDIR | Frontend + Backend |
| D3 | Analytics acesso/conversao (F3) | IMPLEMENTAR SEM N8N | Backend (Django ORM) |
| D4 | Dados enriquecidos + bidirecional (F4) | REDESENHAR | Backend + Frontend (POST silencioso) |
| D5 | Referrer history (F5) | IMPLEMENTAR (1 nivel) | Backend (HTTP_REFERER) |
| D6 | Config via Django (F6) | MIGRAR PARA DJANGO | Backend (DB + Redis + post_save) |
| D7 | Form header (F7) | IMPLEMENTAR | Config Django |
| D8 | Glass/patriotic effects (F8) | MANTER FLAGS | Config Django |
| D9 | Top banner (F9) | IMPLEMENTAR | Config Django + Frontend |
| D10 | Black Friday layout (F10) | IMPLEMENTAR | Config Django + Frontend |
| D11 | Background avancado (F11) | IMPLEMENTAR PARCIAL | Config Django |
| D12 | Segmentacao interesse (F12) | ABSORVER NO DJANGO | Backend (modelos) |
| D13 | Fingerprint retry + server (F13) | PESQUISAR + IMPLEMENTAR | Frontend + Backend |
| D14 | Field styling (F14) | MANTER POSSIBILIDADE | Config Django |
| D15 | Debug/observabilidade (F15) | IMPLEMENTAR | Backend (DjDT + headers) |

---

## Cenario 1 — Slug que EXISTE (wh-rc-v3)

```
USUARIO                    BROWSER                      DJANGO :8844                         FILESYSTEM / SERVICES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Digita: arthuragrelli.com/inscrever-wh-rc-v3/
   ───────────────────────────►
   GET /inscrever-wh-rc-v3/
   Headers:
     Accept: text/html              ┌─────────────────────────────────────────────────────┐
     Cookie: XSRF-TOKEN=...        │                  MIDDLEWARE CHAIN                    │
                                    │                                                     │
                                    │  1. SecurityMiddleware          (headers OK)         │
                                    │  2. CorsMiddleware              (origin OK)          │
                                    │  3. SessionMiddleware           (load session)       │
                                    │  4. CommonMiddleware            (slash redirect)     │
                                    │  5. CsrfViewMiddleware          (GET = skip)         │
                                    │  6. AuthenticationMiddleware    (user=AnonymousUser) │
                                    │  7. SecurityHeadersMiddleware   (add X-Frame etc)    │
                                    │  8. RateLimitMiddleware         (check rate limit)   │
                                    │  9. InertiaMiddleware           (set X-Inertia)      │
                                    │ 10. InertiaJsonParserMiddleware (GET = skip parse)   │
                                    │ 11. InertiaShareMiddleware      (share auth/flash)   │
                                    │ 12. SetupStatusMiddleware       (not /app/ = SKIP)   │
                                    │ 13. DelinquentMiddleware        (not /app/ = SKIP)   │
                                    │ 14. AccountMiddleware           (allauth, pass)      │
                                    └──────────────────────┬──────────────────────────────┘
                                                           │
                                    ┌──────────────────────▼──────────────────────────────┐
                                    │                URL RESOLUTION                        │
                                    │                                                      │
                                    │  config/urls.py                                      │
                                    │    path("admin/", ...)          ✗ no match            │
                                    │    *auth_urlpatterns            ✗ no match            │
                                    │    *onboarding_urlpatterns      ✗ no match            │
                                    │    path("app/", ...)            ✗ no match            │
                                    │    path("accounts/", ...)       ✗ no match            │
                                    │    path("stripe/", ...)         ✗ no match            │
                                    │    path("", include(landing))   ✓ MATCH → landing     │
                                    │                                                      │
                                    │  apps/landing/urls.py                                │
                                    │    re_path(r"^inscrever-(?P<campaign_slug>[\w-]+)/$") │
                                    │    ✓ MATCH → slug = "wh-rc-v3"                       │
                                    │    → views.capture_page(request, "wh-rc-v3")         │
                                    └──────────────────────┬──────────────────────────────┘
                                                           │
                                    ┌──────────────────────▼──────────────────────────────┐
                                    │            views.capture_page() — GET                 │
                                    │                                                      │
                                    │  1. get_campaign("wh-rc-v3")                         │
                                    │     ├─ check _cache dict          → miss (1st req)   │
                                    │     ├─ Path("campaigns/wh-rc-v3.json")  ──────────────┼──► READ wh-rc-v3.json
                                    │     │     exists? ✓                                  │    {slug, meta, headline,
                                    │     ├─ json.load(f)                                  │     background_image:
                                    │     ├─ _cache["wh-rc-v3"] = config                   │     "/static/images/bg-
                                    │     └─ return config (dict)                          │      arthur-mostra-mao.jpg"
                                    │                                                      │     badges, form, ...}
                                    │  2. campaign is not None → no redirect               │
                                    │                                                      │
                                    │  3. request.method == "GET"                          │
                                    │     → _render_capture_page()                         │
                                    │                                                      │
                                    │  4. _build_campaign_props(campaign, "wh-rc-v3")      │
                                    │     ├─ props = {slug, meta, headline, badges,         │
                                    │     │           form, trust_badge, social_proof}      │
                                    │     ├─ background_image != None → include            │
                                    │     ├─ highlight_color != None → include             │
                                    │     └─ return props dict                             │
                                    │                                                      │
                                    │  5. fingerprint_api_key = os.getenv(...)             │
                                    │                                                      │
                                    │  6. inertia_render(request,                          │
                                    │       "Capture/Index",                               │
                                    │       {campaign: props,                              │
                                    │        fingerprint_api_key: "..."},                  │
                                    │       app="landing")                                 │
                                    └──────────────────────┬──────────────────────────────┘
                                                           │
                                    ┌──────────────────────▼──────────────────────────────┐
                                    │        inertia_render() → helpers.py                  │
                                    │                                                      │
                                    │  1. layouts = {"dashboard":"dashboard.html",          │
                                    │                "landing":"landing.html"}              │
                                    │  2. layout_template = "landing.html"                 │
                                    │  3. template_data = {inertia_layout:"landing.html"}  │
                                    │  4. inertia_base_render(request, "Capture/Index",    │
                                    │       props={...}, template_data={...})              │
                                    └──────────────────────┬──────────────────────────────┘
                                                           │
                                    ┌──────────────────────▼──────────────────────────────┐
                                    │     inertia-django library (1st visit = full HTML)    │
                                    │                                                      │
                                    │  Header X-Inertia absent → FULL PAGE RESPONSE        │
                                    │                                                      │
                                    │  Renders landing.html:                               │
                                    │  ┌────────────────────────────────────────────┐      │
                                    │  │ <!DOCTYPE html>                            │      │
                                    │  │ <html lang="pt-BR">                       │      │
                                    │  │ <head>                                    │      │
                                    │  │   {% vite_hmr_client app="landing" %}      │      │
                                    │  │   {% vite_react_refresh app="landing" %}   │      │
                                    │  │   {% vite_asset "src/main.tsx"             │      │
                                    │  │                   app="landing" %}         │      │
                                    │  │ </head>                                   │      │
                                    │  │ <body>                                    │      │
                                    │  │   <div id="app"                           │      │
                                    │  │     data-page='{                          │      │
                                    │  │       "component":"Capture/Index",         │      │
                                    │  │       "props":{                            │      │
                                    │  │         "campaign":{                       │      │
                                    │  │           "slug":"wh-rc-v3",              │      │
                                    │  │           "headline":{parts:[...]},        │      │
                                    │  │           "background_image":              │      │
                                    │  │             "/static/images/bg-arthur..." │      │
                                    │  │           "form":{button_text:"QUERO..."}  │      │
                                    │  │         },                                │      │
                                    │  │         "fingerprint_api_key":"...",       │      │
                                    │  │         "auth":{user:null},               │ ◄── shared via middleware
                                    │  │         "flash":{success:null,...},        │ ◄── shared via middleware
                                    │  │         "app":{name:"Launch",...}          │ ◄── shared via middleware
                                    │  │       },                                  │      │
                                    │  │       "url":"/inscrever-wh-rc-v3/",       │      │
                                    │  │       "version":"1.0"                     │      │
                                    │  │     }'                                    │      │
                                    │  │   ></div>                                 │      │
                                    │  │ </body></html>                            │      │
                                    │  └────────────────────────────────────────────┘      │
                                    │                                                      │
                                    │  HTTP 200 ← Content-Type: text/html                  │
                                    └──────────────────────┬──────────────────────────────┘
                                                           │
                              ◄────────────────────────────┘
   Browser receives HTML

   ┌───────────────────────────────────────────────────────────────────────────────────────┐
   │                           BROWSER EXECUTION                                           │
   │                                                                                       │
   │  1. Parse HTML → encontra <script src="http://localhost:3345/src/main.tsx">            │
   │                                                                                       │
   │  2. Vite dev server (:3345) serve main.tsx                                            │
   │     ├─ import ChatwootGlobalLoader    ← carrega SDK Chatwoot globalmente              │
   │     ├─ import './styles/globals.css'  ← dark theme tokens, animations                 │
   │     └─ createInertiaApp({...})                                                        │
   │                                                                                       │
   │  3. createInertiaApp:                                                                 │
   │     ├─ Le data-page JSON do <div id="app">                                           │
   │     ├─ resolve("Capture/Index")                                                       │
   │     │   └─ import.meta.glob('./pages/**/*.tsx')                                       │
   │     │     └─ dynamic import('./pages/Capture/Index.tsx')   ← lazy load                │
   │     ├─ render(                                                                        │
   │     │   <div>                                                                         │
   │     │     <ChatwootGlobalLoader />     ← injects Chatwoot SDK script                  │
   │     │     <App props={...} />          ← Inertia App wrapper                          │
   │     │   </div>                                                                        │
   │     │ )                                                                               │
   │     └─ App renders <CaptureIndex campaign={...} fingerprint_api_key="..." />          │
   │                                                                                       │
   │  4. CaptureIndex component:                                                           │
   │     ├─ <CaptureLayout backgroundImage="/static/images/bg-arthur-mostra-mao.jpg">     │
   │     │   ├─ <div style="background-image: url(/static/images/bg-arthur...jpg)">       │
   │     │   │   └─ Browser GET /static/images/bg-arthur-mostra-mao.jpg                   │
   │     │   │       └─ Django serves from src/static/images/ ← 263KB JPG                  │
   │     │   ├─ <div class="bg-black/60" />  ← dark overlay                               │
   │     │   ├─ <h1> "Descubra como imigrantes..." </h1>                                  │
   │     │   │   └─ HeadlineSegment: "ganhando +$10mil" → red pill bg                     │
   │     │   ├─ badges: "20-26 Janeiro 8pm" + "Ao vivo no Youtube"                        │
   │     │   ├─ social_proof: "+5.000 alunos"                                             │
   │     │   ├─ <CaptureForm campaignSlug="wh-rc-v3" formConfig={...}>                    │
   │     │   │   ├─ <FingerprintProvider apiKey="..." onResult={...} />                    │
   │     │   │   │   └─ FingerprintJS Pro: identify() → visitorId + requestId              │
   │     │   │   ├─ useForm({email, phone, visitor_id, utm_*})                             │
   │     │   │   ├─ useEffect → parse UTMs from URL search params                         │
   │     │   │   ├─ <Input label="Seu melhor e-mail" />                                   │
   │     │   │   ├─ <PhoneInput label="Seu WhatsApp" />                                   │
   │     │   │   └─ <Button gradient="from-[#0e036b] to-[#fb061a]">                       │
   │     │   │       QUERO PARTICIPAR GRATUITAMENTE                                        │
   │     │   │     </Button>                                                               │
   │     │   ├─ trust_badge: "Suas informacoes estao seguras"                              │
   │     │   └─ <LandingFooter /> ← Terms/Privacy modals + copyright                      │
   │     └─ </CaptureLayout>                                                               │
   │                                                                                       │
   │  5. ChatwootGlobalLoader (parallel):                                                  │
   │     ├─ window.chatwootSettings = {hideMessageBubble: true, ...}                       │
   │     ├─ inject <script src="https://atend.arthuragrelli.com/packs/js/sdk.js">          │
   │     └─ onload → chatwootSDK.run({token, baseUrl})  ← SDK ready for WhatsApp button   │
   │                                                                                       │
   │  PAGINA RENDERIZADA ✓                                                                 │
   └───────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Cenario 2 — Slug que NAO EXISTE

```
USUARIO                    BROWSER                      DJANGO :8844
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Digita: arthuragrelli.com/inscrever-bf-v99/
   ────────────────────────►
   GET /inscrever-bf-v99/
                                    ┌──────────────────────────────┐
                                    │  URL RESOLUTION               │
                                    │  re_path inscrever-(...)/     │
                                    │  ✓ slug = "bf-v99"            │
                                    │  → views.capture_page()       │
                                    └───────────┬──────────────────┘
                                                │
                                    ┌───────────▼──────────────────┐
                                    │  capture_page("bf-v99")       │
                                    │                               │
                                    │  1. get_campaign("bf-v99")    │
                                    │     └─ bf-v99.json exists?    │
                                    │        ✗ NO → return None     │
                                    │                               │
                                    │  2. campaign is None           │
                                    │     slug != "wh-rc-v3"        │
                                    │     → redirect(               │
                                    │        "/inscrever-wh-rc-v3/")│
                                    │                               │
                                    │  HTTP 302                     │
                                    │  Location: /inscrever-wh-rc-v3│
                                    └───────────┬──────────────────┘
                              ◄─────────────────┘
   302 Redirect
   ────────────────────────►
   GET /inscrever-wh-rc-v3/
                                    → (Cenario 1 — fluxo normal)
```

---

## Cenario 3 — Acesso via `/` (home)

```
USUARIO                    BROWSER                      DJANGO :8844
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Digita: arthuragrelli.com/
   ────────────────────────►
   GET /
                                    ┌──────────────────────────────┐
                                    │  URL RESOLUTION               │
                                    │  landing/urls.py              │
                                    │  ...todas as re_path...       │
                                    │  ✗ nenhuma match              │
                                    │  path("", views.home)         │
                                    │  ✓ MATCH (ultimo — catch-all) │
                                    └───────────┬──────────────────┘
                                                │
                                    ┌───────────▼──────────────────┐
                                    │  views.home()                 │
                                    │  → redirect(                  │
                                    │     "/inscrever-wh-rc-v3/")   │
                                    │                               │
                                    │  HTTP 302                     │
                                    └───────────┬──────────────────┘
                              ◄─────────────────┘
   302 Redirect → Cenario 1
```

---

## Cenario 4 — POST do formulario (lead submit)

```
USUARIO                    BROWSER                      DJANGO :8844                    CELERY        N8N
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Preenche email + phone, clica "QUERO PARTICIPAR GRATUITAMENTE"
   ────────────────────────►
   POST /inscrever-wh-rc-v3/
   Headers:
     Content-Type: multipart/form-data   ← forceFormData: true
     X-XSRF-TOKEN: abc123               ← Axios auto-sends from cookie
     X-Inertia: true                     ← Inertia request
     X-Inertia-Version: 1.0
   Body (form-data):
     email=joao@gmail.com
     phone=+5511999887766
     visitor_id=fp_abc123def456
     request_id=req_789
     utm_source=facebook
     utm_medium=cpc
     utm_campaign=wh0126

                                    ┌─────────────────────────────────────────────────┐
                                    │              MIDDLEWARE CHAIN                     │
                                    │                                                  │
                                    │  5. CsrfViewMiddleware                           │
                                    │     ├─ POST → validate CSRF                      │
                                    │     ├─ Cookie XSRF-TOKEN matches                 │
                                    │     │  Header X-XSRF-TOKEN? ✓                    │
                                    │     └─ PASS                                      │
                                    │                                                  │
                                    │ 10. InertiaJsonParserMiddleware                  │
                                    │     ├─ content_type = multipart/form-data        │
                                    │     ├─ NOT JSON → request.data = request.POST    │
                                    │     └─ request.data = {email, phone, visitor_id, │
                                    │                        utm_source, ...}          │
                                    └──────────────────────┬──────────────────────────┘
                                                           │
                                    ┌──────────────────────▼──────────────────────────┐
                                    │          views.capture_page() — POST             │
                                    │                                                  │
                                    │  1. get_campaign("wh-rc-v3") → cached dict ✓    │
                                    │  2. campaign is not None → no redirect           │
                                    │  3. request.method == "POST"                     │
                                    │     → _handle_capture_post()                     │
                                    └──────────────────────┬──────────────────────────┘
                                                           │
                                    ┌──────────────────────▼──────────────────────────┐
                                    │        _handle_capture_post()                    │
                                    │                                                  │
                                    │  1. data = request.data                          │
                                    │                                                  │
                                    │  2. CaptureService.validate_form_data(data)      │
                                    │     ├─ email "joao@gmail.com"                    │
                                    │     │  ├─ not empty ✓                            │
                                    │     │  ├─ regex match ✓                          │
                                    │     │  ├─ len < 254 ✓                            │
                                    │     │  └─ gmail.com not disposable ✓             │
                                    │     ├─ phone "+5511999887766"                    │
                                    │     │  ├─ not empty ✓                            │
                                    │     │  ├─ digits = 13 (≥7, ≤18) ✓               │
                                    │     │  └─ valid ✓                                │
                                    │     └─ errors = {} (VAZIO = VALIDO)              │
                                    │                                                  │
                                    │  3. Extract fields:                              │
                                    │     email = "joao@gmail.com"                     │
                                    │     phone = "+5511999887766"                     │
                                    │     visitor_id = "fp_abc123def456"               │
                                    │     utm_data = {source:"facebook", ...}          │
                                    └──────────────────────┬──────────────────────────┘
                                                           │
                                    ┌──────────────────────▼──────────────────────────┐
                                    │     CaptureService.process_lead()                │
                                    │                                                  │
                                    │  STEP 1 — Identity Resolution                    │
                                    │  ├─ CorrelationService.normalize_phone()         │
                                    │  │   "+5511999887766" → "5511999887766"           │
                                    │  ├─ ResolutionService                             │
                                    │  │   .resolve_identity_from_real_data(            │
                                    │  │     fingerprint={hash:"fp_abc123def456"},      │
                                    │  │     contact={email:"joao@gmail.com",           │
                                    │  │             phone:"5511999887766"})            │
                                    │  │   ├─ Search by fingerprint hash → Identity?   │
                                    │  │   ├─ Search by email → Identity?               │
                                    │  │   ├─ Search by phone → Identity?               │
                                    │  │   ├─ MERGE or CREATE Identity                  │──► PostgreSQL
                                    │  │   ├─ CREATE/UPDATE ContactEmail                │──► PostgreSQL
                                    │  │   ├─ CREATE/UPDATE ContactPhone                │──► PostgreSQL
                                    │  │   └─ return {identity_id, is_new, ...}        │
                                    │  │                                                │
                                    │  STEP 2 — Attribution                             │
                                    │  ├─ CorrelationService.save_attribution(          │
                                    │  │   identity,                                    │
                                    │  │   {utm_source:"facebook",                     │
                                    │  │    utm_medium:"cpc",                          │
                                    │  │    referrer:"...",                             │
                                    │  │    landing_page:"..."},                        │
                                    │  │   touchpoint_type="capture_form")             │──► PostgreSQL
                                    │  │                                                │
                                    │  STEP 3 — Build N8N payload                       │
                                    │  ├─ N8NProxyService.build_n8n_payload(            │
                                    │  │   email, phone, visitor_id, utm_data,          │
                                    │  │   campaign_config, page_url, referrer)         │
                                    │  └─ return {                                      │
                                    │       n8n_webhook_url: "https://n8n.arthur.../    │
                                    │         webhook/leads-lancamento-form",            │
                                    │       n8n_payload: {                               │
                                    │         "E-mail":"joao@gmail.com",                │
                                    │         "phone":"+5511999887766",                 │
                                    │         "utm_source_cp":"facebook",               │
                                    │         "fingerprint":"fp_abc123def456",          │
                                    │         "launch_code":"WH0126",                   │
                                    │         "list":"424",                             │
                                    │         "form_id":"754ef07d",                     │
                                    │         "timestamp":"2026-02-15T..."              │
                                    │       }                                           │
                                    │     }                                             │
                                    └──────────────────────┬──────────────────────────┘
                                                           │
                                    ┌──────────────────────▼──────────────────────────┐
                                    │   Back in _handle_capture_post()                 │
                                    │                                                  │
                                    │  4. n8n_webhook_url is not empty                 │
                                    │     → send_to_n8n_task.delay(url, payload)       │──────────────────►
                                    │       (async — NAO bloqueia o response)          │    Celery worker
                                    │                                                  │    picks up task
                                    │  5. thank_you_url = "/obrigado-wh-rc-v3/"       │         │
                                    │     → redirect(thank_you_url)                    │         │
                                    │                                                  │         ▼
                                    │  HTTP 303 (Inertia redirect)                     │    ┌────────────────┐
                                    │  X-Inertia-Location: /obrigado-wh-rc-v3/         │    │ send_to_n8n()  │
                                    └──────────────────────┬──────────────────────────┘    │                │
                                                           │                              │ N8NProxyService │
                              ◄────────────────────────────┘                              │ .send_to_n8n(  │
   Inertia intercepts 303                                                                 │  webhook_url,  │
   ────────────────────────►                                                              │  payload)      │
   GET /obrigado-wh-rc-v3/                                                                │                │
   X-Inertia: true                                                                        │ httpx.post() ──┼──►
   X-Inertia-Version: 1.0         ┌──────────────────────────────────────┐                │ timeout=15s    │  N8N
                                   │  views.thank_you_page("wh-rc-v3")    │                │ max_retries=3  │  Webhook
                                   │                                      │                │                │
                                   │  get_campaign → cached ✓             │                │ success? ✓     │  ├─ ActiveCamp.
                                   │  Build thank_you_props               │                │ log: "sent OK" │  ├─ Mautic tag
                                   │  inertia_render("ThankYou/Index",    │                └────────────────┘  ├─ WhatsApp
                                   │    {campaign, thank_you}, "landing") │                                    └─ Slack notif
                                   │                                      │
                                   │  X-Inertia: true → JSON response     │
                                   │  (NOT full HTML — SPA navigation)    │
                                   │                                      │
                                   │  HTTP 200                            │
                                   │  Content-Type: application/json      │
                                   │  {                                   │
                                   │   "component":"ThankYou/Index",      │
                                   │   "props":{                          │
                                   │     "campaign":{slug:"wh-rc-v3",...},│
                                   │     "thank_you":{                    │
                                   │       headline:"NAO FECHE...",       │
                                   │       whatsapp_group_link:"...",     │
                                   │       countdown_minutes:15,          │
                                   │       progress_percentage:66         │
                                   │     }                                │
                                   │   },                                 │
                                   │   "url":"/obrigado-wh-rc-v3/"       │
                                   │  }                                   │
                                   └─────────────┬────────────────────────┘
                              ◄──────────────────┘
   Inertia swaps component
   (NO full page reload)
   ThankYou/Index renders:
     - Red banner "NAO FECHE"
     - Progress bar 66%
     - WhatsApp CTA button
     - Countdown 15min
     - LandingFooter
```

---

## Cenario 5 — POST com validacao INVALIDA

```
USUARIO                    BROWSER                      DJANGO :8844
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Submete form com email vazio e phone "123"
   ────────────────────────►
   POST /inscrever-wh-rc-v3/
   Body: email=&phone=123
                                    ┌──────────────────────────────────┐
                                    │  _handle_capture_post()           │
                                    │                                   │
                                    │  CaptureService.validate_form_data│
                                    │  ├─ email "" → empty              │
                                    │  │  errors["email"] =             │
                                    │  │    "E-mail e obrigatorio."     │
                                    │  ├─ phone "123" → digits=3 (<7)  │
                                    │  │  errors["phone"] =             │
                                    │  │    "Telefone invalido."        │
                                    │  └─ errors = {email:...,phone:...}│
                                    │                                   │
                                    │  errors is not empty              │
                                    │  → _render_capture_page(          │
                                    │      errors=errors)               │
                                    │                                   │
                                    │  RE-RENDER Capture/Index          │
                                    │  props.errors = {                 │
                                    │    email:"E-mail e obrigatorio.", │
                                    │    phone:"Telefone invalido."     │
                                    │  }                                │
                                    │                                   │
                                    │  HTTP 200 (Inertia JSON)          │
                                    └──────────────┬───────────────────┘
                              ◄────────────────────┘
   Inertia re-renders page
   with errors inline:
     [Email] "E-mail e obrigatorio."  ← red border + message
     [Phone] "Telefone invalido."     ← red border + message

   (SEM redirect, SEM page reload)
```

---

## Mapa de decisao do servidor

```
                            GET /inscrever-{slug}/
                                    │
                        ┌───────────▼──────────┐
                        │  get_campaign(slug)   │
                        │  JSON file exists?    │
                        └───────┬───────┬──────┘
                            YES │       │ NO
                                │       │
                                ▼       ▼
                        ┌───────┐  ┌──────────────┐
                        │ Load  │  │ slug ==       │
                        │ JSON  │  │ "wh-rc-v3"?  │
                        │ config│  └──┬────────┬──┘
                        └───┬───┘  YES│        │NO
                            │       ▼        ▼
                            │  ┌────────┐  ┌──────────────────┐
                            │  │defaults│  │302 Redirect to   │
                            │  │generate│  │/inscrever-wh-rc-v3│
                            │  └───┬────┘  └──────────────────┘
                            │      │
                            ▼      ▼
                        ┌──────────────────┐
                        │ request.method?  │
                        └──┬────────────┬──┘
                        GET│            │POST
                           ▼            ▼
                  ┌────────────┐  ┌──────────────────┐
                  │Inertia     │  │validate_form_data│
                  │render      │  └──┬────────────┬──┘
                  │Capture/    │  OK │         FAIL│
                  │Index       │     ▼            ▼
                  │+ props     │ ┌────────┐  ┌──────────┐
                  └────────────┘ │process │  │re-render │
                                 │_lead() │  │with      │
                                 │        │  │errors    │
                                 └───┬────┘  └──────────┘
                                     │
                              ┌──────▼───────┐
                              │Identity      │
                              │Resolution    │
                              │+ Attribution │
                              │+ N8N task    │
                              └──────┬───────┘
                                     │
                              ┌──────▼───────┐
                              │302 Redirect  │
                              │/obrigado-    │
                              │{slug}/       │
                              └──────────────┘
```

---

## Arquivos envolvidos

| Camada | Arquivo | Responsabilidade |
|--------|---------|------------------|
| URL | `config/urls.py` | Route to landing app (last) |
| URL | `apps/landing/urls.py` | `re_path inscrever-{slug}` → `capture_page` |
| View | `apps/landing/views.py` | GET/POST dispatch, props building, redirect |
| Config | `apps/landing/campaigns/__init__.py` | JSON loader with in-memory cache |
| Config | `apps/landing/campaigns/wh-rc-v3.json` | Campaign visual + form + N8N config |
| Service | `apps/landing/services/capture.py` | Validation, identity resolution, N8N payload |
| Service | `apps/landing/services/n8n_proxy.py` | Build N8N payload, httpx POST with retry |
| Task | `apps/landing/tasks/__init__.py` | Celery async task for N8N webhook |
| Helper | `core/inertia/helpers.py` | `inertia_render()` with multi-app layout |
| Middleware | `core/inertia/middleware.py` | JSON parser, shared props, guards |
| Template | `templates/landing.html` | Vite assets, Inertia `data-page` div |
| Frontend | `frontends/landing/src/main.tsx` | Inertia app bootstrap + ChatwootGlobalLoader |
| Frontend | `frontends/landing/src/pages/Capture/Index.tsx` | Page component |
| Frontend | `frontends/landing/src/layouts/CaptureLayout.tsx` | Background image + footer |
| Frontend | `frontends/landing/src/components/CaptureForm.tsx` | Email/phone form + UTMs |
| Frontend | `frontends/landing/src/components/PhoneInput.tsx` | International phone input |
| Frontend | `frontends/landing/src/components/FingerprintProvider.tsx` | FingerprintJS Pro SDK |

---

## Analise Funcional: Legado vs Novo (com contexto de paradigma)

> Scan realizado em 2026-02-15.
> Arquivos legados analisados: ~2.800 linhas (capture-form.tsx, capture-config.js, 8x page.json, email-validation.ts, url-enrichment.ts, use-form-tracker.ts, black-friday-layout.tsx, mentoria-banner.tsx, page-layout-v2.tsx, capture-config-context.tsx).
>
> **PARADIGMA FUNDAMENTAL**: O legado era NextJS (frontend-heavy, browser executa tudo). O novo e Django+Inertia (server-driven, Django controla logica e config, frontend renderiza). Muitas features que rodavam no browser agora DEVEM rodar no Django. N8N deixa de ser necessario para persistencia — Django+ORM assume esse papel.

---

### Componente CaptureForm compartilhado

**Status**: CONFIRMADO — manter form unico compartilhado entre todas as paginas de captura.

O legado tinha `components/capture-form.tsx` (758 linhas) usado por todas as 10 variantes. O novo ja tem `CaptureForm.tsx` no landing. Decisao aprovada: continuar com form unico, componentizado.

---

### F1. VALIDACAO DE EMAIL AVANCADA

**Prioridade**: P0 | **Status**: GAP CONFIRMADO

**O que o legado fazia (frontend NextJS):**
- Validacao com debounce (300ms) via `useDebouncedCallback`
- Lista de 20 dominios temporarios bloqueados
- Sugestao de correcao de dominio ("gmial.com" → "Voce quis dizer: gmail.com?") com botao clicavel
- 12 correcoes mapeadas (gmail, hotmail, outlook, yahoo — typos comuns)
- Validacao de caracteres suspeitos (`[._-]{2,}`)
- Auto-lowercase do email ao digitar

**O que o novo tem:**
- Validacao apenas no servidor (regex + len + disposable)
- Nenhuma validacao frontend em tempo real

**Decisao**: IMPLEMENTAR no novo. A validacao de email com sugestao de correcao de typo e feature de alta conversao — evita perda de leads por erro de digitacao. No novo paradigma:
- **Frontend**: Debounce + sugestao de correcao + auto-lowercase (UX imediata, nao depende do server)
- **Backend**: Validacao definitiva (regex, disposable, len) — ja existe, manter

---

### F2. AUTO-FILL VIA LOCALSTORAGE + FINGERPRINT

**Prioridade**: P1 | **Status**: GAP CONFIRMADO + EXPANDIDO

**O que o legado fazia:**
- Auto-fill email/phone do `localStorage` no mount
- Salvar email/phone apos sucesso do webhook (nao antes)
- Salvar tracking data completo (`lead_tracking_data`, `lead_enriched_url`)

**O que o novo tem:**
- Nada. Nao salva nem recupera dados.

**Decisao**: IMPLEMENTAR + EXPANDIR. Alem do localStorage basico, incorporar:
- **visitorId do FingerprintJS** como identificador persistente cross-sessao
- Qualquer informacao imutavel/persistente a longo prazo para identificacao inicial
- Ao retornar, se o visitorId ja for conhecido, buscar dados do lead no Django (nome, email parcial) e pre-preencher
- O Django pode expor um endpoint leve (ou shared prop) que retorna dados conhecidos do visitor

**Paradigma**: O localStorage continua no frontend (rapido, sem roundtrip). Mas o Django pode ENRIQUECER os dados via visitorId quando disponivel.

---

### F3. ANALYTICS DE ACESSO E CONVERSAO (ex- "PRE-SUBMIT")

**Prioridade**: P0 | **Status**: GAP CONFIRMADO + REDESENHADO

**O que o legado fazia:**
- Evento analytics ANTES do POST do form (tentativa de submit)
- Payload com 20+ campos enviado para `webhookFingerprint` no N8N
- N8N persistia no Baserow (acessos, email, phone, visitorId, requestId)
- Custom event `formSubmit` disparado no browser

**O que o novo tem:**
- Apenas Celery task pos-submit para N8N
- Nenhum tracking de acesso a pagina (apenas quem completou o form)

**Decisao**: IMPLEMENTAR — mas **sem N8N**. O Django+ORM assume o papel que N8N+Baserow tinham:

1. **Tracking de acesso (page view)**: Middleware ou view registra cada acesso a `/inscrever-*` no banco. Dados: IP, user_agent, visitorId (se disponivel via cookie/header), UTMs, referrer, timestamp. Pode ser async via Celery task fire-and-forget.

2. **Tracking de tentativa de submit (form_submit_attempt)**: No POST, ANTES de validar, registrar a tentativa. Mesmo que a validacao falhe, sabemos que o usuario tentou.

3. **Tracking de conversao (form_submit_success)**: Apos validacao OK e identity resolution, registrar conversao.

4. **Metricas em tempo real**: Com Django, podemos fazer queries diretas para saber "pagina X teve 500 acessos e 50 conversoes = 10% taxa". Sem depender de N8N+Baserow.

**Modelo sugerido**: `PageView` ou `CaptureEvent` (type: `view` | `attempt` | `conversion`, page_slug, visitor_id, utm_data, timestamp, etc.).

**Paradigma**: Tudo server-side. O frontend so precisa enviar os dados no POST (que ja faz). O tracking de page view e automatico via middleware/view no GET.

---

### F4. CAPTURA DE DADOS ENRIQUECIDOS + COMUNICACAO BI-DIRECIONAL

**Prioridade**: P1 | **Status**: GAP CONFIRMADO + REDESENHADO

**O que o legado fazia (frontend):**
- `enrichCaptureUrl()` adicionava 15+ parametros a URL de origem
- Page load time via `performance.timing`
- UTMs com prefixo `_cp` duplicados
- Email/phone na URL enriquecida

**O que o novo tem:**
- Frontend envia UTMs raw no POST
- Nenhum enriquecimento

**Decisao**: REDESENHAR para o paradigma Django+Inertia:

1. **Captura de UTMs/referrer**: O Django ja recebe tudo no request (headers, query params, cookies). A view ou middleware extrai UTMs, referrer, user_agent, IP — sem depender do frontend para isso.

2. **Page load time**: Em vez de medir no frontend e enviar, duas opcoes melhores:
   - **Server-side**: Middleware pode medir tempo de processamento da view (request → response)
   - **Client-side nao-bloqueante**: React 19+ com Inertia pode enviar um "update" pos-carga via `router.post()` silencioso com `performance.now()` — sem bloquear a exibicao da pagina

3. **Comunicacao bi-direcional (pagina ↔ Django)**:
   - **Django → Pagina**: Shared props, cache de dados imutaveis, props de campanha
   - **Pagina → Django**: POST silencioso pos-carga com metricas de performance, fingerprint resolvido, viewport size
   - Redis para sessao de captura: criar sessao anonima no GET, enriquecer com dados no POST silencioso, finalizar com dados do form submit

4. **Cache de pagina**: O HTML da pagina de captura pode ser cacheado (Redis) para tudo que e imutavel (config, headline, badges, background). Apenas shared props dinamicos (flash, etc.) sao injetados. Resultado: tempo de resposta < 50ms para paginas cacheadas.

**Paradigma**: O frontend NAO precisa enriquecer URLs. O Django ja tem todos os dados no request. O enriquecimento acontece server-side, no service layer, antes de persistir.

---

### F5. REFERRER HISTORY

**Prioridade**: P1 | **Status**: GAP CONFIRMADO (SIMPLIFICADO)

**O que o legado fazia:**
- `origem_lead_history_1`: `document.referrer`
- `origem_lead_history_2`: `sessionStorage.getItem('previous_referrer')`

**O que o novo tem:**
- Nada.

**Decisao**: IMPLEMENTAR apenas o **primeiro nivel**. `document.referrer` no frontend OU `request.META.get('HTTP_REFERER')` no Django. Remover o segundo nivel — complexidade sem retorno comprovado.

**Paradigma**: O Django ja recebe o `Referer` header no request. Nao precisa do frontend para isso.

---

### F6. CONFIG VIA DJANGO (ex- "CAPTURE CONFIG EXTERNO")

**Prioridade**: P0 (estrutural) | **Status**: REDESENHO TOTAL

**O que o legado fazia:**
- `capture-config.js` (900 linhas) no Minio S3 com fallback local
- Hot-reload sem rebuild/redeploy
- 5 interesses, form IDs por versao, copy por interesse, template engine (`{{dates.displayText}}`)

**O que o novo tem:**
- JSONs estaticos no filesystem (`campaigns/wh-rc-v3.json`)
- Sem hot-reload — precisa editar arquivo + restart

**Decisao**: MIGRAR CONFIG PARA DJANGO. O Django se torna a unica fonte de verdade:

1. **Modelo**: A pagina de captura e registrada como parte de um Lancamento. Cada pagina tem um `JSONField` (ou campos estruturados) com a config: headline, badges, background, form config, etc.

2. **Padrao de config**: Heranca de defaults. O lancamento define valores base (launch_code, dates, endpoints). Cada pagina pode sobrescrever (headline, background, CTA). Se nao sobrescrever, herda do lancamento.

3. **Cache**: View ou middleware le a config do banco, cacheia no Redis. `post_save` signal invalida o cache. Resultado: primeira request = DB hit + cache set. Proximas = cache hit (< 1ms).

4. **Hot-reload real**: Editar config no Django Admin (ou via API) → `post_save` invalida cache → proxima request serve config nova. Zero redeploy, zero restart.

5. **Template engine**: Django ja tem template engine. `{{dates.displayText}}` se torna `launch.dates_display_text` direto no Python — sem engine JS customizada.

6. **Admin**: django-unfold para gerenciar configs de paginas de captura com preview.

**Paradigma**: Minio existia para contornar a limitacao do NextJS (rebuild para mudar config). Com Django, a config e dados no banco. O frontend recebe tudo pronto via props.

---

### F7. FORM HEADER CONFIGURAVEL

**Prioridade**: P3 | **Status**: GAP CONFIRMADO

**O que o legado fazia:**
- `form.header.enabled` / `.title` / `.subtitle` via page.json

**Decisao**: IMPLEMENTAR via config Django. Campo no JSONField da pagina de captura. A maioria das variantes tem `enabled: false`, mas a opcao deve existir.

---

### F8. GLASS EFFECT + PATRIOTIC EFFECT

**Prioridade**: P3 | **Status**: GAP CONFIRMADO (MANTER SUPORTE)

**O que o legado fazia:**
- `form.glassEffect` e `form.showPatrioticEffect` — flags no JSON, sempre `false` nas 8 variantes analisadas

**Decisao**: MANTER como flags na config. Nao implementar os efeitos visuais agora, mas o campo deve existir no schema para ativacao futura. Quando o designer pedir backdrop-blur, e so ativar a flag.

---

### F9. TOP BANNER / MENTORIA BANNER

**Prioridade**: P1 | **Status**: GAP CONFIRMADO

**O que o legado fazia:**
- `MentoriaBanner` (v1): Banner fixo gradient com texto "CURSO PRATICO E GRATUITO..."
- `topBanner` (BF): Sticky, configuravel via JSON (texto, cores, fontSize, padding)

**O que o novo tem:**
- Nenhum banner no topo.

**Decisao**: IMPLEMENTAR como componente configuravel via campaign config. Campos: `enabled`, `text`, `backgroundColor`, `textColor`, `sticky`, `fontSize`. Renderizado pelo `CaptureLayout` quando `topBanner.enabled: true`.

---

### F10. BLACK FRIDAY LAYOUT (LAYOUT ALTERNATIVO)

**Prioridade**: P2 | **Status**: GAP CONFIRMADO

**O que o legado fazia:**
- Layout two-column com grid `md:grid-cols-[720px_1fr]`
- Logo Black Friday, description com MarkerText, expert image, footer cross-image
- Botao verde `bg-[#00FF00]` com texto preto
- `pageStructure` configuravel (ordem dos componentes)

**Decisao**: IMPLEMENTAR como layout alternativo. No config Django, campo `layout_type`: `"standard"` (atual) ou `"two-column"` (BF style). O frontend resolve qual layout componente usar. Nao precisa de 1 layout por campanha — 2-3 layouts base cobrem todos os casos.

---

### F11. BACKGROUND IMAGE AVANCADO

**Prioridade**: P2 | **Status**: GAP PARCIAL

**O que o legado fazia:**
- Positions (desktop/mobile/freeze/horizontal), breakpoints, overlay configuravel, effects (blur/parallax)
- `OptimizedBackgroundSimple` com 15+ props

**O que o novo tem:**
- URL da imagem + overlay `bg-black/60` hardcoded

**Decisao**: IMPLEMENTAR positions e overlay configuravel no config. Parallax e blur ficam para futuro. A visao de longo prazo (subdominio `m.` com assets diferentes por device) e registrada mas NAO implementada agora.

**Paradigma**: O Django pode detectar o device via user-agent e servir props diferentes (background mobile vs desktop) direto na view. O frontend so aplica o que recebe.

---

### F12. SEGMENTACAO POR INTERESSE

**Prioridade**: P1 (estrutural) | **Status**: REDESENHO VIA DJANGO

**O que o legado fazia:**
- 5 interesses (rc, td, ds, cp, bf) com `listId`, `thankYouUrl`, `name`, `enabled`
- Deteccao automatica pela URL
- Copy e background diferentes por interesse

**O que o novo tem:**
- Campaign JSONs independentes, sem conceito de "interesse"

**Decisao**: ABSORVER no Django. O conceito de interesse se torna uma **relacao no modelo**:
- Lancamento has_many Paginas de Captura
- Pagina de Captura belongs_to Interesse (ou Tag/Categoria)
- O interesse define defaults (listId para CRM, thankYouUrl, copy base)
- A pagina pode sobrescrever qualquer campo do interesse

**Paradigma**: Com o dado cru chegando no Django server e tendo Celery (sync/async), create/update, FSM — o processamento e infinitamente mais poderoso que o legado. O Django pode:
- Resolver identidade
- Aplicar tags por interesse automaticamente
- Disparar automacoes por tipo de interesse
- Atualizar status do lead em tempo real
- Tudo sem depender de CRM externo para a logica core

---

### F13. FINGERPRINT RETRY + INTEGRACAO SERVER-SIDE

**Prioridade**: P0 (CRITICO) | **Status**: GAP CONFIRMADO + PESQUISA NECESSARIA

**O que o legado fazia:**
- `useFingerprintRetry` com backoff exponencial (10 tentativas, 500ms-5000ms)
- Polling a cada 500ms via `setInterval` checando resultado
- Timeout de 10s, DOM manipulation de hidden fields

**O que o novo tem:**
- `FingerprintProvider` com callback `onResult` — single attempt

**Decisao**: PESQUISAR + IMPLEMENTAR solucao robusta. Pontos criticos:

1. **React SDK do FPJS Pro**: Verificar se o `@fingerprintjs/fingerprintjs-pro-react` ja tem retry built-in. Se sim, configurar. Se nao, implementar wrapper com retry.

2. **Python Server API do FPJS Pro**: Existe SDK Python (`fingerprint-pro-server-api-sdk`) que permite:
   - Buscar eventos por `visitorId` (server-to-server, sem depender do browser)
   - Expandir informacoes do visitor (geolocation, bot detection, incognito, VPN)
   - Webhook de eventos do FPJS Pro direto para o Django
   - Isso ELIMINA a necessidade do frontend enviar `requestId` — o Django busca direto na API do FPJS

3. **Fluxo ideal**:
   - Frontend: Obter `visitorId` o mais rapido possivel (React SDK com retry)
   - Frontend: Enviar `visitorId` no POST do form
   - Backend: Usar Python SDK para expandir dados do visitor (async via Celery)
   - Backend: Webhook do FPJS Pro para receber eventos em tempo real

4. **Nao bloquear pagina**: O `visitorId` deve ser obtido em background. Se nao estiver pronto no momento do submit, o form submete sem ele e o Django resolve depois via sessao ou cookie temporario.

**Este topico requer fase de pesquisa dedicada antes da implementacao.**

---

### F14. FORM FIELD STYLING PER-CAMPAIGN

**Prioridade**: P3 | **Status**: GAP CONFIRMADO

**O que o legado fazia:**
- `form.fields.email.bgColor`, `.textColor`, `.borderColor` por variante
- Botao com cores e texto customizaveis por campanha

**Decisao**: MANTER possibilidade aberta no schema de config. Implementar quando necessario (BF precisa de botao verde/texto preto). O config Django suporta, o frontend aplica condicionalmente.

---

### F15. DEBUG E OBSERVABILIDADE

**Prioridade**: P2 | **Status**: REDESENHO

**O que o legado fazia:**
- `?debug=true` mostrava `ConfigDebug` overlay com toda a config
- `?mode=dynamic/static/hybrid` forcava modo de carregamento

**Decisao**: IMPLEMENTAR observabilidade adequada para Django+Inertia:

1. **Django Debug Toolbar (DjDT)**: Ja essencial. Monitorar queries por request, detectar N+1, medir tempo de view. Em outro projeto ja detectamos queries pesadas — nao podemos repetir.

2. **Config inspector**: Em dev mode, endpoint `/app/debug/capture-config/{slug}/` retorna o JSON completo da config resolvida (com heranca de defaults aplicada). Util para verificar o que o frontend recebe.

3. **Performance headers**: Middleware que adiciona `X-View-Time-Ms` no response header. Permite medir tempo de processamento sem DjDT.

4. **Logging estruturado**: Logs de capture events com correlation_id para rastrear fluxo completo (GET → fingerprint → POST → identity resolution → celery task).

---

## Tabela de decisoes atualizada

| # | Tema | Decisao | Onde executa | Justificativa |
|---|------|---------|--------------|---------------|
| D1 | Validacao email avancada (F1) | IMPLEMENTAR | Frontend (debounce + sugestao) + Backend (definitiva) | Evita perda de leads por typo |
| D2 | Auto-fill + fingerprint (F2) | IMPLEMENTAR + EXPANDIR | Frontend (localStorage) + Backend (visitorId lookup) | Melhora conversao de retornantes |
| D3 | Analytics de acesso/conversao (F3) | IMPLEMENTAR SEM N8N | Backend (Django ORM + Celery) | Django substitui N8N+Baserow |
| D4 | Dados enriquecidos + bidirecional (F4) | REDESENHAR | Backend (extrai do request) + Frontend (POST silencioso pos-carga) | Django ja tem os dados, frontend complementa |
| D5 | Referrer history (F5) | IMPLEMENTAR (1 nivel) | Backend (`HTTP_REFERER` header) | Simplificado — so primeiro nivel |
| D6 | Config via Django (F6) | MIGRAR PARA DJANGO | Backend (DB + Redis cache + post_save) | Elimina Minio, hot-reload real via Admin |
| D7 | Form header configuravel (F7) | IMPLEMENTAR | Config Django (JSONField) | Baixa prioridade, campo no schema |
| D8 | Glass/patriotic effects (F8) | MANTER FLAGS | Config Django (campos boolean) | Nao implementar efeitos agora, so flags |
| D9 | Top banner (F9) | IMPLEMENTAR | Config Django + Frontend (componente) | Elemento de persuasao configuravel |
| D10 | Black Friday layout (F10) | IMPLEMENTAR | Config Django (`layout_type`) + Frontend (2-3 layouts base) | Necessario para campanhas especiais |
| D11 | Background avancado (F11) | IMPLEMENTAR PARCIAL | Config Django (positions, overlay) | Parallax/blur = futuro |
| D12 | Segmentacao por interesse (F12) | ABSORVER NO DJANGO | Backend (modelo Interesse + relacoes) | Django assume papel do CRM para logica core |
| D13 | Fingerprint retry + server (F13) | PESQUISAR + IMPLEMENTAR | Frontend (React SDK retry) + Backend (Python SDK FPJS) | Critico — requer fase de pesquisa |
| D14 | Field styling per-campaign (F14) | MANTER POSSIBILIDADE | Config Django (campos opcionais) | Implementar sob demanda |
| D15 | Debug e observabilidade (F15) | IMPLEMENTAR | Backend (DjDT + headers + logging) | Essencial para qualidade e performance |

---

## Resumo de prioridades revisado

| Prio | Gaps | Esforco total estimado |
|------|------|----------------------|
| **P0** | F1 (email validation), F3 (analytics Django), F6 (config Django), F13 (fingerprint) | Alto — estrutural |
| **P1** | F2 (auto-fill+fp), F4 (dados enriquecidos), F5 (referrer), F9 (banner), F12 (segmentacao) | Medio |
| **P2** | F10 (BF layout), F11 (background), F15 (debug/observabilidade) | Medio |
| **P3** | F7 (form header), F8 (effects flags), F14 (field styling) | Baixo |

---

## Diagnostico profundo do estado atual

> Verificacao realizada em 2026-02-15. Leitura direta do codigo-fonte, nao de suposicoes.

### Resumo executivo

| Area | Status | Detalhe |
|------|--------|---------|
| FingerprintJS versao | **OSS (nao Pro)** | `@fingerprintjs/fingerprintjs` (pacote open-source) |
| requestId | **FALSO** | Gerado client-side com `Date.now()-Math.random()` — zero valor de verificacao |
| localStorage | **Nao usado** | Nenhuma persistencia de formulario ou deteccao de visitante retornante |
| Debounce no email | **Inexistente** | Nenhum debounce em nenhum campo de input |
| capture_token | **Nao existe** | Nao gerado no server, nao enviado ao frontend, nao rastreado |
| Tracking de conversao | **Completamente ausente** | Sem FB Pixel, GA, GTM, ou eventos customizados |
| process_lead() | **Sincrono** | Identity resolution + attribution roda no ciclo do request. So N8N e async (Celery) |
| FingerprintProvider | **Escopo por-form, nao global** | Montado DENTRO de CaptureForm, nao em main.tsx. Sem React Context |
| Resiliencia de erros | **Swallow silencioso** | Todas as falhas de identity/attribution sao capturadas e logadas, form continua |
| Fallback sem fingerprint | **Hash fake do email** | `{"hash": f"no-fp-{email}"}` usado como substituto |
| Sinais/analytics | **Nenhum** | Sem signal `lead_captured`, sem metricas, sem event recording |
| ThankYou tracking | **Nenhum** | Sem correlacao com a captura, sem eventos de conversao |

### Detalhes por arquivo

#### FingerprintProvider.tsx (51 linhas)

```
Imports:   @fingerprintjs/fingerprintjs  ← pacote OSS (nao Pro)
Linha 29:  "Uses the open-source FingerprintJS library."
Linha 38:  requestId = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`  ← FAKE
Linha 42:  Falha = console.warn() — nao bloqueia
Linha 24:  if (!apiKey || hasLoaded.current) return  ← apiKey e guard, mas OSS nao usa API key
```

**Impacto**: O `requestId` que chega no backend e inutil para verificacao server-side via FPJS Pro API. O `visitorId` do OSS tem precisao de ~60% (vs ~99.5% do Pro). Toda a cadeia de identity resolution opera com fingerprint de baixa qualidade.

#### CaptureForm.tsx (133 linhas)

```
Form fields:  email, phone, visitor_id, request_id, utm_source/medium/campaign/content/term/id
Linha 45-69:  UTMs lidos de window.location.search no mount
Linha 86-91:  post(`/inscrever-${campaignSlug}/`, { forceFormData: true })
Linha 95-98:  <FingerprintProvider> montado inline, nao como context
```

**Ausente**: Zero localStorage, zero debounce, zero capture_token, zero callbacks `onBefore/onSuccess/onError`, zero eventos de analytics no submit, zero tracking de abandono de form.

#### Capture/Index.tsx (200 linhas)

```
Props:  { campaign, fingerprint_api_key, errors }
```

**100% presentacional**. Nenhum `useEffect` para page-view tracking. Nenhum capture_token nas props. Nenhum scroll tracking. Nenhum A/B test variant ID.

#### landing/views.py — _handle_capture_post() (linhas 116-173)

```
Linha 125:   data = getattr(request, "data", request.POST)
Linha 128:   CaptureService.validate_form_data(data)          ← SINCRONO
Linha 133-6: Extrai email, phone, visitor_id, request_id
Linha 139-6: Extrai 6 campos UTM
Linha 152-61: CaptureService.process_lead(...)                ← SINCRONO (bloqueia redirect)
Linha 164-7: send_to_n8n_task.delay(url, payload)             ← ASYNC (unico ponto)
Linha 170-3: redirect para /obrigado-{slug}/
```

**Diagrama de bloqueio**:

```
Request ──► validate (sync) ──► process_lead (sync) ──► send_n8n (async) ──► redirect
                                      │
                                      ├─ ResolutionService (DB queries)
                                      ├─ CorrelationService (DB queries)
                                      └─ Attribution (DB write)
                                      
Tempo total no request: validacao + identity resolution + attribution + redirect
Se DB estiver lento: usuario espera TUDO antes de ver a thank-you page
```

#### services/capture.py — CaptureService.process_lead() (linhas 93-200)

```
1. fingerprint_data = {"hash": visitor_id}                    ← linha 130
2. Se visitor_id vazio → {"hash": f"no-fp-{email}"}          ← linha 147-158 (hash fake)
3. ResolutionService.resolve_identity_from_real_data()        ← DB-heavy
4. CorrelationService.save_attribution()                      ← DB write
5. N8NProxyService.build_n8n_payload()                        ← dict builder (leve)
6. return {resolution, identity_id, is_new, n8n_payload, url}
```

**Observacao critica**: Quando nao ha fingerprint, o sistema cria um hash fake baseado no email (`no-fp-joao@gmail.com`). Isso contamina a tabela `FingerprintIdentity` com registros que nao representam fingerprints reais.

#### ThankYou/Index.tsx (103 linhas)

```
Props:  { campaign, thank_you }
Unico useEffect: beforeunload prevention (UX, nao tracking)
```

**Zero tracking**: Nenhum FB Pixel, GA, fingerprint, capture_token, ou correlacao com a captura que gerou a visita.

#### main.tsx (33 linhas)

```
Componentes globais: ChatwootGlobalLoader (unico)
FingerprintProvider: NAO esta aqui — vive dentro de CaptureForm
```

**Consequencia**: Fingerprint so carrega na pagina Capture. Se o usuario navega para ThankYou, Support, Checkout — nenhum fingerprinting acontece. Nenhum React Context global para fingerprint.

---

## Modelo CaptureEvent — Design detalhado (REVISADO v3.1 — Tracker Universal)

### Motivacao

O modelo `FingerprintEvent` existente em `contacts/fingerprint/models.py` tem **FK obrigatoria** para `FingerprintIdentity`. Isso impede o registro de eventos anonimos (page views sem fingerprint). Precisamos de um modelo que:

1. Aceite eventos **anonimos** (view sem fingerprint)
2. Aceite eventos **semi-identificados** (form attempt com email mas sem fingerprint)
3. Aceite eventos **identificados** (form success com fingerprint + identity)
4. Suporte **binding retroativo** (view anonima → linked ao identity apos form success)
5. **(v3.1) Rastreie TODAS as paginas** — nao apenas captura, mas checkout, thank-you, support, conteudo, vendas, dashboard

### Redesign v3.1 — Tracker universal

> **Mudanca arquitetural**: CaptureEvent deixa de ser acoplado a "paginas de captura de lancamentos" e se torna um tracker universal de TODAS as paginas do sistema. O campo `campaign_slug` e substituido por `page_path` (qualquer URL). A FK `capture_page` se torna opcional e complementar.

**Onde vive**: `src/core/tracking/models.py` (novo app, nao mais em `apps/landing/`).

### DeviceProfile — Dimension table (padrao Matomo star schema)

> **Problema**: Armazenar "Chrome" 50.000 vezes na tabela de eventos desperdia storage e dificulta queries.
> **Solucao**: Dimension table com hash-based dedup. Cada combinacao unica de browser+OS+device = 1 linha.
> **Padrao**: Star schema do Matomo — referencia da industria para analytics em PostgreSQL.

```python
# src/core/tracking/models.py

class DeviceProfile(BaseModel):
    """Perfil de dispositivo normalizado. Criado UMA VEZ, referenciado por muitos eventos.
    
    Padrao: star schema (Matomo). Hash-based dedup via profile_hash.
    Cardinalidade esperada: ~200-1.000 linhas (vs milhoes de eventos).
    Cada evento armazena apenas um FK de 4 bytes ao inves de ~200 bytes de strings.
    """
    
    PUBLIC_ID_PREFIX = "dpf"
    
    # Hash unico para dedup rapida (SHA-256 truncado, 32 hex chars)
    # Computado de: browser_family|browser_version_major|os_family|os_version|device_type
    profile_hash = models.CharField(max_length=32, unique=True, db_index=True)
    
    # ─── BROWSER ───
    browser_family = models.CharField(max_length=50)    # "Chrome", "Firefox", "Safari"
    browser_version = models.CharField(max_length=20)    # major version: "120", "17"
    browser_engine = models.CharField(max_length=30, blank=True)  # "Blink", "WebKit", "Gecko"
    
    # ─── OS ───
    os_family = models.CharField(max_length=50)          # "Windows", "macOS", "Android", "iOS"
    os_version = models.CharField(max_length=20, blank=True)  # "11", "14.2", "13"
    
    # ─── DEVICE ───
    device_type = models.CharField(max_length=20)        # "desktop", "smartphone", "tablet", "tv"
    device_brand = models.CharField(max_length=50, blank=True)  # "Apple", "Samsung"
    device_model = models.CharField(max_length=50, blank=True)  # "iPhone 15", "Galaxy S24"
    
    # ─── BOT ───
    is_bot = models.BooleanField(default=False)
    bot_name = models.CharField(max_length=100, blank=True)     # "Googlebot", "Bingbot"
    bot_category = models.CharField(max_length=50, blank=True)  # "search_engine", "crawler"
    
    # ─── EXEMPLO (debug) ───
    user_agent_sample = models.TextField(blank=True)  # 1 exemplo de UA string para debug
    
    class Meta:
        db_table = "tracking_device_profile"
        indexes = [
            models.Index(fields=["browser_family", "os_family"]),
            models.Index(fields=["device_type"]),
        ]
    
    @classmethod
    def compute_hash(cls, browser_family: str, browser_version: str,
                     os_family: str, os_version: str, device_type: str) -> str:
        """Hash deterministico de atributos normalizados."""
        import hashlib
        # Normaliza: lowercase, strip, major version only
        major_version = browser_version.split(".")[0] if browser_version else ""
        parts = [
            browser_family.lower().strip(),
            major_version,
            os_family.lower().strip(),
            os_version.lower().strip(),
            device_type.lower().strip(),
        ]
        canonical = "|".join(parts)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]
```

**Fluxo de get_or_create:**

```
Request chega
  │
  ▼
device-detector parse(User-Agent) → browser="Chrome", version="120.0.6099", os="Windows", device="desktop"
  │
  ▼
compute_hash("chrome", "120", "windows", "11", "desktop") → "a1b2c3d4..."
  │
  ▼
DeviceProfile.objects.get_or_create(
    profile_hash="a1b2c3d4...",
    defaults={browser_family: "Chrome", browser_version: "120", ...}
)
  │
  ├─ Existe? → retorna existente (0 INSERTs)
  └─ Nao existe? → cria novo (1 INSERT, raro)

Resultado: ~200 profiles para todo o trafego.
FK de 4 bytes no CaptureEvent ao inves de ~200 bytes de strings.
```

### CaptureEvent — Modelo universal (REVISADO v3.1)

```python
# src/core/tracking/models.py

class CaptureEvent(BaseModel):
    """Tracker universal de eventos em TODAS as paginas do sistema.
    
    NÃO e acoplado apenas a paginas de captura/lancamento. Rastreia:
    - Landing pages (capture, checkout, thank-you, support, sales, content)
    - Dashboard (futuro)
    - Qualquer pagina onde tracking seja necessario
    
    Tipos de evento:
    - page_view: Acesso GET a qualquer pagina
    - form_attempt: POST de formulario ANTES da validacao
    - form_success: POST validado com sucesso
    - form_error: POST com erros de validacao
    - cta_click: Clique em CTA (WhatsApp, checkout, etc.)
    - scroll_milestone: Scroll atingiu 25%, 50%, 75%, 100% (futuro)
    
    O capture_token agrupa todos os eventos de uma mesma visita/sessao de pagina.
    """
    
    PUBLIC_ID_PREFIX = "cev"
    
    class EventType(models.TextChoices):
        PAGE_VIEW = "page_view", "Page View"
        FORM_ATTEMPT = "form_attempt", "Form Attempt"
        FORM_SUCCESS = "form_success", "Form Success"
        FORM_ERROR = "form_error", "Form Error"
        CTA_CLICK = "cta_click", "CTA Click"
        SCROLL_MILESTONE = "scroll_milestone", "Scroll Milestone"
    
    class PageCategory(models.TextChoices):
        """Categoria da pagina — permite filtrar eventos por tipo de pagina."""
        CAPTURE = "capture", "Pagina de Captura"
        CHECKOUT = "checkout", "Checkout"
        THANK_YOU = "thank_you", "Obrigado"
        SUPPORT = "support", "Suporte"
        SALES = "sales", "Pagina de Vendas"
        CONTENT = "content", "Conteudo"
        LEGAL = "legal", "Pagina Legal"
        DASHBOARD = "dashboard", "Dashboard"
        OTHER = "other", "Outro"
    
    # ─── EVENTO ───
    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        db_index=True,
    )
    
    # Token unico por page load — agrupa eventos da mesma visita
    capture_token = models.UUIDField(
        db_index=True,
        help_text="UUID gerado no GET, passado como prop + hidden input. "
                  "Liga page_view → form_attempt → form_success da mesma sessao.",
    )
    
    # ─── PAGINA (universal, nao acoplado a captura) ───
    page_path = models.CharField(
        max_length=500, db_index=True,
        help_text="Path da pagina: /inscrever-wh-rc-v3/, /obrigado-wh-rc-v3/, "
                  "/checkout-wh-rc-v3/, /suporte/, /app/dashboard/, etc.",
    )
    page_category = models.CharField(
        max_length=20,
        choices=PageCategory.choices,
        default=PageCategory.OTHER,
        db_index=True,
    )
    page_url = models.URLField(max_length=500, blank=True)  # URL completa com query params
    referrer = models.URLField(max_length=500, blank=True)
    
    # ─── IDENTIDADE (todas opcionais — permite eventos anonimos) ───
    fingerprint_identity = models.ForeignKey(
        "contacts.FingerprintIdentity",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="capture_events",
    )
    identity = models.ForeignKey(
        "contacts.Identity",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="capture_events",
    )
    
    # ─── DEVICE (FK para dimension table — 4 bytes, nao strings repetidas) ───
    device_profile = models.ForeignKey(
        DeviceProfile,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="events",
    )
    
    # ─── REFERENCIA A PAGINA DE CAPTURA (opcional, so para page_category=capture) ───
    capture_page = models.ForeignKey(
        "launches.CapturePage",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="events",
    )
    
    # ─── REDE ───
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    geo_data = models.JSONField(
        default=dict, blank=True,
        help_text="Dados GeoIP: {city, country, lat, long, asn, isp}",
    )
    
    # ─── VISITANTE ───
    visitor_id = models.CharField(max_length=100, blank=True, db_index=True)
    
    # ─── CONTEXTO ───
    utm_data = models.JSONField(default=dict, blank=True)
    accept_language = models.CharField(max_length=100, blank=True)
    
    # ─── EXTENSIVEL ───
    metadata = models.JSONField(
        default=dict, blank=True,
        help_text="Dados extras: erros de validacao, scroll_depth, "
                  "time_on_page, cta_label, etc.",
    )
    
    class Meta:
        db_table = "tracking_capture_event"
        ordering = ["-created_at"]
        indexes = [
            # Queries de funil por pagina
            models.Index(fields=["page_path", "event_type", "created_at"]),
            # Queries por categoria de pagina
            models.Index(fields=["page_category", "event_type", "created_at"]),
            # Agrupar eventos da mesma sessao
            models.Index(fields=["capture_token", "event_type"]),
            # Historico do visitante
            models.Index(fields=["visitor_id", "created_at"]),
            # Partial index: so page_views (maioria das queries)
            models.Index(
                fields=["created_at"],
                name="idx_cev_pageview_ts",
                condition=models.Q(event_type="page_view"),
            ),
        ]
```

**Nota sobre `user_agent`**: Removido do CaptureEvent. O User-Agent e armazenado UMA VEZ no `DeviceProfile.user_agent_sample` (debug) e os dados parseados vivem nos campos estruturados do DeviceProfile. O evento referencia o DeviceProfile via FK de 4 bytes.

**Nota sobre `campaign_slug`**: Substituido por `page_path` (generico) + `page_category` (enum). Para queries de captura especificas, use `page_category="capture"` + `capture_page` FK.

### Cadeia ORM completa (REVISADA v3.1)

```
                                CaptureEvent
                                     │
        ┌────────────────────────────┼────────────────────────────┐
        │ (nullable FK)              │ (nullable FK)              │ (nullable FK)
        ▼                            ▼                            ▼
  DeviceProfile             FingerprintIdentity              Identity
  (dimension table)                  │                            │
  ├─ browser_family          ┌───────┘                     ┌─────┼─────┐
  ├─ os_family               │                             │     │     │
  ├─ device_type             │                             ▼     ▼     ▼
  ├─ is_bot             FingerprintContact          ContactEmail  ContactPhone
  └─ profile_hash         (junction)                       │     │     │
                               │                           └─────┼─────┘
                               │                                 │
                               └───────────────┬─────────────────┘
                                               │
                                          Attribution

  CaptureEvent.capture_page ──(nullable)──► CapturePage ──► Launch ──► Interest


Relacionamentos:

CaptureEvent.device_profile           → DeviceProfile (nullable, dimension table)
CaptureEvent.fingerprint_identity     → FingerprintIdentity (nullable)
CaptureEvent.identity                 → Identity (nullable)
CaptureEvent.capture_page             → CapturePage (nullable, so para category=capture)

DeviceProfile: ~200 linhas (todas combinacoes browser+OS+device observadas)
CaptureEvent: milhoes de linhas (cada page view, form submit, click)
FK integer (4 bytes) substitui ~200 bytes de strings repetidas
```

### Ciclo de vida do capture_token (REVISADO v3.1)

```
FASE 1 — GET /inscrever-wh-rc-v3/ (ou qualquer pagina)
    ┌─────────────────────────────────────────────────────────────────┐
    │ Django view gera: capture_token = uuid4()                       │
    │                                                                 │
    │ VisitorMiddleware ja enriqueceu o request:                      │
    │ - request.visitor_id (cookie fpjs_vid)                          │
    │ - request.device_profile (DeviceProfile via device-detector)    │
    │ - request.client_ip (django-ipware)                             │
    │ - request.geo_data (geoip2)                                     │
    │                                                                 │
    │ 1. CaptureEvent.create(                                         │
    │      event_type="page_view",                                    │
    │      capture_token=token,                                       │
    │      page_path="/inscrever-wh-rc-v3/",                          │
    │      page_category="capture",                                   │
    │      device_profile=request.device_profile,  ← FK (4 bytes)   │
    │      ip_address=request.client_ip,                              │
    │      geo_data=request.geo_data,                                 │
    │      utm_data={...extraido do request...},                      │
    │      visitor_id=request.visitor_id,  ← do cookie, se existir   │
    │      accept_language=request.META.get("HTTP_ACCEPT_LANGUAGE"),  │
    │    )                                                            │
    │                                                                 │
    │ 2. Inertia props incluem: capture_token=token                   │
    │ 3. Redis: capture:session:{token} = {page, timestamp, ip}       │
    │    TTL = 30 min                                                 │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
FASE 2 — Frontend renderiza
    ┌─────────────────────────────────────────────────────────────────┐
    │ capture_token chega como prop → hidden input no <form>          │
    │                                                                 │
    │ Se fingerprint_needed=true (sem cookie):                        │
    │   FpjsProvider carrega → getData() no mount → visitorId obtido │
    │   visitorId armazenado em state React                           │
    │                                                                 │
    │ Se fingerprint_needed=false (cookie existe):                    │
    │   FPJS nem carrega → zero JS extra                             │
    │   visitor_id ja esta no request (VisitorMiddleware)             │
    │   Se necessario, known_visitor chega via deferred prop          │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
FASE 3 — POST /inscrever-wh-rc-v3/
    ┌─────────────────────────────────────────────────────────────────┐
    │ Form envia: email, phone, visitor_id, capture_token, UTMs       │
    │                                                                 │
    │ 1. CaptureEvent.create(                                         │
    │      event_type="form_attempt",                                 │
    │      capture_token=token,  ← MESMO token do GET                │
    │      page_path="/inscrever-wh-rc-v3/",                          │
    │      page_category="capture",                                   │
    │      device_profile=request.device_profile,                     │
    │      visitor_id="fp_abc123",                                    │
    │      metadata={"email_domain":"gmail.com", "phone_ddd":"11"},   │
    │    )                                                            │
    │                                                                 │
    │ 2a. Se validacao FALHAR:                                        │
    │     CaptureEvent.create(                                         │
    │       event_type="form_error",                                   │
    │       capture_token=token,                                       │
    │       metadata={"errors": {"email":"obrigatorio"}},              │
    │     )                                                            │
    │     → re-render com erros                                       │
    │                                                                 │
    │ 2b. Se validacao OK:                                            │
    │     → identity resolution (sync rapido)                          │
    │     → process_lead_background.delay() (async)                    │
    │     CaptureEvent.create(                                         │
    │       event_type="form_success",                                 │
    │       capture_token=token,                                       │
    │       identity=identity,                                         │
    │       fingerprint_identity=fp_identity,                          │
    │       device_profile=request.device_profile,                     │
    │       visitor_id="fp_abc123",                                    │
    │       metadata={"is_new": true, "identity_id": "idn_xyz"},      │
    │     )                                                            │
    │     → Django seta cookie fpjs_vid se primeira vez                │
    │     → redirect /obrigado-wh-rc-v3/                              │
    │                                                                 │
    │ 3. Redis: capture:session:{token} enriquecido com identity      │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
FASE 4 — GET /obrigado-wh-rc-v3/ (thank-you — TAMBEM RASTREADO)
    ┌─────────────────────────────────────────────────────────────────┐
    │ Novo capture_token para a thank-you page (nova visita)          │
    │ CaptureEvent.create(                                             │
    │   event_type="page_view",                                        │
    │   page_path="/obrigado-wh-rc-v3/",                               │
    │   page_category="thank_you",                                     │
    │   visitor_id=request.visitor_id,  ← cookie fpjs_vid             │
    │   identity=request.identity,      ← VisitorMiddleware resolveu  │
    │   device_profile=request.device_profile,                         │
    │ )                                                                │
    │ Agora sabemos: quem visitou, quanto tempo ficou, se clicou CTA  │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
FASE 5 — Binding retroativo
    ┌─────────────────────────────────────────────────────────────────┐
    │ Apos form_success, o sistema retroativamente vincula             │
    │ os eventos anteriores (page_view, form_attempt) ao identity:    │
    │                                                                 │
    │ CaptureEvent.objects.filter(                                     │
    │   capture_token=token,                                           │
    │   identity__isnull=True                                          │
    │ ).update(identity=identity, visitor_id=visitor_id)               │
    │                                                                 │
    │ Resultado: TODOS os eventos da sessao ficam vinculados          │
    │ ao mesmo identity + capture_token                                │
    └─────────────────────────────────────────────────────────────────┘
```

### Queries de metricas (REVISADAS v3.1)

```python
# Taxa de conversao por pagina de captura (ultimo mes)
from django.db.models import Count, Q
from datetime import timedelta
from django.utils import timezone

one_month_ago = timezone.now() - timedelta(days=30)

CaptureEvent.objects.filter(
    page_path="/inscrever-wh-rc-v3/",
    page_category="capture",
    created_at__gte=one_month_ago,
).values("event_type").annotate(
    count=Count("id")
)
# Resultado: [
#   {"event_type": "page_view", "count": 5000},
#   {"event_type": "form_attempt", "count": 800},
#   {"event_type": "form_success", "count": 500},
#   {"event_type": "form_error", "count": 300},
# ]
# Taxa: 500/5000 = 10% conversao

# Funil COMPLETO: capture → thank-you → checkout (cross-page via visitor_id)
CaptureEvent.objects.filter(
    visitor_id="fp_abc123",
    created_at__gte=one_month_ago,
).values("page_category", "event_type").annotate(
    count=Count("id")
).order_by("page_category")
# Resultado: [
#   {"page_category": "capture", "event_type": "page_view", "count": 3},
#   {"page_category": "capture", "event_type": "form_success", "count": 1},
#   {"page_category": "thank_you", "event_type": "page_view", "count": 1},
#   {"page_category": "checkout", "event_type": "page_view", "count": 1},
# ]

# Analytics por device (JOIN com dimension table)
CaptureEvent.objects.filter(
    page_category="capture",
    event_type="page_view",
    created_at__gte=one_month_ago,
).values(
    "device_profile__browser_family",
    "device_profile__device_type",
).annotate(
    count=Count("id")
).order_by("-count")
# Resultado: [
#   {"browser_family": "Chrome", "device_type": "smartphone", "count": 3200},
#   {"browser_family": "Safari", "device_type": "smartphone", "count": 1100},
#   {"browser_family": "Chrome", "device_type": "desktop", "count": 700},
# ]

# GeoIP analytics (sem JOIN, dados inline)
CaptureEvent.objects.filter(
    page_category="capture",
    event_type="form_success",
    created_at__gte=one_month_ago,
).values("geo_data__country").annotate(
    count=Count("id")
).order_by("-count")
```

---

## Pesquisa FingerprintJS Pro

> Pesquisa realizada em 2026-02-15. Documentacao oficial + SDKs verificados.

### React SDK v3 (`@fingerprintjs/fingerprintjs-pro-react`)

```
Pacote: @fingerprintjs/fingerprintjs-pro-react
Versao atual: v3.x
Dependencia: @fingerprintjs/fingerprintjs-pro (core)
```

**Componentes principais:**

```tsx
// Provider (global, em main.tsx)
import { FpjsProvider } from '@fingerprintjs/fingerprintjs-pro-react';

<FpjsProvider
  loadOptions={{
    apiKey: 'PUBLIC_API_KEY',
    region: 'us',            // us | eu | ap
    endpoint: ['metrics.yourdomain.com', FingerprintJSPro.defaultEndpoint],
  }}
  cacheOptions={{
    prefix: 'fpjs_',
    cacheType: 'sessionStorage',  // Evita chamadas duplicadas
  }}
>
  <App />
</FpjsProvider>

// Hook (em qualquer componente)
import { useVisitorData } from '@fingerprintjs/fingerprintjs-pro-react';

const { getData, data, isLoading, error } = useVisitorData(
  { extendedResult: true },     // inclui incognito, bot detection, etc.
  { immediate: false }          // NAO chamar no mount — esperar trigger manual
);

// Chamar manualmente (ex: no form submit)
const result = await getData({ ignoreCache: true });
// result.visitorId    → "abc123" (estavel cross-session, ~99.5% precisao)
// result.requestId    → "req_xyz" (unico por chamada, server-verifiable)
// result.confidence   → { score: 0.999 }
// result.incognito    → true/false
// result.ip           → "189.x.x.x"
// result.ipLocation   → { city, country, latitude, longitude }
```

**Caching built-in**: O SDK cacheia `visitorId` por sessao. Chamadas subsequentes retornam cache (nao billable). Para forcar nova chamada: `getData({ ignoreCache: true })`.

### Python Server API SDK

```
Pacote: fingerprint-pro-server-api-sdk
Versao: 8.11.0
Repo: https://github.com/fingerprintjs/fingerprint-pro-server-api-python-sdk
```

**Metodos principais:**

```python
from fingerprint_pro_server_api_sdk import Configuration, FingerprintApi, ApiClient

config = Configuration(api_key=FINGERPRINT_SECRET_API_KEY, region="us")
api = FingerprintApi(ApiClient(config))

# 1. get_event(request_id) — detalhes completos de uma chamada getData()
event = api.get_event(request_id="req_xyz")
# event.products.identification.data.visitor_id
# event.products.identification.data.confidence.score
# event.products.botd.data.bot.result  → "notDetected" | "bad"
# event.products.ip_info.data.geolocation
# event.products.incognito.data.result  → True/False
# event.products.vpn.data.result  → True/False

# 2. get_visits(visitor_id) — historico de visitas
visits = api.get_visits(visitor_id="abc123", limit=50)
# visits.visits[0].timestamp, .ip, .url, .user_agent, etc.

# 3. search_events(limit, visitor_id) — busca flexivel
events = api.search_events(limit=100, visitor_id="abc123")

# 4. get_related_visitors(visitor_id) — visitantes correlacionados
related = api.get_related_visitors(visitor_id="abc123")
# Retorna outros visitor_ids que compartilham mesmo dispositivo/browser
```

**Importante**: Todas as chamadas da Server API sao **GRATUITAS** (nao billable). So `getData()` no frontend e billable.

**Rate limit**: 5 RPS (15 burst). Header `Retry-After` no 429. Recomendacao: usar `tenacity` para retry automatico.

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def get_fpjs_event(request_id: str) -> dict:
    return api.get_event(request_id)
```

### Webhooks FPJS Pro

```
Max: 5 webhooks por environment
Timeout: 3s (1 retry apos 5 min)
Payload: JSON com visitorId, requestId, IP, geolocation, bot, incognito, VPN
Validacao: HMAC SHA-256
```

**Validacao no Django:**

```python
from fingerprint_pro_server_api_sdk import WebhookValidation

def fpjs_webhook_view(request):
    header = request.META.get("HTTP_FPJS_EVENT_VALIDATION")
    is_valid = WebhookValidation.is_valid_webhook_signature(
        header=header,
        data=request.body,
        secret=settings.FPJS_WEBHOOK_SECRET,
    )
    if not is_valid:
        return HttpResponseForbidden("Invalid signature")
    
    payload = json.loads(request.body)
    # Process...
```

### Pricing e estrategia de custos

| Operacao | Custo |
|----------|-------|
| `getData()` no frontend | **BILLABLE** (~$0.002/chamada no plano Pro) |
| Server API (`get_event`, `get_visits`, etc.) | **GRATUITO** |
| Webhook | **GRATUITO** |
| Cache hit no SDK React | **GRATUITO** |

**Estrategia decidida para minimizar custos (REVISADA v3.1):**

> **PRINCIPIO CENTRAL**: FPJS Pro e chamado **UMA VEZ por visitante** para identificacao profissional.
> Apos obter o visitorId, Django sustenta sozinho com suas proprias capacidades de deteccao.
> O FPJS nunca mais e chamado do frontend para aquele visitante.

1. `getData()` chamado no **PAGE LOAD** (nao no submit) → `immediate: true` SE cookie nao existir
2. Cookie `fpjs_vid` persiste `visitorId` no browser → **unica chamada billable por visitante**
3. Python SDK no backend para expandir dados (geolocation, bot, VPN) → **gratis**
4. Webhook como redundancia para receber dados que o frontend falhou em enviar → **gratis**
5. `fingerprint_needed` prop do Django decide se FPJS carrega no frontend — se `fpjs_vid` cookie ja existe, **FPJS nem carrega** (economia total)
6. Para visitas subsequentes, Django captura device/browser/geo via suas proprias libs (`device-detector`, `django-ipware`, `geoip2`) e faz **triagem comparativa** com dados do FPJS Pro expandidos na primeira visita
7. Se Django detecta dados divergentes (browser diferente, IP diferente), pode marcar para re-verificacao

```
FLUXO REVISADO — FPJS UMA VEZ POR VISITANTE:

PRIMEIRA VISITA (sem cookie fpjs_vid):
  ┌────────────────────────────────────────────────────────────────────────┐
  │ 1. GET /inscrever-wh-rc-v3/                                           │
  │    VisitorMiddleware: sem cookie → request.is_known_visitor = False    │
  │    View: fingerprint_needed = True                                     │
  │    Props: { fingerprint_needed: true, fpjs_api_key: "..." }            │
  │                                                                        │
  │ 2. Frontend renderiza                                                  │
  │    <FpjsProvider> global em main.tsx                                    │
  │    useVisitorData({ immediate: true })  ← CHAMA getData() NO MOUNT    │
  │    → visitorId + requestId obtidos em background                       │
  │    → armazenados em state React (disponivel para o form)               │
  │                                                                        │
  │ 3. POST do form (ou navegacao)                                         │
  │    visitorId + requestId enviados no form data                         │
  │    Django: seta cookie fpjs_vid = visitorId na response                │
  │    Django: Celery task → Python SDK get_event(requestId) → GRATIS      │
  │      → expande: bot, VPN, incognito, geolocation, device details       │
  │      → salva TUDO no DeviceProfile + FingerprintIdentity               │
  │                                                                        │
  │ RESULTADO: 1 chamada billable. Backend tem dados COMPLETOS.            │
  └────────────────────────────────────────────────────────────────────────┘

VISITAS SUBSEQUENTES (cookie fpjs_vid existe):
  ┌────────────────────────────────────────────────────────────────────────┐
  │ 1. GET qualquer pagina                                                 │
  │    VisitorMiddleware: cookie fpjs_vid → resolve identity (Redis cache) │
  │    request.is_known_visitor = True                                     │
  │    request.device_profile = DeviceProfile (da 1a visita)               │
  │    View: fingerprint_needed = False                                    │
  │                                                                        │
  │ 2. Frontend renderiza                                                  │
  │    fingerprint_needed = false → FPJS NEM CARREGA (zero JS, zero rede) │
  │                                                                        │
  │ 3. Django captura dados PROPRIOS do request atual:                     │
  │    - User-Agent → device-detector (browser, OS, device, bot)           │
  │    - IP → django-ipware → geoip2 (cidade, pais, ASN/ISP)              │
  │    - Client Hints (Chromium): Sec-CH-UA-*, modelo, arquitetura         │
  │    - Accept-Language, Referer, Sec-Fetch-*                             │
  │                                                                        │
  │ 4. TRIAGEM COMPARATIVA:                                                │
  │    Django compara dados ATUAIS vs DeviceProfile ARMAZENADO:            │
  │    - Mesmo browser? Mesmo OS? Mesmo device type?                       │
  │    - IP mudou? (normal para mobile, suspeito para desktop)             │
  │    - Se mudanca significativa → flag para re-verificacao futura        │
  │    - Se consistente → confianca mantida, zero custo FPJS               │
  │                                                                        │
  │ RESULTADO: 0 chamadas billable. Django sustenta sozinho.               │
  └────────────────────────────────────────────────────────────────────────┘
```

### Migracao open-source → Pro (REVISADA v3.1)

```
ANTES (atual):
  @fingerprintjs/fingerprintjs          ← pacote OSS
  FingerprintProvider.tsx               ← componente custom com requestId fake
  fp.get() → result.visitorId           ← ~60% precisao
  Sem Provider global                   ← montado dentro de CaptureForm

DEPOIS (Phase G.5):
  @fingerprintjs/fingerprintjs-pro-react  ← pacote Pro com React SDK
  <FpjsProvider> em main.tsx              ← global, com cache
  useVisitorData({ immediate: true })     ← getData() NO PAGE LOAD se sem cookie
  fingerprint_needed=false → NEM CARREGA  ← economia total para retornantes
  Cookie fpjs_vid para persistencia       ← cross-page, cross-session, 1 ano TTL
  Python SDK no backend para expansion    ← gratis, async via Celery
  Django libs para deteccao propria       ← device-detector, django-ipware, geoip2
  Triagem comparativa Django vs FPJS      ← deteccao de mudancas sem custo
  Webhook /api/fpjs-webhook/              ← redundancia, HMAC validated
```

---

## Temas adicionais (detalhamento tecnico)

> 14 temas levantados e discutidos com o owner durante a sessao v3.0. Cada tema inclui: o que e, onde vive (Redis? PostgreSQL? cookie? localStorage?), como funciona, e diagrama de fluxo quando aplicavel.

### T1. Cookie `fpjs_vid` — Persistencia do visitorId

**O que e**: Cookie HTTP que armazena o `visitorId` do FingerprintJS Pro. Persiste alem da sessao do browser. Permite identificar visitantes retornantes sem chamar `getData()` novamente (economia).

**Onde vive**: Cookie no browser.

```
Set-Cookie: fpjs_vid=abc123def456; Path=/; Max-Age=31536000; SameSite=Lax; Secure

Ciclo (REVISADO v3.1):
1. Primeiro acesso: fpjs_vid NAO existe → prop fingerprint_needed=true
2. Frontend chama getData() NO PAGE LOAD (immediate: true) → obtem visitorId
3. visitorId fica em state React, disponivel para qualquer form/acao
4. Na primeira response que recebe visitorId (POST ou silent POST) → Django seta cookie
5. Proximos acessos: fpjs_vid EXISTE → prop fingerprint_needed=false
6. FPJS NEM CARREGA no frontend → zero JS, zero rede
7. VisitorMiddleware le cookie → resolve identity → enriquece request
8. Django usa suas proprias libs (device-detector, geoip2) para deteccao complementar
```

**Quem seta**: Django, na primeira response que recebe visitorId (POST do form ou silent POST de telemetria).
**Quem le**: `VisitorMiddleware` no Django, em CADA request subsequente (automatico via cookie).
**TTL**: 1 ano (365 dias). FingerprintJS Pro mantem visitorId estavel por ate 1 ano.
**Vantagem do cookie vs localStorage**: Cookie e enviado automaticamente em cada request HTTP — VisitorMiddleware le sem nenhuma acao do frontend. localStorage exigiria JS para ler e enviar explicitamente.

### T2. VisitorMiddleware — Identificacao e profiling automatico de visitantes (REVISADO v3.1)

**O que e**: Middleware Django que roda em TODAS as requests de landing. Responsavel por 3 funcoes:
1. **Identificacao**: Le cookie `fpjs_vid`, resolve FingerprintIdentity e Identity
2. **Device Profiling**: Extrai browser/OS/device do request (device-detector + Client Hints)
3. **GeoIP**: Resolve IP para localizacao e ASN/ISP (geoip2 + django-ipware)

**Onde vive**: `src/core/tracking/middleware.py` (novo app `core/tracking/`).

```python
from device_detector import DeviceDetector
from ipware import get_client_ip
import geoip2.database

class VisitorMiddleware:
    """Identifica visitante e perfila dispositivo em cada request.
    
    Adiciona ao request:
    
    IDENTIFICACAO (via cookie fpjs_vid):
    - request.visitor_id: str
    - request.fingerprint_identity: FingerprintIdentity | None
    - request.identity: Identity | None
    - request.is_known_visitor: bool
    
    DEVICE PROFILING (via User-Agent + Client Hints):
    - request.device_profile: DeviceProfile | None
    - request.device_data: dict (browser, OS, device type, bot detection)
    
    GEO (via IP → MaxMind):
    - request.client_ip: str
    - request.geo_data: dict (cidade, pais, lat/long, ASN, ISP)
    
    CLIENT HINTS (Chromium browsers, ~65% do trafego):
    - request.client_hints: dict (model, platform_version, arch, etc.)
    """
    
    def __call__(self, request):
        # ─── 1. IDENTIFICACAO (cookie fpjs_vid) ───
        visitor_id = request.COOKIES.get("fpjs_vid", "")
        request.visitor_id = visitor_id
        request.fingerprint_identity = None
        request.identity = None
        request.is_known_visitor = False
        
        if visitor_id:
            cached = cache.get(f"visitor:{visitor_id}")
            if cached:
                request.fingerprint_identity = FingerprintIdentity.objects.get(pk=cached["fp_id"])
                if cached.get("identity_id"):
                    request.identity = Identity.objects.get(pk=cached["identity_id"])
                request.is_known_visitor = True
            else:
                fp = FingerprintIdentity.objects.filter(fingerprint_hash=visitor_id).first()
                if fp:
                    request.fingerprint_identity = fp
                    identity = fp.identities.first()
                    if identity:
                        request.identity = identity
                    request.is_known_visitor = True
                    cache.set(f"visitor:{visitor_id}", {
                        "fp_id": fp.pk,
                        "identity_id": identity.pk if identity else None,
                    }, timeout=3600)
        
        # ─── 2. DEVICE PROFILING (User-Agent + Client Hints) ───
        ua_string = request.META.get("HTTP_USER_AGENT", "")
        dd = DeviceDetector(ua_string).parse()
        
        request.device_data = {
            "browser_family": dd.client_name() or "unknown",      # "Chrome", "Firefox"
            "browser_version": dd.client_version() or "",          # "120.0"
            "browser_engine": dd.engine() or "",                   # "Blink", "WebKit"
            "os_family": dd.os_name() or "unknown",                # "Windows", "Android"
            "os_version": dd.os_version() or "",                   # "11", "14.2"
            "device_type": dd.device_type() or "unknown",          # "desktop", "smartphone"
            "device_brand": dd.device_brand_name() or "",          # "Apple", "Samsung"
            "device_model": dd.device_model() or "",               # "iPhone 15"
            "is_bot": dd.is_bot(),                                 # True/False
            "bot_name": dd.bot_name() if dd.is_bot() else "",     # "Googlebot"
            "bot_category": dd.bot_category() if dd.is_bot() else "",
            "client_type": dd.client_type() or "",                 # "browser", "mobile app"
        }
        
        # Client Hints (Chromium only — mais preciso que User-Agent)
        request.client_hints = {
            "ua": request.META.get("HTTP_SEC_CH_UA", ""),
            "mobile": request.META.get("HTTP_SEC_CH_UA_MOBILE", ""),
            "platform": request.META.get("HTTP_SEC_CH_UA_PLATFORM", ""),
            # High-entropy (requer Accept-CH na response — setado pelo middleware):
            "model": request.META.get("HTTP_SEC_CH_UA_MODEL", ""),
            "platform_version": request.META.get("HTTP_SEC_CH_UA_PLATFORM_VERSION", ""),
            "full_version": request.META.get("HTTP_SEC_CH_UA_FULL_VERSION_LIST", ""),
            "arch": request.META.get("HTTP_SEC_CH_UA_ARCH", ""),
        }
        
        # Se Client Hints disponivel e mais preciso, sobrescreve device_data
        if request.client_hints["platform"]:
            ch_platform = request.client_hints["platform"].strip('"')
            if ch_platform:
                request.device_data["os_family"] = ch_platform
        if request.client_hints["model"]:
            ch_model = request.client_hints["model"].strip('"')
            if ch_model:
                request.device_data["device_model"] = ch_model
        
        # DeviceProfile: get_or_create via hash (dimension table)
        request.device_profile = DeviceProfileService.get_or_create_from_request(request)
        
        # ─── 3. GEO (IP → MaxMind GeoLite2) ───
        client_ip, is_routable = get_client_ip(request)
        request.client_ip = str(client_ip) if client_ip else ""
        request.geo_data = {}
        
        if client_ip and is_routable:
            cached_geo = cache.get(f"geo:{client_ip}")
            if cached_geo:
                request.geo_data = cached_geo
            else:
                try:
                    city_reader = geoip2.database.Reader(settings.GEOIP_CITY_DB)
                    city = city_reader.city(str(client_ip))
                    asn_reader = geoip2.database.Reader(settings.GEOIP_ASN_DB)
                    asn = asn_reader.asn(str(client_ip))
                    request.geo_data = {
                        "city": city.city.name or "",
                        "country": city.country.iso_code or "",
                        "country_name": city.country.name or "",
                        "region": city.subdivisions.most_specific.name if city.subdivisions else "",
                        "latitude": city.location.latitude,
                        "longitude": city.location.longitude,
                        "timezone": city.location.time_zone or "",
                        "asn": asn.autonomous_system_number,
                        "isp": asn.autonomous_system_organization or "",
                    }
                    cache.set(f"geo:{client_ip}", request.geo_data, timeout=86400)
                except Exception:
                    pass  # GeoIP lookup failure is non-critical
        
        # ─── RESPONSE PROCESSING ───
        response = self.get_response(request)
        
        # Solicitar Client Hints de alta entropia para proximas requests
        response["Accept-CH"] = (
            "Sec-CH-UA-Model, Sec-CH-UA-Platform-Version, "
            "Sec-CH-UA-Full-Version-List, Sec-CH-UA-Arch"
        )
        
        return response
```

**Stack de deteccao Django (sem FPJS):**

```
DADOS DO REQUEST (automaticos, zero frontend):
─────────────────────────────────────────────────────────────────
Fonte                     │ Lib                  │ Dados extraidos
──────────────────────────┼──────────────────────┼─────────────────────────
User-Agent header         │ device-detector 5.x  │ browser (family, version, engine)
                          │ (Matomo port)        │ OS (name, version, platform)
                          │                      │ device (type, brand, model)
                          │                      │ bot (is_bot, name, category)
                          │                      │ client_type (browser, app, lib)
──────────────────────────┼──────────────────────┼─────────────────────────
IP address                │ django-ipware 7.x    │ real client IP (proxies, CDN)
                          │ geoip2 4.8.x +       │ cidade, pais, lat/long
                          │   GeoLite2-City       │ timezone, regiao
                          │   GeoLite2-ASN        │ ASN, ISP/organizacao
──────────────────────────┼──────────────────────┼─────────────────────────
Client Hints              │ (nativo, sem lib)    │ browser version (full)
(Sec-CH-UA-* headers)     │                      │ OS version
(~65% do trafego,         │                      │ device model
 Chromium only)            │                      │ CPU arquitetura (arm, x86)
──────────────────────────┼──────────────────────┼─────────────────────────
Accept-Language            │ Django built-in      │ idioma preferido
Referer                   │ request.META         │ pagina anterior
Sec-Fetch-*               │ request.META         │ contexto da request
──────────────────────────┼──────────────────────┼─────────────────────────

DADOS DO FPJS PRO (1a visita apenas):
─────────────────────────────────────────────────────────────────
Fonte                     │ Lib                  │ Dados extraidos
──────────────────────────┼──────────────────────┼─────────────────────────
getData() frontend        │ React SDK v3         │ visitorId (~99.5% precisao)
(1 chamada billable)      │                      │ requestId (server-verifiable)
                          │                      │ confidence score
──────────────────────────┼──────────────────────┼─────────────────────────
get_event() backend       │ Python SDK 8.x       │ bot detection (avancado)
(gratis)                  │                      │ incognito mode
                          │                      │ VPN detection
                          │                      │ IP info + geolocation
                          │                      │ device details expandidos
──────────────────────────┼──────────────────────┼─────────────────────────
```

**Triagem comparativa (visitas subsequentes):**

```
DeviceProfile armazenado     vs     Request atual (device-detector)
────────────────────────            ─────────────────────────────
browser: "Chrome"                   browser: "Chrome"         → OK
os: "Windows"                       os: "Windows"             → OK
device_type: "desktop"              device_type: "desktop"    → OK
ip: "189.x.x.x" (SP)               ip: "201.y.y.y" (RJ)     → MUDOU (normal p/ mobile)
                                    
Se desktop + IP mudou muito → flag para possivel re-verificacao
Se mobile + IP mudou → normal (rede movel muda IP)
Se browser/OS mudou → novo device, considerar novo DeviceProfile
```

**Cache Redis**: `visitor:{visitorId}` TTL 1 hora. `geo:{ip}` TTL 24 horas.

**Posicao na middleware chain**: Apos `AuthenticationMiddleware`, antes de `InertiaShareMiddleware`.

**Dependencias novas no pyproject.toml:**
```
device-detector >= 5.0
django-ipware >= 7.0
geoip2 >= 4.8
```

**Arquivos MaxMind (download gratuito, requer conta):**
```
GeoLite2-City.mmdb   (~70MB)  → IP → cidade, pais, lat/long, timezone
GeoLite2-ASN.mmdb    (~8MB)   → IP → ASN, ISP/organizacao
```
Atualizados semanalmente via `geoipupdate` (cron job).

### T3. capture_token — UUID por page load

**O que e**: UUID v4 gerado pelo Django no GET de cada pagina de captura. Serve como chave de binding para agrupar todos os eventos (view, attempt, success, error) de uma mesma visita.

**Onde vive**: 
- Gerado na view Django (server-side)
- Enviado como prop Inertia
- Armazenado como hidden input no `<form>`
- Salvo em cada `CaptureEvent.capture_token`
- Armazenado no Redis como `capture:session:{token}`

```
Django GET                    Frontend                      Django POST
────────────                  ────────                      ──────────
token = uuid4()               <input type="hidden"          token vem no
                               name="capture_token"          form data
CaptureEvent(                  value={token} />             
  type="view",                                              CaptureEvent(
  capture_token=token          CaptureForm seta via           type="form_attempt",
)                              prop do Inertia                capture_token=token
                                                            )
Redis: capture:session:
  {token} = {...}              
```

**Nao e sessao do usuario**: E sessao da VISITA. Se o usuario recarrega a pagina, gera novo token. Se abre em outra aba, gera novo token. Cada page load = novo capture_token.

### T4. Inertia v2 Deferred Props — Prefill nao-bloqueante

**O que e**: Recurso do Inertia.js v2 que permite enviar props que sao carregadas DEPOIS do render inicial. O frontend renderiza imediatamente com os dados basicos, e os dados extras chegam depois via request separado.

**Uso planejado**: Quando `VisitorMiddleware` detecta um visitante retornante (`is_known_visitor=True`), a view envia `known_visitor` como deferred prop:

```python
# views.py
from inertia import defer

def capture_page(request, campaign_slug):
    props = {
        "campaign": campaign_props,
        "capture_token": str(uuid4()),
        "fingerprint_needed": not bool(request.COOKIES.get("fpjs_vid")),
    }
    
    if request.is_known_visitor:
        props["known_visitor"] = defer(lambda: {
            "email_hint": mask_email(request.identity.primary_email),
            "phone_hint": mask_phone(request.identity.primary_phone),
            "name": request.identity.display_name,
            "visits_count": request.identity.capture_events.count(),
        })
    
    return inertia_render(request, "Capture/Index", props, app="landing")
```

```tsx
// Frontend
const { campaign, capture_token, known_visitor } = usePage().props;

// known_visitor chega DEPOIS do render inicial
// Enquanto nao chega: known_visitor = undefined
// Quando chega: prefill dos campos com hints
useEffect(() => {
  if (known_visitor?.email_hint) {
    setData('email', known_visitor.email_hint);
  }
}, [known_visitor]);
```

**Vantagem**: A pagina renderiza INSTANTANEAMENTE. O lookup de identity (que pode envolver DB queries) acontece em background, sem bloquear.

### T5. Capture session no Redis

**O que e**: Estado temporario no Redis que rastreia a jornada de captura de um visitante durante uma unica visita. Criado no GET, enriquecido no POST, expirado automaticamente.

**Onde vive**: Redis, chave `capture:session:{capture_token}`.

```
GET /inscrever-wh-rc-v3/
  Redis SET capture:session:abc123 = {
    "slug": "wh-rc-v3",
    "started_at": "2026-02-15T10:00:00",
    "ip": "189.x.x.x",
    "visitor_id": "",               ← ainda nao tem
    "status": "viewing"
  } EX 1800                        ← TTL 30 min

POST /inscrever-wh-rc-v3/ (com capture_token=abc123)
  Redis GET capture:session:abc123  ← verifica se sessao existe
  Redis SET capture:session:abc123 = {
    "slug": "wh-rc-v3",
    "started_at": "2026-02-15T10:00:00",
    "ip": "189.x.x.x",
    "visitor_id": "fp_abc123",      ← agora tem
    "email": "joao@gmail.com",
    "identity_id": "idn_xyz",
    "status": "converted",
    "converted_at": "2026-02-15T10:02:30"
  } EX 1800

GET /obrigado-wh-rc-v3/
  Redis GET capture:session:abc123  ← thank-you pode usar dados da sessao
```

**Uso principal**: Dedup rapida. Se o usuario der F5 no POST e reenviar, a sessao Redis mostra `status=converted` → skip reprocessamento.

### T6. PostgreSQL materialized views para dashboards

**O que e**: Views materializadas no PostgreSQL que pre-computam metricas de captura. Refreshed periodicamente via Celery beat. Evitam queries pesadas em tempo real.

**Onde vive**: PostgreSQL (DDL gerenciado via migration). Django model com `managed = False`.

```sql
-- Migration SQL (nao Django ORM) — REVISADO v3.1
CREATE MATERIALIZED VIEW tracking_daily_summary AS
SELECT
    page_path,
    page_category,
    DATE(created_at) AS date,
    event_type,
    COUNT(*) AS event_count,
    COUNT(DISTINCT visitor_id) FILTER (WHERE visitor_id != '') AS unique_visitors,
    COUNT(DISTINCT ip_address) AS unique_ips
FROM tracking_capture_event
WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY page_path, page_category, DATE(created_at), event_type
WITH DATA;

CREATE UNIQUE INDEX idx_tracking_daily_summary
    ON tracking_daily_summary (page_path, page_category, date, event_type);
```

```python
# src/core/tracking/models.py
class TrackingDailySummary(models.Model):
    """View materializada — somente leitura."""
    page_path = models.CharField(max_length=500)
    page_category = models.CharField(max_length=20)
    date = models.DateField()
    event_type = models.CharField(max_length=20)
    event_count = models.IntegerField()
    unique_visitors = models.IntegerField()
    unique_ips = models.IntegerField()
    
    class Meta:
        managed = False
        db_table = "tracking_daily_summary"
```

**Refresh**: Celery beat a cada 5 minutos.

```python
# tasks.py
@shared_task
def refresh_capture_summary():
    with connection.cursor() as cursor:
        cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY capture_daily_summary")
```

### T7. View nao-materializada para queries ad-hoc

```sql
-- REVISADO v3.1 — agora agrupa por page_path + page_category
CREATE VIEW tracking_page_metrics AS
SELECT
    page_path,
    page_category,
    COUNT(*) FILTER (WHERE event_type = 'page_view') AS views,
    COUNT(*) FILTER (WHERE event_type = 'form_attempt') AS attempts,
    COUNT(*) FILTER (WHERE event_type = 'form_success') AS conversions,
    COUNT(*) FILTER (WHERE event_type = 'form_error') AS errors,
    CASE
        WHEN COUNT(*) FILTER (WHERE event_type = 'page_view') > 0
        THEN ROUND(
            COUNT(*) FILTER (WHERE event_type = 'form_success')::numeric /
            COUNT(*) FILTER (WHERE event_type = 'page_view') * 100, 2
        )
        ELSE 0
    END AS conversion_rate_pct
FROM tracking_capture_event
GROUP BY page_path, page_category;
```

```python
class TrackingPageMetrics(models.Model):
    """View nao-materializada — sempre atualizada, mas pode ser lenta."""
    page_path = models.CharField(max_length=500, primary_key=True)
    page_category = models.CharField(max_length=20)
    views = models.IntegerField()
    attempts = models.IntegerField()
    conversions = models.IntegerField()
    errors = models.IntegerField()
    conversion_rate_pct = models.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta:
        managed = False
        db_table = "tracking_page_metrics"
```

### T8. FPJS open-source → Pro: Plano de migracao (REVISADO v3.1)

```
Etapa 1 (G.5.1) — Pesquisa ✅ CONCLUIDA
  - React SDK v3 documentado
  - Python SDK documentado
  - Webhooks documentados
  - Pricing e estrategia definidos
  - Stack de deteccao Django pesquisado (device-detector, django-ipware, geoip2)

Etapa 2 (G.5.2) — Backend
  - uv add fingerprint-pro-server-api-sdk
  - uv add device-detector django-ipware geoip2
  - Download GeoLite2-City.mmdb + GeoLite2-ASN.mmdb (MaxMind, gratis)
  - Criar FingerprintProService em src/apps/contacts/fingerprint/services/
  - Criar DeviceProfileService em src/core/tracking/services/
  - Endpoint /api/fpjs-webhook/ com HMAC validation
  - Celery task para expansion async (get_event, get_visits)
  - VisitorMiddleware expandido com device profiling + GeoIP
  - Cookie fpjs_vid setado na response
  - fingerprint_needed prop logic

Etapa 3 (G.5.3) — Frontend
  - npm install @fingerprintjs/fingerprintjs-pro-react
  - npm uninstall @fingerprintjs/fingerprintjs (OSS)
  - Remover FingerprintProvider.tsx custom
  - <FpjsProvider> condicional em main.tsx (so monta se fingerprint_needed=true)
  - useVisitorData({ immediate: true }) — getData() NO PAGE LOAD
  - FPJS NEM CARREGA se cookie existe (fingerprint_needed=false)
  - visitorId em state React, incluido automaticamente no form submit
```

### T9. `fingerprint_needed` prop — Controle de carregamento do FPJS (REVISADO v3.1)

**O que e**: Prop boolean que o Django envia ao frontend indicando se o SDK do FPJS Pro deve **carregar e executar no page load**. Nao se trata de "chamar no submit" — FPJS roda no mount da pagina ou nao roda de forma alguma.

```python
# views.py (REVISADO)
fingerprint_needed = not bool(request.COOKIES.get("fpjs_vid"))

# Se fpjs_vid existe → False → FPJS NEM CARREGA (zero JS, zero rede)
# Se fpjs_vid nao existe → True → FPJS carrega e chama getData() no mount
```

```tsx
// Frontend (REVISADO)
const { fingerprint_needed, fpjs_api_key } = usePage().props;

// Em main.tsx — FpjsProvider so monta se necessario:
{fingerprint_needed && fpjs_api_key && (
  <FpjsProvider loadOptions={{ apiKey: fpjs_api_key, region: 'us' }}>
    <App />
  </FpjsProvider>
)}
{!fingerprint_needed && <App />}

// No componente que precisa do fingerprint (ex: CaptureForm):
// useVisitorData({ immediate: true }) — chama getData() automaticamente no mount
// visitorId fica em state React, incluido automaticamente no form
// NAO espera o submit — fingerprint ja esta pronto quando usuario preenche o form

// Se fingerprint_needed=false:
// - Nenhum SDK carregado
// - visitor_id vem do cookie (VisitorMiddleware ja resolveu no server)
// - request.visitor_id disponivel via shared props se necessario
```

**Diferenca da v3.0**: Antes, FPJS carregava sempre e so chamava no submit. Agora, FPJS **nem carrega** se o cookie existe. Economia maxima: zero bytes de JS para visitantes retornantes.

### T10. process_lead_background — Split sync/async

**O que e**: Dividir o `process_lead()` atual (sincrono, bloqueia redirect) em duas partes:

```
ANTES (atual):
  POST → validate → process_lead(sync) → send_n8n(async) → redirect
                     └─ identity resolution (DB heavy)
                     └─ attribution (DB write)
                     └─ N8N payload build
  Tempo total: 200-500ms (depende do DB)

DEPOIS (Phase G.2):
  POST → validate → identity_resolution_quick(sync) → redirect
                     └─ resolve identity (otimizado, ~50ms)
                     └─ retorna identity_id
                    
         Em paralelo (Celery):
           process_lead_background.delay(identity_id, data)
             └─ attribution (DB write)
             └─ N8N payload + send
             └─ FPJS expansion via Python SDK
             └─ CaptureEvent enrichment
             └─ Signals/hooks
  Tempo no request: ~50ms (vs 200-500ms antes)
```

**Justificativa**: O usuario nao precisa esperar attribution + N8N payload + expansion. So precisa que a identity seja resolvida (para dedup) e o redirect aconteca.

### T11. Dedup inscricao — Visitante retornante

**O que e**: Quando `VisitorMiddleware` detecta um visitante retornante que JA converteu para a mesma campanha, pode pular o reprocessamento.

```python
# No POST handler:
if request.is_known_visitor:
    existing = CaptureEvent.objects.filter(
        visitor_id=request.visitor_id,
        campaign_slug=campaign_slug,
        event_type="form_success",
    ).exists()
    
    if existing:
        # Visitante ja converteu para esta campanha
        # Opacoes:
        # 1. Redirect direto para thank-you (skip processamento)
        # 2. Atualizar dados se mudaram (email/phone novo)
        # 3. Registrar CaptureEvent type="form_success" com metadata={"is_resubmit": true}
```

### T12. page_type — Tipos de pagina suportados

**O que e**: Campo no modelo `CapturePage` (G.1) que define o tipo da pagina. Permite que o mesmo sistema sirva diferentes tipos de landing pages.

```python
class CapturePage(BaseModel):
    class PageType(models.TextChoices):
        CAPTURE = "capture", "Captura (email + phone)"
        WAITLIST = "waitlist", "Lista de espera (email only)"
        CPL = "cpl", "CPL (conteudo + captura)"
        CHECKOUT = "checkout", "Checkout (redirect para Stripe)"
        CONTENT = "content", "Conteudo (blog, artigo)"
        SALES = "sales", "Pagina de vendas"
    
    page_type = models.CharField(
        max_length=20,
        choices=PageType.choices,
        default=PageType.CAPTURE,
    )
```

### T13. Webhook FPJS endpoint

**O que e**: Endpoint Django que recebe webhooks do FingerprintJS Pro com dados de fingerprint. Serve como redundancia — se o frontend falhar em enviar os dados, o webhook garante que o Django recebe.

```
FingerprintJS Pro Cloud ──► POST /api/fpjs-webhook/ ──► Django
                              │
                              ├─ Valida HMAC signature
                              ├─ Extrai visitorId, requestId, bot, VPN, etc.
                              ├─ Atualiza FingerprintIdentity com dados expandidos
                              └─ Dispara signal fpjs_data_received
```

**URL**: `/api/fpjs-webhook/` (excluida do CSRF via decorator, validada via HMAC).

### T14. Django unmanaged models para views SQL

**O que e**: Models Django com `managed = False` que mapeiam para views SQL no PostgreSQL. O Django nao cria/altera a tabela — ela e gerenciada por migrations SQL customizadas.

**Padrao de migration:**

```python
# migrations/000X_create_capture_views.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [("landing", "000Y_capture_event")]
    
    operations = [
        migrations.RunSQL(
            sql="""
            CREATE MATERIALIZED VIEW capture_daily_summary AS
            SELECT ... FROM landing_capture_event ...
            WITH DATA;
            """,
            reverse_sql="DROP MATERIALIZED VIEW IF EXISTS capture_daily_summary;",
        ),
        migrations.RunSQL(
            sql="""
            CREATE VIEW capture_page_metrics AS
            SELECT ... FROM landing_capture_event ...;
            """,
            reverse_sql="DROP VIEW IF EXISTS capture_page_metrics;",
        ),
    ]
```

---

## Plano de implementacao G.1-G.8

> Plano aprovado pelo owner. 8 sub-fases, ~10 sessoes de implementacao.
> Ordem definida por dependencias tecnicas.

### Sequencia e dependencias

```
G.5.1 ──► G.1 ──► G.2 ──► G.3 ──► G.5.2/3 ──► G.4 ──► G.6 ──► G.7 ──► G.8
  │         │       │                  │
  │         │       │                  └─ Depende de G.1 (CapturePage model)
  │         │       └─ Depende de G.1 (CapturePage FK no CaptureEvent)
  │         └─ Depende de G.5.1 (pesquisa informa design dos models)
  └─ CONCLUIDO (pesquisa FPJS Pro)
```

### G.1 — Models Launch + Config Django (~2 sessoes)

**Gaps cobertos**: F6 (config Django), F12 (segmentacao interesse), F7 (form header), F8 (glass/patriotic), F14 (field styling)

**Entregaveis:**
1. Novo app `src/apps/launches/` com:
   - `Launch` model (nome, launch_code, dates, status, default config)
   - `Interest` model (rc, td, ds, cp, bf — segmentacao)
   - `CapturePage` model (slug, page_type, JSONField config, FK→Launch, FK→Interest)
2. Admin django-unfold para Launch e CapturePage
3. Management command para migrar JSONs existentes → DB
4. Cache Redis + `post_save` signal invalidation
5. View atualizada para ler config do DB (com fallback para JSON durante migracao)
6. Tests

**Dependencia**: G.5.1 concluida (pesquisa FPJS informou design dos models).

### G.2 — Tracking Universal + DeviceProfile + VisitorMiddleware (~3 sessoes, REVISADO v3.1)

**Gaps cobertos**: F3 (analytics), F4 (dados enriquecidos bidirecional), F5 (referrer)

**Entregaveis:**
1. Novo app `src/core/tracking/` com:
   - `DeviceProfile` model (dimension table, hash-based dedup)
   - `CaptureEvent` model universal (page_path, page_category, FK→DeviceProfile)
   - `DeviceProfileService` (compute_hash, get_or_create_from_request)
   - `TrackingDailySummary` + `TrackingPageMetrics` (unmanaged models)
2. `VisitorMiddleware` expandido com 3 funcoes:
   - Identificacao (cookie fpjs_vid → FingerprintIdentity → Identity)
   - Device Profiling (device-detector → DeviceProfile)
   - GeoIP (django-ipware + geoip2 → geo_data)
3. `capture_token` gerado no GET, passado como prop + hidden input
4. Tracking automatico em TODAS as paginas: page_view (GET), form_attempt, form_success, form_error
5. Binding retroativo (vincular page_view anonimo ao identity apos conversao)
6. Capture session Redis (dedup, estado temporario)
7. `process_lead_background` — split sync/async (T10)
8. PostgreSQL views (materializada + nao-materializada) com BRIN indexes
9. Celery beat task para refresh da view materializada
10. Dependencias Python: `device-detector`, `django-ipware`, `geoip2`
11. Download GeoLite2-City.mmdb + GeoLite2-ASN.mmdb
12. Accept-CH header para Client Hints (Chromium)
13. Tests

**Dependencia**: G.1 concluida (CapturePage FK no CaptureEvent).

### G.3 — Email validation avancada (~1 sessao)

**Gaps cobertos**: F1 (validacao email)

**Entregaveis:**
1. Frontend: debounce (300ms) no campo email
2. Frontend: sugestao de correcao de typo ("gmial.com" → "gmail.com?") com botao clicavel
3. Frontend: auto-lowercase
4. Frontend: lista de 20 dominios temporarios (client-side, UX rapida)
5. Backend: validacao definitiva mantida (ja existe)
6. Mapa de 12+ correcoes de typo (gmail, hotmail, outlook, yahoo, etc.)
7. Tests

**Dependencia**: Nenhuma. Pode rodar em paralelo com G.2 se necessario.

### G.4 — Auto-fill + localStorage (~1 sessao)

**Gaps cobertos**: F2 (auto-fill + fingerprint)

**Entregaveis:**
1. Frontend: salvar email/phone no localStorage apos form_success
2. Frontend: recuperar e prefill no mount do CaptureForm
3. Backend: `known_visitor` deferred prop via VisitorMiddleware (T4)
4. Frontend: usar `known_visitor` para prefill com hints mascarados
5. Tests

**Dependencia**: G.2 concluida (VisitorMiddleware necessario para deferred props).

### G.5 — Fingerprint Pro migration (~2 sessoes)

**Sub-fases:**

**G.5.1** — Pesquisa (✅ CONCLUIDA)
- React SDK v3 documentado
- Python SDK documentado  
- Webhooks documentados
- Pricing e estrategia definidos

**G.5.2** — Backend (~1 sessao)
- `uv add fingerprint-pro-server-api-sdk`
- `FingerprintProService` em `contacts/fingerprint/services/`
- Endpoint `/api/fpjs-webhook/` com HMAC validation
- Celery task para expansion async (`get_event`, `get_visits`)
- Cookie `fpjs_vid` setado na response (1 ano TTL)
- `fingerprint_needed` prop logic (controla se FPJS CARREGA no frontend)
- Integracao com DeviceProfileService (dados FPJS expandidos enriquecem DeviceProfile)

**G.5.3** — Frontend (~1 sessao, REVISADO v3.1)
- `npm install @fingerprintjs/fingerprintjs-pro-react`
- `npm uninstall @fingerprintjs/fingerprintjs` (OSS)
- Remover `FingerprintProvider.tsx` custom
- `<FpjsProvider>` condicional em `main.tsx` (so monta se `fingerprint_needed=true`)
- `useVisitorData({ immediate: true })` — getData() NO PAGE LOAD (nao no submit)
- Se `fingerprint_needed=false` → FPJS NEM CARREGA (zero JS, zero rede)
- visitorId em state React, incluido automaticamente no form submit

**Dependencia**: G.1 concluida (CapturePage model). G.2 concluida (VisitorMiddleware + DeviceProfile).

### G.6 — Visual components (~1 sessao)

**Gaps cobertos**: F9 (top banner), F10 (BF layout), F11 (background avancado)

**Entregaveis:**
1. Componente `TopBanner` configuravel (texto, cores, sticky)
2. Layout `TwoColumnLayout` para campanhas estilo Black Friday
3. Background avancado: positions (desktop/mobile), overlay configuravel
4. `layout_type` field no CapturePage ("standard" | "two-column")
5. CaptureLayout resolve layout dinamicamente baseado na config
6. Tests

**Dependencia**: G.1 concluida (config Django com layout_type).

### G.7 — Observabilidade (~1 sessao)

**Gaps cobertos**: F15 (debug/observabilidade)

**Entregaveis:**
1. Django Debug Toolbar configurado (dev only)
2. `X-View-Time-Ms` response header via middleware
3. Config inspector endpoint: `/app/debug/capture-config/{slug}/`
4. Logging estruturado com correlation_id no fluxo de captura
5. Tests

**Dependencia**: Nenhuma. Pode rodar a qualquer momento.

### G.8 — Schema completion (~0.5 sessao)

**Gaps cobertos**: F7 (detalhes form header), F8 (detalhes glass/patriotic)

**Entregaveis:**
1. Campos detalhados no JSONField config: `form.header.enabled`, `.title`, `.subtitle`
2. Campos: `form.glassEffect`, `form.showPatrioticEffect` (flags boolean)
3. Campos: `form.fields.email.bgColor`, `.textColor`, `.borderColor`
4. Validacao do JSONField via schema (opcional: jsonschema ou Pydantic)
5. Tests

**Dependencia**: G.1 concluida (CapturePage model).

### Resumo do plano (REVISADO v3.1)

| Fase | Sessoes | Gaps | Deps | Novidades v3.1 |
|------|---------|------|------|----------------|
| G.5.1 | ✅ | F13 (pesquisa) | — | Stack Django pesquisado |
| G.1 | ~2 | F6, F12, F7, F8, F14 | G.5.1 | — |
| G.2 | **~3** | F3, F4, F5 | G.1 | +DeviceProfile, +GeoIP, +device-detector, tracking universal |
| G.3 | ~1 | F1 | — | — |
| G.5.2 | ~1 | F13 (backend) | G.1, G.2 | +DeviceProfile integration |
| G.5.3 | ~1 | F13 (frontend) | G.5.2 | getData() no page load (nao submit) |
| G.4 | ~1 | F2 | G.2 | — |
| G.6 | ~1 | F9, F10, F11 | G.1 | — |
| G.7 | ~1 | F15 | — | — |
| G.8 | ~0.5 | F7, F8 (detalhes) | G.1 | — |
| **Total** | **~11** | **15 gaps** | — | +1 sessao (G.2 expandido) |
