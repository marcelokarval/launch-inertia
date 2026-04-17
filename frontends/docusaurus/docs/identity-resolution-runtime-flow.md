---
title: Identity Resolution Runtime Flow
description: Fluxo real e exato de sessão, fingerprint, merge e duplicação no runtime atual.
---

# Identity Resolution Runtime Flow

## Objetivo

Este documento consolida o comportamento **real** do sistema para:

- primeira identificação de um visitante
- criação e recuperação da `Identity` anônima de sessão
- chegada posterior do fingerprint (`visitorId`)
- associação `FingerprintIdentity -> Identity`
- envio do cadastro
- merge entre identities
- duplicação em diferentes camadas

Este documento foi montado a partir do código e dos testes atuais, sem usar inferência de produto como fonte primária.

## Entidades Canônicas

```text
AUTH SIDE
┌─────────────────────────────┐
│ identity.User              │
│ identity.Profile           │
└─────────────────────────────┘

LEAD / PERSON SIDE
┌──────────────────────────────────────────────────────┐
│ Identity                                             │
│  ├─ ContactEmail[]                                   │
│  ├─ ContactPhone[]                                   │
│  ├─ FingerprintIdentity[]                            │
│  ├─ Attribution[]                                    │
│  └─ IdentityHistory[]                                │
└──────────────────────────────────────────────────────┘

RUNTIME / FACTS
┌──────────────────────────────────────────────────────┐
│ DeviceProfile                                        │
│ CaptureEvent                                         │
│ CaptureIntent                                        │
│ CaptureSubmission                                    │
│ LeadIntegrationOutbox                                │
│ LeadCaptureIdempotencyKey                            │
└──────────────────────────────────────────────────────┘
```

## Separação de Responsabilidade

- `identity.User` = conta autenticável do sistema privado
- `contacts.identity.Identity` = pessoa/lead/entidade do funil
- `contacts.fingerprint.FingerprintIdentity` = `visitorId` do FingerprintJS Pro
- `core.tracking.CaptureEvent` = trilha factual universal
- `core.tracking.CaptureIntent` = prelead explícito antes do submit

## Sequence Diagram — Fluxo Principal

```text
╔════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                     FLUXO REAL — SESSÃO, FINGERPRINT, SUBMIT E MERGE                             ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════╝

┌──────────────┐   ┌────────────────────┐   ┌──────────────────────────────┐   ┌───────────────────┐
│  Visitante   │   │ Django Middleware  │   │ Landing / Identity Services  │   │ Banco / Async     │
└──────┬───────┘   └──────────┬─────────┘   └──────────────┬───────────────┘   └────────┬──────────┘
       │                      │                            │                            │
       ━━━━━ GET capture ━━━━→│                            │                            │
       │                      │ VisitorMiddleware          │                            │
       │                      │ ├─ cookie fpjs_vid?        │                            │
       │                      │ ├─ DeviceProfile           │──────────────────────────→ │ DeviceProfile
       │                      │ └─ attach fingerprint?     │                            │
       │                      │                            │                            │
       │                      │ IdentitySessionMiddleware  │                            │
       │                      │ ├─ recover Identity        │                            │
       │                      │ └─ or create anonymous     │──────────────────────────→ │ Identity
       │                      │                            │──────────────────────────→ │ IdentityHistory
       │                      │                            │                            │
       │                      │ capture_page()             │                            │
       │                      │                            │──────────────────────────→ │ CaptureEvent(PAGE_VIEW)
       │                      │                            │──────────────────────────→ │ capture session (cache)
       │                      │◄════════ render page ══════│                            │
       │◄━━━━━━━━━━━━━━━━━━━━━ page ready ━━━━━━━━━━━━━━━━━│                            │
       │                      │                            │                            │
       │━━ fingerprint ready ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━→│ fp_resolve()               │
       │                      │                            │ ├─ get/create fingerprint   │──────────────────────────→ │ FingerprintIdentity
       │                      │                            │ ├─ link to session identity │──────────────────────────→ │ FingerprintIdentity.identity
       │                      │                            │ └─ update PAGE_VIEW         │──────────────────────────→ │ CaptureEvent update
       │◄══════════════════════════════════════════════════│                            │
       │                      │                            │                            │
       │━━ blur email/phone ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━→│ capture_intent()           │
       │                      │                            │ ├─ save session hints       │
       │                      │                            │ ├─ upsert CaptureIntent     │──────────────────────────→ │ CaptureIntent
       │                      │                            │ └─ FORM_INTENT              │──────────────────────────→ │ CaptureEvent(FORM_INTENT)
       │◄══════════════════════════════════════════════════│                            │
       │                      │                            │                            │
       │━━ submit form ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━→│ complete_capture()         │
       │                      │                            │ ├─ idempotency lock         │──────────────────────────→ │ LeadCaptureIdempotencyKey
       │                      │                            │ ├─ process_lead()           │
       │                      │                            │ │  ├─ resolve identity      │──────────────────────────→ │ Identity / channels
       │                      │                            │ │  ├─ maybe merge           │──────────────────────────→ │ MergeService
       │                      │                            │ │  └─ save attribution      │──────────────────────────→ │ Attribution
       │                      │                            │ ├─ FORM_SUCCESS            │──────────────────────────→ │ CaptureEvent(FORM_SUCCESS)
       │                      │                            │ ├─ bind previous events    │──────────────────────────→ │ CaptureEvent update
       │                      │                            │ ├─ complete CaptureIntent  │──────────────────────────→ │ CaptureIntent.completed
       │                      │                            │ ├─ CaptureSubmission       │──────────────────────────→ │ CaptureSubmission
       │                      │                            │ └─ create outbox           │──────────────────────────→ │ LeadIntegrationOutbox
       │                      │                            │                            │ - - - - - - - - - - - → │ outbox tasks
       │◄════════════════════ redirect thank-you ═════════│                            │
```

## Cenários Exatos

## 1. Primeira visita sem cadastro

### O que acontece

1. `VisitorMiddleware` tenta resolver fingerprint e criar `DeviceProfile`
2. `IdentitySessionMiddleware` cria `Identity` anônima se a sessão estiver vazia
3. a landing cria `CaptureEvent(PAGE_VIEW)` e sessão curta de captura

### Writes

- `DeviceProfile` (se ainda não existir para aquela assinatura)
- `Identity`
- `IdentityHistory`
- `CaptureEvent(PAGE_VIEW)`
- cache de sessão de captura

### Sessão

- `identity_id`
- `identity_pk`
- `visitor_status = new`
- `first_seen`
- `last_page`

### Cookies

- `_lid`
- `_vs`

### Código

- `backend/src/core/tracking/identity_middleware.py:265`
- `backend/src/core/tracking/services.py:141`
- `backend/src/apps/landing/views.py`

### Testes que provam

- `backend/src/tests/test_middleware.py:401`

---

## 2. Visita de retorno com sessão válida

### O que acontece

- `IdentitySessionMiddleware` recupera a mesma `Identity` pelo `identity_pk`
- o `visitor_status` sobe para `returning`

### Código

- `backend/src/core/tracking/identity_middleware.py:246`

### Testes que provam

- `backend/src/tests/test_middleware.py:418`

---

## 3. Fingerprint chega depois da sessão já existir

### O que acontece em `fp_resolve()`

1. `FingerprintIdentity.objects.get_or_create(hash=visitor_id)`
2. se o fingerprint estiver órfão, ele é ligado à `Identity` da sessão
3. se já estiver ligado à mesma `Identity`, no-op lógico
4. se já estiver ligado a outra `Identity`, merge assíncrono é disparado
5. `CaptureEvent(PAGE_VIEW)` daquele `capture_token` é atualizado com fingerprint/visitor

### Writes possíveis

- `FingerprintIdentity`
- `FingerprintIdentity.identity`
- `Identity.confidence_score` (quando o fingerprint órfão é ligado)
- `CaptureEvent` update
- task de merge async, se houver conflito

### Código

- `backend/src/apps/landing/views.py:851`
- `backend/src/core/tracking/identity_middleware.py:168`
- `backend/src/apps/contacts/fingerprint/services/fingerprint_service.py:28`
- `backend/src/apps/contacts/fingerprint/tasks.py:193`

### Observação importante

O sistema aceita divergência temporária entre:

- `Identity` da sessão
- `Identity` já ligada ao fingerprint

e tenta reconciliar isso via merge, não necessariamente em linha.

---

## 4. Blur de email/telefone antes do submit

### O que acontece

- frontend envia `email_hint`, `phone_hint`, `capture_token`, `visitor_id`, `request_id`
- backend salva hints na sessão
- faz `upsert_capture_intent()`
- opcionalmente faz `bind_events_to_identity()` se já houver `identity`
- grava `CaptureEvent(FORM_INTENT)`

### O que não acontece mais

- não cria `ContactEmail`
- não cria `ContactPhone`

### Writes

- sessão (`email_hint`, `phone_hint`)
- `CaptureIntent`
- `CaptureEvent(FORM_INTENT)`

### Código

- `backend/src/apps/landing/views.py:1029`
- `backend/src/core/tracking/services.py:360`

### Testes que provam

- `backend/src/tests/test_capture.py:652`

---

## 5. Submit com email/phone/fingerprint novos

### O que acontece

- `complete_capture()` trava idempotência
- `process_lead()` chama `ResolutionService.resolve_identity_from_real_data()`
- como não há contato prévio, ele cria nova `Identity`
- cria/associa `ContactEmail`
- cria/associa `ContactPhone`
- associa `FingerprintIdentity`
- grava `Attribution`
- marca `CaptureIntent` como completed
- cria `CaptureSubmission`
- cria `LeadIntegrationOutbox`

### Código

- `backend/src/apps/landing/services/capture.py:418`
- `backend/src/apps/contacts/identity/services/resolution_service.py:227`

### Testes que provam

- `backend/src/tests/test_contact_system.py:609`

---

## 6. Submit com email já conhecido

### O que acontece

- `find_existing_identities(contact_data)` encontra a `Identity` pelo email
- `associate_fingerprint_to_identity()` liga o novo fingerprint nessa identity
- não cria nova pessoa
- ainda cria nova `CaptureSubmission` para este evento de captura

### Código

- `backend/src/apps/contacts/identity/services/resolution_service.py:127`
- `backend/src/apps/contacts/identity/services/resolution_service.py:307`

### Testes que provam

- `backend/src/tests/test_contact_system.py:627`

---

## 7. Submit com email numa identity e phone em outra

### O que acontece

- `find_existing_identities()` retorna múltiplas identities
- `merge_multiple_identities()` escolhe a mais antiga como master
- `MergeService.execute_merge(source, target)` transfere todas as relações

### O que o merge transfere

- `ContactEmail`
- `ContactPhone`
- `FingerprintIdentity`
- `CaptureEvent`
- `CaptureSubmission`
- `Attribution`
- enriquecimento de `display_name`, `operator_notes`, `tags`

### Side effects

- `source.status = merged`
- `source.merged_into = target`
- `identity_post_merge` signal
- tasks async de confidence, graph, lifecycle e redirect de sessões

### Código

- `backend/src/apps/contacts/identity/services/resolution_service.py:371`
- `backend/src/apps/contacts/identity/services/merge_service.py:67`
- `backend/src/apps/contacts/identity/services/merge_service.py:170`
- `backend/src/apps/contacts/identity/signals.py:66`

### Testes que provam

- `backend/src/tests/test_contact_system.py:645`
- `backend/src/tests/test_contact_system.py:538`

---

## 8. Já existia uma identity anônima da sessão antes do submit

### O que acontece

Esse é o cenário mais importante no runtime atual.

Se a resolução por contato encontrar ou criar uma `Identity` diferente da `session_identity`, o sistema faz:

- `MergeService.execute_merge(source=session_identity, target=identity)`

Ou seja:

- a identity anônima da sessão é fundida na identity final
- o histórico pré-formulário é preservado

### Código

- `backend/src/apps/landing/services/capture.py:245`

---

## 9. Duplicação em camadas diferentes

### A. Duplicação de pessoa

Resolvida por:

- reuse
- associação
- merge

Camada:

- `ResolutionService`
- `MergeService`

### B. Duplicação de submissão

`CaptureSubmission` ainda pode ser criada, mas com `is_duplicate=True` quando já existe submissão com:

- mesmo `email_raw` case-insensitive
- mesmo `launch`

Código:

- `backend/src/apps/landing/services/capture.py:365`

### C. Replay do mesmo submit

Bloqueado por:

- `LeadCaptureIdempotencyKey`

Replay não recria:

- `FORM_SUCCESS`
- `CaptureSubmission`
- `LeadIntegrationOutbox`

Código:

- `backend/src/apps/landing/models.py:8`
- `backend/src/apps/landing/services/capture.py:68`
- `backend/src/apps/landing/services/capture.py:82`

Teste:

- `backend/src/tests/test_capture.py:535`

## Matriz — Situação -> Writes -> Side Effects -> Prova

```text
┌──────────────────────────────┬──────────────────────────────────────────────┬──────────────────────────────────────────────┬──────────────────────────────────────┐
│ Situação                     │ Writes principais                            │ Side effects                                 │ Testes                               │
├──────────────────────────────┼──────────────────────────────────────────────┼──────────────────────────────────────────────┼──────────────────────────────────────┤
│ 1º GET real                  │ Identity, IdentityHistory, PAGE_VIEW         │ cookies _lid/_vs, session new                │ test_middleware.py:401               │
│ retorno com sessão           │ none/new only if stale                       │ visitor_status=returning                     │ test_middleware.py:418               │
│ fingerprint chega            │ FingerprintIdentity, CaptureEvent update     │ confidence boost, merge async possível       │ coberto por código, sem teste E2E    │
│ blur de campo                │ CaptureIntent, FORM_INTENT                   │ bind events se identity já existir           │ test_capture.py:652                  │
│ submit totalmente novo       │ Identity, ContactEmail, ContactPhone, facts  │ attribution, outbox, complete intent         │ test_contact_system.py:609           │
│ email conhecido              │ Fingerprint ligado à identity existente      │ não cria nova pessoa                         │ test_contact_system.py:627           │
│ email e phone em pessoas distintas │ merge de identities                   │ transfer de events/submissions/attribution   │ test_contact_system.py:645,538       │
│ replay do mesmo submit       │ idempotency row                              │ não duplica success/submission/outbox        │ test_capture.py:535                  │
└──────────────────────────────┴──────────────────────────────────────────────┴──────────────────────────────────────────────┴──────────────────────────────────────┘
```

## Gatilhos e tarefas async

### `post_save(Identity)`

Dispara:

- `calculate_confidence_score`
- `update_identity_history`
- `analyze_identity_graph`
- `recalculate_lifecycle`

Arquivo:

- `backend/src/apps/contacts/identity/signals.py:39`

### `identity_post_merge`

Dispara:

- `calculate_confidence_score`
- `analyze_identity_graph`
- `recalculate_lifecycle`
- `redirect_merged_sessions`

Arquivo:

- `backend/src/apps/contacts/identity/signals.py:66`

### `LeadIntegrationOutbox`

Dispara entrega async para:

- `n8n`
- `meta_capi`

Arquivos:

- `backend/src/apps/landing/services/outbox.py:74`
- `backend/src/apps/landing/tasks/__init__.py:147`

## Conclusão Canônica

O comportamento real do sistema hoje é:

1. a pessoa ganha uma `Identity` anônima no primeiro GET
2. o fingerprint chega depois e tenta se reconciliar com a sessão
3. o blur cria `CaptureIntent`, não lead final
4. o submit roda resolução forte por `fingerprint + email + phone`
5. se preciso, ocorre merge:
   - entre identities por contato
   - da session identity anônima para a identity final
6. o submit válido cria:
   - `FORM_SUCCESS`
   - `CaptureSubmission`
   - `LeadIntegrationOutbox`
7. replay do mesmo submit é bloqueado por idempotência

## Referências de código

- `backend/src/core/tracking/identity_middleware.py`
- `backend/src/core/tracking/services.py`
- `backend/src/core/tracking/models.py`
- `backend/src/apps/landing/views.py`
- `backend/src/apps/landing/services/capture.py`
- `backend/src/apps/landing/models.py`
- `backend/src/apps/landing/services/outbox.py`
- `backend/src/apps/contacts/identity/services/resolution_service.py`
- `backend/src/apps/contacts/identity/services/merge_service.py`
- `backend/src/apps/contacts/identity/signals.py`
- `backend/src/apps/contacts/fingerprint/services/fingerprint_service.py`
- `backend/src/apps/contacts/fingerprint/tasks.py`

## Referências de teste

- `backend/src/tests/test_middleware.py`
- `backend/src/tests/test_contact_system.py`
- `backend/src/tests/test_capture.py`
- `backend/src/tests/test_tracking.py`
