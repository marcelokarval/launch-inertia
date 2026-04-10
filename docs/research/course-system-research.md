# Pesquisa: Sistema de Cursos em Django

> Pesquisa realizada em 2026-02-14. Objetivo: avaliar todas as opções disponíveis no ecossistema Django para implementar um sistema de cursos/LMS, identificar a melhor abordagem para o stack Launch (Django 6 + Inertia.js v2 + React 19 + HeroUI v3).

---

## Sumario executivo

**Nao existe** nenhuma biblioteca Django reutilizavel, mantida e compativel com Django 6 + Inertia.js para sistema de cursos. O ecossistema e fragmentado entre:

1. Plataformas monoliticas gigantes (Open edX) que nao podem ser embeddadas
2. Poucos projetos headless com comunidades minusculas (Joanie, Smart Learn)
3. Dezenas de projetos abandonados baseados em templates Django

**Decisao**: Construir domain customizado `backend/src/apps/courses/` seguindo a arquitetura existente do projeto (BaseModel, service layer, PublicID), usando Joanie e Smart Learn como referencia arquitetural.

---

## Inventario completo

### Tier 1: Plataformas Enterprise

| Projeto | Stars | Ultima Atividade | Django | API-First | Licenca | PyPI |
|---|---|---|---|---|---|---|
| **Open edX Platform** | ~8.000 | Fev 2026 | 4.2-5.2 | Parcial (MFEs) | AGPL-3.0 | Nao (plataforma completa) |
| **RELATE** | 423 | Out 2025 | 4.x | Nao (templates) | MIT | Nao |

### Tier 2: Headless / API-First (mais relevantes)

| Projeto | Stars | Ultima Atividade | Django | API-First | Licenca | PyPI |
|---|---|---|---|---|---|---|
| **Joanie** (openfun) | 29 | Nov 2025 | 4.x (DRF) | **Sim** | MIT | Nao |
| **Smart Learn** | 27 | 2023-2024 | 4.0+ (DRF) | **Sim** | MIT | Nao |
| **openedx-learning** | 10 | Fev 2026 | 4.2, 5.2 | Sim | AGPL-3.0 | Sim (alpha) |

### Tier 3: Comunidade / Educacional

| Projeto | Stars | Ultima Atividade | Django | API-First | Licenca | Status |
|---|---|---|---|---|---|---|
| **Richie** (openfun) | ~300 | Nov 2025 | 4.x | Nao (DjangoCMS) | MIT | Catalogo, nao delivery |
| **adilmohak/django-lms** | 683 | Arquivado | Antigo | Nao | - | **Arquivado** |
| **django-quiz-app** | ~623 | **2015** | 1.5-1.8 | Nao | BSD | **Morto** |
| **DataTalksClub CMP** | 78 | Nov 2025 | 5.x | Parcial | - | Nicho (peer review) |
| **eLMS-SWE** | 113 | 2023-2024 | 4.0.4 | Nao | MIT | Demo |
| **AcademicsToday** | 222 | Stale | Antigo | Nao | Apache 2.0 | Abandonado |

### Tier 4: PyPI Packages

| Package | Versao | Ultima Atualizacao | Django | Status |
|---|---|---|---|---|
| **openedx-learning** | 0.32.0 | Fev 2026 | 4.2, 5.2 | Alpha (AGPL) |
| **edx-enterprise** | 6.6.4 | Fev 2026 | 4.2, 5.2 | Acoplado ao edX |
| **edx-django-utils** | 8.0.1 | Set 2025 | 4.2, 5.2 | Utilitarios edX |
| **richie** | 3.2.1 | 2024-2025 | 4.x | Requer DjangoCMS |
| **django-courses** | 1.0a0 | Set 2021 | 2.2-3.2 | Alpha abandonado |
| **pinax-lms-activities** | 0.18.0 | Mar 2016 | Generico | **Morto** |
| **django-classroom** | 0.1.6 | Desconhecido | Desconhecido | **Morto** |
| **django-danceschool** | 0.9.3 | Mai 2021 | 3.1.6+ | Nicho (danca) |
| **django-uocLTI** | 0.1.3 | Dez 2014 | Legacy | **Morto** |

---

## Analise detalhada dos candidatos relevantes

### 1. Open edX Platform

- **Repo**: [openedx/openedx-platform](https://github.com/openedx/openedx-platform)
- **Numeros**: ~8.000 stars, ~4.200 forks, 795 contribuidores
- **Stack**: Django 4.2-5.2, Python 3.11-3.12, MySQL, MongoDB, Memcached
- **Licenca**: AGPL-3.0
- **Producao**: Harvard, MIT, edX.org, milhares de instituicoes globais
- **Features**: LMS completo + CMS (Studio), course authoring, grading, certificados, xBlock plugins, analytics, foruns, mobile apps

**Por que NAO serve**:
- E uma plataforma completa com sua propria infraestrutura (MySQL, MongoDB, Memcached, Tutor orchestration)
- Nao pode ser `pip install` como library dentro de outro projeto Django
- Substituiria completamente a aplicacao, nao integra
- Requer infraestrutura propria (MySQL como DB primario, nao PostgreSQL)
- AGPL-3.0 e licenca viral

### 2. Joanie (openfun) — MELHOR REFERENCIA ARQUITETURAL

- **Repo**: [openfun/joanie](https://github.com/openfun/joanie)
- **Numeros**: ~29 stars, 2 forks, 19 contribuidores, 2.032 commits, 37 releases
- **Ultimo release**: v3.1.2 (Novembro 2025)
- **Stack**: Django + DRF, Python 3.x
- **Licenca**: MIT
- **Producao**: France Universite Numerique (FUN) — educacao superior francesa

**Features**:
- Enrollment e subscription management
- Processamento de pagamentos (multiplos providers)
- Geracao e entrega de certificados
- Sincronizacao de course runs
- Interface admin
- Deploy Docker com Terraform

**Pontos fortes**:
- Production-proven, MIT license
- Arquitetura API-only limpa (headless ERP)
- 725 PRs fechadas, ciclo de releases proper
- Pattern headless alinha com Inertia.js

**Pontos fracos**:
- Comunidade minuscula (29 stars)
- Documentacao esparsa
- Opinionado para sistema educacional frances
- **NAO cobre**: conteudo de aulas, quizzes, progresso (foco em enrollment/payment/certificates)

**O que extrair como referencia**:
- Enrollment flow e lifecycle
- Integracao com payment providers
- Geracao de certificados
- Padroes de API para course catalog

### 3. Smart Learn — BOA REFERENCIA DE API

- **Repo**: [chukaibejih/smart_learn](https://github.com/chukaibejih/smart_learn)
- **Numeros**: 27 stars, 19 forks, 12 contribuidores
- **Stack**: Django 4.0+, DRF, Python 3.10
- **Licenca**: MIT

**Features**:
- User auth, courses, modules, lessons
- Quizzes, enrollment, progress tracking
- Stripe payments (test mode)
- TDD com 80%+ coverage

**Pontos fortes**:
- API design limpo para course → module → lesson → quiz → progress
- Testes abrangentes
- Estrutura de endpoints bem organizada

**Pontos fracos**:
- WIP status, comunidade minuscula
- Sem multimedia
- Single payment provider
- English-only
- Analytics basico

**O que extrair como referencia**:
- Hierarquia Course → Module → Lesson → Quiz
- Endpoints de progress tracking
- Estrutura de API para enrollment

### 4. openedx-learning

- **Repo**: [openedx/openedx-learning](https://github.com/openedx/openedx-learning)
- **PyPI**: `openedx-learning` v0.32.0 (13 Fev 2026)
- **Numeros**: 10 stars, 19 forks, 30+ contribuidores
- **Stack**: Django 4.2/5.2, Python 3.11+
- **Licenca**: AGPL-3.0

**O que e**: Django apps extraidas do edx-platform representando conceitos core de aprendizado. Primeiro app e `authoring` para editar/publicar conteudo.

**Por que NAO serve**:
- AGPL-3.0 (licenca viral e restritiva)
- Alpha status (breaking changes constantes)
- Projetado para ecossistema Open edX, nao projetos Django genericos
- Nao suporta Django 6

**O que extrair como referencia** (somente patterns, nao copiar codigo AGPL):
- Versionamento e publicacao de conteudo
- Strict dependency isolation (`.importlinter`)
- Quatro tipos de identificadores (id, uuid, key, num)

### 5. RELATE

- **Repo**: [inducer/relate](https://github.com/inducer/relate)
- **Numeros**: 423 stars, 126 forks, 19 contribuidores
- **Licenca**: MIT
- **Producao**: University of Illinois

**Features**: YAML/Markdown course content, Git-based versioning, code execution, auto-grading, live quizzes, gradebook

**Por que NAO serve**: Template-based, acoplado ao proprio UI, projetado para departamentos CS academicos. Sem API layer.

### 6. Richie (openfun)

- **Repo**: [openfun/richie](https://github.com/openfun/richie)
- **Numeros**: ~300 stars, 93 forks, 35+ contribuidores, 3.719 commits
- **Stack**: DjangoCMS, Elasticsearch
- **Licenca**: MIT

**O que e**: CMS para portais educacionais. Catalogo de cursos, busca full-text, multi-lingue.

**Por que NAO serve**: Requer DjangoCMS como dependencia. E um catalogo/portal, nao sistema de delivery/progresso. Incompativel com Inertia.js.

### 7. DataTalksClub CMP

- **Repo**: [DataTalksClub/course-management-platform](https://github.com/DataTalksClub/course-management-platform)
- **Numeros**: 78 stars, 32 forks, Python 3.13, usa uv
- **Producao**: courses.datatalks.club

**O que extrair como referencia**:
- Homework submission pattern
- Peer review workflow
- Leaderboard implementation

---

## Matriz de compatibilidade com nosso stack

| Requisito | Open edX | Joanie | Smart Learn | openedx-learning |
|---|---|---|---|---|
| Django 6+ | Nao | Nao | Nao | Nao |
| Inertia.js (sem templates) | Nao | Sim (API) | Sim (API) | Sim |
| BaseModel/PublicID | Nao | Nao | Nao | Nao |
| Service layer pattern | Nao | Parcial | Parcial | Nao |
| MIT license | Nao (AGPL) | Sim | Sim | Nao (AGPL) |
| Production-ready | Sim | Sim (nicho) | Nao | Nao (alpha) |
| pip install como app | Nao | Nao | Nao | Sim (mas alpha) |

**Resultado**: Nenhum projeto atende todos os requisitos do nosso stack.

---

## Decisao: Build Custom

### Justificativa

1. **Nenhuma lib encaixa** — Nada suporta Django 6, Inertia.js, ou nossos patterns (BaseModel, PublicID, service layer)
2. **Dominio bem-definido** — Course/Module/Lesson/Quiz/Enrollment/Progress sao modelos conhecidos e documentados
3. **Infraestrutura ja existe** — dj-stripe (pagamentos), Celery (certificados, notificacoes), Redis (cache de progresso), PostgreSQL
4. **Controle total** — Sem dependencia de lib com AGPL ou comunidade morta
5. **Integracao nativa** — Service layer, middleware, Inertia props funcionam out-of-the-box

### Riscos de build custom

| Risco | Mitigacao |
|---|---|
| Reinventar a roda | Usar Joanie e Smart Learn como referencia arquitetural |
| Escopo crescer | Definir MVP com escopo fechado antes de implementar |
| Complexidade de quizzes | Comecar com quiz simples (multiple choice), expandir depois |
| Certificados PDF | Usar WeasyPrint ou ReportLab via Celery task |

### Referencia arquiteturais para implementacao

| Fonte | O que extrair |
|---|---|
| **Joanie** ([openfun/joanie](https://github.com/openfun/joanie)) | Enrollment lifecycle, payment integration, certificate generation, course run sync |
| **Smart Learn** ([chukaibejih/smart_learn](https://github.com/chukaibejih/smart_learn)) | Course → Module → Lesson → Quiz hierarquia, progress tracking endpoints, API structure |
| **DataTalksClub CMP** ([DataTalksClub/course-management-platform](https://github.com/DataTalksClub/course-management-platform)) | Homework submission, peer review, leaderboard patterns |
| **openedx-learning** ([openedx/openedx-learning](https://github.com/openedx/openedx-learning)) | Content versioning/publishing patterns (referencia apenas, NAO copiar codigo AGPL) |

---

## Estrutura proposta do domain

Seguindo a arquitetura existente do projeto (5-level Soft-DDD, BaseModel, service layer):

```
src/apps/courses/
├── models/
│   ├── __init__.py
│   ├── course.py          # Course (crs_), Module (mod_)
│   ├── lesson.py          # Lesson (les_), LessonContent (lct_)
│   ├── quiz.py            # Quiz (quz_), Question (qst_), Answer (ans_)
│   ├── enrollment.py      # Enrollment (enr_), Progress (prg_)
│   └── certificate.py     # Certificate (crt_)
├── services/
│   ├── __init__.py
│   ├── course_service.py        # CourseService(BaseService[Course])
│   ├── enrollment_service.py    # Enrollment + progress tracking
│   ├── quiz_service.py          # Grading, attempts, scoring
│   └── certificate_service.py   # PDF generation, validation
├── views.py               # Thin Inertia views
├── tasks.py               # Celery: PDF cert, email notifications
├── signals.py             # course_completed, quiz_passed, enrolled
├── urls.py
└── admin.py               # django-unfold admin
```

### Modelos core

```
Course (crs_)
├── Module (mod_)          # Agrupador logico de lições
│   ├── Lesson (les_)      # Aula individual
│   │   └── LessonContent (lct_)  # Video, texto, PDF, etc.
│   └── Quiz (quz_)        # Avaliacao do modulo
│       ├── Question (qst_) # Pergunta
│       └── Answer (ans_)   # Alternativa
├── Enrollment (enr_)      # Matricula do usuario
│   └── Progress (prg_)    # Progresso por lesson/quiz
└── Certificate (crt_)     # Certificado de conclusao
```

### Integracao com infra existente

| Necessidade | Solucao existente |
|---|---|
| Pagamentos | dj-stripe (ja configurado) |
| Tarefas async (certs, emails) | Celery (ja configurado) |
| Cache de progresso | Redis (ja configurado) |
| Email de notificacao | EmailService (ja existe) |
| Auth/ownership | @require_ownership + PublicID (ja existe) |
| Admin | django-unfold (ja configurado) |
| Frontend | Inertia.js + React + HeroUI (ja existe) |

---

## Fontes da pesquisa

- [Open edX Platform - GitHub](https://github.com/openedx/openedx-platform)
- [RELATE - GitHub](https://github.com/inducer/relate)
- [Joanie - Headless Education ERP - GitHub](https://github.com/openfun/joanie)
- [Richie - Education Portal CMS - GitHub](https://github.com/openfun/richie)
- [openedx-learning - PyPI](https://pypi.org/project/openedx-learning/)
- [openedx-learning - GitHub](https://github.com/openedx/openedx-learning)
- [Smart Learn - GitHub](https://github.com/chukaibejih/smart_learn)
- [adilmohak/django-lms - GitHub (Archived)](https://github.com/adilmohak/django-lms)
- [eLMS-SWE - GitHub](https://github.com/nz-m/eLMS-SWE)
- [DataTalksClub Course Management Platform - GitHub](https://github.com/DataTalksClub/course-management-platform)
- [AcademicsToday - GitHub](https://github.com/AcademicsToday/academicstoday-django)
- [django-quiz-app - PyPI](https://pypi.org/project/django-quiz-app/)
- [Django Packages - LMS Grid](https://djangopackages.org/grids/g/lms/)
- [edx-enterprise - PyPI](https://pypi.org/project/edx-enterprise/)
- [edx-django-utils - PyPI](https://pypi.org/project/edx-django-utils/)
- [richie - PyPI](https://pypi.org/project/richie/)
- [django-courses - PyPI](https://pypi.org/project/django-courses/)
- [Django Stars - LMS Development Guide](https://djangostars.com/blog/learning-management-system-development/)

---

*Pesquisa concluida em 2026-02-14. Decisao: build custom com referencia em Joanie e Smart Learn. Proximo passo: domain modeling detalhado em sessao dedicada.*
