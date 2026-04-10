# A relação Session ↔ Fingerprint: o que realmente acontece

> Documento de referência para discussão. Gerado em 2026-02-21.

---

## O ciclo de vida, passo a passo

Imagina um visitante entrando pela primeira vez em qualquer página do site.

### Passo 1 — Django cria a Session e a Identity (backend, síncrono)

Quando o request HTTP chega ao Django, **antes de renderizar qualquer página**, dois middlewares rodam em sequência:

**VisitorMiddleware** (roda primeiro):
- Olha se tem o cookie `fpjs_vid` → na primeira visita, **não tem**. Resultado: `request.visitor_id = ""`, `request.fingerprint_identity = None`.
- Parseia o User-Agent → cria ou encontra um `DeviceProfile` (tabela dimensão, dedup por hash do UA).
- Resolve o IP → geodados via MaxMind (cache Redis 24h).

**IdentitySessionMiddleware** (roda depois):
- Olha na session se já tem `identity_pk` → na primeira visita, **não tem**.
- Olha se tem cookies `_em`/`_ph` (hashes de email/telefone) → na primeira visita, **não tem**.
- **Cria uma Identity anônima**: `Identity.objects.create(confidence_score=0.05, first_seen_source="session", status=ACTIVE)`.
- **Cria um IdentityHistory** registrando essa criação.
- **Grava na session**: `identity_pk`, `identity_id` (public_id), `visitor_status="new"`, `first_seen`.
- **Seta cookies na response**: `_lid={public_id}`, `_vs=new`.

**Nesse ponto**: existe 1 Identity no banco, amarrada à session do Django. Mas **zero fingerprint**. A Identity existe sozinha, sem nenhum `FingerprintIdentity` apontando pra ela.

---

### Passo 2 — Frontend carrega o FingerprintJS (client-side, assíncrono)

A página carrega no browser. O componente `GlobalFingerprintInit` (que roda em **TODAS** as páginas via `AppShell` layout) faz o seguinte:

1. Checa se já existe o cookie `fpjs_vid`. Na primeira visita, **não existe**.
2. Importa dinamicamente o SDK `@fingerprintjs/fingerprintjs-pro`.
3. Chama `fp.get()` → a API do FingerprintJS retorna um `visitorId` (string única do dispositivo).
4. **Seta o cookie `fpjs_vid`** com esse `visitorId` (365 dias).
5. Seta `window.fpResult` e dispara o evento `fingerprint-ready`.
6. **Envia um beacon** (POST assíncrono via `sendBeacon`) para `/api/fp-resolve/` com:
   ```json
   {
     "visitor_id": "abc123...",
     "request_id": "req_xyz...",
     "confidence": 0.9995,
     "capture_token": ""
   }
   ```

**Isso acontece em TODAS as páginas**, não só nas de captura. Qualquer página que o visitante acessa, o `GlobalFingerprintInit` roda.

---

### Passo 3 — Django recebe o beacon e amarra tudo (backend, `fp_resolve`)

O endpoint `/api/fp-resolve/` (`src/apps/landing/views.py:972`) recebe o beacon e faz:

1. **`FingerprintIdentity.objects.get_or_create(hash=visitor_id)`** → cria o registro de fingerprint no banco se é a primeira vez. Se já existe, atualiza `last_seen`.

2. **Lê `request.session["identity_pk"]`** → pega a Identity que o `IdentitySessionMiddleware` criou/recuperou no Passo 1.

3. **Se o `FingerprintIdentity` não tem identity** (é órfão):
   - `fp_identity.identity = session_identity` → **faz o link**.
   - Aumenta o `confidence_score` da Identity em +0.15 (de 0.05 pra 0.20).
   - Resultado: agora a Identity tem um fingerprint apontando pra ela.

4. **Se o `FingerprintIdentity` já tem uma identity diferente** da session:
   - Dispara um merge assíncrono (Celery task) pra unificar as duas identities.
   - Isso acontece quando, por exemplo, o visitante voltou num browser diferente e ganhou uma nova session/identity, mas o fingerprint já conhecia ele por outra identity.

---

### Passo 4 — Próxima visita (request seguinte)

Agora o visitante tem:
- Cookie `sessionid` → Django session com `identity_pk`
- Cookie `fpjs_vid` → visitor ID do FingerprintJS

Quando o próximo request chega:

**VisitorMiddleware**: Lê o cookie `fpjs_vid` → busca no Redis (`visitor:{vid}`) ou no banco → encontra o `FingerprintIdentity` → resolve a `Identity` via FK. Seta `request.identity`, `request.fingerprint_identity`, `request._visitor_mw_identity`.

**IdentitySessionMiddleware**: Lê `identity_pk` da session → recupera a mesma Identity do banco. Compara com o que o VisitorMiddleware achou (`_visitor_mw_identity`):
- Se são a **mesma** Identity → tudo ok, segue.
- Se são **diferentes** → dispara merge assíncrono (linha 215).

**O `GlobalFingerprintInit` no frontend**: Vê que o cookie `fpjs_vid` já existe → **NÃO chama a API do FingerprintJS de novo** (linha 82-99). Popula `window.fpResult` a partir do cookie e retorna. **NÃO envia beacon pro `fp_resolve`**.

---

## Resumo visual da amarração

```
PRIMEIRA VISITA:
                                    
  Request HTTP ──► VisitorMW (sem fpjs_vid = nada)
                 ├► IdentitySessionMW
                 │   └── cria Identity(score=0.05) ──► DB
                 │   └── session["identity_pk"] = pk
                 │   └── cookies: _lid, _vs
                 └► Renderiza página
                 
  Browser carrega ──► GlobalFingerprintInit
                      └── chama FingerprintJS API
                      └── seta cookie fpjs_vid
                      └── beacon POST /api/fp-resolve/
                      
  fp_resolve ──► get_or_create FingerprintIdentity ──► DB
               └── lê session["identity_pk"]
               └── fp_identity.identity = session_identity ──► DB (link!)
               └── score 0.05 → 0.20


VISITA SEGUINTE:

  Request HTTP ──► VisitorMW (lê fpjs_vid → busca FingerprintIdentity → Identity)
                 ├► IdentitySessionMW (lê session → mesma Identity)
                 │   └── compara: visitor MW identity == session identity? ✓
                 └► Renderiza página
                 
  Browser carrega ──► GlobalFingerprintInit
                      └── cookie fpjs_vid existe → NÃO chama API
                      └── NÃO envia beacon
```

---

## O que aparece no Dashboard (Identity Hub)

Quando você olha uma Identity no dashboard:

- **Confidence Score**: 0.05 (session only) → 0.20 (com fingerprint) → maior após conversão
- **First seen source**: "session" 
- **Fingerprints vinculados**: na aba de devices/fingerprints, aparece o `FingerprintIdentity` linkado
- **DeviceProfile**: browser, OS, tipo de device (parseado do User-Agent)
- **Visitor status**: "new" → "returning" → "converted"

---

## Sobre o bug "só disparava em página de inscrição"

Isso **era** verdade antes do fix do `main.tsx` que fizemos nessa sessão. O `GlobalFingerprintInit` existia mas estava fora da árvore do Inertia (era sibling do `<App>`, não filho). Ele crashava com `usePage must be used within the Inertia component` e silenciosamente não funcionava.

O fix que fizemos (mover pro `AppShell` layout via `page.default.layout`) fez ele funcionar **em todas as páginas**. Antes do fix, o fingerprint só era resolvido nas páginas de captura porque lá existe um componente **separado** (`FingerprintProvider`) que faz a mesma coisa mas sem depender do Inertia.

Então o cenário era:
- Páginas de captura: fingerprint funcionava (via `FingerprintProvider` local)
- Todas as outras páginas: fingerprint **não funcionava** (crash silencioso do `GlobalFingerprintInit`)

Agora ambos os caminhos funcionam.

---

## DISCUSSÃO: Perguntas sobre o Passo 1

> Perguntas levantadas em 2026-02-21. Respostas baseadas no código real.

### Pergunta 1 — Como é feita a "amarração" entre session, identity, IP, device e outros?

**Resposta curta: não existe amarração direta no banco entre esses conceitos. Cada um vive isolado.**

Vamos ser precisos sobre o que está no banco:

| Entidade | Tabela | Campos relevantes | FK pra Identity? | FK pra Session? | FK pra DeviceProfile? | Campos de IP/Geo? |
|----------|--------|-------------------|-------------------|------------------|------------------------|---------------------|
| **Identity** | `contact_identity` | status, confidence_score, last_seen, display_name | — (é a raiz) | **NÃO** | **NÃO** | **NÃO** |
| **Session** | `django_session` (padrão Django) | session_key, session_data (blob), expire_date | **NÃO** (guarda identity_pk dentro do blob JSON, mas não é FK) | — | **NÃO** | **NÃO** |
| **DeviceProfile** | `tracking_device_profile` | browser, OS, device_type, profile_hash | **NÃO** | **NÃO** | — | **NÃO** |
| **FingerprintIdentity** | `contact_fingerprint` | hash (visitor_id), confidence_score, ip_address, geo_info | **SIM** (FK) | **NÃO** | **NÃO** | **SIM** (ip_address + geo_info JSON) |
| **CaptureEvent** | `tracking_capture_event` | event_type, page_path, capture_token | **SIM** (FK) | **NÃO** | **SIM** (FK) | **SIM** (ip_address + geo_data JSON) |
| **CaptureSubmission** | `ads_capture_submission` | form data, campaign | **SIM** (FK) | **NÃO** | **SIM** (FK) | **SIM** (ip_address + geo_data JSON) |

**O que isso significa na prática:**

1. **Identity ↔ Session**: A amarração é **só via session data** (blob serializado). O `IdentitySessionMiddleware` grava `identity_pk` dentro do dicionário da session Django. Não existe uma FK real no banco. Se a session expira, o link desaparece.

2. **Identity ↔ DeviceProfile**: **Não existe link direto.** O DeviceProfile só é linkado ao `CaptureEvent`. Pra saber qual device uma Identity usa, você tem que fazer: `Identity → CaptureEvent (FK) → DeviceProfile (FK)`. Não tem como ir direto de Identity pra DeviceProfile.

3. **Identity ↔ IP/Geo**: **Não existe no model Identity.** IP e geodados são gravados em cada `CaptureEvent` e `CaptureSubmission` individualmente. São dados **por evento**, não por identity.

4. **Identity ↔ FingerprintIdentity**: Esse sim é **FK real** no banco. `FingerprintIdentity.identity_id` aponta pra `Identity.pk`.

**Diagrama real das FKs no banco:**

```
Identity (raiz, não aponta pra ninguém)
   ▲ FK            ▲ FK              ▲ FK
   │               │                 │
FingerprintIdentity  ContactEmail  ContactPhone
                     
   ▲ FK  ▲ FK  ▲ FK
   │     │     │
CaptureEvent ──► DeviceProfile (FK)
                 (tabela dimensão, sem FK pra Identity)
```

**Consequência prática**: A Identity é uma entidade "pura" — só tem score, status, display_name. Toda informação contextual (device, IP, geo, UTM) vive nos **eventos** associados a ela, não nela mesma.

---

### Pergunta 2 — A session não é persistente. Como é feita a renovação e amarração entre sessões?

**Resposta: a session É persistente no banco, mas tem prazo de expiração.**

O Django usa `SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"`. Isso significa:
- A session é gravada na tabela `django_session` no PostgreSQL
- Uma cópia é mantida no Redis (cache) pra leitura rápida
- A session tem um `expire_date`

**Prazos de expiração** (definidos no `IdentitySessionMiddleware`):
- Visitante anônimo (só session): **90 dias**
- Visitante com fingerprint: **180 dias**
- Visitante convertido (tem email/phone): **365 dias**

**O que acontece quando a session expira:**

1. O cookie `sessionid` no browser expira ou o Django limpa sessions expiradas
2. Na próxima visita, o Django cria uma **session nova e vazia**
3. O `IdentitySessionMiddleware` não acha `identity_pk` na session nova
4. **Mecanismo de recuperação por cookies `_em`/`_ph`**:
   - Se o visitante já converteu antes, tem cookies `_em` (SHA-256 do email) e `_ph` (SHA-256 do telefone) — esses cookies duram **365 dias**
   - O middleware busca: `ContactEmail.filter(value_sha256=em_hash)` → encontra a Identity anterior
   - Regrava `identity_pk` na session nova → **reconectou**
5. **Se NÃO tem cookies `_em`/`_ph`** (nunca converteu):
   - Cria uma **Identity nova** (anônima, score 0.05)
   - A Identity antiga fica órfã no banco
   - **MAS**: quando o `VisitorMiddleware` lê o cookie `fpjs_vid` (que dura 365 dias), ele encontra o `FingerprintIdentity` que aponta pra Identity antiga
   - O `IdentitySessionMiddleware` detecta divergência (session identity ≠ fingerprint identity) → **dispara merge**
   - Resultado: as duas Identities são unificadas

**Resumo dos 3 mecanismos de recuperação entre sessions:**

| Mecanismo | Cookie | Duração | O que recupera | Funciona pra anônimos? |
|-----------|--------|---------|----------------|------------------------|
| Session direta | `sessionid` | 90-365 dias | Identity via `identity_pk` no blob | Sim |
| Hash de PII | `_em` / `_ph` | 365 dias | Identity via `ContactEmail.value_sha256` | **Não** (só pós-conversão) |
| Fingerprint | `fpjs_vid` | 365 dias | Identity via `FingerprintIdentity.identity` FK | Sim (se o fingerprint já foi linkado) |

**Lacuna**: Se um visitante anônimo perde a session E não tem fingerprint (ex: bloqueou JS, ou veio antes do fix do `GlobalFingerprintInit`), ele vira uma Identity nova. A antiga fica órfã. Não tem como reconectar.

---

### Pergunta 3 — A associação entre session e identity é sync ou async?

**Resposta: 100% síncrona.**

O `IdentitySessionMiddleware` roda dentro do ciclo de request-response do Django, **antes** de renderizar a página. Ele:

1. `Identity.objects.create(...)` → INSERT síncrono no PostgreSQL
2. `IdentityHistory.objects.create(...)` → INSERT síncrono no PostgreSQL
3. `session["identity_pk"] = identity.pk` → grava na session (cached_db: Redis + PostgreSQL)

Tudo isso acontece **antes** da response ser enviada pro browser. O visitante nunca vê a página sem ter uma Identity no banco.

A **única parte async** nesse passo é quando existe divergência entre a identity da session e a identity do fingerprint — nesse caso, o merge é despachado via `merge_identities_from_fingerprint.delay()` (Celery task). Mas a criação e associação da Identity à session é sempre síncrona.

---

### Pergunta 4 — Geodados não são persistentes? Só sobrevivem no Redis? Existe duplicidade?

**Resposta: depende de qual geodado você está falando. Existem 3 locais com geo, e sim, tem duplicidade.**

#### Local 1: Redis (efêmero, cache do middleware)
- **Chave**: `geo:{ip}` 
- **TTL**: 24 horas
- **Conteúdo**: `{city, country, country_name, region, latitude, longitude, timezone, asn, isp}`
- **Quem grava**: `VisitorMiddleware._resolve_geo()` — chama MaxMind GeoLite2, cacheia o resultado
- **Quem lê**: o mesmo middleware no próximo request do mesmo IP
- **Persiste no banco?** **NÃO.** Esses dados vivem só no Redis e no `request.geo_data` (atributo do request, morre quando o request termina).
- **São gravados em algum lugar permanente?** SÓ se um `CaptureEvent` for criado nesse request (via `TrackingService.create_event()`). Se o visitante só navega sem gerar evento, **o geodado se perde quando o cache Redis expira.**

#### Local 2: CaptureEvent.geo_data (persistente, por evento)
- **Tabela**: `tracking_capture_event`
- **Campo**: `geo_data` (JSONField) + `ip_address` (GenericIPAddressField)
- **Quem grava**: `TrackingService.create_event()` — copia `request.geo_data` e `request.client_ip` pro evento
- **Quando é gravado**: quando acontece um page_view, form_attempt, form_success, etc
- **Cada evento tem sua cópia completa** dos geodados. Se o visitante gera 5 eventos, são 5 JSONs com geo.

#### Local 3: FingerprintIdentity.geo_info (persistente, por fingerprint)
- **Tabela**: `contact_fingerprint`
- **Campo**: `geo_info` (JSONField) + `ip_address` (GenericIPAddressField)
- **Quem grava**: o SDK do FingerprintJS Pro envia localização (client-side), que é gravada quando o `FingerprintIdentity` é criado ou atualizado
- **Diferente do Local 2**: esse vem do **lado do cliente** (FingerprintJS), não do MaxMind server-side

#### Local 4: CaptureSubmission.geo_data (persistente, por submissão de form)
- **Tabela**: `ads_capture_submission`
- **Campo**: `geo_data` (JSONField) + `ip_address` (GenericIPAddressField)
- **Quem grava**: `CaptureService.process_lead()` — copia `request.geo_data` pra submission

**Duplicidade: SIM, existe.**

| Dado | CaptureEvent | CaptureSubmission | FingerprintIdentity | Redis |
|------|:------------:|:-----------------:|:-------------------:|:-----:|
| IP | ✓ | ✓ | ✓ | (efêmero) |
| País | ✓ (geo_data) | ✓ (geo_data) | ✓ (geo_info) | (efêmero) |
| Cidade | ✓ (geo_data) | ✓ (geo_data) | ✓ (geo_info) | (efêmero) |
| Lat/Long | ✓ (geo_data) | ✓ (geo_data) | ✓ (geo_info) | (efêmero) |
| ASN/ISP | ✓ (geo_data) | ✓ (geo_data) | ✗ | (efêmero) |

O mesmo IP e geodados são copiados em **cada evento** e **cada submission** individualmente. Não existe uma tabela `GeoLocation` normalizada (como existe pro `DeviceProfile`).

**O que NÃO tem geo**: A tabela `Identity` **não guarda geo nenhum**. Pra saber de onde uma identity vem, você precisa consultar os eventos ou submissions dela.

**A navegação pura (sem eventos) não persiste geo.** Se o visitante abre a homepage e não gera nenhum `CaptureEvent`, os geodados dele existem só no Redis por 24h e depois somem.

---

## PROBLEMAS IDENTIFICADOS NO MODELO ATUAL (análise honesta)

> Análise de 2026-02-21. Baseada no código real.

### Problema 1: Identity é uma ilha — não sabe nada sobre quem ela é

A `Identity` hoje tem esses campos úteis: `status`, `confidence_score`, `display_name`, `last_seen`, `first_seen_source`. Só isso. Não tem:
- **Nenhum FK pra Session** → a session guarda `identity_pk` num blob, mas a Identity não sabe em qual session está
- **Nenhum FK pra DeviceProfile** → pra saber o device, precisa fazer `Identity → CaptureEvent → DeviceProfile` (join de 3 tabelas)
- **Nenhum campo de IP** → vive só no CaptureEvent e CaptureSubmission
- **Nenhum campo de Geo** → mesmo problema, vive só nos eventos

**Consequência**: no dashboard, pra mostrar "de onde veio essa identity", precisa fazer queries complexas cruzando CaptureEvent. E se a identity nunca gerou um CaptureEvent (ex: só navegou), **não existe nenhuma informação de device/geo/IP persistida pra ela**.

### Problema 2: Geodados duplicados em 3+ lugares, sem normalização

| Local | Campo | Formato | Fonte |
|-------|-------|---------|-------|
| `CaptureEvent.geo_data` | JSONField | `{city, country, lat, long, asn, isp}` | MaxMind (server-side) |
| `CaptureSubmission.geo_data` | JSONField | `{city, region, country, lat, lng, asn, isp}` | MaxMind (server-side) |
| `FingerprintIdentity.geo_info` | JSONField | `{country, city, timezone, coordinates, accuracy}` | FingerprintJS (client-side) |
| Redis `geo:{ip}` | Cache | `{city, country, country_name, region, lat, lng, timezone, asn, isp}` | MaxMind (efêmero, 24h) |

Os nomes dos campos dentro do JSON nem são iguais (`lat/long` vs `lat/lng` vs `coordinates`). Não tem tabela `GeoLocation` normalizada como existe pro `DeviceProfile`.

### Problema 3: DeviceProfile é normalizado mas não pertence a ninguém

O `DeviceProfile` foi bem feito como tabela dimensão (star schema, dedup por hash). MAS ele só é referenciado por:
- `CaptureEvent.device_profile` (FK)
- `CaptureSubmission.device_profile` (FK)

**Não tem FK de Identity → DeviceProfile.** Não tem como ir direto de uma Identity pros seus devices.

### Problema 4: Session não é uma entidade — é um blob opaco

O Django usa `django.contrib.sessions.backends.cached_db`. A tabela `django_session` tem:
- `session_key` (string)
- `session_data` (blob serializado com pickle/JSON)
- `expire_date`

O `identity_pk` está **dentro do blob**, não como FK real. Não dá pra fazer `SELECT * FROM django_session WHERE identity_pk = 123` sem deserializar cada session.

### Problema 5: Navegação sem evento não persiste nada

Se o visitante entra na homepage e navega por 5 páginas sem submeter nenhum form, sem clicar em nenhum CTA, os únicos dados persistentes são:
- `Identity` (anônima, score 0.05)
- `IdentityHistory` (1 row de criação)
- `session["last_page"]` (dentro do blob)

**IP, geo, device** — tudo vive só no request e no Redis cache. Quando a session expira e o cache Redis expira, **essas informações se perdem pra sempre**.

---

## PROPOSTA DE REDESIGN v3: Arquitetura de Apps Vivos

> Status: EM DISCUSSÃO — revisão 2026-02-21.
> v3: Corrige erro conceitual das v1/v2. Backend recupera dados via FPJS Pro Server API.

### Erro das propostas anteriores (v1 e v2)

As v1 e v2 tentavam resolver o problema no lugar errado:
- v1: propunha normalizar sem entender o fluxo
- v2: propunha engordar o beacon do frontend com dados ricos

**Ambas erraram.** O frontend NÃO deve ser onerado com payload rico. A função dele é UMA: **gerar o `visitor_id` o mais rápido possível e enviar pro backend com o mínimo de dados**. O connect rate (% de visitantes que completam o fingerprint) precisa ser o mais próximo de 100% — qualquer ms a mais no frontend é risco.

### O que aprendemos com o legado (revisado)

O legado acertou nos princípios mas usava webhook server-to-server (FingerprintJS Pro Cloud → Django). Nós não temos webhook, mas temos algo equivalente: **a Server API do FPJS Pro**.

| Capacidade | Legado | Nós (v3) |
|------------|--------|----------|
| Receber dados ricos do FP | Webhook (push) | `GET /visitors/{visitor_id}` (pull, async) |
| Enviar metadata pro FP | Não tinha | `PUT /events/{request_id}` — envia `tag` e `linkedId` |
| Trigger | Automático (webhook) | Backend dispara Celery task após `fp_resolve` |

**A Server API retorna POR VISITA (cada `request_id`):**
```json
{
  "requestId": "1655373953086.DDlfmP",
  "browserDetails": {
    "browserName": "Chrome", "browserMajorVersion": "102",
    "browserFullVersion": "102.0.5005", "os": "Mac OS X",
    "osVersion": "10.15.7", "device": "Other",
    "userAgent": "Mozilla/5.0 ..."
  },
  "incognito": false,
  "ip": "82.118.30.68",
  "ipLocation": {
    "accuracyRadius": 1000,
    "latitude": 50.0805, "longitude": 14.467,
    "postalCode": "130 00", "timezone": "Europe/Prague",
    "city": { "name": "Prague" },
    "country": { "code": "CZ", "name": "Czechia" },
    "continent": { "code": "EU", "name": "Europe" },
    "subdivisions": [{ "isoCode": "10", "name": "Hlavni mesto Praha" }]
  },
  "confidence": { "score": 1 },
  "visitorFound": true,
  "firstSeenAt": { "global": "2022-02-04T11:31:20Z" },
  "lastSeenAt": { "global": "2022-06-16T10:03:00.912Z" },
  "url": "https://dashboard.fingerprint.com/",
  "tag": {},
  "time": "2022-06-16T10:05:53Z"
}
```

**E via `PUT /events/{request_id}` podemos ENVIAR pro FPJS:**
```json
{
  "linkedId": "idt_xk7Yz2mN9p",  // nosso identity public_id
  "tag": {
    "identity_id": "idt_xk7Yz2mN9p",
    "session_id": "vss_abc123",
    "converted": true,
    "email_hash": "sha256...",
    "source": "landing_lista_espera"
  }
}
```

**Isso cria um cross de dados bidirecional**: nós temos os dados do FPJS, e o FPJS tem os nossos dados. Dois sistemas que se complementam.

### Filosofia v3: Apps que se intercomunicam

> **Cada entidade é um app vivo que cresce em complexidade própria. Apps se comunicam via FK ou public_id. Dados NUNCA se duplicam — marcam-se RELAÇÕES e datas.**

| App | Responsabilidade | Cresce em... |
|-----|------------------|-------------|
| **Identity** | Centro gravitacional. Tudo converge aqui. | Score, status, merge, graph |
| **Fingerprint** | Dispositivo + browser + dados do FPJS cloud | Visitas, device evolution, cross-device |
| **Email** | Canal email do lead | Bounce, deliverability, warmup, verificação |
| **Phone** | Canal telefone/WhatsApp | Carrier, WhatsApp check, validação, tipo linha |
| **Session** | Verdade do backend Django | Páginas, duração, UTM, conversão |
| **GeoLocation** | Tabela dimensão normalizada | Precisão, fonte, timezone analytics |
| **DeviceProfile** | Tabela dimensão normalizada | Browser family, capabilities |
| **Page** | Página como entidade (não string) | Views, conversão rate, heatmap, A/B test |

**Exemplo do ponto de "não duplicar, marcar relações":**

Em vez de criar um `CaptureEvent` com IP, geo, device copiados TODA VEZ que o visitor_id X acessa a página Y:

```
ERRADO (duplicação):
  CaptureEvent(visitor=X, page="/lista-espera", ip="1.2.3.4", geo={...}, device={...})
  CaptureEvent(visitor=X, page="/lista-espera", ip="1.2.3.4", geo={...}, device={...})
  CaptureEvent(visitor=X, page="/lista-espera", ip="1.2.3.4", geo={...}, device={...})
  → 3 rows com dados repetidos

CERTO (relação + incremento):
  PageVisit(session=S, page=P, identity=I)  ← primeiro acesso
  PageVisit atualiza: visit_count=F('visit_count')+1, last_visited_at=now()  ← acessos seguintes
  → 1 row, dados de IP/geo/device via FK da Session, não copiados
```

### O fluxo completo (v3)

```
═══════════════════════════════════════════════════════════════════════
 FASE 1: PRIMEIRO REQUEST (sync, middleware, ~5ms)
═══════════════════════════════════════════════════════════════════════

  Browser → Request HTTP (sem cookies)
  
  VisitorMiddleware (sync, rápido):
    1. Parseia User-Agent → get_or_create DeviceProfile (dedup por hash)
    2. Resolve IP → get_or_create GeoLocation via MaxMind (cache Redis 24h)
    3. Seta request.device_profile, request.geo_location, request.client_ip

  IdentitySessionMiddleware (sync, rápido):
    1. Sem identity_pk na session → cria Identity(confidence=0.05)
    2. get_or_create VisitorSession(session_key, identity)
       → preenche: device_profile, first_geo, first_ip, first_page, utm, referrer
    3. Identity.last_session = visitor_session
    4. Identity.last_device_profile = device_profile
    5. Identity.last_geo = geo_location
    6. Grava identity_pk + visitor_session_pk na session
    7. Seta cookies: _lid (identity public_id), _vs (status)

  Response → Renderiza página
  → Cookies: sessionid, _lid, _vs

═══════════════════════════════════════════════════════════════════════
 FASE 2: FINGERPRINT (async no browser, ~200ms após page load)
═══════════════════════════════════════════════════════════════════════

  GlobalFingerprintInit (frontend):
    1. Sem cookie fpjs_vid → chama fp.get()
    2. Recebe visitorId, requestId, confidence
    3. Seta cookie fpjs_vid (365 dias)
    4. sendBeacon('/api/fp-resolve/', {
         visitor_id,       // o ID único — é tudo que o backend precisa
         request_id,       // pra buscar dados completos via Server API
         confidence_score,  // score do momento
         capture_token      // pra retroactive update se tiver
       })
    → Beacon MINIMALISTA. Frontend leve. Connect rate alto.

═══════════════════════════════════════════════════════════════════════
 FASE 3: fp_resolve (sync no backend, ~10ms)
═══════════════════════════════════════════════════════════════════════

  Endpoint /api/fp-resolve/ recebe o beacon:
    1. get_or_create FingerprintIdentity(hash=visitor_id)
       → Se novo: confidence_score, metadata={request_id, source}
    2. Lê identity_pk da session → linka FP.identity = session_identity
    3. Atualiza VisitorSession.fingerprint = fp_identity
    4. Se é o primeiro FP da Identity → Identity.primary_fingerprint = fp
    5. Confidence: identity.confidence_score += 0.15
    6. ★ DISPARA CELERY TASK: enrich_fingerprint.delay(fp_identity.pk, request_id)
    7. Retorna {status: "ok"} imediatamente

═══════════════════════════════════════════════════════════════════════
 FASE 4: ENRIQUECIMENTO (async, Celery, ~500ms-2s)
═══════════════════════════════════════════════════════════════════════

  Task enrich_fingerprint(fp_pk, request_id):
  
    4a. PULL: GET api.fpjs.io/visitors/{visitor_id}?request_id={request_id}
        → Recebe payload COMPLETO: browserDetails, ip, ipLocation, incognito, etc.
    
    4b. PARSE + MERGE (como payload_service do legado):
        → Extrai device_info, browser_info, geo_info
        → fp_identity.update_from_payload(parsed_data)
          - dict.update() nos JSONs (merge shallow, complementa)
          - max() no confidence_score (nunca diminui)
          - first-write-wins pra browser, os, ip_address
    
    4c. NORMALIZA GEO:
        → get_or_create GeoLocation do ipLocation do FPJS
          (mais preciso que MaxMind — tem accuracyRadius, subdivisions)
        → Atualiza Identity.last_geo_location se FPJS geo é melhor
    
    4d. PUSH: PUT api.fpjs.io/events/{request_id}
        → Envia pro FPJS cloud:
          {
            "linkedId": identity.public_id,
            "tag": {
              "identity_id": identity.public_id,
              "session_id": visitor_session.public_id,
              "source": "landing",
              "first_page": visitor_session.first_page
            }
          }
        → Agora o FPJS cloud SABE quem é esse visitor no nosso sistema.
        → Consultável via FPJS dashboard ou API por linkedId.
    
    4e. REGISTRA: FingerprintEnrichment(fp_identity, request_id, raw_response)
        → Guarda o response da API pra auditoria/debug
        → Não duplica dados — é log do enriquecimento, não cópia

═══════════════════════════════════════════════════════════════════════
 FASE 5: REQUESTS SEGUINTES (sync, middleware, ~3ms)
═══════════════════════════════════════════════════════════════════════

  Browser → Request HTTP (com sessionid + fpjs_vid)
  
  VisitorMiddleware:
    → Lê fpjs_vid → busca FingerprintIdentity (cache Redis) → resolve Identity
    → Resolve DeviceProfile, GeoLocation (do request atual)
  
  IdentitySessionMiddleware:
    → Lê identity_pk da session → compara com fingerprint identity
    → Se iguais: atualiza VisitorSession (pages_viewed++, last_page, last_activity)
    → Se diferentes: merge async
    → Atualiza Identity.last_* se mudaram (device, geo, ip)
  
  GlobalFingerprintInit (frontend):
    → Cookie fpjs_vid existe → NÃO chama SDK → NÃO envia beacon
    → Zero overhead no frontend nas visitas seguintes

═══════════════════════════════════════════════════════════════════════
 FASE 6: CONVERSÃO (form submit)
═══════════════════════════════════════════════════════════════════════

  CaptureSubmission criado com FKs (não cópias):
    → identity (FK), device_profile (FK), geo_location (FK), fp_identity (FK)
    → ZERO campos geo_data JSON duplicados
  
  ContactEmail/ContactPhone criados → FK pra Identity
  
  ★ DISPARA CELERY TASK: post_conversion_enrich.delay(identity.pk)
    → PUT pro FPJS cloud com tag atualizada:
      { "linkedId": identity.public_id, "tag": { "converted": true, "email_hash": "sha256..." } }
    → FPJS cloud agora sabe que esse visitor converteu
    → Nosso sistema sabe tudo via FKs, FPJS sabe via tags
```

### Modelos revisados (v3)

#### Nova tabela: `GeoLocation` (tabela dimensão)

```python
class GeoLocation(BaseModel):
    """Localização geográfica normalizada. Dedup por hash como DeviceProfile."""
    PUBLIC_ID_PREFIX = "geo"
    
    location_hash = CharField(max_length=64, unique=True)  # hash(country_code+region+city)
    country_code = CharField(max_length=2)     # ISO 3166-1 alpha-2
    country_name = CharField(max_length=100)
    region = CharField(max_length=100, blank=True)
    city = CharField(max_length=100, blank=True)
    latitude = DecimalField(max_digits=9, decimal_places=6, null=True)
    longitude = DecimalField(max_digits=9, decimal_places=6, null=True)
    timezone = CharField(max_length=50, blank=True)
```

Não tem `source` nem `asn`/`isp`. Esses dados vivem onde fazem sentido:
- `FingerprintIdentity.geo_info` (JSON do FPJS, com `accuracyRadius`)
- Futuro: tabela `IPAddress` como entidade própria (app IP, com ASN, ISP, etc.)

#### Nova tabela: `VisitorSession` (sessão como entidade)

```python
class VisitorSession(BaseModel):
    """Sessão real do visitante. Complementa (não substitui) django_session."""
    PUBLIC_ID_PREFIX = "vss"
    
    identity = ForeignKey(Identity, NOT_NULL, related_name="sessions")
    session_key = CharField(max_length=40)  # link pro django_session
    device_profile = ForeignKey(DeviceProfile, SET_NULL, null=True)
    fingerprint = ForeignKey(FingerprintIdentity, SET_NULL, null=True)
    first_geo = ForeignKey(GeoLocation, SET_NULL, null=True)
    first_ip = GenericIPAddressField(null=True)
    first_page = CharField(max_length=500)
    last_page = CharField(max_length=500)
    pages_viewed = PositiveIntegerField(default=1)
    started_at = DateTimeField(auto_now_add=True)
    last_activity_at = DateTimeField(auto_now=True)
    status = CharField(max_length=20)  # active/expired/converted
    utm_data = JSONField(default=dict, blank=True)
    referrer = URLField(blank=True)
```

#### Identity ganha contexto direto

```python
# Campos adicionais na Identity existente:
primary_fingerprint = ForeignKey(FingerprintIdentity, SET_NULL, null=True, related_name="+")
last_device_profile = ForeignKey(DeviceProfile, SET_NULL, null=True, related_name="+")
last_geo_location = ForeignKey(GeoLocation, SET_NULL, null=True, related_name="+")
last_ip_address = GenericIPAddressField(null=True)
last_session = ForeignKey(VisitorSession, SET_NULL, null=True, related_name="+")
total_sessions = PositiveIntegerField(default=0)
total_page_views = PositiveIntegerField(default=0)
```

#### CaptureEvent/CaptureSubmission: FK pra GeoLocation, sem geo_data JSON

```python
# Substituições nos modelos existentes:
# REMOVE: geo_data = JSONField(...)
# ADD:
geo_location = ForeignKey(GeoLocation, SET_NULL, null=True)
# KEEP: ip_address (IP específico do evento, diferente do geo que é cidade)
```

#### FingerprintIdentity: mantém JSONs mas com merge inteligente

Os campos `device_info`, `browser_info`, `geo_info` continuam como JSONField no `FingerprintIdentity`. Eles são o **espelho local** do que o FPJS Pro cloud tem. O `update_from_payload()` usa merge do legado (`dict.update()` + `max(confidence)`).

A diferença é que esses JSONs são preenchidos via **Celery task que chama a Server API**, não via beacon do frontend.

#### Nova tabela: `FingerprintEnrichment` (log de enriquecimento)

```python
class FingerprintEnrichment(BaseModel):
    """Log de cada chamada à FPJS Pro Server API. Auditoria, não duplicação."""
    PUBLIC_ID_PREFIX = "fpe"
    
    fingerprint = ForeignKey(FingerprintIdentity, CASCADE, related_name="enrichments")
    request_id = CharField(max_length=100)
    api_response = JSONField()  # response crua da API (pra debug/auditoria)
    enriched_at = DateTimeField(auto_now_add=True)
    metadata_sent = JSONField(default=dict)  # o que enviamos via PUT /events/
```

### Diagrama v3: Apps que se intercomunicam

```
                           ┌──────────────────────────┐
                           │    FPJS Pro Cloud         │
                           │  (fonte externa, via API) │
                           │                           │
                           │  GET /visitors/{vid}      │◄── pull (Celery)
                           │  PUT /events/{rid}        │◄── push (Celery)
                           └────────────┬─────────────┘
                                        │ Server API
                                        ▼
                        ┌───── FingerprintIdentity ─────┐
                        │  hash (visitor_id)             │
                        │  device_info, browser_info,    │
                        │  geo_info (JSONs do FPJS)      │
                        │  confidence_score              │
                        │  ← FingerprintEnrichment (log) │
                        │  ← FingerprintEvent (timeline) │
                        │  ← FingerprintContact (M2M)    │
                        └───────────┬───────────────────┘
                                    │ FK
                                    ▼
    ┌─────────────── Identity (centro gravitacional) ─────────────────┐
    │  primary_fingerprint → FP    last_device → DeviceProfile        │
    │  last_geo → GeoLocation      last_session → VisitorSession      │
    │  last_ip, total_sessions, total_page_views                      │
    │  confidence_score, status, display_name                         │
    └──┬──────────┬──────────┬──────────┬──────────┬────────────────┘
       │          │          │          │          │
       ▼ FK       ▼ FK       ▼ FK       ▼ FK       ▼ FK
  VisitorSession  ContactEmail ContactPhone CaptureSubmission Attribution
  ├ device→DP    (app Email)  (app Phone)  ├ geo→GeoLoc
  ├ fp→FP        bounce?      whatsapp?    ├ device→DP
  ├ geo→GeoLoc   verified?    carrier?     └ fp→FP
  ├ utm, pages   domain?      line_type?
  └ referrer


  Tabelas dimensão (dedup por hash, ~centenas/milhares de rows):
  ┌─────────────┐  ┌──────────────┐
  │ DeviceProfile│  │ GeoLocation  │
  │ (UA hash)    │  │ (geo hash)   │
  │ browser, OS  │  │ country,city │
  │ device_type  │  │ lat, lng, tz │
  └─────────────┘  └──────────────┘

  Futuro (apps que vão nascer):
  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐
  │ Page (app)   │  │ IPAddress    │  │ Campaign     │
  │ path, title  │  │ (app)        │  │ (app)        │
  │ conv_rate    │  │ asn, isp     │  │ utm, source  │
  │ total_views  │  │ vpn?, proxy? │  │ budget, ROI  │
  └─────────────┘  └──────────────┘  └──────────────┘
```

### As duas verdades que se cruzam

```
SESSION (verdade do Django/backend):
  ├── Criada no primeiro request (middleware sync)
  ├── Disponível IMEDIATAMENTE (cookie sessionid)
  ├── Sabe: Identity, DeviceProfile, GeoLocation, páginas, UTM
  ├── Cresce a cada request (pages_viewed++, last_page, last_activity)
  └── Persiste: 90-365 dias dependendo do status

VISITOR_ID (verdade do FPJS/frontend):
  ├── Criado na primeira vez que o SDK roda (~200ms após page load)
  ├── Disponível via cookie fpjs_vid (365 dias)
  ├── Sabe: device fingerprint único cross-session
  ├── Enriquecido via Server API (browser, geo, IP completos)
  └── Bidirecional: nós enviamos metadata, FPJS retorna dados

CRUZAMENTO (onde se encontram):
  ├── fp_resolve: beacon envia visitor_id, backend lê session → LINK
  ├── VisitorSession.fingerprint FK → FingerprintIdentity
  ├── Identity.primary_fingerprint FK → FingerprintIdentity
  ├── Celery: enrich_fingerprint → pull FPJS API → enriquece FP local
  ├── Celery: post_conversion_enrich → push metadata pro FPJS cloud
  └── Resultado: 3 dados no primeiro beacon (session + identity + fpjs)
       que se retroalimentam e crescem em informação
```

### Comparação v1 → v2 → v3

| Aspecto | v1 | v2 | v3 |
|---------|----|----|-----|
| Beacon frontend | Não mencionava | Engordar com payload rico | **MÍNIMO** (visitor_id + request_id) |
| Dados ricos do FPJS | Não mencionava | Frontend envia | **Backend recupera via Server API (async)** |
| Metadata pro FPJS | Não existia | Não existia | **PUT /events/ com identity, session, conversão** |
| Entidades como apps | Modelos estáticos | Modelos estáticos | **Apps vivos que crescem em complexidade** |
| Duplicação de dados | Normaliza geo | Normaliza geo | **Zero duplicação — FKs e contadores, não cópias** |
| Page como entidade | Não existia | Não existia | **Futuro: app Page com vida própria** |
| Enriquecimento | Sync no fp_resolve | Sync no fp_resolve | **Async Celery task (não bloqueia response)** |
| Frontend overhead | Não mencionava | Maior (payload rico) | **Zero — beacon mínimo, SDK roda 1x** |
| Backend overhead | Middleware pesado | Middleware pesado | **Middleware leve (sync) + Celery (async)** |

### O que NÃO fazemos (e por quê)

| Decisão | Por quê |
|---------|---------|
| NÃO engordamos o beacon | Frontend = velocidade. Connect rate > 99% é prioridade. |
| NÃO copiamos geo/device em cada evento | FK pro GeoLocation/DeviceProfile. Uma row, N referências. |
| NÃO fazemos enriquecimento sync | Celery task. Response do fp_resolve em <10ms. |
| NÃO duplicamos dados que o FPJS tem | Guardamos JSONs no FP local como espelho, enriquecemos via API. |
| NÃO criamos tabela Page agora | Vai nascer quando precisar. A arquitetura permite. |
| NÃO implementamos fraud detection agora | Pode ser adicionado como feature do app Fingerprint depois. |

### Resumo em uma frase

> **Frontend gera o visitor_id em <200ms e sai do caminho. Backend faz TUDO: cruza session + identity + fingerprint no sync, enriquece via FPJS Pro API no async, e manda nossos dados de volta pro FPJS cloud. Cada entidade é um app vivo que cresce. Dados nunca se duplicam — marcam-se relações.**

Isso é **zero custo**: os dados já estão na memória do browser, só precisam ir no JSON do beacon.

### Mudança 1: `fp_resolve` extrai e persiste dados ricos (backend)

O endpoint `fp_resolve` passa a:
1. Parsear o payload rico do beacon (como o `payload_service.py` do legado fazia)
2. Chamar `FingerprintIdentity.update_from_payload()` com merge inteligente (como o legado)
3. Criar/atualizar `GeoLocation` normalizada a partir do `ip_location`
4. Atualizar `Identity.last_*` com os dados enriquecidos

### Mudança 2: Nova tabela `GeoLocation` (tabela dimensão normalizada)

```
GeoLocation (tabela dimensão, dedup por hash como DeviceProfile)
├── location_hash     CharField unique (hash de country+region+city, pra dedup)
├── country_code      CharField(2) — ISO 3166-1 alpha-2
├── country_name      CharField
├── region            CharField (blank)
├── city              CharField (blank)
├── latitude          DecimalField(9,6) (nullable)
├── longitude         DecimalField(9,6) (nullable)
├── timezone          CharField (blank)
├── source            CharField — "fingerprintjs" | "maxmind" (de onde veio o dado)
└── (herda BaseModel: public_id, timestamps)
```

**Dedup**: `get_or_create(location_hash=hash(country+region+city))`. São Paulo sempre aponta pro mesmo row.

**Dois fontes de geo**:
- `source="fingerprintjs"` — do `ip_location` do SDK (vem no beacon, uma vez)
- `source="maxmind"` — do MaxMind server-side (vem em cada request via middleware)

Ambos resolvem pro mesmo `GeoLocation` row quando são a mesma cidade. O `source` registra qual deu mais dados (FingerprintJS tem `accuracyRadius`, MaxMind tem `asn`/`isp`).

### Mudança 3: Nova tabela `VisitorSession` (sessão como entidade real)

```
VisitorSession (modelo gerenciado, complementa django_session)
├── identity          FK → Identity (NOT NULL)
├── session_key       CharField (link pro django_session.session_key)
├── device_profile    FK → DeviceProfile (nullable)
├── fingerprint       FK → FingerprintIdentity (nullable, preenchido no fp_resolve)
├── first_geo         FK → GeoLocation (nullable, geo do primeiro request)
├── first_ip          GenericIPAddressField (nullable)
├── first_page        CharField (path da primeira página)
├── last_page         CharField (path da última página)
├── pages_viewed      PositiveIntegerField (default=1)
├── started_at        DateTimeField (auto)
├── last_activity_at  DateTimeField
├── status            CharField (active/expired/converted)
├── utm_data          JSONField (UTM capturado no primeiro request)
├── referrer          URLField (blank)
└── (herda BaseModel)
```

**Diferenças da proposta v1**:
- `first_geo` em vez de `geo_location` — registra o geo do **primeiro request** da sessão, não o último. Geo muda pouco dentro de uma sessão.
- `first_ip` em vez de `ip_address` — mesmo raciocínio.
- Removido `last_geo`/`last_ip` — não vale a carga de UPDATE em cada request por dado que quase não muda.

### Mudança 4: Identity ganha contexto direto (sem precisar de joins)

```
Identity (campos adicionais)
├── primary_fingerprint  FK → FingerprintIdentity (nullable)  — substitui is_master flag
├── last_device_profile  FK → DeviceProfile (nullable)
├── last_geo_location    FK → GeoLocation (nullable)
├── last_ip_address      GenericIPAddressField (nullable)
├── last_session         FK → VisitorSession (nullable)
├── total_sessions       PositiveIntegerField (default=0, incrementado atomicamente)
├── total_page_views     PositiveIntegerField (default=0)
```

**`primary_fingerprint`** substitui o padrão `is_master` do legado. Em vez de um flag no FingerprintIdentity, a Identity aponta diretamente pro "fingerprint principal" dela. Mais limpo: `identity.primary_fingerprint` em vez de `FingerprintIdentity.filter(identity=id, is_master=True).first()`.

**`total_sessions` e `total_page_views`** são contadores desnormalizados (atualizados via `F()` atômico). Evitam `COUNT(*)` em queries de listagem.

### Mudança 5: CaptureEvent e CaptureSubmission normalizam geo

```
CaptureEvent (mudanças)
├── geo_location    FK → GeoLocation (nullable, substitui geo_data JSONField)
├── ip_address      GenericIPAddressField (mantém — IP específico do evento)
├── REMOVE          geo_data JSONField (não mais necessário)

CaptureSubmission (mudanças)
├── geo_location    FK → GeoLocation (nullable, substitui geo_data JSONField)
├── ip_address      GenericIPAddressField (mantém)
├── REMOVE          geo_data JSONField
```

### Mudança 6: `update_from_payload()` com merge inteligente (como o legado)

```python
# FingerprintIdentity.update_from_payload() — versão revisada
def update_from_payload(self, payload_data: dict) -> None:
    """
    Merge inteligente dos dados do FingerprintJS Pro.
    Princípio do legado: dados se complementam, nunca se perdem.
    """
    update_fields = ["updated_at", "last_seen"]
    self.last_seen = timezone.now()

    # Confidence: sempre mantém o MAIOR visto (como o legado)
    new_confidence = payload_data.get("confidence_score", 0.0)
    if new_confidence > self.confidence_score:
        self.confidence_score = new_confidence
        update_fields.append("confidence_score")

    # visitor_found: sobrescreve (último status é o relevante)
    if "visitor_found" in payload_data:
        self.visitor_found = payload_data["visitor_found"]
        update_fields.append("visitor_found")

    # JSONs: merge shallow (como o legado — dict.update())
    # Dados novos complementam, chaves existentes são atualizadas
    for json_field in ("device_info", "browser_info", "geo_info"):
        new_data = payload_data.get(json_field, {})
        if new_data:
            current = getattr(self, json_field) or {}
            current.update(new_data)
            setattr(self, json_field, current)
            update_fields.append(json_field)

    # Campos planos: first-write-wins (como o legado)
    for field, source_path in [
        ("browser", ("device_info", "browser_name")),
        ("os", ("device_info", "os")),
        ("ip_address", ("browser_info", "ip")),
    ]:
        if not getattr(self, field):
            source_dict = payload_data.get(source_path[0], {})
            value = source_dict.get(source_path[1]) if isinstance(source_dict, dict) else None
            if value:
                setattr(self, field, value)
                update_fields.append(field)

    self.save(update_fields=list(set(update_fields)))
```

### Mudança 7: Middleware atualiza VisitorSession em cada request

O `IdentitySessionMiddleware` revisado:

```
Request chega
  1. Lê/cria Identity (como hoje)
  2. Lê/cria DeviceProfile (como hoje, via VisitorMiddleware)
  3. Lê/cria GeoLocation via hash do MaxMind geo (NOVO)
  4. Lê/cria VisitorSession pra essa combinação session_key + identity (NOVO)
     - Se nova: preenche first_geo, first_ip, first_page, utm_data, referrer
     - Se existente: incrementa pages_viewed, atualiza last_page, last_activity_at
  5. Atualiza Identity.last_* (device, geo, ip, session) (NOVO)
     - Usa UPDATE com SET direto, sem ler o objeto todo
  6. Grava identity_pk na session (como hoje)
```

### Quando o beacon do fingerprint chega (fp_resolve revisado):

```
Beacon chega (uma vez por visitante)
  1. Parsear payload rico (visitor_id, ip, ip_location, browser_details, etc.)
  2. Estruturar dados como o payload_service do legado fazia
  3. get_or_create FingerprintIdentity(hash=visitor_id)
     - Se novo: preencher TUDO (device_info, browser_info, geo_info, ip, browser, os)
     - Se existente: update_from_payload() com merge inteligente
  4. Criar GeoLocation do ip_location do FingerprintJS (mais preciso que MaxMind)
  5. Linkar FP → Identity da session (como hoje)
  6. Atualizar VisitorSession.fingerprint = fp_identity
  7. Atualizar Identity.primary_fingerprint (se é o primeiro FP)
  8. Atualizar Identity.last_geo_location com o geo do FP (mais preciso)
```

### Diagrama do modelo revisado

```
                        Identity (centro de tudo)
                        ├── primary_fingerprint ──→ FingerprintIdentity
                        ├── last_device_profile ──→ DeviceProfile
                        ├── last_geo_location ────→ GeoLocation
                        ├── last_session ─────────→ VisitorSession
                        │
        ┌───────────────┼───────────────┬──────────────┬───────────────┐
        ↓ FK            ↓ FK            ↓ FK           ↓ FK            ↓ FK
  VisitorSession   FingerprintIdentity  ContactEmail  ContactPhone  CaptureSubmission
  ├── device ──→ DeviceProfile  │                                  ├── geo ──→ GeoLocation
  ├── fp ────→ FP Identity      ↓ FK (CASCADE)                     └── device ──→ DeviceProfile
  └── geo ───→ GeoLocation    FingerprintEvent
                               (sempre tem dono, ZERO órfãos)

  CaptureEvent
  ├── identity ──→ Identity (NOT NULL)
  ├── device ────→ DeviceProfile
  ├── geo ───────→ GeoLocation
  └── fp_identity → FingerprintIdentity (nullable, preenchido retroativamente)


  GeoLocation (tabela dimensão, dedup por hash, ~5-50k rows)
  ├── ← VisitorSession.first_geo
  ├── ← CaptureEvent.geo_location
  ├── ← CaptureSubmission.geo_location
  └── ← Identity.last_geo_location

  DeviceProfile (tabela dimensão, dedup por hash, ~200-1k rows)
  ├── ← VisitorSession.device_profile
  ├── ← CaptureEvent.device_profile
  ├── ← CaptureSubmission.device_profile
  └── ← Identity.last_device_profile
```

### Comparação: Proposta v1 → Proposta v2

| Aspecto | v1 (pré-legado) | v2 (pós-legado) |
|---------|------------------|-------------------|
| Beacon | Não mencionava o problema | **Corrige**: beacon envia payload rico |
| GeoLocation | Tabela dimensão básica | + campo `source` (fingerprintjs/maxmind) |
| VisitorSession | `geo_location` (último) | `first_geo` (primeiro — geo não muda numa sessão) |
| Identity | `last_*` FKs | + `primary_fingerprint` FK + contadores desnormalizados |
| update_from_payload | Não mencionava | Implementação detalhada com merge inteligente do legado |
| fp_resolve | Não mencionava | Fluxo completo revisado com extração de dados ricos |
| Fraud detection | Não mencionava | Descartada conscientemente (não relevante pro contexto de captura) |
| CaptureEvent.identity | Não mencionava | `NOT NULL` (zero órfãos, como o legado) |

### O que NÃO copiamos do legado (e por quê)

| Feature do legado | Por que não copiar |
|-------------------|--------------------|
| Webhook server-to-server | Nosso SDK roda client-side (beacon). O beacon rico resolve. |
| Celery task pra processar FP | Desnecessário — beacon é leve, `fp_resolve` é sync e rápido |
| Fraud detection (incognito, VPN, timezone) | Não relevante pra captura de leads. Pode ser adicionado depois se necessário. |
| `is_master` flag no FingerprintIdentity | Substituído por `Identity.primary_fingerprint` FK (mais limpo) |
| `session_id` como string sintética | Substituído por `VisitorSession` modelo real |
| Re-chamada do SDK em cada visita | SDK roda uma vez (cookie 365 dias). Dados persistem no banco. |

### Resumo da estratégia de dados

```
PRIMEIRO REQUEST (sem cookie fpjs_vid):
  Middleware → Identity + VisitorSession + DeviceProfile(UA) + GeoLocation(MaxMind)
  SDK → fp.get() → beacon rico → fp_resolve → FingerprintIdentity(dados completos)
  Resultado: Identity tem tudo — FP, device, geo (MaxMind + FingerprintJS), IP

REQUESTS SEGUINTES (com cookie fpjs_vid):
  Middleware → Atualiza VisitorSession(pages_viewed++, last_page, last_activity)
  Middleware → Atualiza Identity.last_device/geo/ip (se mudou)
  SDK → NÃO roda (cookie existe)
  Resultado: Sessão cresce, Identity se mantém enriquecida

CONVERSÃO (form submit):
  CaptureEvent + CaptureSubmission → FK pra Identity, DeviceProfile, GeoLocation
  ContactEmail/ContactPhone criados → FK pra Identity
  Identity.confidence_score aumenta
  Resultado: Lead completo com toda a cadeia rastreável
```

---

## ANÁLISE DO BACKEND LEGADO (projeto original Django)

> Fonte: `/home/marcelo-karval/Backup/Projetos/all-agrelli-projects/zzz-backup-projeto-launch-antigo/backend/`
> Análise de 2026-02-21.

### Arquitetura do legado: como funcionava

No projeto original, **o FingerprintJS Pro era o centro de tudo**. Não tinha middleware que criava Identity automaticamente. O fluxo era:

```
Browser → FingerprintJS Pro SDK → FingerprintJS Pro Cloud → Webhook → Django Celery Task → Resolution
```

Ou seja: o **FingerprintJS Pro enviava um webhook pro Django** com todos os dados (visitor_id, device_info, browser_info, geo_info, ip). O Django processava tudo via Celery.

### Modelos do legado

#### Identity (mesma ideia, mas mais simples)
- `status` (active/merged/inactive)
- `merged_into` → FK pra self
- `last_seen`, `first_seen_source`
- `metadata` (JSONField — guardava confidence_score e graph_analysis)
- **NÃO tinha** `confidence_score` como campo direto (era no metadata)
- **NÃO tinha** `display_name`, `operator_notes`, `tags`, `lifecycle_global`

#### FingerprintIdentity (o modelo principal — guardava TUDO)
- `identity` → FK pra Identity (SET_NULL, nullable)
- `hash` → visitor_id do FingerprintJS Pro (unique)
- `confidence_score` → score do FingerprintJS Pro
- `device_type` → mobile/tablet/desktop
- `device_info` → JSONField (`{browser_name, browser_version, os, os_version, device, screen_resolution}`)
- `browser_info` → JSONField (`{incognito, ip, timezone}`)
- `geo_info` → JSONField (`ipLocation` completo do FingerprintJS Pro)
- `ip_address` → GenericIPAddressField (extraído de browser_info.ip)
- `browser`, `os` → campos planos (extraídos dos JSONs)
- `user_agent` → TextField
- `is_master` → BooleanField (primeiro fingerprint de uma Identity = master)
- `visitor_found` → se o FingerprintJS Pro já conhecia
- `first_seen`, `last_seen`

**Método importante**: `update_from_payload()` → fazia **MERGE** dos JSONs (`.update()`), não substituía. Dados mais recentes complementavam os anteriores. Confidence sempre mantinha o **máximo** visto.

#### FingerprintEvent (timeline de eventos por fingerprint)
- `fingerprint` → FK pra FingerprintIdentity (CASCADE)
- `event_type` → page_view, form_submit, CREATED, VISIT, FIRST_VISIT
- `page_url` → URL onde aconteceu
- `timestamp`
- `user_data` → JSONField (dados de formulário)
- `event_data` → JSONField (dados extras)
- `session_id` → CharField (gerado como `fp_{visitorId}_{timestamp}`)

#### FingerprintContact (junction table)
- `fingerprint` → FK pra FingerprintIdentity
- `contact` → GenericForeignKey (aponta pra ContactEmail ou ContactPhone)
- `verification_status` → unverified/pending/verified

#### ContactEmail e ContactPhone
- Ambos herdam `ContactBase`
- `identity` → FK pra Identity (CASCADE)
- `value` (normalizado, unique), `original_value`
- `is_verified`, `verified_at`
- `first_seen`, `last_seen`
- ContactEmail: `domain`
- ContactPhone: `country_code`

### O workflow de resolução do legado (o que FUNCIONAVA)

```
1. FingerprintJS Pro SDK no browser coleta dados do visitante
2. SDK envia pro cloud do FingerprintJS Pro
3. FingerprintJS Pro envia webhook pro Django com payload completo:
   - visitorId, confidence, browserDetails, ipLocation, etc.
4. Django recebe no endpoint /webhook/events/
5. Enfileira Celery task: process_fingerprint_event.delay(data)

6. Celery task (queue: fingerprint_events):
   a. Extrai: visitorId, confidence, device_info, geo_info, browser_info
   b. Classifica device_type (mobile/tablet/desktop)
   c. Gera session_id sintético: fp_{visitorId}_{timestamp}
   d. Se tem formData → correlaciona fingerprint com form (email/phone)
   e. Chama resolution_service.resolve_identity_from_real_data()

7. Resolution Service (dentro de transaction.atomic()):
   a. get_or_create FingerprintIdentity pelo hash (visitor_id)
   b. Se existente: update_from_payload() → MERGE dos JSONs
   c. Se NÃO tem dados de contato (email/phone):
      → Se FP já tem identity → retorna ela
      → Se não → cria Identity anônima + marca FP como is_master
   d. Se TEM dados de contato:
      → Busca ContactEmail/ContactPhone existentes pelo value
      → Se achou 0 identities → cria nova Identity + contatos + linka FP
      → Se achou 1 identity → associa FP à identity existente
      → Se achou 2+ identities → MERGE (mais antiga sobrevive) → associa FP

8. Merge (quando necessário):
   a. Valida: ambos active, não é self-merge, source não é merged
   b. Signal: identity_pre_merge
   c. Transfere TUDO do source pro target (bulk update):
      - FingerprintIdentity.filter(identity=source).update(identity=target)
      - ContactEmail.filter(identity=source).update(identity=target)
      - ContactPhone.filter(identity=source).update(identity=target)
   d. source.status = 'merged', source.merged_into = target
   e. IdentityHistory registra o merge
   f. Signal: identity_post_merge

9. Pós-resolução (signals):
   - calculate_confidence_score.delay()
   - analyze_identity_graph.delay()
   - detect_suspicious_activity.delay()
```

### Cálculo de confidence score do legado

```
score = base_fpjs_confidence (do FingerprintJS Pro)
      + (emails verificados * 0.15) + (emails não verificados * 0.05)
      + (phones verificados * 0.20) + (phones não verificados * 0.10)
      + cross_device_bonus (min(device_types * 0.05, 0.15))
      - incognito_penalty (0.10 por FP incógnito)
      - vpn_penalty (0.15 por FP com accuracyRadius > 1000)
      
Clamped to [0.0, 1.0]
```

### O que o legado NÃO tinha

1. **NÃO tinha middleware que criava Identity automaticamente** — Identity só era criada pelo Resolution Service, acionado pelo webhook ou pela API de tracking
2. **NÃO tinha DeviceProfile normalizado** — device/browser/OS viviam nos JSONs do FingerprintIdentity
3. **NÃO tinha GeoLocation normalizado** — geo vivia no JSON `geo_info` do FingerprintIdentity
4. **NÃO tinha CaptureEvent** — eventos eram `FingerprintEvent`, sempre ligados a um FingerprintIdentity
5. **NÃO tinha Session como entidade** — session_id era só uma string gerada (`fp_{visitorId}_{timestamp}`)
6. **NÃO tinha cookies `_em`/`_ph`/`_lid`/`_vs`** — toda a identificação vinha via FingerprintJS Pro

### O que o legado TINHA e o projeto atual perdeu

1. **Tudo pertencia a alguém**: FingerprintEvent → FingerprintIdentity → Identity. Não existia evento "órfão".
2. **Dados não se duplicavam**: device/geo/IP viviam APENAS no FingerprintIdentity, não copiados em cada evento.
3. **Resolution era event-driven**: o webhook do FingerprintJS Pro trazia tudo, não dependia de middleware sync.
4. **update_from_payload() fazia MERGE** dos JSONs: dados se complementavam, nunca se perdiam.
5. **is_master flag**: primeiro fingerprint de uma Identity era marcado como master.
6. **Fraud detection** integrada: incognito, VPN, timezone mismatch, suspicious activity.

---

## COMPARAÇÃO: Legado vs Atual

| Aspecto | Legado | Atual |
|---------|--------|-------|
| **Trigger de criação de Identity** | Webhook FingerprintJS Pro → Celery task → Resolution Service | Middleware sync em cada request HTTP |
| **Onde vive device/geo/IP** | Nos JSONs do `FingerprintIdentity` (1 lugar só) | Duplicado em `CaptureEvent.geo_data`, `CaptureSubmission.geo_data`, `FingerprintIdentity.geo_info`, Redis |
| **Session** | String `fp_{visitorId}_{timestamp}` no FingerprintEvent | Blob opaco do `django_session` sem FK |
| **Identity sem dono** | Não existia: toda Identity era criada pelo resolution service | Existe: `IdentitySessionMiddleware` cria Identity anônima que pode nunca ser linkada a nada |
| **DeviceProfile** | Não existia (JSON no FP) | Existe mas não tem FK pra Identity |
| **GeoLocation** | Não existia (JSON no FP) | Não existe (duplicado em JSONs) |
| **Eventos** | `FingerprintEvent` → sempre com FK pra `FingerprintIdentity` | `CaptureEvent` → FK pra Identity nullable, FK pra FingerprintIdentity nullable |
| **Merge** | Idêntico conceito: mais antiga sobrevive, bulk update de tudo | Mesmo conceito preservado |
| **Confidence score** | Multi-fator com penalidades de fraude | Simplificado (0.05 base + 0.15 por fingerprint) |
| **Fraud detection** | incognito, VPN, timezone mismatch, login_failed | Removida |

---

## Arquivos de referência

| Arquivo | Responsabilidade |
|---------|-----------------|
| `backend/src/core/tracking/middleware.py` | VisitorMiddleware — lê `fpjs_vid`, resolve FingerprintIdentity, DeviceProfile, GeoIP |
| `backend/src/core/tracking/identity_middleware.py` | IdentitySessionMiddleware — cria/recupera Identity na session, linka fingerprint, seta cookies |
| `backend/src/apps/landing/views.py` | `fp_resolve` — endpoint que recebe o beacon e amarra FingerprintIdentity ↔ Identity |
| `frontends/landing/src/components/GlobalFingerprintInit.tsx` | Carrega FingerprintJS, seta cookie, envia beacon |
| `frontends/landing/src/main.tsx` | AppShell layout que garante GlobalFingerprintInit roda em todas as páginas |
