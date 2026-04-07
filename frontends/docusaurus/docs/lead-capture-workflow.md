---
title: Workflow Completo de Captura
description: Fluxo real e fluxo esperado para um usuario que envia email e telefone em uma landing page.
---

# Workflow Completo de Captura

## Nota de Atualizacao

Este documento nasceu como radiografia do fluxo original. O codigo ja evoluiu desde entao e hoje incorpora as Fases 1-5 do plano de melhoria.

Implementado no estado atual:

- `capture_page_public_id` no fluxo real
- `CaptureIntent` como entidade explicita de prelead
- `capture-intent` sem criacao prematura de `ContactEmail`/`ContactPhone`
- `CaptureService.complete_capture()` como caminho transacional unico do submit
- `LeadIntegrationOutbox` para `n8n` e `meta_capi`
- fallback JSON controlado por `LANDING_JSON_FALLBACK_ENABLED`
- `sync_legacy_capture_pages` para convergencia do legado em `CapturePage`

Leitura complementar:

- alvo arquitetural: [Fluxo To-Be Ideal de Captura](./lead-capture-workflow-to-be.md)
- checklist restante: [Checklist de Hardening para Producao](./lead-capture-production-hardening.md)

## Premissa

Para o usuario, o workflow parece simples:

1. ele abre a landing
2. preenche email e telefone
3. clica em enviar
4. vai para a pagina de obrigado

Para o sistema, o workflow real e mais amplo e comeca antes do submit.

Existe uma diferenca importante entre:

- `cadastro tecnico do visitante`
- `cadastro consolidado do lead`

## Modelo Mental

- no `GET`, o visitante ja nasce como identidade anonima
- no `fp-resolve`, o sistema fortalece a identificacao tecnica
- no `capture-intent`, o sistema pode guardar hints parciais
- no `submit valido`, o sistema consolida o lead

## Visao do Usuario vs Visao do Sistema

```text
╔══════════════════════════════════════╗    ╔══════════════════════════════════════════════╗
║ O QUE O USUARIO PENSA               ║    ║ O QUE O SISTEMA REALMENTE FAZ               ║
╠══════════════════════════════════════╣    ╠══════════════════════════════════════════════╣
║ 1. Abri a pagina                    ║    ║ 1. Cria/recupera identidade anonima          ║
║ 2. Preenchi email e telefone        ║    ║ 2. Registra page view e sessao de captura    ║
║ 3. Enviei o formulario              ║    ║ 3. Tenta resolver fingerprint                 ║
║ 4. Fui para o obrigado              ║    ║ 4. Pode salvar hints no blur                  ║
║                                      ║    ║ 5. No submit, resolve/mescla a identidade     ║
║                                      ║    ║ 6. Cria eventos, fatos e integra async       ║
╚══════════════════════════════════════╝    ╚══════════════════════════════════════════════╝
```

## Fluxo Real Atual

```text
Legenda:
  ━━━━━→   caminho critico / fluxo principal
  ─────→   chamada sincrona
  - - - →   chamada assincrona
  ═════→   retorno / response
  ╌╌╌╌╌→   caminho alternativo / fallback
  ──×──     falha / erro

╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                    FLUXO REAL HOJE — USUARIO EM UMA LANDING DE CAPTURA                             ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝

┌──────────────┐    ┌──────────────────────┐    ┌──────────────────────────┐    ┌──────────────────┐
│   Usuario    │    │  Frontend Landing    │    │      Django / Core       │    │   Banco / Async  │
└──────┬───────┘    └──────────┬───────────┘    └────────────┬─────────────┘    └────────┬─────────┘
       │                        │                              │                           │
       ━━━━━[1] GET /inscrever-...━━━━━━━━━━━━━━━━━━━━━━━━━━━→│                           │
       │                        │                              │──[2] IdentitySession────→│ Identity anonima
       │                        │                              │──[3] PAGE_VIEW──────────→│ CaptureEvent
       │                        │                              │──[4] start session──────→│ sessao curta / redis
       │                        │←════ render Capture/Index ═══│                           │
       │◄━━━━━━━━━━━━ pagina renderizada ━━━━━━━━━━━━━━━━━━━━━━━│                           │
       │                        │                              │                           │
       │                        │──[5] FingerprintProvider────→│ /api/fp-resolve/         │
       │                        │                              │──[6] get/create FP──────→│ FingerprintIdentity
       │                        │                              │──[7] link sessao────────→│ Identity <-> FP
       │                        │                              │──[8] update PAGE_VIEW───→│ CaptureEvent
       │                        │←════ ok ═════════════════════│                           │
       │                        │                              │                           │
       │── digita email/phone ─→│                              │                           │
       │                        │──[9] blur beacon────────────→│ /api/capture-intent/     │
       │                        │                              │──[10] save hints────────→│ session
       │                        │                              │──[11] create pending────→│ ContactEmail/Phone [1]
       │                        │                              │──[12] FORM_INTENT───────→│ CaptureEvent
       │                        │←════ ok ═════════════════════│                           │
       │                        │                              │                           │
       │── clica enviar ───────→│                              │                           │
       │                        ━━━━━[13] POST /inscrever-...━━━━━━━━━━━━━━━━━━━━━━━━━━━━→│
       │                        │                              │──[14] FORM_ATTEMPT──────→│ CaptureEvent
       │                        │                              │──[15] validate()         │
       │                        │                              ◆ dados validos?           │
       │                        │                    nao       │                           │
       │                        │╌╌╌╌╌ re-render com errors ╌╌╌│──[16] FORM_ERROR────────→│ CaptureEvent
       │                        │                    sim       │                           │
       │                        │                              │──[17] process_lead()     │
       │                        │                              │    ├─ resolve identity    │
       │                        │                              │    ├─ merge se preciso    │
       │                        │                              │    ├─ link email/phone    │
       │                        │                              │    └─ save attribution    │
       │                        │                              │──────────────────────────→│ Identity
       │                        │                              │──────────────────────────→│ ContactEmail
       │                        │                              │──────────────────────────→│ ContactPhone
       │                        │                              │──[18] FORM_SUCCESS──────→│ CaptureEvent
       │                        │                              │──[19] bind events───────→│ eventos retroativos
       │                        │                              │──[20] mark converted────→│ session/redis
       │                        │                              │──[21] create fact [2]──→│ CaptureSubmission
       │                        │                              │- -[22] enqueue N8N - - →│ Celery
       │                        │                              │- -[23] enqueue Meta - -→│ Celery
       │                        │←════ 302 /obrigado-... ═════│                           │
       │◄━━━━━━━━━━━━ usuario ve a pagina de obrigado ━━━━━━━━━│                           │
       │                        │                              │- -[24] worker envia - -→│ N8N webhook
       │                        │                              │- -[25] worker envia - -→│ Meta CAPI
       │                        │                              │- -[26] update status -→ │ CaptureSubmission.n8n_status
```

**Legenda de callouts**

| # | Elemento | Observacao |
|---|---|---|
| 1 | `ContactEmail/ContactPhone` pendente | Pode nascer no `capture-intent`, antes do submit final |
| 2 | `CaptureSubmission` | Hoje depende de existir `identity` e `capture_page_model` |

## Linha do Tempo por Estagio

```text
╭──────────────────────────────────────────────────────────────────────────────────────────────╮
│ FASE 0 - PAGE LOAD                                                                          │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ [A] visitante chega                                                                         │
│ [B] middleware cria ou recupera Identity anonima                                            │
│ [C] view cria PAGE_VIEW e capture_token                                                     │
│ [D] frontend recebe props + prefill opcional                                                │
╰──────────────────────────────────────────────────────────────────────────────────────────────╯

╭──────────────────────────────────────────────────────────────────────────────────────────────╮
│ FASE 1 - IDENTIFICACAO TECNICA                                                              │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ [A] FingerprintJS resolve visitorId + requestId                                             │
│ [B] cookie fpjs_vid e salvo                                                                 │
│ [C] beacon /api/fp-resolve/ vincula o fingerprint a identidade da sessao                    │
│ [D] PAGE_VIEW e atualizado retroativamente                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────╯

╭──────────────────────────────────────────────────────────────────────────────────────────────╮
│ FASE 2 - INTENCAO DE CAPTURA                                                                │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ [A] usuario digita email/telefone                                                           │
│ [B] blur dispara /api/capture-intent/                                                       │
│ [C] sistema salva hints e pode criar contatos pendentes                                     │
│ [D] FORM_INTENT entra no funil analitico                                                    │
╰──────────────────────────────────────────────────────────────────────────────────────────────╯

╭──────────────────────────────────────────────────────────────────────────────────────────────╮
│ FASE 3 - SUBMIT                                                                             │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ [A] FORM_ATTEMPT sempre nasce                                                               │
│ [B] validacao server-side                                                                   │
│ [C] se falhar: FORM_ERROR + re-render                                                       │
│ [D] se passar: resolve/merge da identidade                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────╯

╭──────────────────────────────────────────────────────────────────────────────────────────────╮
│ FASE 4 - CONSOLIDACAO DO LEAD                                                               │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ [A] ContactEmail e ContactPhone ficam vinculados a Identity                                 │
│ [B] attribution e salva                                                                     │
│ [C] FORM_SUCCESS e gravado                                                                  │
│ [D] eventos anteriores sao amarrados a mesma identidade                                     │
│ [E] sessao vira converted                                                                    │
╰──────────────────────────────────────────────────────────────────────────────────────────────╯

╭──────────────────────────────────────────────────────────────────────────────────────────────╮
│ FASE 5 - FATO ANALITICO E INTEGRACOES                                                       │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ [A] CaptureSubmission e criado quando a page existe como CapturePage no banco               │
│ [B] N8N webhook e enfileirado                                                               │
│ [C] Meta CAPI e enfileirada                                                                 │
│ [D] usuario nao espera por isso para ver o obrigado                                         │
╰──────────────────────────────────────────────────────────────────────────────────────────────╯
```

## O Que E Persistido em Cada Etapa

| Etapa | Origem | Modelos / storage afetados | Objetivo |
|---|---|---|---|
| Page load | `GET /inscrever-{slug}/` | `Identity`, `CaptureEvent(PAGE_VIEW)`, sessao, redis | iniciar tracking e correlacao |
| Fingerprint | `/api/fp-resolve/` | `FingerprintIdentity`, update em `CaptureEvent` | fortalecer identificacao tecnica |
| Capture intent | `/api/capture-intent/` | `session.email_hint`, `session.phone_hint`, `ContactEmail`, `ContactPhone`, `CaptureEvent(FORM_INTENT)` | capturar abandono parcial e prefill |
| Submit invalido | `POST /inscrever-{slug}/` | `CaptureEvent(FORM_ATTEMPT)`, `CaptureEvent(FORM_ERROR)` | medir tentativa e erro |
| Submit valido | `CaptureService.process_lead()` | `Identity`, `ContactEmail`, `ContactPhone`, attribution, `CaptureEvent(FORM_SUCCESS)` | consolidar o lead |
| Pos-submit | `_handle_capture_post()` | bind retroativo, sessao converted, redis | consolidar historico |
| Fato operacional | `_create_capture_submission()` | `CaptureSubmission` | linha fato da captura |
| Integracao externa | Celery tasks | `CaptureSubmission.n8n_status`, `n8n_response`, webhook externo | integracao sem bloquear UX |

## Workflow Esperado / Ideal

```text
╔════════════════════════════════════════════════════════════════════════════════════╗
║                     FLUXO ESPERADO / IDEAL DO PONTO DE VISTA DE NEGOCIO           ║
╚════════════════════════════════════════════════════════════════════════════════════╝

┌────────────────────────────────────────────────────────────────────────────────────┐
│ 1. GET landing                                                                    │
│    - cria identidade anonima                                                      │
│    - cria PAGE_VIEW                                                               │
└────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│ 2. Fingerprint resolve                                                            │
│    - visitor ganha identificacao tecnica mais forte                               │
└────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│ 3. Capture intent opcional                                                        │
│    - hints e prefill, sem promover isso a lead final                              │
└────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│ 4. Submit valido                                                                  │
│    - sempre consolida o lead                                                      │
│    - sempre grava Identity + ContactEmail + ContactPhone + FORM_SUCCESS           │
│    - sempre grava CaptureSubmission                                               │
└────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│ 5. Integracoes async                                                              │
│    - N8N                                                                          │
│    - Meta CAPI                                                                    │
│    - retries e observabilidade                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│ 6. Obrigado                                                                       │
│    - redirect imediato                                                            │
│    - UX nao depende do N8N                                                        │
└────────────────────────────────────────────────────────────────────────────────────┘
```

## Gap Entre o Real e o Ideal

### Gap 1 — `CaptureSubmission` ainda nao e universal

Hoje o fluxo ideal so fecha completamente quando a landing vem de `CapturePage` no banco.

Se a campanha ainda vier de fallback JSON, o sistema pode:

- resolver a identidade
- salvar email e telefone
- gravar eventos
- disparar N8N

Mas ainda assim nao criar `CaptureSubmission`.

### Gap 2 — `capture-intent` cria dados antes do submit final

Isso e bom para:

- prefill
- abandono de formulario
- enriquecimento progressivo

Mas isso exige clareza semantica:

- `hint salvo` nao e igual a `lead capturado`
- `contato pendente` nao e igual a `conversao`

### Gap 3 — sucesso visual nao significa integracao externa concluida

O usuario vai para o obrigado antes do N8N terminar.

Isso esta certo para UX, mas exige:

- monitoramento de fila
- visibilidade de `n8n_status`
- estrategia de retry confiavel

## Decisao de Produto + Engenharia Que Esta Emerindo

```text
╔════════════════════════════════════════════════════════════════════╗
║ REGRA SUGERIDA                                                   ║
╠════════════════════════════════════════════════════════════════════╣
║ Visitante identificado   != Lead capturado                       ║
║ Hint salvo              != Conversao                             ║
║ Submit valido           == Momento oficial da captura de lead    ║
╚════════════════════════════════════════════════════════════════════╝
```

## Referencias de Codigo

- Entrada da landing e submit:
  - `src/apps/landing/views.py`
- Validacao e processamento do lead:
  - `src/apps/landing/services/capture.py`
- Identidade anonima por sessao:
  - `src/core/tracking/identity_middleware.py`
- Fingerprint beacon:
  - `src/apps/landing/views.py#fp_resolve`
  - `frontends/landing/src/components/FingerprintProvider.tsx`
- Capture intent:
  - `src/apps/landing/views.py#capture_intent`
  - `frontends/landing/src/hooks/use-capture-intent.ts`
- Form submit do frontend:
  - `frontends/landing/src/components/CaptureForm.tsx`
- Resolucao de identidade:
  - `src/apps/contacts/identity/services/resolution_service.py`
- Async N8N:
  - `src/apps/landing/tasks/__init__.py`

## Leitura Final

O fluxo real hoje e este:

- `page load -> identidade anonima -> fingerprint -> hints opcionais -> submit -> resolucao/merge -> eventos -> CaptureSubmission quando existir CapturePage -> N8N/Meta async -> obrigado`

O fluxo esperado ideal e este:

- `toda capture page de producao deve existir como CapturePage no banco`
- `todo submit valido deve gerar CaptureSubmission`
- `capture-intent deve continuar existindo, mas como prelead e nao como conversao`
