---
title: Fluxo To-Be Ideal de Captura
description: Desenho alvo do fluxo de captura com mudanças concretas no backend e no frontend.
---

# Fluxo To-Be Ideal de Captura

## Status de Implementacao

As Fases 1-5 deste plano ja foram implementadas no codigo.

```text
╔══════════════════════════════════════════════════════════════════════╗
║ STATUS DAS FASES                                                    ║
╠══════════════════════════════════════════════════════════════════════╣
║ Fase 1  capture_page_public_id                     [IMPLEMENTADA]    ║
║ Fase 2  CaptureIntent / prelead claro             [IMPLEMENTADA]    ║
║ Fase 3  complete_capture() transacional           [IMPLEMENTADA]    ║
║ Fase 4  LeadIntegrationOutbox                     [IMPLEMENTADA]    ║
║ Fase 5  fallback JSON controlado + sync legado    [IMPLEMENTADA]    ║
╚══════════════════════════════════════════════════════════════════════╝
```

O que permanece em aberto agora nao e mais a espinha dorsal do fluxo, e sim o hardening operacional final.

Documento complementar:

- [Checklist de Hardening para Producao](./lead-capture-production-hardening.md)

## Objetivo

Transformar o fluxo atual em um fluxo operacionalmente mais claro, mais auditavel e mais consistente para:

- produto
- engenharia
- analytics
- CRM / automacoes
- operacao

Partimos de 3 fatos ja estabelecidos:

1. `submit valido` e o momento oficial da captura de lead
2. `capture-intent` continua valioso, mas como prelead
3. `CaptureSubmission` deve existir em todo submit valido de producao

## Resultado Alvo

No estado ideal, o fluxo de producao deve obedecer a esta regra:

```text
Page load              -> cria visitante identificado tecnicamente
Capture intent         -> cria sinal de interesse, nao conversao
Submit valido          -> cria lead oficial e fato operacional
Integracoes assincronas -> propagam a captura, mas nao definem a captura
```

## Fluxo To-Be em Alta Resolucao

```text
Legenda:
  ━━━━━→   caminho critico / fluxo principal
  ─────→   chamada sincrona
  - - - →   chamada assincrona
  ═════→   retorno / response
  ╌╌╌╌╌→   caminho alternativo / fallback
  ──×──     falha / erro

╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                         FLUXO TO-BE IDEAL — CAPTURA DE LEAD EM PRODUCAO                            ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝

┌──────────────┐    ┌──────────────────────┐    ┌────────────────────────────┐    ┌──────────────────┐
│   Usuario    │    │  Frontend Landing    │    │  Backend Capture Domain    │    │ Async / External │
└──────┬───────┘    └──────────┬───────────┘    └────────────┬───────────────┘    └────────┬─────────┘
       │                        │                               │                            │
       ━━━━━[1] GET landing ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━→│                            │
       │                        │                               │──[2] resolve CapturePage──→│ DB
       │                        │                               │──[3] ensure visitor ctx───→│ DB/session
       │                        │←════ page props + ids ════════│                            │
       │◄━━━━━━━━━━━━ page ready ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│                            │
       │                        │                               │                            │
       │                        │──[4] fp-resolve──────────────→│──[5] link fingerprint────→│ DB
       │                        │←════ ok ══════════════════════│                            │
       │                        │                               │                            │
       │── digita campos ──────→│                               │                            │
       │                        │──[6] debounce intent────────→ │──[7] save intent only ───→│ DB [1]
       │                        │←════ 202 accepted ════════════│                            │
       │                        │                               │                            │
       │── envia formulario ───→│                               │                            │
       │                        ━━━━━[8] POST submit ━━━━━━━━━━→│                            │
       │                        │                               │──[9] validate payload────→│
       │                        │                               ◆ valido?                    │
       │                        │                     nao       │                            │
       │                        │╌╌╌╌╌ show field errors ╌╌╌╌→ │──[10] FORM_ERROR─────────→│ events
       │                        │                     sim       │                            │
       │                        │                               │──[11] complete_capture()  │
       │                        │                               │    ├─ lock/idempotency     │
       │                        │                               │    ├─ resolve identity     │
       │                        │                               │    ├─ persist contacts     │
       │                        │                               │    ├─ persist submission   │
       │                        │                               │    └─ persist outbox       │
       │                        │                               │───────────────────────────→│ DB
       │                        │                               │──[12] FORM_SUCCESS───────→│ events
       │                        │←════ 303 thank-you ═══════════│                            │
       │◄━━━━━━━━━━━━ thank-you / success ━━━━━━━━━━━━━━━━━━━━━━│                            │
       │                        │                               │- -[13] dispatch outbox -→│ N8N / Meta / CRM
       │                        │                               │- -[14] update statuses -→│ DB
```

**Legenda de callouts**

| # | Elemento | Observacao |
|---|---|---|
| 1 | `intent only` | O to-be ideal evita promover blur/hint para contato final; a persistencia antecipada vira entidade propria de intencao |

## Diferenca Principal Entre Atual e To-Be

```text
╔══════════════════════════════════════╗    ╔══════════════════════════════════════════════╗
║ ATUAL                               ║    ║ TO-BE                                       ║
╠══════════════════════════════════════╣    ╠══════════════════════════════════════════════╣
║ JSON fallback ainda participa       ║    ║ CapturePage e obrigatorio em producao       ║
║ do runtime                          ║    ║ antes do trafego real                        ║
║                                      ║    ║                                              ║
║ blur pode criar contato pendente    ║    ║ blur grava intent/prelead, nao contato final║
║                                      ║    ║                                              ║
║ submit espalha responsabilidades    ║    ║ submit fecha tudo via um service transacional║
║ por view + helpers                  ║    ║ unico                                        ║
║                                      ║    ║                                              ║
║ tasks async saem do request path    ║    ║ request cria outbox e worker despacha depois ║
║ mas sem fronteira formal unica      ║    ║ com rastreabilidade unica                    ║
╚══════════════════════════════════════╝    ╚══════════════════════════════════════════════╝
```

## Mudancas Concretas no Backend

## B1. Eliminar JSON fallback do caminho de producao

### Problema atual

- o runtime ainda aceita `CapturePageService -> JSON file -> default`
- isso e util para migracao, mas ruim como estado permanente

### To-be

- toda landing de producao deve existir como `CapturePage` no banco
- JSON fica apenas como:
  - fixture de migracao
  - backup de conteudo
  - seed/import tool

### Mudanca concreta

1. criar comando de sync/import:
   - `manage.py sync_legacy_capture_pages`
2. publicar landing em producao apenas se `CapturePage` existir
3. manter fallback JSON apenas em ambientes de migracao/dev, atras de flag

### Efeito

- `CaptureSubmission` deixa de depender de runtime materialization
- campaign config fica observavel e editavel pelo admin / DB

## B2. Criar uma entidade explicita de intent/prelead

### Problema atual

- `capture-intent` pode criar `ContactEmail`/`ContactPhone` cedo demais
- isso mistura hint com lead

### To-be

- `capture-intent` escreve numa entidade propria, por exemplo:
  - `CaptureIntent`
  - ou `LeadIntent`

### Shape sugerido

```text
CaptureIntent
- public_id
- capture_page
- identity
- fingerprint_identity
- email_hint
- phone_hint
- visitor_id
- request_id
- first_seen_at
- last_seen_at
- submit_status: pending | completed | abandoned
- metadata
```

### Mudanca concreta

1. `capture-intent` para de criar `ContactEmail`/`ContactPhone`
2. `capture-intent` passa a atualizar apenas `CaptureIntent`
3. no submit valido, `complete_capture()` consome o intent e o marca `completed`

### Efeito

- taxonomia mais limpa
- analytics e CRM deixam de ler prelead como lead

## B3. Consolidar o submit em um service transacional unico

### Problema atual

- a view ainda coordena varias partes do fluxo
- isso aumenta risco de acoplamento e regressao

### To-be

- criar um service orquestrador, exemplo:
  - `LeadCaptureService.complete_capture(...)`

### Responsabilidades desse service

```text
1. validar payload final
2. aplicar idempotencia por capture_token / request_id
3. resolver identidade
4. criar/atualizar ContactEmail e ContactPhone
5. criar CaptureSubmission
6. gravar eventos finais
7. criar outbox para integracoes externas
8. retornar DTO de sucesso para a view
```

### Mudanca concreta

- mover a parte final de `_handle_capture_post()` para esse service
- deixar a view apenas como thin controller

## B4. Tornar idempotencia explicita

### Problema atual

- o request usa `capture_token` e `request_id`, mas a fronteira de idempotencia nao esta claramente modelada

### To-be

- o submit deve ser idempotente por `request_id` ou por `capture_token + email_normalized`

### Mudanca concreta

1. adicionar campo de idempotencia em `CaptureSubmission` ou em tabela dedicada
2. garantir que reenvio do mesmo form nao replique fatos/automacoes

## B5. Introduzir outbox para integracoes externas

### Problema atual

- o request decide algumas tarefas async diretamente
- ainda ha acoplamento entre captura e envio

### To-be

- submit cria registros de outbox, por exemplo:
  - `LeadIntegrationOutbox`

### Shape sugerido

```text
LeadIntegrationOutbox
- public_id
- capture_submission
- integration_type: n8n | meta_capi | crm
- payload
- status: pending | processing | sent | failed
- attempts
- last_error
- next_retry_at
```

### Mudanca concreta

1. request grava outbox dentro da mesma transacao da captura
2. worker le outbox e despacha
3. status da integracao vira observavel e reprocessavel

### Efeito

- maior confiabilidade
- retry disciplinado
- painel operacional possivel

## Mudancas Concretas no Frontend

## F1. Separar nitidamente intent de submit final

### Problema atual

- blur faz muita coisa conceitualmente sensivel

### To-be

- blur / debounce salva apenas `intent`
- UI nunca comunica isso como cadastro concluido

### Mudanca concreta

- manter hook de intent, mas renomear semanticamente para algo como:
  - `useLeadIntent`
- response `202 Accepted`
- sem qualquer mensagem de “sucesso” nesse ponto

## F2. Incluir IDs estruturais no payload final

### To-be

o frontend deve receber e reenviar explicitamente:

- `capture_page_public_id`
- `capture_token`
- `visitor_id`
- `request_id`

### Mudanca concreta

- GET da page entrega `capture_page_public_id`
- POST do form sempre inclui esse valor

### Efeito

- menor ambiguidade no backend
- menos dependencia de resolver por slug no submit

## F3. Tratar submit como operacao com idempotencia local

### Mudanca concreta

- desabilitar botao com trava mais forte durante submit
- manter `request_id` estavel por tentativa real
- se houver retry automatico, reaproveitar idempotency key

## F4. Melhorar UX de erro e duplicidade

### To-be

- distinguir claramente:
  - erro de validacao
  - erro tecnico temporario
  - lead duplicado / ja capturado

### Mudanca concreta

- mensagem de duplicidade amigavel no thank-you ou inline
- event tracking separado para:
  - `FORM_ERROR_VALIDATION`
  - `FORM_ERROR_TECHNICAL`
  - `FORM_DUPLICATE`

## F5. Thank-you orientado a proximo passo

### To-be

- thank-you nao e so “pagina final”; ele vira etapa operacional do funil

### Mudanca concreta

- thank-you deve receber status estruturado, por exemplo:
  - `capture_status: success | duplicate | pending_review`
- CTA muda de acordo com esse status

## Arquitetura Alvo por Camada

```text
╔════════════════════════════════════════════════════════════════════════════════╗
║ CAMADA 1 — EXPERIENCE                                                        ║
╠════════════════════════════════════════════════════════════════════════════════╣
║ Landing page                                                                 ║
║ Fingerprint provider                                                         ║
║ Intent tracking                                                              ║
║ Submit final                                                                 ║
║ Thank-you orientado a status                                                 ║
╚════════════════════════════════════════════════════════════════════════════════╝

╔════════════════════════════════════════════════════════════════════════════════╗
║ CAMADA 2 — CAPTURE DOMAIN                                                    ║
╠════════════════════════════════════════════════════════════════════════════════╣
║ CapturePage                                                                  ║
║ CaptureIntent                                                                ║
║ LeadCaptureService.complete_capture()                                        ║
║ CaptureEvent                                                                 ║
║ CaptureSubmission                                                            ║
╚════════════════════════════════════════════════════════════════════════════════╝

╔════════════════════════════════════════════════════════════════════════════════╗
║ CAMADA 3 — IDENTITY DOMAIN                                                   ║
╠════════════════════════════════════════════════════════════════════════════════╣
║ Identity                                                                     ║
║ FingerprintIdentity                                                          ║
║ ContactEmail                                                                 ║
║ ContactPhone                                                                 ║
║ ResolutionService                                                            ║
╚════════════════════════════════════════════════════════════════════════════════╝

╔════════════════════════════════════════════════════════════════════════════════╗
║ CAMADA 4 — DELIVERY / OPERATIONS                                             ║
╠════════════════════════════════════════════════════════════════════════════════╣
║ LeadIntegrationOutbox                                                        ║
║ Celery workers                                                               ║
║ N8N                                                                          ║
║ Meta CAPI                                                                    ║
║ Future CRM destinations                                                      ║
╚════════════════════════════════════════════════════════════════════════════════╝
```

## Plano de Evolucao Sugerido

## Fase 1 — Consolidacao do runtime

- manter a melhoria recente que garante `CaptureSubmission`
- criar docs e observabilidade do fluxo atual
- adicionar `capture_page_public_id` nas props e no POST

## Fase 2 — Limpeza de semantica

- introduzir `CaptureIntent`
- parar de promover blur para contato final
- separar eventos de validacao, duplicidade e erro tecnico

## Fase 3 — Fechamento do dominio de captura

- criar `LeadCaptureService.complete_capture()`
- mover o request path para service transacional unico
- implementar idempotencia formal

## Fase 4 — Operacao e entrega externa

- criar `LeadIntegrationOutbox`
- workers processam integracoes via outbox
- dashboard de reprocessamento e falhas

## Fase 5 — Sunset do legado

- remover JSON fallback do runtime de producao
- manter apenas import/sync tooling
- `CapturePage` vira unica fonte de verdade

## Criterios de Pronto do To-Be

```text
☑ Toda landing de producao existe como CapturePage
☑ Toda tentativa de submit tem idempotency boundary clara
☑ Todo submit valido cria CaptureSubmission
☑ capture-intent nao conta como lead oficial
☑ Integracoes externas sao outbox-driven
☑ Dashboard operacional consegue ver pending / sent / failed
```

## O Que Fizemos Ate Agora

```text
╔══════════════════════════════════════════════════════════════════════╗
║ RESUMO DO QUE JA FOI FEITO NESTA SESSAO                            ║
╠══════════════════════════════════════════════════════════════════════╣
║ 1. Analise profunda do projeto real                                 ║
║ 2. Validacao por testes e builds                                    ║
║ 3. Correcao do fluxo delinquent                                     ║
║ 4. Criacao da base docs em frontends/docusaurus                     ║
║ 5. Documentacao do workflow real + esperado                         ║
║ 6. ADR formalizando submit valido como fronteira oficial do lead    ║
║ 7. Fechamento do gap de CaptureSubmission em campanhas JSON         ║
║    via materializacao de CapturePage no submit valido               ║
╚══════════════════════════════════════════════════════════════════════╝
```

## Referencias Relacionadas

- [Workflow Completo de Captura](./lead-capture-workflow.md)
- [ADR-0001: Fronteira Oficial de Captura](./adr/0001-lead-capture-boundary.md)
