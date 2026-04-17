# Accelerate Subagent Handoff Templates

> Objetivo: fornecer templates prontos de spawn/handoff para o time multi-agent baseado em `accelerate`, com scopes delimitados, validacao e formato de retorno padrao.

---

## 1. Regra Geral

Todo subagente deve receber um pacote delimitado e devolver um `Subagent Return Packet`.

Template de retorno padrao:

```text
Subagent Return Packet

- scope handled: <escopo>
- files changed / surfaces inspected: <...>
- evidence used: <...>
- tests / verification run: <...>
- self-review: <...>
- self-forensic review: <...>
- unresolved risks: <...>
- recommendation: <done|partial|follow-up|blocked>
```

---

## 2. Spawn Packet Base

Use este template como base para qualquer subagente:

```text
Subagent Handoff Packet

- role: <persona>
- objective: <objetivo claro>
- repo context: <stack e area do repo>
- write scope:
  - <arquivo ou pasta permitida>
- forbidden scope:
  - <arquivos/pastas proibidas>
- required validation:
  - <comandos / checks>
- escalation path:
  - <quando devolver blocker ao mestre>
- expected completion format:
  - Subagent Return Packet
```

---

## 3. Template — Backend Implementer

```text
Subagent Handoff Packet

- role: Backend Implementer
- objective: implementar a fatia backend da tarefa sem alterar o frontend
- repo context: backend/src, Django + Inertia + services + tasks
- write scope:
  - backend/src/apps/<domain>/...
  - backend/src/core/... (somente se explicitamente permitido)
- forbidden scope:
  - frontends/**
  - docs/**
  - backend/src/apps/<outro-domain>/** sem autorizacao explicita
- mandatory skills:
  - django-service-patterns
  - django-pro
  - security-patterns
- required validation:
  - cd backend && uv run python manage.py check
  - pytest focado da fatia alterada
- escalation path:
  - se o contrato exigir mudanca de props/frontend, retornar blocker em vez de improvisar
- expected completion format:
  - Subagent Return Packet
```

### Quando usar

- models
- services
- views
- urls
- tasks
- forms
- tracking/backend contracts

---

## 4. Template — Frontend Implementer (shadcn/Tailwind)

```text
Subagent Handoff Packet

- role: Frontend Implementer
- objective: implementar a fatia frontend sem alterar backend fora do contrato acordado
- repo context: frontends/*, React/Next/Inertia, Tailwind, shadcn/HeroUI
- write scope:
  - frontends/<app>/src/**
- forbidden scope:
  - backend/**
  - docs/**
- mandatory skills:
  - front-react-shadcn (ou react-frontend quando for HeroUI)
  - frontend-boundary-governance
  - i18n-patterns
- required validation:
  - npm run build --workspace @launch/<app>
  - type-check quando aplicavel
- escalation path:
  - se faltar prop/backend contract, devolver blocker ao mestre
- expected completion format:
  - Subagent Return Packet
```

### Quando usar

- forms
- pages
- layouts
- estados visuais
- i18n/locales
- integrações de componentes

---

## 5. Template — Backend Tester

```text
Subagent Handoff Packet

- role: Backend Tester
- objective: adicionar ou ajustar cobertura da fatia backend alterada
- repo context: backend/src/tests, pytest, factories, runtime contracts
- write scope:
  - backend/src/tests/**
- forbidden scope:
  - frontends/**
  - docs/**
  - backend/src/apps/** (a menos que o mestre permita um ajuste de teste auxiliar)
- mandatory skills:
  - python-testing
  - backend stack skills relevantes
- required validation:
  - pytest focado
  - sinalizar gaps de cobertura honestamente
- escalation path:
  - se o codigo nao for testavel sem mudar implementacao, devolver follow-up tecnico claro
- expected completion format:
  - Subagent Return Packet
```

### Quando usar

- regressao backend
- contratos de service
- captura, billing, tracking, auth

---

## 6. Template — Security Reviewer

```text
Subagent Handoff Packet

- role: Security Reviewer
- objective: revisar riscos de auth, ownership, abuse, billing, secrets e boundary drift
- repo context: backend + frontend + runtime contracts
- write scope:
  - read-only por padrao
- forbidden scope:
  - escrita em codigo sem autorizacao do mestre
- mandatory skills:
  - security-patterns
  - anti-abuse-review quando a superficie for user-facing
- required validation:
  - apontar findings com severidade e arquivo/linha quando possivel
- escalation path:
  - se houver risco material, recommendation=blocked ou partial
- expected completion format:
  - Subagent Return Packet
```

### Quando usar

- auth
- onboarding
- billing
- capture forms
- exports/imports
- tracking com PII

---

## 7. Template — Explore / Recon

```text
Subagent Handoff Packet

- role: Explorer / Recon
- objective: mapear codigo, arquivos, contratos, rotas e testes afetados
- repo context: leitura rapida do workspace
- write scope:
  - nenhuma (read-only)
- forbidden scope:
  - qualquer escrita
- mandatory skills:
  - accelerate (entry)
- required validation:
  - devolver mapa de impacto com arquivos e riscos
- escalation path:
  - se a tarefa estiver subespecificada, explicitar os unknowns
- expected completion format:
  - Subagent Return Packet
```

---

## 8. Template — Browser-Proof Auditor

```text
Subagent Handoff Packet

- role: Browser-Proof Auditor
- objective: validar o comportamento real do fluxo em navegador antes de persistir cenarios automatizados
- repo context: user-facing surfaces
- write scope:
  - read-only por padrao
- forbidden scope:
  - backend/frontend mutation sem autorizacao explicita
- mandatory skills:
  - product-runtime-review
- required validation:
  - packet com intensidade: sampled | targeted | broad sweep | full route-family audit
- escalation path:
  - se o fluxo nao estiver entendivel, devolver blocker para nao automatizar cedo demais
- expected completion format:
  - Browser-Proof Packet / Subagent Return Packet
```

---

## 9. Template — Docs / Change Communicator

```text
Subagent Handoff Packet

- role: Docs / Change Communicator
- objective: atualizar docs vivas e handoff notes da fatia implementada
- repo context: docs/, frontends/docusaurus/docs/
- write scope:
  - docs/**
  - frontends/docusaurus/docs/**
- forbidden scope:
  - backend/**
  - frontends/** (codigo)
- mandatory skills:
  - accelerate (entry)
- required validation:
  - links internos consistentes
  - docs refletindo estado atual, nao estado planejado
- escalation path:
  - se houver divergencia entre codigo e docs, devolver como finding explicito
- expected completion format:
  - Subagent Return Packet
```

---

## 10. Regras de Uso

### Quando spawnar

- se ha uma fatia backend independente
- se ha uma fatia frontend independente
- se ha necessidade de teste/review sidecar

### Quando nao spawnar

- quando dois agentes precisariam editar o mesmo arquivo
- quando o contrato ainda nao foi decidido
- quando o trabalho e pequeno demais para justificar coordenacao

### Regra final

O mestre sempre continua dono de:

- plano global
- reconciliacao de contratos
- verificacao integrada
- fechamento final
