---
title: Rollout Sem JSON Fallback
description: Procedimento operacional para desligar o fallback JSON do runtime de capture com segurança.
---

# Rollout Sem JSON Fallback

## Objetivo

Executar o sunset do fallback JSON do runtime de capture/checkout com um procedimento reproduzivel e verificavel.

## Precondicoes

- `sync_legacy_capture_pages` ja existe
- `check_capture_page_readiness` ja existe
- `LANDING_JSON_FALLBACK_ENABLED` ja existe
- `LeadIntegrationOutbox` e health checks ja existem

## Fluxo de Rollout

```text
╔══════════════════════════════════════════════════════════════════════╗
║ 1. AUDITAR LEGADO                                                   ║
╠══════════════════════════════════════════════════════════════════════╣
║ uv run python manage.py check_capture_page_readiness                ║
╚══════════════════════════════════════════════════════════════════════╝
                              │
                              ▼
╔══════════════════════════════════════════════════════════════════════╗
║ 2. SINCRONIZAR CAPTURE PAGES FALTANTES                              ║
╠══════════════════════════════════════════════════════════════════════╣
║ uv run python manage.py sync_legacy_capture_pages --dry-run         ║
║ uv run python manage.py sync_legacy_capture_pages                   ║
╚══════════════════════════════════════════════════════════════════════╝
                              │
                              ▼
╔══════════════════════════════════════════════════════════════════════╗
║ 3. VALIDAR READINESS EM MODO ESTRITO                                ║
╠══════════════════════════════════════════════════════════════════════╣
║ uv run python manage.py check_capture_page_readiness --strict       ║
╚══════════════════════════════════════════════════════════════════════╝
                              │
                              ▼
╔══════════════════════════════════════════════════════════════════════╗
║ 4. DESLIGAR FALLBACK NO AMBIENTE                                    ║
╠══════════════════════════════════════════════════════════════════════╣
║ LANDING_JSON_FALLBACK_ENABLED=False                                 ║
╚══════════════════════════════════════════════════════════════════════╝
                              │
                              ▼
╔══════════════════════════════════════════════════════════════════════╗
║ 5. MONITORAR HEALTH DA OUTBOX E FLUXO DE CAPTURA                    ║
╠══════════════════════════════════════════════════════════════════════╣
║ uv run python manage.py check_lead_integration_health               ║
╚══════════════════════════════════════════════════════════════════════╝
```

## Staging

Sequencia recomendada em staging:

1. `uv run python manage.py check_capture_page_readiness`
2. `uv run python manage.py sync_legacy_capture_pages --dry-run`
3. `uv run python manage.py sync_legacy_capture_pages`
4. `uv run python manage.py check_capture_page_readiness --strict`
5. setar `LANDING_JSON_FALLBACK_ENABLED=False`
6. subir a aplicacao
7. validar manualmente:
   - `GET /inscrever-wh-rc-v3/`
   - `GET /checkout-wh-rc-v3/`
   - submit valido da captura
   - thank-you
   - outbox / health check

## Producao

Sequencia recomendada em producao:

1. rodar `check_capture_page_readiness --strict` antes do deploy
2. garantir backup/config freeze dos slugs ativos
3. aplicar `LANDING_JSON_FALLBACK_ENABLED=False`
4. deploy
5. monitorar:
   - `check_lead_integration_health`
   - admin da `LeadIntegrationOutbox`
   - admin da `LeadCaptureIdempotencyKey`

## Comandos Utiles

```bash
uv run python manage.py check_capture_page_readiness
uv run python manage.py check_capture_page_readiness --strict
uv run python manage.py sync_legacy_capture_pages --dry-run
uv run python manage.py sync_legacy_capture_pages
uv run python manage.py check_lead_integration_health
uv run python manage.py requeue_failed_lead_integrations --dry-run
```

## Criterio de Go/No-Go

**Go**

- `check_capture_page_readiness --strict` passa
- health da outbox esta saudavel
- slugs criticos de capture/checkout foram testados no ambiente

**No-Go**

- existe slug critico sem `CapturePage`
- health da outbox esta degradada
- staging ainda depende de fallback JSON para slugs ativos

## Referencias

- [Checklist de Hardening para Producao](./lead-capture-production-hardening.md)
- [Workflow Completo de Captura](./lead-capture-workflow.md)
- [Fluxo To-Be Ideal de Captura](./lead-capture-workflow-to-be.md)
