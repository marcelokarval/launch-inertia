# Arquitetura de Dados de Captura — Launch Inertia

---

## Frontmatter

| Campo | Valor |
|-------|-------|
| **Documento** | CAPTURE_DATA_ARCHITECTURE.md |
| **Tipo** | Documento de controle — modelagem de dados e decisoes arquiteturais |
| **Versao** | 1.0 |
| **Criado em** | 2026-02-17 |
| **Atualizado em** | 2026-02-17 |
| **Autor** | Claude (assistente) + Marcelo (owner) |
| **Status** | DECISOES CONSOLIDADAS — pronto para implementacao |
| **Referencia** | CAPTURE_WORKFLOW.md v3.1, IMPLEMENTATION_PLAN.md |

### Objetivo

Documentar a arquitetura de dados para o sistema de captura de leads, substituindo
o fluxo legado Next.js + Baserow por Django + PostgreSQL com modelagem relacional
otimizada e uso estrategico de JSONb.

### Historico de alteracoes

| Versao | Data | Descricao |
|--------|------|-----------|
| 1.0 | 2026-02-17 | Consolidacao inicial: analise dado-a-dado das URLs legadas, decisoes de modelagem, schema star com dimensoes normalizadas, progressao visitante→lead, integracao CaptureEvent↔CaptureSubmission |

---

## 1. Premissa Fundamental: Inversao de Paradigma

### Legado (Next.js + Baserow)

O Next.js era "burro" — nao tinha acesso ao backend. Precisava empacotar TUDO na URL
para que o N8N/Baserow recebesse todos os dados como uma "planilha flat":

```
Usuario → Next.js → URL com 30+ parametros → N8N → Baserow (tabela flat)
```

### Novo (Django + PostgreSQL)

O Django **ja sabe** quem e a pagina, o launch, o interesse, a lista, o webhook.
O frontend so envia o que **somente ele** sabe: dados do usuario e dados do navegador.

```
Usuario → Django (ja sabe tudo sobre a pagina)
  → Frontend envia: email, phone, fingerprint, UTMs, click_ids
  → Backend resolve: launch, interest, n8n config, page version
  → Backend persiste: relacional + JSONb
  → Backend encaminha: N8N (async, Celery)
```

**Regra:** Se o backend ja tem a informacao (via CapturePage, Launch, Interest), ela
NAO deve ser enviada pelo frontend. O frontend e fino.

---

## 2. Analise Dado-a-Dado das URLs Legadas

### 2.1 Estrutura das URLs de Producao

URLs analisadas de `cp.arthuragrelli.com` com dados reais de trafego pago (Meta Ads)
e organico (Instagram link in bio). Os parametros se dividem em 3 camadas:

- **Camada A**: Parametros de trafego (Meta Ads injeta na URL do anuncio)
- **Camada B**: Dados do formulario (usuario preenche + FingerprintJS enriquece)
- **Camada C**: Contexto de campanha (legado Next.js→Baserow, agora resolvido server-side)

### 2.2 Convencao de Naming dos UTMs (Padrao Meta Ads)

O time de trafego adota uma convencao pipe-separated (`|`) nos UTMs:

#### utm_source (Padrao Meta, nao custom)

Formato: `{Platform}_{Placement}` — gerado automaticamente pelo Meta Ads.

```
Instagram_Reels    → provider=meta, platform=instagram, placement=reels
Facebook_Feed      → provider=meta, platform=facebook, placement=feed
ig                 → provider=meta, platform=instagram (organico)
```

#### utm_medium (Composto, pipe-separated)

Formato: `{payment_type}|{audience_temp}|{adset_name}|{meta_adset_id}`

```
Pago|Quente|01 - [Mix Quente] [AD364_RC_CAPT_WH0725]|120237085840210543
 │      │              │                                    │
 │      │              └── nome do adset (legivel)          └── Meta Adset ID
 │      └── temperatura do publico (hot/cold/warm)
 └── tipo de trafego (paid/organic)
```

O adset_name tambem contem sub-informacoes:
- Numero sequencial: `01`
- Tipo de audiencia: `[Mix Quente]`, `[Aberto]`
- Codigo do criativo: `[AD364_RC_CAPT_WH0725]`

#### utm_campaign (Composto, pipe-separated)

Formato: `{launch_code}|{campaign_name}|{meta_campaign_id}`

```
WH0126|[WH0126] [Captacao] [Quente] [Repasse] [V1] - Melhores 2|120237085838390543
  │              │                                                    │
  │              └── nome da campanha (estruturado)                   └── Meta Campaign ID
  └── launch code (= Launch.launch_code)
```

O campaign_name segue padrao: `[{launch}] [{stage}] [{temp}] [{interest}] [{version}] - {variant}`

#### utm_content (Codigo do criativo)

Formato: `AD{numero}_{interest_code}_{funnel_stage}_{launch_code}`

```
AD364_RC_CAPT_WH0725
  │    │    │     │
  │    │    │     └── launch onde o criativo foi criado (pode ser diferente do atual!)
  │    │    └── estagio do funil: CAPT=captacao
  │    └── codigo do interesse: RC=repasse-contrato, TD=tax-deed
  └── ID sequencial do criativo: #364
```

**DESCOBERTA IMPORTANTE:** Criativos sao reutilizados entre launches e cross-testados
entre interesses. AD338 (Tax Deed) roda em campanha de Repasse Contrato. O interesse
do criativo e independente do interesse da campanha.

#### utm_term e utm_id (REDUNDANTES)

- `utm_term` = Meta Adset ID (identico ao segmento 4 de utm_medium)
- `utm_id` = Meta Campaign ID (identico ao segmento 3 de utm_campaign)

Existem como conveniencia para ferramentas de analytics. O parser usa como **fallback**
se o split de utm_medium/utm_campaign falhar.

#### vk_ad_id (Meta Ad ID)

O valor `120237085839820543` e o ID do **anuncio** no Meta (nivel mais granular:
Campaign > Adset > Ad). Vem do Voluum (tracking intermediario).

**Este e o unico lugar onde o Ad ID aparece.** Nao esta em nenhum UTM padrao.
Fallback: se utm_content contiver `|` com ID no final, extrai de la.

#### vk_source (Classificacao Voluum)

Exemplo: `paid_metaads`. Indica provedor + tipo de trafego. Vai como metadado
no provider_data JSONField da entidade relevante.

#### fbclid (Facebook Click ID)

**ESSENCIAL** para:
1. Meta Conversions API (CAPI) — server-side tracking de conversoes
2. Deduplicacao em reenvios server-to-server
3. Match de conversao offline

Unico por clique. NAO pode ir em dimensao (cardinalidade = clicks).
Fica na tabela de fato (CaptureSubmission).

### 2.3 Dados do Formulario

| Dado | Quem gera | Destino no Django |
|------|-----------|-------------------|
| email | Usuario digita | CaptureSubmission.email_raw + ContactEmail.value |
| phone | Usuario digita | CaptureSubmission.phone_raw + ContactPhone.value |
| visitor_id | FingerprintJS (cookie ou SDK) | FingerprintIdentity.hash |
| request_id | FingerprintJS (ou Django) | Nullable — Django gera timestamp proprio |
| capture_token | Django (prop Inertia, echo back) | CaptureSubmission.capture_token |

### 2.4 Dados que o Backend Ja Sabe (NAO enviar do frontend)

| Dado legado | Fonte no Django | Motivo |
|-------------|----------------|--------|
| `_interesse` | `CapturePage.interest` FK | Resolvido pelo slug da URL |
| `_list` | `CapturePage.n8n_list_id` | Configurado no backend |
| `_launch` | `CapturePage.launch.launch_code` | FK no modelo |
| `_utm_*_cp` | N8NProxyService transforma | Sufixo `_cp` adicionado no payload builder |
| `_versao_page_cp` | Extraido do slug | Pre-computado na criacao do CapturePage |
| `_versao_copy_cp` | Derivado do slug ou config | Pre-computado |
| `_load` | `time.monotonic()` na view | Mais preciso que JS |
| `_ts` | `CaptureEvent.created_at` | Timestamp do servidor |

### 2.5 Dados que o Frontend DEVE Enviar

| Dado | Fonte | Observacao |
|------|-------|------------|
| email | Input do usuario | Obrigatorio |
| phone | Input do usuario | Obrigatorio |
| visitor_id | Cookie fpjs_vid ou SDK | FingerprintJS visitorId |
| request_id | SDK (quando dispara) | Nullable — nao dispara se cookie existe |
| capture_token | Prop Inertia (echo back) | UUID gerado no GET |
| utm_source | URL query param | Lido da URL pelo JS |
| utm_medium | URL query param | Lido da URL pelo JS |
| utm_campaign | URL query param | Lido da URL pelo JS |
| utm_content | URL query param | Lido da URL pelo JS |
| utm_term | URL query param | Usado como fallback de adset_id |
| utm_id | URL query param | Usado como fallback de campaign_id |
| fbclid | URL query param | **NOVO** — essencial para Meta CAPI |
| vk_ad_id | URL query param | **NOVO** — Meta Ad ID |
| vk_source | URL query param | **NOVO** — classificacao de trafego |

### 2.6 Trafego Organico vs Pago

| Aspecto | Pago (Meta Ads) | Organico (Link in Bio, etc.) |
|---------|-----------------|------------------------------|
| utm_source | `Instagram_Reels` (padrao Meta) | `ig` (padrao Instagram) |
| utm_medium | `Pago\|{temp}\|{adset}\|{id}` (composto) | `social` (padrao GA) |
| utm_campaign | `{launch}\|{name}\|{id}` (composto) | Ausente |
| utm_content | `AD{N}_{interest}_{stage}_{launch}` | `link_in_bio`, `captura-post-viral` |
| utm_term/utm_id | Meta IDs | Ausentes |
| vk_ad_id | Meta Ad ID | Ausente |
| fbclid | Facebook Click ID | Presente (Instagram gera) |
| `_cp` suffix params | Ausentes (UTMs ja sao custom) | Presentes (preservam taxonomia interna) |

**Decisao:** No organico, os campos `_cp` (que chegam via `utm_source_cp`, `utm_medium_cp`,
etc.) contem a taxonomia interna da equipe. O parser deve verificar primeiro os UTMs padrao;
se forem genericos (`social`, `ig`), consulta os `_cp` como fonte primaria da taxonomia.

---

## 3. Progressao Visitante → Lead

### 3.1 Fases com FingerprintIdentity

```
FASE 0: Visita pura (primeiros ~500ms)
  ├── capture_token gerado pelo Django (GET)
  ├── CaptureEvent(page_view) criado
  ├── visitor_id = "" (cookie ainda nao lido ou SDK nao disparou)
  ├── DeviceProfile vinculado (VisitorMiddleware, server-side)
  └── Identity: NAO existe ainda

FASE 1: Identificacao via Fingerprint (~500ms-2s)
  ├── CENARIO A: Cookie fpjs_vid existe
  │   └── visitor_id recuperado do cookie instantaneamente
  │   └── FpJS Pro NAO dispara (economia de chamada)
  │   └── Timestamp gerado pelo Django
  │
  ├── CENARIO B: Cookie NAO existe
  │   └── FpJS Pro dispara em background
  │   └── Retorna visitorId + requestId
  │   └── Cookie fpjs_vid salvo para futuro
  │
  ├── Em AMBOS os cenarios:
  │   └── FingerprintIdentity.get_or_create(hash=visitorId)
  │   └── Identity CRIADA (anonima, confidence_score baixo)
  │   └── FingerprintIdentity.identity = esta Identity
  │   └── Primeiro visitorId = MASTER do Identity
  │
  └── CaptureEvent(page_view) ATUALIZADO com:
      ├── visitor_id
      ├── fingerprint_identity FK
      └── identity FK (a anonima)

FASE 2: Tentativa de Captura
  ├── POST do formulario com email + phone + visitor_id + UTMs + capture_token
  ├── CaptureEvent(form_attempt) criado
  ├── Validacao server-side
  │   ├── Se FALHA: CaptureEvent(form_error) + re-render com mesmo capture_token
  │   └── Se OK: continua para FASE 3
  └── Identity JA EXISTE (da FASE 1, anonima)

FASE 3: Lead Capturado
  ├── ResolutionService ENRIQUECE a Identity existente (+email, +phone)
  │   OU faz MERGE se email/phone ja pertence a outra Identity
  │   └── visitorId mais antigo = master, outros = slaves
  ├── CaptureSubmission CRIADO (registro do lead)
  ├── CaptureEvent(form_success) criado
  ├── bind_events_to_identity() retroativo (FASE 0 e 1 vinculadas)
  ├── Attribution salva (UTMs → modelo Attribution)
  ├── UTMs parseados → dimensoes (TrafficSource, AdCampaign, AdGroup, AdCreative)
  └── N8N webhook disparado (Celery async)

FASE 4: Lead Encaminhado
  ├── N8N webhook recebe payload
  ├── CaptureSubmission.n8n_status = "sent"
  └── CaptureSubmission.n8n_response = resposta do webhook

FASE 5: Visitante Retorna (outra sessao)
  ├── Cookie fpjs_vid existe → visitor_id recuperado
  ├── Identity JA EXISTE com email+phone da FASE 3
  ├── CaptureEvent(page_view) ja nasce com identity FK vinculada
  └── Se submeter novamente → CaptureSubmission com is_duplicate=True, mesmo Identity
```

### 3.2 Progressao Inferida (nao armazenada como estado)

A progressao NAO e um campo de status mutavel — e inferida dos fatos imutaveis:

| Consulta | Resultado | Significado |
|----------|-----------|-------------|
| capture_token com page_view sem form_attempt | Visitante que nao tentou | Bounce ou browsing |
| capture_token com form_attempt sem form_success | Abandono pos-attempt | Possivel erro de validacao |
| capture_token com form_success | Lead capturado | CaptureSubmission existe |
| CaptureSubmission com n8n_status="sent" | Lead encaminhado | N8N processou |
| Multiplos CaptureSubmission para mesmo Identity | Lead recorrente | Participou de mais de um launch |

---

## 4. Comunicacao CaptureEvent ↔ CaptureSubmission

### 4.1 Vinculo via capture_token

```
capture_token: "a1b2c3d4-..."
│
├── CaptureEvent(page_view)      ← GET /inscrever-wh-rc-v3/ (t=0s)
├── CaptureEvent(form_attempt)   ← POST (t=47s)
├── CaptureEvent(form_error)     ← validacao falhou (t=47s)
├── CaptureEvent(form_attempt)   ← segundo POST (t=63s)
├── CaptureEvent(form_success)   ← sucesso (t=63s)
│
└── CaptureSubmission             ← criado no form_success
    ├── capture_token: "a1b2c3d4-..."  ← join logico
    ├── identity: FK(Identity)
    ├── capture_page: FK(CapturePage)
    ├── ad_creative: FK(AdCreative)
    ├── ad_group: FK(AdGroup)
    ├── traffic_source: FK(TrafficSource)
    └── click_id: "PAZXh0bg..."
```

### 4.2 Papeis distintos

| | CaptureEvent | CaptureSubmission |
|---|---|---|
| **O que e** | Diario do visitante | Registro do lead |
| **Granularidade** | N eventos por sessao | 1 por conversao |
| **Identidade** | Pode ser anonima (FASE 0) | Sempre tem Identity |
| **Uso principal** | Funil de conversao, metricas de UX | CRM, N8N, dedup |
| **Relacao** | NAO tem FK para Submission | NAO tem FK para Event |
| **Vinculo** | Via capture_token (join logico) | Via capture_token |

### 4.3 Metricas derivadas do vinculo

```python
# Tempo na pagina
time_on_page = form_attempt.created_at - page_view.created_at

# Tentativas antes de sucesso
attempts = CaptureEvent.objects.filter(
    capture_token=token, event_type="form_attempt"
).count()

# Teve erro de validacao?
had_error = CaptureEvent.objects.filter(
    capture_token=token, event_type="form_error"
).exists()

# Tempo de renderizacao da view (time.monotonic())
render_time_ms = page_view.extra_data.get("server_render_time_ms")
```

---

## 5. Schema Star — Modelagem de Dados

### 5.1 Visao Geral

```
REFERENCIAS (config, muito baixa cardinalidade):
  AdProvider (~5-10 rows)
  AdPlatform (~15-20 rows) → FK AdProvider

DIMENSOES (baixa-media cardinalidade, get_or_create):
  TrafficSource (~50-200 rows) → FK AdPlatform
  AdCampaign (~50/launch) → FK AdProvider, FK Launch, FK Interest
  AdGroup (~200/launch) → FK AdCampaign
  AdCreative (~500 total, reutilizaveis) → FK AdProvider, FK Interest
  CapturePage (existente, ~20/launch) → FK Launch, FK Interest
  DeviceProfile (existente, ~1000 total)

ENTIDADES:
  Identity (existente) ← FingerprintIdentity, ContactEmail, ContactPhone
  Attribution (existente) ← UTMs raw por touchpoint

FATOS (alta cardinalidade):
  CaptureEvent (existente) ← page_view, form_attempt, success, error
  CaptureSubmission (NOVO) ← 1 por lead convertido
```

### 5.2 Tabelas de Referencia

#### AdProvider (~5-10 rows)

Tabela de configuracao dos provedores de ads. Armazena config de API e convencao
de naming para o parser de UTMs.

```
AdProvider
├── code: CharField(20, primary_key=True)
│   Valores: "meta", "google", "tiktok", "linkedin", "organic", "direct"
│   Motivo PK natural: nunca muda, evita join extra via surrogate key
│
├── name: CharField(100)
│   Ex: "Meta Ads", "Google Ads", "TikTok Ads", "Organico", "Direto"
│
├── api_config: JSONField
│   Configuracao da API do provedor para enriquecimento:
│   {
│     "base_url": "https://graph.facebook.com/v21.0",
│     "auth_type": "oauth2",
│     "insights_endpoint": "/{id}/insights",
│     "rate_limit_per_minute": 200,
│     "available_metrics": ["spend", "impressions", "reach", "cpm", "cpl"]
│   }
│
├── source_patterns: JSONField
│   Padroes para auto-deteccao do provider a partir dos UTMs:
│   {
│     "utm_source_patterns": ["Instagram_.*", "Facebook_.*", "ig", "fb"],
│     "vk_source_values": ["paid_metaads"],
│     "click_id_param": "fbclid"
│   }
│
└── naming_convention: JSONField
    Instrucoes para o UTMParserService:
    {
      "utm_medium_separator": "|",
      "utm_medium_segments": ["payment_type", "audience_temp", "adgroup_name", "adgroup_provider_id"],
      "utm_campaign_separator": "|",
      "utm_campaign_segments": ["launch_code", "campaign_name", "campaign_provider_id"],
      "utm_content_separator": "_",
      "utm_content_segments": ["creative_seq", "interest_code", "funnel_stage", "creative_launch_code"],
      "ad_id_param": "vk_ad_id",
      "adset_id_fallback": "utm_term",
      "campaign_id_fallback": "utm_id"
    }
```

#### AdPlatform (~15-20 rows)

Plataformas de cada provedor. Cada provedor pode ter multiplas plataformas.

```
AdPlatform
├── provider: FK(AdProvider)
│   Ex: AdProvider(code="meta")
│
├── code: CharField(50, unique)
│   Valores: "instagram", "facebook", "youtube", "google_search",
│            "google_display", "tiktok", "linkedin"
│
├── name: CharField(100)
│   Ex: "Instagram", "Facebook", "YouTube"
│
├── platform_data: JSONField
│   {
│     "icon_url": "/static/icons/instagram.svg",
│     "valid_placements": ["reels", "feed", "stories", "explore"],
│     "default_placement": "feed"
│   }
│
└── unique_together: (provider, code)
```

### 5.3 Tabelas Dimensao

#### TrafficSource (~50-200 rows)

Combinacao normalizada de plataforma + posicionamento. Referenciada por
muitas submissions. Elimina repeticao de "Instagram_Reels" etc.

```
TrafficSource (BaseModel, PUBLIC_ID_PREFIX = "tfs")
├── platform: FK(AdPlatform)
│   Resolve provider automaticamente: traffic_source.platform.provider
│
├── placement: CharField(50)
│   Valores: "reels", "feed", "stories", "search", "shorts", "display"
│
└── unique_together: (platform, placement)

Resolucao:
  utm_source="Instagram_Reels"
    → split("_") → platform_code="instagram", placement="reels"
    → AdPlatform.get(code="instagram") → provider=meta
    → TrafficSource.get_or_create(platform=instagram_obj, placement="reels")

  1000 clicks de Instagram_Reels = 1 row TrafficSource. Zero repeticao.
```

#### AdCampaign (~50 por launch)

Campanha no provedor de ads. Contem o Meta Campaign ID para queries de API.

```
AdCampaign (BaseModel, PUBLIC_ID_PREFIX = "acp")
├── provider: FK(AdProvider)
├── provider_id: CharField(50, db_index=True)
│   Ex: "120237085838390543" (Meta Campaign ID)
│   Nullable para organico (nao tem ID de campanha)
│
├── name: TextField
│   Ex: "[WH0126] [Captacao] [Quente] [Repasse] [V1] - Melhores 2"
│
├── launch: FK(Launch, nullable)
│   Extraido automaticamente do nome (WH0126 → Launch.launch_code)
│
├── interest: FK(Interest, nullable)
│   Extraido automaticamente do nome ([Repasse] → Interest com slug contendo "rc")
│
├── funnel_stage: CharField(20)
│   Valores: "capture", "sales", "checkout", "content", "retention"
│   Extraido do nome: [Captacao] → "capture"
│
├── parsed_data: JSONField
│   Dados derivados da naming convention (podem mudar sem migration):
│   {
│     "temperature": "hot",
│     "page_version": "V1",
│     "variant_name": "Melhores 2",
│     "raw_campaign_string": "WH0126|[WH0126]...|120237085838390543"
│   }
│
├── api_data: JSONField
│   Enriquecido pela API do provedor:
│   {
│     "spend": 1250.50,
│     "impressions": 45000,
│     "reach": 32000,
│     "cpm": 27.79,
│     "cpl": 3.47,
│     "last_synced_at": "2026-02-17T10:30:00Z"
│   }
│
└── constraints:
    UniqueConstraint(fields=["provider", "provider_id"],
        condition=Q(provider_id__isnull=False) & ~Q(provider_id=""),
        name="unique_paid_campaign")
    UniqueConstraint(fields=["provider", "name", "launch"],
        condition=Q(provider_id__isnull=True) | Q(provider_id=""),
        name="unique_organic_campaign")
```

#### AdGroup (~200 por launch)

Adset/Ad Group — nivel de otimizacao operacional. Contem os campos mais
usados como filtro em dashboards: payment_type e audience_temperature.

**DECISAO: Dimensao separada (nao JSON dentro de AdCampaign).**

Razoes:
1. `payment_type` e `audience_temperature` sao filtros primarios de dashboard
   — precisam de indice B-tree, nao JSON path
2. O Meta Adset ID e essencial para API queries (insights por adset)
3. O time de trafego liga/desliga adsets individualmente — precisa ser entidade queryavel
4. Enriquecimento via API e por nivel (insights do adset != da campanha)
5. ~200 rows/launch e dimensao pequena, custo negligivel

```
AdGroup (BaseModel, PUBLIC_ID_PREFIX = "agr")
├── campaign: FK(AdCampaign)
│   Resolve provider: ad_group.campaign.provider
│
├── provider_id: CharField(50, db_index=True)
│   Ex: "120237085840210543" (Meta Adset ID)
│   Nullable para organico
│
├── name: TextField
│   Ex: "01 - [Mix Quente] [AD364_RC_CAPT_WH0725]"
│
├── payment_type: CharField(10, db_index=True)
│   Valores: "paid", "organic"
│   Coluna indexada — filtro primario de dashboard
│
├── audience_temperature: CharField(10, db_index=True)
│   Valores: "hot", "cold", "warm"
│   Coluna indexada — filtro primario de dashboard
│
├── parsed_data: JSONField
│   {
│     "audience_type": "mix_quente",
│     "sequence_number": "01",
│     "creative_codes_in_name": ["AD364_RC_CAPT_WH0725"],
│     "raw_medium_string": "Pago|Quente|01 - ...|120237085840210543"
│   }
│
├── api_data: JSONField
│   Enriquecido pela API: spend, impressions, reach, CPM por adset
│
└── constraints:
    UniqueConstraint(fields=["campaign", "provider_id"],
        condition=Q(provider_id__isnull=False) & ~Q(provider_id=""),
        name="unique_paid_adgroup")
    UniqueConstraint(fields=["campaign", "name"],
        condition=Q(provider_id__isnull=True) | Q(provider_id=""),
        name="unique_organic_adgroup")
```

#### AdCreative (~500 total, reutilizaveis entre launches)

Criativo publicitario. Entidade INDEPENDENTE com ciclo de vida proprio.
Pode ser cross-testado entre interesses e reutilizado entre launches.

```
AdCreative (BaseModel, PUBLIC_ID_PREFIX = "acr")
├── provider: FK(AdProvider)
│
├── provider_id: CharField(50, db_index=True)
│   Ex: "120237085839820543" (de vk_ad_id)
│   Nullable — organico nao tem, fallback por creative_code
│
├── creative_code: CharField(20)
│   Ex: "AD364" (parsed de utm_content, prefixo numerico)
│
├── full_code: CharField(100)
│   Ex: "AD364_RC_CAPT_WH0725" (utm_content completo)
│
├── original_interest: FK(Interest, nullable)
│   O interesse do CRIATIVO (RC), nao da campanha onde roda
│   AD338_TD_CAPT → interest="tax-deed" (mesmo rodando em campanha de Repasse)
│
├── original_launch_code: CharField(20, blank=True)
│   O launch onde o criativo foi criado: "WH0725"
│   Diferente do launch atual (WH0126) — criativos sao reutilizados
│
├── funnel_stage: CharField(20)
│   Ex: "capture" (de CAPT no codigo)
│
├── provider_data: JSONField
│   Dados especificos do provedor, enriquecimento da API:
│   {
│     "ad_name": "Video Repasse Miami Beach 30s",
│     "format": "video",
│     "thumbnail_url": "https://...",
│     "performance": {"ctr": 2.3, "cpl": 4.50}
│   }
│
└── constraints:
    UniqueConstraint(fields=["provider", "provider_id"],
        condition=Q(provider_id__isnull=False) & ~Q(provider_id=""),
        name="unique_paid_creative")
    UniqueConstraint(fields=["provider", "full_code"],
        condition=Q(provider_id__isnull=True) | Q(provider_id=""),
        name="unique_organic_creative")
```

### 5.4 Tabela de Fato: CaptureSubmission

Uma linha por lead convertido. Substituicao direta do Baserow.
Todas as dimensoes sao FKs — zero repeticao de dados.

```
CaptureSubmission (BaseModel, PUBLIC_ID_PREFIX = "csb")

  # ── QUEM ──
  identity: FK(Identity)
    Resolvido pelo ResolutionService. Nunca null (FASE 3 garante).

  email_raw: CharField(254)
    Valor exato do formulario (antes de normalizar).
    Diferente de ContactEmail.value que e normalizado.

  phone_raw: CharField(30)
    Valor exato do formulario.

  # ── ONDE ──
  capture_page: FK(CapturePage)
    Resolve TUDO: launch, interest, slug, n8n config, page version.
    Nunca null — toda submissao tem uma pagina.

  # ── TRAFEGO (dimensoes normalizadas) ──
  traffic_source: FK(TrafficSource, nullable)
    Null se trafego direto (sem utm_source).

  ad_group: FK(AdGroup, nullable)
    Null se organico sem adset. Resolve → campaign → provider.

  ad_creative: FK(AdCreative, nullable)
    Null se sem utm_content parseavel.

  click_id: CharField(200, blank=True, db_index=True)
    fbclid / gclid / ttclid — unico por clique.
    Essencial para Meta CAPI e deduplicacao.

  # ── FINGERPRINT ──
  visitor_id: CharField(100, blank=True, db_index=True)
    FingerprintJS visitorId.

  # ── TRACKING ──
  capture_token: UUIDField(db_index=True)
    Vinculo com CaptureEvents (join logico, nao FK).

  device_profile: FK(DeviceProfile, nullable)
    Dimensao de device do VisitorMiddleware.

  # ── REDE ──
  ip_address: GenericIPAddressField(nullable)
  geo_data: JSONField(default=dict)
    GeoIP: {city, region, country, lat, lng, asn, isp}

  # ── N8N ──
  n8n_status: CharField(20, default="pending")
    Valores: "pending", "sent", "failed", "skipped"

  n8n_response: JSONField(default=dict)
    Resposta do webhook. Para debug e reenvio:
    {
      "status_code": 200,
      "sent_at": "2026-02-17T10:30:00Z",
      "attempts": 1,
      "payload_hash": "abc123..."
    }

  # ── METRICAS ──
  server_render_time_ms: FloatField(nullable)
    Tempo de renderizacao da view (time.monotonic()).
    Para monitoramento de performance de cada pagina/rota.

  is_duplicate: BooleanField(default=False)
    Mesmo email + mesmo launch ja existia.

  # ── HERANCA ──
  created_at, updated_at: do BaseModel
  public_id: do PublicIDMixin (csb_xxxxxxxxxxxx)
  is_deleted, deleted_at: do SoftDeleteMixin

  # ── INDICES ──
  indexes:
    - (capture_page, created_at)     ← metricas por pagina
    - (click_id)                     ← dedup CAPI
    - (capture_token)                ← join com CaptureEvents
    - (n8n_status)                   ← reenvios pendentes
    - (visitor_id, created_at)       ← historico do visitante

  db_table: "landing_capture_submission"
```

### 5.5 O que NAO se repete

| Dado | Onde esta (1 vez) | Quantas FKs apontam |
|------|-------------------|---------------------|
| "Instagram_Reels" | TrafficSource (1 row) | N submissions |
| "Pago" | AdGroup.payment_type | N submissions via FK |
| "Quente" | AdGroup.audience_temperature | N submissions via FK |
| Campaign name + ID | AdCampaign (1 row) | N adgroups, N submissions |
| Launch code | Launch model (existente) | Via CapturePage FK |
| Interest slug | Interest model (existente) | Via CapturePage FK |
| Device info | DeviceProfile (1 row) | N events, N submissions |

### 5.6 O que USA JSONField

| Campo | Modelo | Motivo |
|-------|--------|--------|
| `api_config` | AdProvider | Config de API varia por provedor |
| `source_patterns` | AdProvider | Padroes de deteccao variam |
| `naming_convention` | AdProvider | Instrui o parser, pode mudar |
| `platform_data` | AdPlatform | Placements, icone, extras |
| `parsed_data` | AdCampaign, AdGroup | Derivados de naming convention, podem mudar |
| `api_data` | AdCampaign, AdGroup, AdCreative | Enriquecimento da API, schema varia |
| `provider_data` | AdCreative | Dados especificos por plataforma |
| `geo_data` | CaptureSubmission | GeoIP semi-estruturado |
| `n8n_response` | CaptureSubmission | Debug/reenvio, schema variavel |

### 5.7 O que NAO usa JSONField (precisa de indice/FK)

| Campo | Modelo | Motivo |
|-------|--------|--------|
| `provider_id` | AdCampaign, AdGroup, AdCreative | Queries de API, indices |
| `payment_type` | AdGroup | Filtro primario de dashboard, B-tree |
| `audience_temperature` | AdGroup | Filtro primario de dashboard, B-tree |
| `click_id` | CaptureSubmission | Deduplicacao CAPI, indice |
| `capture_token` | CaptureSubmission | Join com CaptureEvents, indice |
| FKs | Todos | Integridade referencial, joins |

---

## 6. UTMParserService

### 6.1 Arquitetura

Servico que parseia UTMs recebidos, auto-detecta o provider, e aplica a
naming convention configurada no AdProvider.

```
UTMParserService
├── parse(utm_data: dict, extra_params: dict) -> ParsedUTMResult
│   ├── 1. Auto-detecta provider via AdProvider.source_patterns
│   ├── 2. Carrega naming_convention do AdProvider
│   ├── 3. Aplica parser com split_with_fallback()
│   ├── 4. get_or_create em todas as dimensoes
│   └── 5. Retorna ParsedUTMResult com FKs prontos
│
├── ParsedUTMResult (dataclass):
│   ├── provider: AdProvider
│   ├── traffic_source: TrafficSource (get_or_create)
│   ├── campaign: AdCampaign (get_or_create)
│   ├── ad_group: AdGroup (get_or_create)
│   ├── creative: AdCreative (get_or_create)
│   ├── click_id: str
│   └── raw_utms: dict (original, para auditoria)
```

### 6.2 Auto-deteccao de Provider

```python
def _detect_provider(utm_data: dict, extra_params: dict) -> AdProvider:
    """Auto-detecta provider baseado nos parametros recebidos."""
    for provider in AdProvider.objects.all():
        patterns = provider.source_patterns
        utm_source = utm_data.get("utm_source", "")
        
        # Checa utm_source contra patterns
        for pattern in patterns.get("utm_source_patterns", []):
            if re.match(pattern, utm_source, re.IGNORECASE):
                return provider
        
        # Checa vk_source
        vk_source = extra_params.get("vk_source", "")
        if vk_source in patterns.get("vk_source_values", []):
            return provider
        
        # Checa presenca de click_id especifico
        click_param = patterns.get("click_id_param", "")
        if click_param and extra_params.get(click_param):
            return provider
    
    return AdProvider.objects.get(code="direct")  # fallback
```

### 6.3 Resiliencia no Parse

```python
def _split_with_fallback(value: str, separator: str, expected_segments: list) -> dict:
    """Split pipe-separated value. Fallback para raw se nao bater."""
    if not value or separator not in value:
        return {"_raw": value}
    
    parts = value.split(separator)
    if len(parts) >= len(expected_segments):
        result = dict(zip(expected_segments, parts[:len(expected_segments)]))
        if len(parts) > len(expected_segments):
            result["_extra_segments"] = parts[len(expected_segments):]
        return result
    
    # Fallback: nao conseguiu parsear, armazena raw
    return {
        "_raw": value,
        "_parse_error": f"expected {len(expected_segments)} segments, got {len(parts)}"
    }
```

Se parsing falha, o dado NAO se perde — vai para `parsed_data._raw` e pode ser
re-processado quando a convencao for ajustada no admin.

### 6.4 Parse de Trafego Organico

Para organico, UTMs padrao (`ig`, `social`, `link_in_bio`) sao genericos.
A taxonomia interna esta nos parametros `_cp`:

```python
def _resolve_organic_taxonomy(utm_data: dict, extra_params: dict) -> dict:
    """Para organico, usa parametros _cp como fonte primaria da taxonomia."""
    # UTMs padrao sao genericos — consulta _cp
    return {
        "utm_source": extra_params.get("utm_source_cp", utm_data.get("utm_source", "")),
        "utm_medium": extra_params.get("utm_medium_cp", utm_data.get("utm_medium", "")),
        "utm_campaign": extra_params.get("utm_campaign_cp", utm_data.get("utm_campaign", "")),
        "utm_content": extra_params.get("utm_content_cp", utm_data.get("utm_content", "")),
        "utm_term": extra_params.get("utm_term_cp", utm_data.get("utm_term", "")),
    }
```

---

## 7. Metricas Server-Side

### 7.1 Tempo de Renderizacao (time.monotonic)

```python
def capture_page(request, campaign_slug):
    t_start = time.monotonic()
    # ... processamento da view ...
    response = _render_capture_page(...)
    t_elapsed = time.monotonic() - t_start
    
    # Armazena no CaptureEvent
    # extra_data = {"server_render_time_ms": round(t_elapsed * 1000, 2)}
```

Fornece metrica precisa de performance de cada pagina/rota/slug para
identificar paginas com "peso extra" e impacto na conversao.

### 7.2 Tempo na Pagina (delta de CaptureEvents)

```python
# page_view.created_at = momento do GET
# form_attempt.created_at = momento do POST
time_on_page_seconds = (form_attempt.created_at - page_view.created_at).total_seconds()
```

Sem necessidade de JavaScript timestamps. O capture_token vincula os eventos.

### 7.3 URL de Debug (funcao de servico, nao campo)

A URL legada como "vetor unico de verdade" era necessaria para o Baserow.
No Django, a verdade esta no banco. A URL pode ser reconstruida sob demanda:

```python
class CaptureSubmissionService:
    @classmethod
    def build_debug_url(cls, submission: CaptureSubmission) -> str:
        """Reconstroi URL completa com todos os parametros para debug/reenvio N8N."""
        # Monta a partir dos relacionamentos, sem armazenar
```

---

## 8. Fluxo de Dados Resumido

```
                                    ┌─────────────────────┐
                                    │    AdProvider        │
                                    │  (meta, google, ...) │
                                    └─────────┬───────────┘
                                              │ FK
                                    ┌─────────┴───────────┐
                                    │    AdPlatform        │
                                    │ (instagram, youtube) │
                                    └─────────┬───────────┘
                                              │ FK
                        ┌─────────────────────┴──────────────────────┐
                        │              TrafficSource                  │
                        │  (instagram+reels, facebook+feed, ...)     │
                        └─────────────────────┬──────────────────────┘
                                              │ FK
                                              │
   ┌──────────────┐    ┌──────────────┐       │       ┌──────────────┐
   │  AdCampaign  │───▶│   AdGroup    │       │       │  AdCreative  │
   │  (~50/launch)│    │ (~200/launch)│       │       │ (~500 total) │
   │              │    │ payment_type │       │       │ reutilizavel │
   │  provider_id │    │ audience_temp│       │       │ cross-launch │
   │  → Meta API  │    │ → Meta API   │       │       │ → Meta API   │
   └──────┬───────┘    └──────┬───────┘       │       └──────┬───────┘
          │                   │               │              │
          │                   │ FK            │ FK           │ FK
          │                   ▼               ▼              ▼
          │            ┌─────────────────────────────────────────────┐
          │            │            CaptureSubmission                 │
          │            │                                             │
          │            │  identity ──────────▶ Identity              │
          │            │  capture_page ──────▶ CapturePage           │
          │            │    └── .launch ────▶ Launch                 │
          │            │    └── .interest ──▶ Interest               │
          │            │  ad_group ──────────▶ AdGroup               │
          │            │    └── .campaign ──▶ AdCampaign             │
          │            │  ad_creative ──────▶ AdCreative             │
          │            │  traffic_source ───▶ TrafficSource          │
          │            │    └── .platform ──▶ AdPlatform             │
          │            │      └── .provider▶ AdProvider              │
          │            │  device_profile ───▶ DeviceProfile          │
          │            │  click_id (fbclid)                          │
          │            │  capture_token ────── join ──▶ CaptureEvent │
          │            │  email_raw, phone_raw                       │
          │            │  n8n_status, n8n_response                   │
          │            └─────────────────────────────────────────────┘
```

---

## 9. Proximos Passos de Implementacao

| # | Tarefa | Dependencia |
|---|--------|-------------|
| 1 | Criar modelos AdProvider, AdPlatform | Nenhuma |
| 2 | Criar modelos TrafficSource, AdCampaign, AdGroup, AdCreative | #1 |
| 3 | Criar modelo CaptureSubmission | #2 + modelos existentes |
| 4 | Implementar UTMParserService | #1 (naming_convention) |
| 5 | Integrar parser + get_or_create na view capture_page | #3, #4 |
| 6 | Adicionar fbclid/vk_ad_id/vk_source ao CaptureForm.tsx | Nenhuma |
| 7 | Adicionar time.monotonic() nas views | Nenhuma |
| 8 | Seed de AdProvider (meta, google, tiktok, organic, direct) | #1 |
| 9 | Seed de AdPlatform (instagram, facebook, youtube, etc.) | #8 |
| 10 | Testes unitarios para UTMParserService | #4 |
| 11 | Testes de integracao para fluxo completo | #5 |
| 12 | Migration para SQL views de metricas | #3 |

---

*Documento gerado a partir de discussao colaborativa entre Claude (assistente) e Marcelo (owner).*
*Referencia: URLs reais de producao de cp.arthuragrelli.com analisadas em 2026-02-17.*
