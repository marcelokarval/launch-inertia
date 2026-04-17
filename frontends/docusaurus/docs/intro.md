---
title: Visao Geral
description: Ponto de partida da documentacao funcional do fluxo de captura.
---

# Visao Geral

Esta area inicia a documentacao do fluxo de captura da stack `landing -> Django -> contacts identity -> tracking -> billing/analytics integrations`.

Status atual da trilha de implementacao:

- Fase 1 implementada: `capture_page_public_id`
- Fase 2 implementada: `CaptureIntent` como prelead
- Fase 3 implementada: `CaptureService.complete_capture()`
- Fase 4 implementada: `LeadIntegrationOutbox`
- Fase 5 implementada: fallback JSON controlado por flag + sync de legado

Documentos iniciados:

- [Workflow Completo de Captura](./lead-capture-workflow.md)
- [Fluxo To-Be Ideal de Captura](./lead-capture-workflow-to-be.md)
- [Identity Resolution Runtime Flow](./identity-resolution-runtime-flow.md)
- [Identity Resolution Gap Analysis](./identity-resolution-gap-analysis.md)
- [Checklist de Hardening para Producao](./lead-capture-production-hardening.md)
- [Rollout Sem JSON Fallback](./lead-capture-rollout-no-json-fallback.md)
- [ADR Index](./adr/README.md)
- [ADR-0001: Fronteira Oficial de Captura](./adr/0001-lead-capture-boundary.md)

Objetivo desta documentacao:

- explicar o que o usuario percebe
- explicar o que o sistema realmente faz
- mostrar o que e persistido em cada etapa
- separar claramente o que ja existe do que ainda precisa ser fechado
