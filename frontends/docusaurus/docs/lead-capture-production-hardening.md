---
title: Checklist de Hardening para Producao
description: Itens restantes para endurecer o fluxo de captura apos as Fases 1-5.
---

# Checklist de Hardening para Producao

## Objetivo

As Fases 1-5 fecharam a estrutura principal do fluxo de captura. Este documento lista os itens restantes para elevar o sistema de `estruturalmente correto` para `operacionalmente forte` em producao.

## Resumo Visual

```text
╔══════════════════════════════════════════════════════════════════════╗
║ O QUE JA ESTA PRONTO                                                ║
╠══════════════════════════════════════════════════════════════════════╣
║ ☑ CaptureIntent como prelead                                        ║
║ ☑ complete_capture() como caminho unico do submit                   ║
║ ☑ CaptureSubmission garantido no submit valido                      ║
║ ☑ Outbox para N8N e Meta CAPI                                       ║
║ ☑ Fallback JSON controlado por flag                                 ║
║ ☑ Idempotencia formal persistida para submit valido                 ║
╚══════════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════╗
║ O QUE AINDA FALTA                                                   ║
╠══════════════════════════════════════════════════════════════════════╣
║ ☐ Admin/observabilidade da outbox                                   ║
║ ☐ Reprocessamento e repair operacional                              ║
║ ☐ Rollout real sem fallback JSON em producao                        ║
║ ☐ Padronizacao dos fluxos especiais fora do capture standard        ║
╚══════════════════════════════════════════════════════════════════════╝
```

## 1. Idempotencia Formal do Submit

Estado atual:

- existe uma chave persistida via `LeadCaptureIdempotencyKey`
- replay do mesmo submit nao recria `FORM_SUCCESS`, `CaptureSubmission` nem outbox
- a implementacao esta coberta por teste de replay

Checklist:

- [x] definir chave oficial de idempotencia
- [x] persistir a chave no dominio
- [x] bloquear replay/duplo submit com teste automatizado

## 2. Observabilidade da Outbox

Estado atual:

- `LeadIntegrationOutbox` existe
- worker processa `n8n` e `meta_capi`
- status e tentativas ja ficam persistidos
- admin operacional foi adicionado para `LeadIntegrationOutbox`
- admin de apoio foi adicionado para `LeadCaptureIdempotencyKey`

Checklist:

- [x] admin/list view para `LeadIntegrationOutbox`
- [x] filtros por `integration_type`, `status` e `attempts`
- [x] relacao navegavel com `CaptureSubmission`
- [x] destaque operacional para `failed` e `pending`

## 3. Reprocessamento Operacional

Estado atual:

- existe retry automatico
- existe comando manual de requeue para `LeadIntegrationOutbox`
- existe comando de repair para payloads antigos/incompletos

Checklist:

- [x] comando `requeue_failed_lead_integrations`
- [x] reprocessamento por `outbox_id`
- [x] reprocessamento por `integration_type`
- [x] estrategia de repair para payloads antigos

## 4. Rollout Real do Sunset do JSON Fallback

Estado atual:

- a flag `LANDING_JSON_FALLBACK_ENABLED` existe
- o comando `sync_legacy_capture_pages` existe
- o comando `check_capture_page_readiness` existe
- o runtime ja prefere DB e so usa JSON quando permitido

Checklist:

- [ ] executar `sync_legacy_capture_pages --dry-run` em staging
- [ ] executar sync real em staging
- [ ] validar slugs ativos de capture/checkout no banco
- [ ] desligar `LANDING_JSON_FALLBACK_ENABLED` em staging
- [ ] repetir o rollout em producao

## 5. Fluxos Especiais Fora do Capture Standard

Checklist:

- [ ] revisar `checkout_page` contra a mesma politica de fonte unica
- [ ] revisar `agrelliflix` e outros JSONs especiais
- [ ] decidir explicitamente o que fica fora do dominio de captura

## 6. Operacao e SLOs

Checklist:

- [x] definir SLI de entrega/saude minima da outbox
- [x] alerta para crescimento de `failed` (health check + task periodica)
- [x] alerta para `pending` acima da janela esperada (health check + threshold)
- [x] objetivo de tempo maximo por integracao

Objetivos atuais:

- `n8n`: 10 minutos
- `meta_capi`: 15 minutos

Esses objetivos ja entram no `health snapshot` e passam a gerar `reasons` explicitas quando houver pending vencido por tipo de integracao.

## 7. Hardening de Testes

Checklist:

- [ ] teste de replay / submit duplicado
- [x] teste de rollback transacional em falha interna de `complete_capture()`
- [x] teste de falha final da outbox com status `failed`
- [ ] teste staging-like com fallback JSON desligado

## Fechamento

Quando os itens acima estiverem prontos, o fluxo de captura passa de `arquiteturalmente alinhado` para `operacionalmente endurecido`.

## Referencias

- [Workflow Completo de Captura](./lead-capture-workflow.md)
- [Fluxo To-Be Ideal de Captura](./lead-capture-workflow-to-be.md)
- [ADR-0001: Fronteira Oficial de Captura](./adr/0001-lead-capture-boundary.md)
