# Accelerate Stack Team Matrix

> Objetivo: oferecer uma matriz operacional especifica para a stack recorrente de trabalho: Django + Inertia + React/Next.js + Tailwind + shadcn/HeroUI + Stripe + Celery + tracking.

---

## 1. Stack Base

Esta matriz assume uma stack recorrente com:

- Django
- Inertia.js
- React ou Next.js
- Tailwind CSS
- shadcn/ui ou HeroUI
- Stripe / billing
- Celery / filas / integrações async
- tracking / fingerprint / forms / onboarding

---

## 2. Matriz por Superfície

| Superficie | Persona líder | Skills obrigatórias | Sidecars típicos | Ferramentas |
|---|---|---|---|---|
| Django domain logic | Backend Implementer | `django-service-patterns`, `django-pro`, `security-patterns` | Backend Tester, Security Reviewer | Task(django-backend), pytest, manage.py check |
| Inertia contract | Data / Contract Steward | `django-inertia-integration`, `server-prop-governance`, `validation-governance` | Frontend Implementer | Read, Grep, apply_patch |
| React + shadcn | Frontend Implementer | `front-react-shadcn`, `frontend-boundary-governance`, `i18n-patterns` | Frontend Tester, Browser-Proof Auditor | Task(react-frontend-shadcn), build |
| React + HeroUI | Frontend Implementer | `react-frontend`, `i18n-patterns` | Frontend Tester | Task(react-frontend), build |
| Billing / Stripe | Backend Implementer | `stripe-integration`, `payment-integration`, `security-patterns` | Security Reviewer, Anti-Abuse Reviewer | backend task + focused tests |
| Tracking / fingerprint | Backend Implementer | `security-patterns`, tracking/domain references | Backend Tester, Data / Contract Steward | backend task + pytest |
| Celery / async integrations | Backend Implementer | `celery-tasks`, `security-patterns` | Performance / Observability Reviewer | backend task + celery-aware tests |
| User-facing runtime flow | Runtime/Product Reviewer | `product-runtime-review`, active stack skills | Browser-Proof Auditor, Anti-Abuse Reviewer | browser proof, targeted QA |

---

## 3. Team Profiles

### Condensado

```text
Master Integrator
Specification PM + Prompt Hardening Editor
Product Planner + Issue Architect
Backend Implementer OR Frontend Implementer
Backend Tester OR Frontend Tester
Closure / Forensic Reviewer
```

### Expandido

```text
Master Integrator
Specification PM
Product Planner
Implementation Designer
Backend Implementer
Frontend Implementer
Backend Tester
Security Reviewer
Closure / Forensic Reviewer
```

### Máximo

```text
Master Integrator
Specification PM
Prompt Hardening Editor
Product Planner
Issue Architect / Linear PM
Implementation Designer
Wireframe / Design Contract Extractor
Backend Implementer
Frontend Implementer
Delivery PM
Backend Tester
Frontend Tester
Browser-Proof Auditor
E2E Regression Engineer
Security Reviewer
Anti-Abuse Reviewer
Accessibility Reviewer
Performance / Observability Reviewer
Data / Contract Steward
Provider Boundary Auditor
Stack Constitution Auditor
Legacy Truth Analyst
Recovery Surface Reviewer
Migration Steward
Fixture / Test Data Steward
Experiment / Rollout Planner
Docs / Change Communicator
Release / Handoff Manager
Closure / Forensic Reviewer
```

---

## 4. Quem lidera cada tipo de trabalho

| Tipo de tarefa | Time recomendado | Observação |
|---|---|---|
| bug backend pequeno | condensado | backend implementer + tester bastam |
| bug user-facing sensível | expandido | incluir security/runtime reviewer |
| feature full-stack | expandido | baseline ideal |
| billing/auth/onboarding | expandido ou máximo | security e anti-abuse quase sempre entram |
| refactor estrutural | expandido | implementation designer é importante |
| rollout delicado / migração | máximo | migration + rollout + observability |
| redesign ou UI premium | expandido ou máximo | wireframe + browser proof |

---

## 5. Leitura mínima por perfil

### Sempre que o mestre estiver ativo

- `docs/process/accelerate-multi-agent-team-os.md`
- `docs/process/accelerate-subagent-handoff-templates.md`
- `~/.agents/skills/accelerate/SKILL.md`

### Se o trabalho for backend-heavy

- `django-service-patterns`
- `django-pro`
- `security-patterns`

### Se o trabalho for frontend-heavy

- `front-react-shadcn` ou `react-frontend`
- `frontend-boundary-governance`
- `i18n-patterns`

### Se o trabalho for user-facing sensível

- `product-runtime-review`
- `anti-abuse-review`
- `security-patterns`

---

## 6. Decisões de merge por stack

### Merges bons nesta stack

- `Backend Implementer` + `Data / Contract Steward`
  - quando o contrato for local e simples
- `Frontend Implementer` + `Wireframe Extractor`
  - quando a UI for pequena e sem conflito estrutural
- `Security Reviewer` + `Anti-Abuse Reviewer`
  - quando o fluxo sensível for curto e bem delimitado

### Merges ruins nesta stack

- `Backend Implementer` + `Backend Tester`
  - em billing/tracking/auth
- `Frontend Implementer` + `Frontend Tester`
  - em onboarding/forms/flows sensíveis
- `Implementer` + `Closure Reviewer`
  - quebra o fechamento forense

---

## 7. Exemplo de time para uma feature típica sua

### Caso: novo fluxo Django + Inertia + React + shadcn + Stripe

```text
Master Integrator
Specification PM
Product Planner
Backend Implementer
Frontend Implementer (shadcn)
Backend Tester
Security Reviewer
Closure / Forensic Reviewer
```

Se houver browser sensitivity:

```text
+ Browser-Proof Auditor
```

Se houver rollout delicado:

```text
+ Experiment / Rollout Planner
+ Performance / Observability Reviewer
```

---

## 8. Regra de Evolução

Sempre que surgir nova necessidade recorrente, decidir:

1. **nova skill?**
   - quando a persona atual continua suficiente, mas precisa de mais contexto

2. **nova referencia `.md`?**
   - quando a regra e durável e precisa ser lembrada por múltiplas execuções

3. **nova persona?**
   - quando a responsabilidade, a prova e o handoff sao próprios e recorrentes

4. **novo subagente concreto?**
   - quando o ganho operacional de paralelismo e especialização justificar
