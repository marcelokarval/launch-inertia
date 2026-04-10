# Identity & Launch System -- Analysis & Architecture

**Data**: 2026-02-12
**Versao**: 4 (decisoes Q33/Q39/Q40 tomadas + estrategia materialized views + schema lifecycle_global completo)
**Status**: QUASE FINAL -- Q41 (ordem de implementacao) aguardando confirmacao

---

## 1. Entendimento do Negocio

### 1.1 O Modelo Mental Correto

O sistema tem **4 camadas**:

```
CAMADA 1: Identity (Cadastro Universal)
  "Quem e essa pessoa no universo de todos os dados"
  - Permanente, cross-launch, cross-produto
  - Agnostico a lancamentos -- e a MATRIZ de dados
  - Apps: email, phone, fingerprint, identity resolution
  - Qualquer fonte gera Identity: formulario, webhook WhatsApp, import, API

CAMADA 2: Launch (O Lancamento)
  "O evento comercial com tag raiz, fases, produtos, paginas"
  - CONSOME do Identity (busca ou solicita criacao)
  - NAO e dono dos dados da pessoa
  - Tem seu proprio lifecycle para cada participante

CAMADA 3: LaunchParticipant (A Relacao)
  "O que essa pessoa e/fez NESTE lancamento"
  - visitor → lead → engaged → buyer → student → ...
  - Status por lancamento E por produto
  - Tags cascata: ALUNO + ALUNO_WH0325 + ALUNO_MDL0325_DOWNSELL

CAMADA 4: External Systems (N8N como Bridge)
  "Sincronizacao e automacao com mundo externo"
  - Mautic, ManyChat, Stripe, SendFlow/Evolution, Chatwoot
  - Via RabbitMQ queues + Redis shared memory
  - N8N consome filas, executa workflows, devolve resultado
```

### 1.2 O Funil Invertido de Informacao

O funil **nao afunila** -- ele EXPANDE. Cada interacao adiciona dados ao Identity:

```
Dia 1: Visitou pagina (anonimo)
  Identity: { fingerprint: fpi_abc }
  Sabemos: device, browser, geo, URL, UTMs
  Nao sabemos: quem e

Dia 2: Se inscreveu (email + phone)
  Identity: { fingerprint: fpi_abc, email: cem_xyz, phone: cph_123 }
  Badge: "1 inscricao"

Dia 5: Voltou por outra campanha (mesmo lancamento)
  Identity: mesma, +1 FingerprintEvent, +1 Attribution
  Badge: "2 entradas" -- custo da campanha 2 rastreado

Dia 10: Entrou no WhatsApp com phone diferente
  Identity: merge! phone_whatsapp adicionado
  "Nao rastreado" no contexto do lancamento, mas tooltip mostra historico

Mes seguinte: Novo lancamento, mesma pessoa
  Identity: mesma (persistente cross-launch)
  Novo LaunchParticipant para novo lancamento
  Dashboard: "lead recorrente de WH0125"

Comprou:
  Tags cascata: ALUNO + ALUNO_WH0325 + ALUNO_MDL0325
  Stripe metadata: turma, seller, identity, fingerprint
  Sincroniza via N8N: Mautic + ManyChat + plataforma de ensino
```

### 1.3 Identity = Email x Phone x Fingerprint

A resolucao funciona por QUALQUER combinacao dos 3 campos base:

```
email + phone + fingerprint  → Identity completo (confianca maxima)
email + phone                → Identity sem device (import, API)
email + fingerprint          → Identity sem phone
phone + fingerprint          → Identity sem email (ex: WhatsApp + visita)
fingerprint sozinho          → Identity anonimo (so visitou)
phone sozinho                → Identity parcial (webhook WhatsApp)
email sozinho                → Identity parcial (import de lista)
```

**Regras:**
- Proibido duplicidades -- get_or_create para todos
- Qualquer match gera merge nao-destrutivo (master = primeiro Identity criado)
- ResolutionService busca por QUALQUER match (email OR phone OR fingerprint)
- ConfidenceEngine pontua baseado na quantidade e qualidade dos dados

### 1.4 O Formulario de Captura

O formulario captura **exclusivamente**: `email + phone`
- Campos hidden: fingerprint data (visitorId, requestId), URL source/dest, UTMs
- `company` e `job_title` **nao existem** no formulario de captura (B2C)
- Apos cadastro: redireciona para grupos WhatsApp

---

## 2. O Que Esta Errado no Codigo Atual

### 2.1 O Model "Contact" e um CRM Generico Que Nao Serve

O model `Contact` (con_*) foi criado como wrapper CRM com campos que nao existem no negocio real:

| Campo | Problema | Decisao |
|-------|----------|---------|
| `Contact.email` | Duplica `ContactEmail` no Identity | REMOVER -- email vive no Identity |
| `Contact.phone` | Duplica `ContactPhone` no Identity | REMOVER -- phone vive no Identity |
| `Contact.company` | Nao existe no formulario de captura (B2C) | REMOVER |
| `Contact.job_title` | Nao existe no formulario de captura (B2C) | REMOVER |
| `Contact.status` (lead/prospect/customer/churned) | Lifecycle pertence ao LaunchParticipant | REMOVER do Contact |
| `Contact.source` | Redundante com Attribution no Identity | REMOVER |
| `Contact.lead_score` | Calculado pelo ConfidenceEngine | REMOVER como campo manual |
| `Contact.email_verified` | Duplica `ContactEmail.is_verified` | REMOVER |
| `Contact.phone_verified` | Duplica `ContactPhone.is_verified` | REMOVER |
| `AdditionalEmail` model | Redundante com `ContactEmail` no Identity | REMOVER inteiro |
| `AdditionalPhone` model | Redundante com `ContactPhone` no Identity | REMOVER inteiro |
| `ContactNote` model | Conceito CRM generico nao solicitado | REMOVER (reavaliar depois) |
| `CustomFieldDefinition` | Pode ser util, mas depende de contexto (por launch?) | MANTER -- discutir escopo |

### 2.2 O Que "Contact" Deveria Ser

**Contact nao deveria existir como entidade separada.** O Identity JA E o cadastro universal. O que o operador precisa no dashboard e:

1. **Visualizar Identities** com seus canais (emails, phones, fingerprints)
2. **Visualizar participacao em lancamentos** (LaunchParticipant)
3. **Adicionar anotacoes/tags manuais** se necessario

Isso pode viver diretamente no Identity (que ja tem `metadata` JSONField) ou como extensao leve. O model Contact como existe hoje -- com 15+ campos duplicados -- precisa ser eliminado ou radicalmente simplificado.

### 2.3 Frontend Completamente Desalinhado

O frontend de Contatos (Index, Show, Create, Edit, Delete) foi construido para o model CRM generico. Com a eliminacao/simplificacao do Contact:

- **Create/Edit**: nao fazem sentido como "criar contato manualmente" com company/job_title. O correto seria "importar cadastro" (email + phone) ou visualizar/editar dados do Identity
- **Index**: deveria listar Identities, nao Contacts
- **Show**: a parte de Identity (abas) esta no caminho certo, mas a parte CRM (card principal) esta errada

---

## 3. Respostas Consolidadas (Q1-Q32)

### Bloco 1: Ciclo de Vida

| Q | Pergunta | Resposta |
|---|----------|---------|
| Q1 | Como nasce um cadastro? | **(d) Todas**: formulario, webhook WhatsApp, import, API, manual |
| Q2 | Status muda automatico? | **Sim**, baseado em eventos, mas aceita correcoes pontuais |
| Q3 | Source automatico? | **Ambos**, mas `source` no Contact nao faz sentido -- UTMs via Attribution ja cobrem |

### Bloco 2: Identity Resolution

| Q | Pergunta | Resposta |
|---|----------|---------|
| Q4 | Identity e automatica? | **Sim**. Sistema atual (Baserow+N8N) ja faz isso. Novo sistema e virgem |
| Q5 | Fluxo de resolucao? | ContactEmail + ContactPhone + FingerprintIdentity → ResolutionService → Identity. Proibido duplicidades. Qualquer match = merge nao-destrutivo |
| Q6 | Persiste entre lancamentos? | **Totalmente**. Identity e agnostica a lancamentos |

### Bloco 3: Visitantes

| Q | Pergunta | Resposta |
|---|----------|---------|
| Q7-Q8 | Visitante vs cadastrado | Visitante anonimo tem FingerprintIdentity. Visitante conhecido (ja cadastrou antes) e identificado pelo visitorId mesmo sem formulario. Todos sao "visitantes" ate se inscreverem |

### Bloco 4: Duplicacoes

| Q | Pergunta | Resposta |
|---|----------|---------|
| Q9-Q10 | Contact.email vs ContactEmail | **ContactEmail no Identity e a verdade**. Contact.email e duplicacao. Eliminar |

### Bloco 5: Tags e Lancamentos

| Q | Pergunta | Resposta |
|---|----------|---------|
| Q11 | Tag raiz = Tag model? | **Sim**, criada manualmente no step 1 do setup do lancamento. Precisa de model Launch dedicado |
| Q12 | Tags automaticas? | **Sim**, ao se inscrever recebe tag do lancamento. Ao comprar recebe tags do produto |
| Q13 | Tags cross-launch? | **Sim**. WH0125 + WH0325 no mesmo Identity |

### Bloco 6: Outros

| Q | Pergunta | Resposta |
|---|----------|---------|
| Q14-Q15 | ContactNote | **Nao solicitado**. Conceito CRM generico |
| Q16-Q17 | CustomFields | **A discutir**. Pode ser por lancamento |
| Q18-Q19 | Create/Edit manual | Faz sentido para import manual (email+phone), nao com company/job_title |
| Q21 | company/job_title | **Remover**. Formulario captura so email+phone |
| Q22 | Tag raiz | **Criada manualmente** no step 1 do wizard de lancamento |
| Q23 | Produtos no Stripe | **Sim**, referencia ao Stripe com metadata rico (turma, seller, etc). N8N na pipeline de setup |
| Q24 | Fases do lancamento | **Configuradas pelo operador**. Geralmente padrao (CPLs, abertura, fechamento). Varia em downsell e Black Friday |
| Q25 | Paginas de captura | **No proprio sistema Inertia**, container separado (padrao prop4you-inertia) |
| Q26 | Lifecycle do participante | visitor → lead → engaged → buyer → student → refunded → delinquent → churned (+ mais) |
| Q27 | Status por produto? | **Sim**. ALUNO (launch), ALUNO_WH0125 (launch-specific), ALUNO_MDL0125_DOWNSELL (product-specific) |
| Q28 | Stripe → status | **Automatico** via webhook |
| Q29 | Tag sync externo | **Sim**. Bidirecional. N8N le JSON com raiz e gera todas + sincroniza |
| Q30 | N8N continua? | **Sim, fortemente**. Mesma pilha Docker, RabbitMQ, Redis compartilhado. Usar para Mautic, ManyChat, Stripe pipelines |
| Q31 | Ordem de implementacao | **Funil logico**: Identity (base) → Launch → Participant → Captura → Analytics |
| Q32 | MVP minimo | **Tudo necessario para um lancamento funcionar**: captura, identity, fases, produtos. Meta: Q2 2026 |

---

## 4. Questao Critica: Lifecycle Global

> Pergunta levantada pelo owner: "E o lifecycle global, vai ficar onde? No mesmo grupo de apps do identity? Ele sera o concentrador dos dados ou vai ter relacionamento com os lancamentos? Ou e o lancamento que se relaciona com o lifecycle global extraindo seus chunks?"

### 4.1 O Problema

Existem DOIS lifecycles distintos:

**Lifecycle por lancamento** (LaunchParticipant):
- visitor → lead → engaged → buyer → student → refunded
- Especifico de UM lancamento
- "Neste lancamento, essa pessoa e student"

**Lifecycle global** (cross-launch):
- "Essa pessoa participou de 3 lancamentos, comprou em 2, reembolsou 1"
- "Primeira vez vista em 2025-01, ultimo acesso em 2026-02"
- "Total gasto: R$ 5.000, LTV estimado: R$ 12.000"
- "Devices: 2 celulares + 1 desktop"
- "Emails: 2 (um principal, um alternativo)"
- "Comportamento: sempre compra no ultimo dia do carrinho"

### 4.2 Onde Vive o Lifecycle Global

**Proposta: O Identity E o lifecycle global.**

O Identity ja concentra:
- Todos os emails (ContactEmail)
- Todos os phones (ContactPhone)
- Todos os fingerprints (FingerprintIdentity → Events)
- Todas as attributions (Attribution)
- Todo o historico (IdentityHistory)

O que falta e a **agregacao dos LaunchParticipants**. Quando um lancamento cria um LaunchParticipant, esse participant aponta para o Identity. Portanto:

```
Identity (idt_*)
  |
  |-- [dados proprios: emails, phones, fingerprints, attributions]
  |
  |-- [reverso]: LaunchParticipant.objects.filter(identity=self)
  |     → "todos os lancamentos que essa pessoa participou"
  |     → cada um com seu status, tags, lifecycle DTO
  |
  |-- [calculado/cache]: lifecycle_global (JSONField no Identity)
  |     {
  |       "first_seen": "2025-01-15T10:00:00Z",
  |       "last_seen": "2026-02-12T14:30:00Z",
  |       "total_launches": 3,
  |       "total_purchases": 2,
  |       "total_spent": 5000.00,
  |       "ltv_estimated": 12000.00,
  |       "tags_global": ["WH0125", "WH0325", "ALUNO", "MDL0125"],
  |       "behavior_pattern": "late_buyer",
  |       "risk_score": 0.15,
  |       ...
  |     }
```

**O lancamento extrai seu chunk** consultando `LaunchParticipant.objects.filter(launch=self)`, e o dashboard global consulta `Identity` com seus `LaunchParticipants` agregados.

### 4.3 Decisao Proposta

```
Identity = concentrador global (dados + lifecycle global como JSONB cache)
LaunchParticipant = chunk por lancamento (aponta para Identity)
LaunchProductParticipant = chunk por produto (aponta para LaunchParticipant)

O lancamento NAO armazena dados do Identity.
O lancamento REFERENCIA o Identity via LaunchParticipant.
O lifecycle global e CALCULADO a partir dos chunks e cacheado no Identity.
```

---

## 5. Arquitetura Proposta de Models

### 5.1 Apps do Identity (ja existem, ajustes minimos)

```
apps/contacts/identity/    → Identity, Attribution, IdentityHistory
apps/contacts/email/       → ContactEmail (cem_*)
apps/contacts/phone/       → ContactPhone (cph_*)
apps/contacts/fingerprint/ → FingerprintIdentity, FingerprintEvent, FingerprintContact
```

**Ajustes necessarios no Identity:**
- Adicionar `lifecycle_global: JSONField` (cache calculado)
- Adicionar `display_name: CharField` (preenchido na captura ou inferido)
- Remover dependencia do model Contact (Identity deve funcionar standalone)

### 5.2 App de Lancamentos (NOVA)

```
apps/launches/
  ├── models/
  │   ├── launch.py             → Launch (lch_*)
  │   ├── launch_product.py     → LaunchProduct (lpr_*)
  │   ├── launch_phase.py       → LaunchPhase (lph_*)
  │   ├── launch_page.py        → LaunchPage (lpg_*)
  │   ├── participant.py        → LaunchParticipant (lpt_*)
  │   └── product_participant.py→ LaunchProductParticipant (lpp_*)
  ├── services/
  │   ├── launch_service.py     → CRUD + setup wizard
  │   ├── participant_service.py→ lifecycle management
  │   ├── capture_service.py    → processa formulario de captura
  │   └── tag_service.py        → tag generation + sync
  ├── tasks/
  │   ├── sync_tasks.py         → tag sync via N8N/RabbitMQ
  │   └── lifecycle_tasks.py    → lifecycle transitions async
  ├── signals.py
  └── views.py
```

### 5.3 Model Contact -- Eliminar ou Simplificar

**Opcao A: Eliminar Contact**
- Identity se torna a entidade principal no dashboard
- `notes`, `custom_fields`, `owner` movem para Identity ou viram extensao
- Paginas de "Contatos" no dashboard listam Identities

**Opcao B: Contact ultra-slim (apenas gestao)**
```python
class Contact(BaseModel):
    identity = OneToOneField(Identity)
    owner = ForeignKey(User)         # quem gerencia
    created_by = ForeignKey(User)    # quem criou
    tags = M2MField(Tag)             # tags MANUAIS do operador
    notes = TextField(blank=True)    # anotacoes livres
    custom_fields = JSONField()      # campos dinamicos
    # NENHUM outro campo -- tudo vem do Identity
```

**Em ambas as opcoes**: `AdditionalEmail`, `AdditionalPhone`, `ContactNote`, e os campos `email`, `phone`, `company`, `job_title`, `status`, `source`, `lead_score`, `email_verified`, `phone_verified` sao ELIMINADOS.

---

## 6. Fluxos Completos (Todos os Cenarios)

### Cenario A: Visitante Anonimo

```
FingerprintJS dispara → webhook → Django/N8N fila
  ├── FingerprintIdentity.get_or_create(hash=visitorId)
  ├── FingerprintEvent.create(page_view, url, requestId→timestamp)
  ├── Attribution.create(utms da URL)
  ├── URL → identifica Launch (pagina pertence ao WH0325)
  ├── Identity: existe? (busca por fingerprint)
  │   ├── SIM (cadastrou em lancamento anterior):
  │   │   └── LaunchParticipant.get_or_create(identity, WH0325, status=visitor)
  │   │       "Visitante conhecido -- NAO se inscreveu neste lancamento"
  │   │       Tooltip: historico de WH0125 onde era Lead
  │   └── NAO:
  │       └── Identity nova + LaunchParticipant(status=visitor)
  │           "Visitante anonimo"
  └── Dashboard WH0325: +1 visitor
```

### Cenario B: Inscricao (email + phone)

```
Formulario POST → Django
  ├── ContactEmail.get_or_create(value=email)
  ├── ContactPhone.get_or_create(value=phone)
  ├── FingerprintIdentity: ja existe do page_view
  ├── ResolutionService.resolve(email, phone, fingerprint)
  │   └── Merge nao-destrutivo → Identity unica
  ├── LaunchParticipant: visitor → lead
  │   enrolled_at = now, entry_count = 1
  │   Tags auto: WH0325
  └── Via RabbitMQ → N8N:
      ├── Mautic: criar contato + tags
      ├── ManyChat: sincronizar
      └── WhatsApp: enviar link do grupo
```

### Cenario C: Re-entrada (mesmo lancamento)

```
Mesmo Identity, nova visita por outra campanha
  ├── FingerprintEvent novo (URL, UTMs, requestId)
  ├── Attribution novo (custo da campanha rastreado)
  ├── LaunchParticipant: entry_count++ (badge "2", "3"...)
  └── Lifecycle: entries[].append({at, utm, url, cost})
```

### Cenario D: Re-inscricao com dados diferentes

```
Mesmo email, phone diferente (ou vice-versa)
  ├── ContactPhone NOVO → merge no Identity
  ├── Identity agora tem: 1 email, 2 phones, 1+ fingerprints
  ├── LaunchParticipant: entry_count++
  └── Confianca do Identity SOBE
```

### Cenario E: Entrada no WhatsApp (webhook SendFlow/Evolution)

```
Webhook: phone entrou no grupo do WH0325
  ├── ContactPhone.get_or_create(value=phone_whatsapp)
  ├── ResolutionService.resolve(phone=phone_whatsapp)
  │   ├── Match: Identity existente → merge
  │   └── Sem match: Identity nova (so phone, sem email/fingerprint)
  ├── LaunchParticipant:
  │   ├── Ja existe? → lifecycle.whatsapp_joined_at = now
  │   └── Nao existe? → create(status=lead)
  └── Se phone_whatsapp ≠ phone_cadastro:
      Identity tem 2 phones
      Dashboard: "phone WhatsApp divergente" com tooltip historico
```

### Cenario F: Cross-launch

```
Identity do WH0125 visita pagina do WH0325
  ├── FingerprintJS: visitorId match → Identity conhecida
  ├── LaunchParticipant NOVO para WH0325 (status=visitor)
  ├── Se se inscrever: status → lead, tags WH0125 + WH0325
  └── Dashboard: "1,247 leads recorrentes de lancamentos anteriores"
```

### Cenario G: Compra (Stripe webhook)

```
payment_intent.succeeded → Django (via dj-stripe signals)
  ├── Metadata do Stripe: identity_id, fingerprint, turma, seller
  ├── LaunchParticipant: lead → buyer, converted_at = now
  ├── LaunchProductParticipant.create:
  │   product = MDL0325, status = student
  │   tags cascata: ALUNO + ALUNO_WH0325 + ALUNO_MDL0325
  │   turma: da config do produto
  ├── Se comprou bump/upsell:
  │   Outro LaunchProductParticipant com suas tags
  ├── Identity.lifecycle_global: atualiza cache (total_spent, total_purchases)
  └── Via RabbitMQ → N8N:
      ├── Mautic: atualizar tags
      ├── ManyChat: atualizar tags
      ├── Plataforma de ensino: adicionar a turma
      └── Email: boas-vindas
```

---

## 7. Analise do prop4you-inertia (Referencia Arquitetural)

### 7.1 Padrao de Multi-Interface

prop4you usa **settings modules separados** para servir diferentes interfaces do mesmo backend:
- `config.settings.web` (porta 8001) → Inertia (dashboard)
- `config.settings.api` (porta 8002) → REST API
- `config.settings.admin` (porta 8003) → Django admin

Cada settings module ajusta MIDDLEWARE e ROOT_URLCONF. **NAO e multi-frontend** -- e o mesmo backend com rotas diferentes.

### 7.2 Aplicacao ao Launch

Para captura pages em container separado, podemos:
- `config.settings.web` → dashboard do operador
- `config.settings.capture` → paginas de captura (sem auth middleware, sem sidebar)
- Mesmo backend, mesmos models, URLs diferentes

### 7.3 Docker Planejado (prop4you)

```
django-web     (8001) → Dashboard Inertia
django-api     (8002) → REST API
frontend       (3333) → Vite dev
postgres, redis, rabbitmq → infra
celery-worker  → background tasks
```

Escalamento via Docker Swarm: `docker service scale prop4you_django-web=3`

### 7.4 Padroes Reutilizaveis

- **BaseModel com 8 mixins** (mais que o nosso atual de 5)
- **Service layer**: BaseService[T] instance ou classmethod
- **Celery routing**: 6 filas nomeadas com prioridades
- **Middleware chain**: JSON parse → shared data → setup status → delinquent
- **Code splitting**: `import.meta.glob('./pages/**/*.tsx')`

---

## 8. Decisoes Tomadas

### Q33 — Model Contact: ELIMINADO (Opcao A)

**Decisao**: Eliminar Contact completamente. O Identity passa a ser a entidade principal em todo o sistema.

**O que muda:**
- Dashboard lista Identities, nao Contacts
- `notes` do operador vira campo no Identity (`operator_notes: TextField`)
- Tags manuais do operador ficam como M2M no Identity (Tag model ja existe e e reutilizado)
- `custom_fields` (CustomFieldDefinition) sera reavaliado no contexto de Launch (campos customizados por lancamento fazem mais sentido)
- `owner` / `created_by` nao fazem sentido no Identity (Identity e da pessoa, nao do operador)

**Models a ELIMINAR:**
- `Contact` (con_*) — inteiro
- `AdditionalEmail` — redundante com ContactEmail
- `AdditionalPhone` — redundante com ContactPhone
- `ContactNote` — conceito CRM nao solicitado

**Model a MANTER com ajustes:**
- `Tag` — reutilizado para tags manuais no Identity E tags de lancamento
- `CustomFieldDefinition` — movido para escopo de Launch (discutir depois)

**Frontend a REESCREVER:**
- Pages de Contacts (Index, Show, Create, Edit, Delete) serao reescritas como pages de Identity
- Create/Edit muda para "importar cadastro" (email + phone) ou editar dados do Identity
- Index lista Identities com seus canais e participacoes em lancamentos
- Show mostra Identity completo com abas de canais, lancamentos, timeline

### Q39 — Lifecycle Global: JSONB Cache + Expand On Demand

**Decisao**: Sim, `lifecycle_global` como JSONField cache no Identity. Com duas camadas:

**Camada 1 — Cache rapido (JSONB no Identity)**
- Sempre disponivel, atualizado por signals/tasks quando eventos acontecem
- Usado para listagens, cards, filtros, dashboards resumidos
- Nao requer queries adicionais — esta no proprio record do Identity

**Camada 2 — Expand on demand (carregamento sob demanda)**
- Quando o operador clica para expandir/detalhar, o frontend faz request para endpoint dedicado
- Esse endpoint carrega todos os LaunchParticipants da Identity com seus lifecycles completos
- Retorna array de objetos com dados ricos por lancamento
- Usado na pagina de detalhe do Identity (aba "Lancamentos") e em modais de analytics

**Fluxo no frontend:**
```
Identity card no dashboard:
  → lifecycle_global (JSONB) = "3 lancamentos, 2 compras, R$ 5k"
  → rapido, ja vem no props do Inertia

Clicou "Ver detalhes":
  → GET /api/identity/{id}/launches/ (lazy load)
  → retorna: [
      { launch: "WH0125", status: "student", purchased: [...], tags: [...] },
      { launch: "WH0325", status: "lead", enrolled_at: "...", entries: 2 },
    ]
  → renderiza tabela expandida com timeline por lancamento
```

### Q40 — Schema do Lifecycle Global: Completo Para Dashboards

**Decisao**: Tudo que for necessario para gerar dashboards sem queries adicionais. O PostgreSQL com materialized views torna a estrategia ainda mais robusta.

O schema completo do `lifecycle_global` JSONField:

```json
{
  "_version": 1,
  "_updated_at": "2026-02-12T14:30:00Z",

  "timeline": {
    "first_seen": "2025-01-15T10:00:00Z",
    "last_seen": "2026-02-12T14:30:00Z",
    "first_purchase": "2025-03-20T18:45:00Z",
    "last_purchase": "2026-01-10T09:15:00Z",
    "days_since_first_seen": 393,
    "days_since_last_seen": 0,
    "days_since_last_purchase": 33
  },

  "launches": {
    "total_participated": 3,
    "total_as_visitor": 1,
    "total_as_lead": 2,
    "total_as_buyer": 2,
    "total_as_student": 1,
    "total_refunded": 0,
    "total_churned": 0,
    "active": ["WH0325"],
    "history": ["WH0125", "WH0225", "WH0325"],
    "is_recurrent": true,
    "recurrence_rate": 0.66
  },

  "financial": {
    "total_spent": 5000.00,
    "total_refunded": 0.00,
    "net_revenue": 5000.00,
    "average_ticket": 2500.00,
    "ltv_estimated": 12000.00,
    "currency": "BRL",
    "products_purchased": [
      {"tag": "MDL0125", "price": 2000.00, "type": "main"},
      {"tag": "MDL0325_BUMP", "price": 500.00, "type": "bump"},
      {"tag": "MDL0325", "price": 2500.00, "type": "main"}
    ],
    "has_active_subscription": false,
    "is_delinquent": false
  },

  "behavior": {
    "pattern": "late_buyer",
    "avg_days_to_purchase": 8,
    "total_page_views": 47,
    "total_form_submissions": 3,
    "total_entries": 5,
    "preferred_device": "mobile",
    "preferred_time": "evening",
    "engagement_score": 0.82,
    "risk_score": 0.15
  },

  "channels": {
    "emails": {
      "total": 2,
      "verified": 1,
      "primary": "email@example.com"
    },
    "phones": {
      "total": 3,
      "verified": 2,
      "whatsapp": 1,
      "primary": "+5511999999999"
    },
    "fingerprints": {
      "total": 2,
      "devices": ["mobile", "desktop"]
    }
  },

  "tags": {
    "accumulated": ["WH0125", "WH0325", "ALUNO", "ALUNO_WH0125", "MDL0125", "MDL0325"],
    "current_active": ["WH0325", "ALUNO", "ALUNO_WH0125"],
    "manual": ["vip", "influencer"]
  },

  "scores": {
    "confidence": 0.92,
    "engagement": 0.82,
    "risk": 0.15,
    "ltv_tier": "high"
  }
}
```

**Notas sobre o schema:**
- `_version` permite migracao progressiva do formato sem quebrar dados antigos
- `_updated_at` permite saber quao fresco e o cache
- Cada secao (`timeline`, `launches`, `financial`, `behavior`, `channels`, `tags`, `scores`) e um "bloco de dashboard" — pode ser renderizado independentemente
- `financial.products_purchased` e um array que cresce com cada compra — pode ser grande em identities muito ativas, mas JSONB do PostgreSQL lida bem
- `behavior.pattern` e inferido por regras (ex: sempre compra no ultimo dia = "late_buyer")

---

## 9. Estrategia de Dados Para Dashboards

### 9.1 As 3 Camadas de Performance

O sistema usa **3 camadas complementares** para garantir performance em dashboards:

```
CAMADA 1: Identity.lifecycle_global (JSONB inline)
  ├── Velocidade: instantanea (ja esta no record)
  ├── Uso: listagens, cards, filtros, busca
  ├── Atualizacao: signal/task quando evento acontece
  └── Custo: 0 queries adicionais

CAMADA 2: Materialized Views do PostgreSQL
  ├── Velocidade: muito rapida (pre-computada)
  ├── Uso: dashboards agregados, metricas de lancamento, funis
  ├── Atualizacao: REFRESH periodico (Celery beat) ou por evento
  └── Custo: storage do PostgreSQL (gerenciado automaticamente)

CAMADA 3: Expand On Demand (queries sob demanda)
  ├── Velocidade: normal (query real-time)
  ├── Uso: detalhe expandido, historico completo, auditoria
  ├── Atualizacao: sempre fresh (real-time)
  └── Custo: 1+ queries por request
```

### 9.2 Materialized Views Planejadas

```sql
-- Dashboard de lancamento: metricas agregadas por fase
CREATE MATERIALIZED VIEW mv_launch_metrics AS
SELECT
  lp.launch_id,
  l.tag_root,
  l.name,
  COUNT(DISTINCT lp.identity_id) as total_participants,
  COUNT(DISTINCT lp.identity_id) FILTER (WHERE lp.status = 'visitor') as visitors,
  COUNT(DISTINCT lp.identity_id) FILTER (WHERE lp.status = 'lead') as leads,
  COUNT(DISTINCT lp.identity_id) FILTER (WHERE lp.status = 'buyer') as buyers,
  COUNT(DISTINCT lp.identity_id) FILTER (WHERE lp.status = 'student') as students,
  COUNT(DISTINCT lp.identity_id) FILTER (WHERE lp.status = 'refunded') as refunded,
  SUM(lp.total_spent) as revenue,
  AVG(lp.total_spent) FILTER (WHERE lp.total_spent > 0) as avg_ticket,
  -- Funil
  ROUND(COUNT(*) FILTER (WHERE lp.status = 'lead')::numeric /
    NULLIF(COUNT(*) FILTER (WHERE lp.status = 'visitor'), 0) * 100, 2) as visitor_to_lead_rate,
  ROUND(COUNT(*) FILTER (WHERE lp.status = 'buyer')::numeric /
    NULLIF(COUNT(*) FILTER (WHERE lp.status = 'lead'), 0) * 100, 2) as lead_to_buyer_rate
FROM launches_launchparticipant lp
JOIN launches_launch l ON l.id = lp.launch_id
GROUP BY lp.launch_id, l.tag_root, l.name;

-- Dashboard global: metricas de todas as identities
CREATE MATERIALIZED VIEW mv_identity_overview AS
SELECT
  COUNT(*) as total_identities,
  COUNT(*) FILTER (WHERE i.status = 'active') as active_identities,
  COUNT(*) FILTER (WHERE (i.lifecycle_global->>'launches'->>'total_as_buyer')::int > 0) as buyers,
  AVG((i.lifecycle_global->'financial'->>'total_spent')::numeric) as avg_ltv,
  COUNT(*) FILTER (WHERE (i.lifecycle_global->'launches'->>'is_recurrent')::boolean = true) as recurrent,
  -- Por tier
  COUNT(*) FILTER (WHERE i.lifecycle_global->'scores'->>'ltv_tier' = 'high') as tier_high,
  COUNT(*) FILTER (WHERE i.lifecycle_global->'scores'->>'ltv_tier' = 'medium') as tier_medium,
  COUNT(*) FILTER (WHERE i.lifecycle_global->'scores'->>'ltv_tier' = 'low') as tier_low
FROM contacts_identity_identity i
WHERE i.is_deleted = false;

-- Cross-launch: identities que participaram de multiplos lancamentos
CREATE MATERIALIZED VIEW mv_cross_launch_identities AS
SELECT
  lp.identity_id,
  COUNT(DISTINCT lp.launch_id) as launches_count,
  ARRAY_AGG(DISTINCT l.tag_root ORDER BY l.tag_root) as launch_tags,
  SUM(lp.total_spent) as total_cross_launch_spent,
  MIN(lp.enrolled_at) as first_enrollment,
  MAX(lp.enrolled_at) as last_enrollment
FROM launches_launchparticipant lp
JOIN launches_launch l ON l.id = lp.launch_id
GROUP BY lp.identity_id
HAVING COUNT(DISTINCT lp.launch_id) > 1;

-- Timeline de eventos para dashboard de atividade
CREATE MATERIALIZED VIEW mv_daily_activity AS
SELECT
  DATE(fe.timestamp) as day,
  fe.event_type,
  COUNT(*) as event_count,
  COUNT(DISTINCT fi.identity_id) as unique_identities
FROM contacts_fingerprint_fingerprintevent fe
JOIN contacts_fingerprint_fingerprintidentity fi ON fi.id = fe.fingerprint_id
WHERE fe.timestamp >= NOW() - INTERVAL '90 days'
GROUP BY DATE(fe.timestamp), fe.event_type;
```

**Refresh strategy:**
```python
# Celery beat: refresh a cada 5 minutos para views leves, 30 min para pesadas
CELERY_BEAT_SCHEDULE = {
    'refresh-launch-metrics': {
        'task': 'apps.launches.tasks.refresh_launch_metrics',
        'schedule': 300,  # 5 min
    },
    'refresh-identity-overview': {
        'task': 'apps.launches.tasks.refresh_identity_overview',
        'schedule': 1800,  # 30 min
    },
    'refresh-daily-activity': {
        'task': 'apps.launches.tasks.refresh_daily_activity',
        'schedule': 600,  # 10 min
    },
}

# Refresh sob demanda apos eventos criticos (compra, merge, etc)
# Signal: post_purchase → refresh mv_launch_metrics WHERE launch_id = X
# Isso usa REFRESH MATERIALIZED VIEW CONCURRENTLY (nao bloqueia leitura)
```

### 9.3 Indices JSONB Para Performance

```sql
-- GIN index no lifecycle_global para queries em campos especificos
CREATE INDEX idx_identity_lifecycle_global ON contacts_identity_identity
  USING GIN (lifecycle_global jsonb_path_ops);

-- Indices especificos para campos mais consultados em filtros
CREATE INDEX idx_identity_ltv_tier ON contacts_identity_identity
  ((lifecycle_global->'scores'->>'ltv_tier'));

CREATE INDEX idx_identity_total_spent ON contacts_identity_identity
  (((lifecycle_global->'financial'->>'total_spent')::numeric));

CREATE INDEX idx_identity_last_seen ON contacts_identity_identity
  (((lifecycle_global->'timeline'->>'last_seen')::timestamp));
```

---

## 10. Ajustes no Identity Model

### 10.1 Campos a Adicionar

```python
# No Identity model existente:
class Identity(BaseModel):
    # ... campos existentes (status, confidence_score, etc) ...

    # NOVOS campos (pos-decisao Q33):
    display_name = models.CharField(
        max_length=255, blank=True, default="",
        help_text="Nome de exibicao (preenchido na captura ou inferido do email)"
    )
    operator_notes = models.TextField(
        blank=True, default="",
        help_text="Anotacoes livres do operador sobre esta identity"
    )
    tags = models.ManyToManyField(
        "contacts.Tag", blank=True,
        help_text="Tags manuais do operador + tags automaticas de lancamentos"
    )
    lifecycle_global = models.JSONField(
        default=dict, blank=True,
        help_text="Cache JSONB do lifecycle global (atualizado por signals/tasks)"
    )
```

### 10.2 Campos Existentes que Permanecem

O Identity model atual ja tem e mantem:
- `status` (active/merged/inactive) — status da IDENTITY, nao do participante
- `confidence_score` — ConfidenceEngine (ja funciona)
- `master_identity` — para merges (ja funciona)
- `merged_at` — timestamp do merge (ja funciona)
- `metadata` — JSONField generico (ja existe no BaseModel)

### 10.3 Servicos que Permanecem (ja construidos)

Todos os 5 servicos em `contacts/identity/services/` permanecem:
- `IdentityService` — CRUD + timeline + confidence
- `ResolutionService` — pipeline de resolucao (core do sistema)
- `ConfidenceEngine` — scoring unificado
- `AnalysisService` — grafos e similaridade
- `MergeService` — merge workflow com validacao

**Novo servico necessario:**
- `LifecycleService` — gerencia o cache `lifecycle_global`, recalcula quando necessario, expoe endpoint de expand-on-demand

---

## 11. Pergunta Aberta Restante

### Q41 — Ordem de Implementacao

**Proposta (atualizada com as decisoes):**

```
FASE 0: Cleanup (1-2 dias)
  ├── Eliminar models: Contact, AdditionalEmail, AdditionalPhone, ContactNote
  ├── Mover CustomFieldDefinition para escopo futuro (nao implementar agora)
  ├── Adicionar campos no Identity: display_name, operator_notes, tags, lifecycle_global
  ├── Ajustar ContactService para IdentityService (ou eliminar ContactService)
  ├── Reescrever frontend: pages de Contacts → pages de Identity
  ├── Ajustar testes (remover testes de Contact, adaptar para Identity)
  └── Gerar migracoes, rodar testes, garantir build limpo

FASE 1: Identity Standalone (2-3 dias)
  ├── Identity funciona sem nenhuma dependencia de Contact
  ├── Dashboard lista Identities com canais (emails, phones, fingerprints)
  ├── CRUD basico: importar (email+phone), editar display_name/notes/tags
  ├── LifecycleService (gerencia lifecycle_global JSONB)
  ├── Endpoint expand-on-demand (placeholder ate ter LaunchParticipant)
  └── Testes completos

FASE 2: Webhook FingerprintJS + Captura (2-3 dias)
  ├── Endpoint webhook FingerprintJS Pro (recebe visitorId, requestId, geo, device)
  ├── Endpoint formulario de captura (email + phone + hidden fields)
  ├── Integracao com ResolutionService existente
  ├── FingerprintEvent para page_view, form_submit
  ├── Attribution para UTMs
  └── Testes de integracao

FASE 3: Launch Models (3-5 dias)
  ├── App nova: apps/launches/
  ├── Models: Launch (lch_*), LaunchProduct (lpr_*), LaunchPhase (lph_*), LaunchPage (lpg_*)
  ├── LaunchService: CRUD + wizard de setup
  ├── TagService: geracao de tags cascata + sync via RabbitMQ
  ├── Frontend: pages de Launches (Index, Show, Create/Wizard, Edit)
  └── Testes

FASE 4: LaunchParticipant (3-5 dias)
  ├── Models: LaunchParticipant (lpt_*), LaunchProductParticipant (lpp_*)
  ├── ParticipantService: lifecycle management (visitor → lead → buyer → student → ...)
  ├── Integracao com Stripe webhooks (payment → buyer → student)
  ├── Integracao com LifecycleService (atualiza lifecycle_global no Identity)
  ├── Materialized views SQL
  ├── Frontend: dashboard de lancamento com metricas, funil, participantes
  └── Testes

FASE 5: Capture Pages (3-5 dias)
  ├── Settings module separado: config.settings.capture
  ├── URLs/middleware proprios (sem auth, sem sidebar)
  ├── Pages Inertia de captura (formulario email+phone, redirect WhatsApp)
  ├── Integracao FingerprintJS no frontend da captura
  └── Testes end-to-end

FASE 6: Analytics Dashboard (2-3 dias)
  ├── Materialized views rodando em Celery beat
  ├── Dashboard global: total identities, buyers, LTV, recorrentes
  ├── Dashboard por lancamento: funil, metricas, custo por lead
  ├── Dashboard cross-launch: identities recorrentes, comportamento
  └── Testes
```

**Estimativa total: 16-26 dias de desenvolvimento**
**Meta: Q2 2026 (final de junho)**

**Concorda com essa sequencia? Quer ajustar algo?**

---

*Status: Q33, Q39, Q40 RESPONDIDAS. Q41 aguardando confirmacao. Apos Q41, comecamos a implementar.*
*Ultima atualizacao: 2026-02-12*
