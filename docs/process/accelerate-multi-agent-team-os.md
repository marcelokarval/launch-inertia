# Accelerate Multi-Agent Team OS

> Objetivo: definir um modelo prático de equipe multi-agent no OpenCode usando `accelerate` como raiz de orquestração, com personas explícitas, handoffs, sincronização e contratos de validação.

---

## 1. Princípio

Aqui, multi-agent não significa vários agentes livres mexendo ao mesmo tempo sem coordenação.

Significa:

1. `accelerate` classifica e orquestra o trabalho como sistema operacional da equipe
2. o agente mestre define o plano, as fronteiras e os gates
3. subagentes recebem fatias delimitadas
4. resultados voltam com evidência e auto-review
5. o mestre reconcilia tudo e valida o resultado integrado

---

## 2. Branch Entry Packet Padrão

```text
Branch Entry Packet

- classification: non-trivial
- active branch: orchestrated engineering execution
- active persona: Master Integrator
- active stack: Django + Inertia + React/Next.js + Tailwind/shadcn + async integrations
- active skills: accelerate, subagent-governance, ascii-wireframe
- active ADRs / references:
  - ~/.agents/skills/accelerate/SKILL.md
  - ~/.agents/skills/accelerate/references/persona-model.md
  - ~/.agents/skills/accelerate/references/team-operating-model.md
  - ~/.agents/skills/accelerate/references/runtime-packet-templates.md
  - ~/.claude/skills/subagent-governance/SKILL.md
- gate ledger: classification=passed, branch=passed, delegation-bounds=required, integration-review=open
- phase / SDLC: Frame+Load+Classify / Design
- persona handoff artifact: Team Execution Packet
- mandatory gates: bounded scopes, integration revalidation, final closure review
- required artifacts: orchestration diagram, role map, return packet contract
- closure blockers: integrated verification, cross-slice contract check, final forensic review
- QA / proof lane: proportional to task
- issue stack status: optional unless issue-driven run is required
- browser-proof intensity: task-dependent
- persistent E2E status: n/a by default
- single-threaded exception: n/a
```

---

## 3. Equipe Base

### Mestre

- **Persona**: `Master Integrator`
- **Função**:
  - classifica o trabalho via `accelerate`
  - ativa personas e skills
  - decide paralelismo
  - define write scopes
  - integra resultados
  - faz a revisão final

### Núcleo de trabalho

1. **Specification PM**
   - clarifica objetivo, acceptance, non-goals

2. **Product Planner**
   - quebra em slices e dependências

3. **Implementation Designer**
   - transforma o plano em contratos de execução

4. **Backend Implementer**
   - implementa Django/models/services/views/tasks/contracts

5. **Frontend Implementer**
   - implementa React/Inertia/Next.js/pages/layouts/forms/states

6. **Backend Tester**
   - cobre pytest/integration/regression/fixtures

7. **Security Reviewer**
   - audita auth, abuse, IDOR, billing, data boundaries

8. **Closure / Forensic Reviewer**
   - reconcilia pedido vs entrega, promessa vs evidência

---

## 4. Mapeamento Para Subagentes Reais no OpenCode

```text
Persona                         -> OpenCode / available agent

Backend Implementer             -> Task(subagent_type="django-backend")
Frontend Implementer (HeroUI)   -> Task(subagent_type="react-frontend")
Frontend Implementer (shadcn)   -> Task(subagent_type="react-frontend-shadcn")
Backend Tester                  -> Task(subagent_type="test-engineer")
Security Reviewer               -> Task(subagent_type="security-review")
Explorer / Recon                -> Task(subagent_type="explore")
General planner / sidecar       -> Task(subagent_type="general")
```

Personas como `Specification PM`, `Product Planner`, `Implementation Designer` e `Master Integrator` normalmente são exercidas pelo agente mestre usando `accelerate`, não necessariamente por subagentes separados.

---

## 5. Wireframe ASCII — Orquestração da Equipe

```text
╔════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                          ACCELERATE MULTI-AGENT TEAM OS                                           ║
╠══════════════════════╦══════════════════════╦══════════════════════╦══════════════════════════════╣
║ FRAME / PLAN         ║ IMPLEMENT            ║ VERIFY               ║ CLOSE                        ║
╠══════════════════════╬══════════════════════╬══════════════════════╬══════════════════════════════╣
║ Master Integrator    ║ Backend Implementer  ║ Backend Tester       ║ Closure / Forensic Reviewer  ║
║ [1]                  ║ [4]                  ║ [6]                  ║ [8]                          ║
║ accelerate root      ║ django-backend       ║ test-engineer        ║ req vs impl                  ║
║ classification       ║ models/services      ║ pytest/regression    ║ residual risk                ║
║ gating               ║ views/tasks          ║ fixtures             ║ evidence check               ║
║                      ║                      ║                      ║                              ║
║ Specification PM     ║ Frontend Implementer ║ Security Reviewer    ║ Master Integrator            ║
║ [2]                  ║ [5]                  ║ [7]                  ║ [9]                          ║
║ actor/goal/accept    ║ react-frontend*      ║ security-review      ║ integration authority        ║
║                      ║ UI/forms/states      ║ auth/billing/abuse   ║ final decision               ║
║ Product Planner [3]  ║                      ║                      ║                              ║
║ slices/deps/owners   ║                      ║                      ║                              ║
╠══════════════════════╩══════════════════════╩══════════════════════╩══════════════════════════════╣
║ Parallel sidecars on demand: explore, general, Browser-Proof Auditor, Docs / Change Communicator ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════╝
```

**Legenda**

| # | Papel | Observação |
|---|---|---|
| 1 | Master Integrator | papel obrigatório e sempre ativo |
| 2 | Specification PM | entra quando há ambiguidade de intenção/escopo |
| 3 | Product Planner | entra quando precisa fatiar ou ordenar o trabalho |
| 4 | Backend Implementer | fatia backend bounded |
| 5 | Frontend Implementer | `react-frontend` ou `react-frontend-shadcn` conforme stack |
| 6 | Backend Tester | cobertura e regressão |
| 7 | Security Reviewer | sidecar de risco, não “opcional de luxo” |
| 8 | Closure Reviewer | confere coerência e completude |
| 9 | Master Integrator | continua dono da reconciliação final |

---

## 6. Wireframe ASCII — Sincronização Entre Agentes

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ RAW TASK / USER GOAL                                                                       │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ accelerate                                                                          [root] │
│ - classifica                                                                         [A]   │
│ - ativa personas                                                                     [B]   │
│ - define slices                                                                      [C]   │
│ - define write scopes                                                                [D]   │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
┌──────────────────────────────┐            ┌──────────────────────────────┐
│ Backend slice                │            │ Frontend slice               │
│ Task(django-backend)         │            │ Task(react-frontend*)        │
│ - exact files                │            │ - exact files                │
│ - forbidden scope            │            │ - forbidden scope            │
│ - validation contract        │            │ - validation contract        │
└──────────────────────────────┘            └──────────────────────────────┘
                    │                                   │
                    └─────────────────┬─────────────────┘
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ Verification sidecars                                                                     │
│ - Task(test-engineer)                                                                     │
│ - Task(security-review)                                                                   │
│ - optional Task(explore/general)                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ Master Integrator                                                                          │
│ - reads child return packets                                                               │
│ - checks cross-slice contracts                                                             │
│ - runs final proof                                                                         │
│ - decides done / partial / follow-up                                                       │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Regra de Sincronização

Para a equipe funcionar como uma equipe de verdade, use estas regras.

### 7.1 Uma autoridade final

- o mestre sempre decide o plano global
- o mestre sempre integra os resultados
- subagentes não fecham o trabalho sozinhos

### 7.2 Fatias delimitadas

Cada subagente recebe:

- objetivo
- escopo exato
- arquivos permitidos
- arquivos proibidos
- validação obrigatória
- formato de retorno

### 7.3 Paralelismo só quando as fatias não colidem

Pode paralelizar quando:

- backend e frontend mexem em camadas diferentes
- review/teste é sidecar read-only
- exploração é separável da implementação

Não paralelizar quando:

- dois agentes vão editar o mesmo arquivo
- a decisão arquitetural ainda não foi fechada
- o contrato entre camadas ainda está indefinido

### 7.4 Retorno padronizado do subagente

Todo subagente deve devolver algo no formato:

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

## 8. Time Base Para a Sua Stack

Para projetos com:

- Django
- Inertia
- React ou Next.js
- Tailwind
- shadcn ou HeroUI
- Stripe
- Celery
- tracking / forms / billing / auth

eu recomendo este time base:

### Time mínimo

1. **Master Integrator**
2. **Backend Implementer**
3. **Frontend Implementer**
4. **Backend Tester**

### Time padrão

1. Master Integrator
2. Specification PM
3. Product Planner
4. Backend Implementer
5. Frontend Implementer
6. Backend Tester
7. Security Reviewer
8. Closure / Forensic Reviewer

### Time expandido

Adicionar sob demanda:

- Browser-Proof Auditor
- Accessibility Reviewer
- Performance / Observability Reviewer
- Docs / Change Communicator
- Migration Steward

### Time maximo

Para uma operacao madura, multi-projeto, centrada em Django + Inertia + React/Next.js + shadcn/Tailwind + billing + tracking + async integrations, o time maximo sugerido e este:

1. Master Integrator
2. Specification PM
3. Prompt Hardening Editor
4. Product Planner
5. Issue Architect / Linear PM
6. Implementation Designer
7. Wireframe / Design Contract Extractor
8. Backend Implementer
9. Frontend Implementer
10. Delivery PM
11. Backend Tester
12. Frontend Tester
13. Browser-Proof Auditor
14. E2E Regression Engineer
15. Security Reviewer
16. Anti-Abuse Reviewer
17. Accessibility Reviewer
18. Performance / Observability Reviewer
19. Data / Contract Steward
20. Provider Boundary Auditor
21. Stack Constitution Auditor
22. Legacy Truth Analyst
23. Recovery Surface Reviewer
24. Migration Steward
25. Fixture / Test Data Steward
26. Experiment / Rollout Planner
27. Docs / Change Communicator
28. Release / Handoff Manager
29. Closure / Forensic Reviewer

Esse nao e o time para toda tarefa. E o catalogo maximo de papeis disponiveis quando a stack e o risco justificam alta especializacao.

---

## 8.1 Wireframe ASCII — Time Maximo

```text
╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                 ACCELERATE — TIME MAXIMO                                                           ║
╠══════════════════════╦══════════════════════╦══════════════════════╦══════════════════════╦══════════════════════╣
║ ENTRY / SHAPING      ║ ISSUE / PLANNING     ║ IMPLEMENTATION       ║ QA / PROOF           ║ GOVERN / CLOSE       ║
╠══════════════════════╬══════════════════════╬══════════════════════╬══════════════════════╬══════════════════════╣
║ Specification PM     ║ Issue Architect /    ║ Backend Implementer  ║ Backend Tester       ║ Governance Auditor   ║
║ Prompt Hardening     ║ Linear PM            ║ Frontend Implementer ║ Frontend Tester      ║ Stack Constitution   ║
║ Product Planner      ║ Implementation       ║ Wireframe Extractor  ║ Browser-Proof        ║ Auditor              ║
║                      ║ Designer             ║ Delivery PM          ║ E2E Regression       ║ Security Reviewer    ║
║                      ║ Experiment / Rollout ║                      ║                      ║ Anti-Abuse Reviewer  ║
║                      ║ Planner              ║                      ║                      ║ Accessibility Rev.   ║
║                      ║                      ║                      ║                      ║ Perf/Observability   ║
║                      ║                      ║                      ║                      ║ Data/Contract Steward║
║                      ║                      ║                      ║                      ║ Provider Boundary    ║
║                      ║                      ║                      ║                      ║ Closure Reviewer     ║
║                      ║                      ║                      ║                      ║ Release/Handoff Mgr  ║
║                      ║                      ║                      ║                      ║ Master Integrator    ║
╚══════════════════════╩══════════════════════╩══════════════════════╩══════════════════════╩══════════════════════╝
```

---

## 9. Condensacao e Merge de Personas

Nem toda execucao precisa de 20+ papeis separados. A forma correta de "ter o time maximo" e possuir o catalogo completo, mas condensar papeis por risco, scope e custo de integracao.

### Regra de condensacao

- **merge permitido** quando os outputs sao proximos e a perda de independencia nao compromete a qualidade
- **merge proibido** quando um papel deveria revisar ou contestar o outro

### Merges recomendados

| Persona final | Pode absorver | Quando |
|---|---|---|
| `Specification PM` | `Prompt Hardening Editor` | quando a ambiguidade e moderada e o mesmo owner consegue fechar `Prompt A -> Prompt B` sem perda |
| `Product Planner` | `Issue Architect / Linear PM` | quando a tarefa nao exige grande governanca de issue separada |
| `Implementation Designer` | `Wireframe / Design Contract Extractor` | quando a incerteza estrutural e moderada e o design contract cabe no mesmo pacote |
| `Backend Implementer` | `Data / Contract Steward` | quando o contrato e local ao backend e nao exige auditoria independente |
| `Frontend Implementer` | `Wireframe / Design Contract Extractor` | quando a UI e simples e o contrato visual nao precisa de sidecar dedicado |
| `Backend Tester` | `Fixture / Test Data Steward` | quando a criticidade dos dados de teste e limitada |
| `Security Reviewer` | `Anti-Abuse Reviewer` | quando a superficie sensivel e pequena e o mesmo revisor consegue cobrir auth/abuse |
| `Governance Auditor` | `Stack Constitution Auditor` | quase sempre em auditorias menores |
| `Closure / Forensic Reviewer` | `Release / Handoff Manager` | quando o fechamento e local e sem cerimonia de release complexa |

### Merges que exigem cuidado

| Merge | Risco |
|---|---|
| `Backend Implementer` + `Backend Tester` | reduz independencia da prova |
| `Frontend Implementer` + `Frontend Tester` | tende a mascarar regressao visual/estado |
| `Implementer` + `Security Reviewer` | risco de autojustificativa |
| `Implementer` + `Closure Reviewer` | quebra a revisao forense |

### Merges proibidos por padrao

- `Master Integrator` + `Closure / Forensic Reviewer` como unico papel de uma run grande
- `Implementer` + `Closure / Forensic Reviewer`
- `Implementer` + `Security Reviewer` em auth/billing/abuse-sensitive branches

---

## 10. Time Condensado, Expandido e Maximo

### Time condensado

Use em tarefas pequenas, mas ainda nao triviais.

```text
1. Master Integrator
2. Specification PM + Prompt Hardening Editor
3. Product Planner + Issue Architect
4. Backend Implementer ou Frontend Implementer
5. Backend Tester ou Frontend Tester
6. Closure / Forensic Reviewer
```

### Time expandido

Use como padrao para feature full-stack.

```text
1. Master Integrator
2. Specification PM
3. Product Planner
4. Implementation Designer
5. Backend Implementer
6. Frontend Implementer
7. Backend Tester
8. Security Reviewer
9. Closure / Forensic Reviewer
```

### Time maximo

Use quando houver combinacao de:

- multiplas camadas
- risco de seguranca/abuse
- rollout delicado
- browser proof
- provider/runtime boundaries
- necessidade de docs e handoff forte

Nessa situacao, use o catalogo maximo e condense apenas os papeis que realmente nao precisarem de independencia.

---

## 11. Capacidade por Persona

### Tabela executiva

| Persona | Capacidade central | Tipo de saida |
|---|---|---|
| `Specification PM` | clarificar problema, acceptance, non-goals | `Specification Handoff Packet` |
| `Prompt Hardening Editor` | converter prompt fraco em prompt executavel | `Prompt Hardening Packet` |
| `Product Planner` | quebrar escopo, dependencias e rollout | `Planning Handoff Packet` |
| `Issue Architect / Linear PM` | issue tree, metadata, hierarchy | issue packet |
| `Implementation Designer` | fatiar execucao e contratos | `Implementation Design Packet` |
| `Wireframe / Design Contract Extractor` | transformar intencao em artefato visual | design packet |
| `Backend Implementer` | alterar backend com ownership claro | backend implementation packet |
| `Frontend Implementer` | alterar frontend com boundary claro | frontend implementation packet |
| `Delivery PM` | checkpoints e pacing | `Delivery Packet` |
| `Backend Tester` | prova backend, query, runtime | `QA / Proof Packet` |
| `Frontend Tester` | prova TS/UI/i18n | `QA / Proof Packet` |
| `Browser-Proof Auditor` | verdade de navegador | `Browser-Proof Packet` |
| `E2E Regression Engineer` | persistencia de fluxo | regression packet |
| `Security Reviewer` | auth/ownership/secret/race review | security packet |
| `Anti-Abuse Reviewer` | spam/abuse/replay/enum review | anti-abuse packet |
| `Accessibility Reviewer` | semantica, teclado, foco | accessibility packet |
| `Performance / Observability Reviewer` | N+1, throughput, telemetry | perf packet |
| `Data / Contract Steward` | DTOs, props, truth ownership | contract packet |
| `Provider Boundary Auditor` | integrações externas, transport, provider contracts | provider packet |
| `Legacy Truth Analyst` | verdade herdada de sistemas antigos | adaptation packet |
| `Recovery Surface Reviewer` | fluxos especiais e estados isolados | recovery packet |
| `Migration Steward` | schema/data rollout | migration packet |
| `Fixture / Test Data Steward` | realismo de fixtures | fixture packet |
| `Experiment / Rollout Planner` | flags, rollout, safe sequencing | rollout packet |
| `Docs / Change Communicator` | docs vivas e handoff | docs packet |
| `Release / Handoff Manager` | release readiness | release packet |
| `Closure / Forensic Reviewer` | req vs impl, promised vs delivered | `Closure Packet` |
| `Master Integrator` | julgamento global final | `Master Revalidation Checklist` |

---

## 12. Leitura Obrigatoria por Papel

### Leitura base do mestre

Sempre que estiver operando o time:

- `~/.agents/skills/accelerate/SKILL.md`
- `~/.agents/skills/accelerate/references/persona-model.md`
- `~/.agents/skills/accelerate/references/team-operating-model.md`
- `~/.agents/skills/accelerate/references/runtime-packet-templates.md`
- `~/.claude/skills/subagent-governance/SKILL.md`

### Leitura obrigatoria por papel ativo

| Persona | Leitura obrigatória |
|---|---|
| `Specification PM` | `prompt-hardening`, `architecture`, `persona-model.md` |
| `Product Planner` | `linear-pm`, `linear-implementation-planner` |
| `Implementation Designer` | `planning-with-files`, `executing-plans` |
| `Wireframe / Design Contract Extractor` | `ascii-wireframe` |
| `Backend Implementer` | `django-service-patterns`, `django-pro`, `security-patterns` |
| `Frontend Implementer` | `front-react-shadcn`, `frontend-boundary-governance`, `i18n-patterns` |
| `Backend Tester` | `python-testing`, backend stack skills |
| `Frontend Tester` | frontend stack skills, `i18n-patterns` |
| `Browser-Proof Auditor` | `product-runtime-review`, active stack skills |
| `Security Reviewer` | `security-patterns` + branch-specific security skills |
| `Anti-Abuse Reviewer` | `anti-abuse-review` |
| `Governance Auditor` | `governance-audit`, `p4y-stack-constitution` |
| `Closure / Forensic Reviewer` | `verification-before-completion` |

---

## 13. Ferramentas por Papel

| Persona | Ferramentas principais |
|---|---|
| Mestre | `Task`, `Read`, `Glob`, `Grep`, `Bash`, skills |
| Backend Implementer | `Task(django-backend)` ou edição direta, `Read`, `Grep`, `apply_patch`, `Bash` |
| Frontend Implementer | `Task(react-frontend*)`, `Read`, `Grep`, `apply_patch`, `Bash` |
| Tester | `Task(test-engineer)` ou `Bash` para suites focadas |
| Security Reviewer | `Task(security-review)`, `Read`, `Grep` |
| Browser-Proof Auditor | browser tooling / Playwright / DevTools when available |
| Docs / Change Communicator | `Read`, `apply_patch` |

Regra prática:

- subagentes de implementação recebem write scope delimitado
- subagentes de review/auditoria preferem read-only scope
- o mestre sempre faz a reconciliação final, mesmo quando todos os subagentes “passam”

---

## 14. Como Evoluir o Time

A sua ideia de “ir adicionando personas, capacidades e arquivos de orientação conforme as necessidades surjam” é compatível com o modelo do `accelerate`.

### Forma correta de evoluir

1. detectar repetição de um tipo de trabalho
2. identificar qual persona do `accelerate` já cobre isso
3. decidir se:
   - basta adicionar skill/referência a essa persona
   - ou se vale materializar um subagente concreto
4. adicionar:
   - skill específica
   - referência `.md`
   - packet de saída esperado
   - regra de quando ativar

### Quando criar nova persona

Crie uma persona nova apenas quando houver:

- responsabilidade recorrente
- pacote de leitura obrigatório próprio
- tipo de prova próprio
- handoff próprio
- valor claro em mantê-la separada de outra persona

### Quando só expandir uma persona existente

Expanda a persona atual quando a nova necessidade for apenas:

- um novo skill obrigatório
- um novo runbook
- um novo tipo de checklist
- uma nova referência de domínio

Exemplo:

- se surgirem muitos fluxos `Django + Inertia + Stripe + billing recovery`, talvez não precise nova persona; basta reforçar `Backend Implementer` + `Recovery Surface Reviewer` + `Security Reviewer`

---

## 15. Regra de Ouro

Tenha sempre:

- **catálogo máximo** de papéis
- **condensação inteligente** na execução
- **independência preservada** nos papéis de revisão
- **mestre invariável** como integrador final

Essa é a forma de ter um “time máximo” reutilizável sem cair em caos operacional.

---

## 9. Playbooks de Execução

### 9.1 Feature full-stack

```text
Master Integrator
  -> explore (mapa de impacto)
  -> django-backend (implementa contrato)
  -> react-frontend* (consome contrato)
  -> test-engineer (regressão)
  -> security-review (se auth/billing/input sensível)
  -> integração final + validação
```

### 9.2 Bug difícil / regressão

```text
Master Integrator
  -> explore (reprodução/localização)
  -> django-backend OU react-frontend* (fix)
  -> test-engineer (repro test)
  -> closure review
```

### 9.3 Refactor estrutural

```text
Master Integrator
  -> Product Planner
  -> Implementation Designer
  -> backend/frontend implementers em slices
  -> test-engineer
  -> governance/security sidecar se houver risco de boundary drift
```

---

## 10. Template de Delegação

Use este template ao spawnar um subagente:

```text
Subagent Handoff Packet

- role: Backend Implementer
- objective: implementar endpoint e service para X
- repo context: Django + Inertia + React stack
- write scope:
  - backend/src/apps/foo/views.py
  - backend/src/apps/foo/services.py
- forbidden scope:
  - frontends/*
  - docs/*
- required validation:
  - pytest arquivo X
  - manage.py check if needed
- escalation path:
  - se precisar mudar contrato frontend, devolver como blocker
- expected completion format:
  - Subagent Return Packet
```

---

## 11. Regra Final

O sistema multi-agent só funciona bem se `accelerate` permanecer como raiz visível.

Ou seja:

- classificação explícita
- personas explícitas
- fatias explícitas
- handoffs explícitos
- validação explícita
- integração final explícita

Sem isso, você não tem equipe. Você tem apenas múltiplas execuções concorrentes.
