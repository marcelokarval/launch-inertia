# Local Development

Todos os comandos abaixo devem ser executados a partir da raiz do projeto.

================================================================================
 ATALHOS (make) - Rodar da raiz do projeto
================================================================================

 make dev              Django (8844) + Dashboard Vite (3344) em paralelo
 make dev-full         Django + Dashboard + Landing + Celery (tudo)
 make dev-all          Django + Dashboard + Celery (sem landing)
 make dev-back         Apenas Django (porta 8844)
 make dev-dashboard    Apenas Dashboard Vite (porta 3344)
 make dev-landing      Apenas Landing Vite (porta 3345)

================================================================================
 COMANDOS INDIVIDUAIS (terminais separados)
================================================================================

 Se preferir rodar cada servico em um terminal separado:

  TERMINAL 1 - Django backend (porta 8844):
    Diretorio: launch-inertia/backend/
    Comando:   cd backend && uv run python manage.py runserver 8844

 TERMINAL 2 - Dashboard Vite dev server (porta 3344):
   Diretorio: launch-inertia/frontends/dashboard/
   Comando:   npm run dev --prefix frontends/dashboard/

 TERMINAL 3 - Landing Vite dev server (porta 3345):
   Diretorio: launch-inertia/frontends/landing/
   Comando:   npm run dev --prefix frontends/landing/

  TERMINAL 4 - Celery worker (opcional, para tarefas async):
    Diretorio: launch-inertia/backend/
    Comando:   cd backend && uv run celery -A infrastructure.tasks.celery worker -l info -Q celery,default --concurrency=2

  TERMINAL 5 - Celery beat (opcional, tarefas agendadas):
    Diretorio: launch-inertia/backend/
    Comando:   cd backend && uv run celery -A infrastructure.tasks.celery beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

================================================================================
 URLs PARA VISUALIZAR
================================================================================

 Dashboard (requer login):
   http://localhost:8844/app/
   http://localhost:8844/app/login/
   http://localhost:8844/app/register/

  Landing (publico):
    http://localhost:8844/
    http://localhost:8844/suporte/
    http://localhost:8844/terms/
    http://localhost:8844/privacy/
    http://localhost:8844/inscrever-wh-rc-v3/

  Admin (django-unfold):
    http://localhost:8844/admin/

  Nota: As paginas de captura (ex: /inscrever-wh-rc-v3/) e checkout
  dependem de campanhas configuradas no banco de dados.

================================================================================
 PORTAS
================================================================================

 8844  -  Django dev server
 3344  -  Dashboard Vite HMR (Hot Module Replacement)
 3345  -  Landing Vite HMR

================================================================================
 TESTES
================================================================================

 make test             Roda todos os testes (backend + frontend)
 make test-back        Apenas testes backend (pytest)
 make test-front       Apenas testes frontend (vitest)

  Ou manualmente:
    Backend:   cd backend && uv run python -m pytest
   Frontend:  cd frontends/dashboard && npx vitest run

================================================================================
 BUILD (producao)
================================================================================

 Dashboard:  npm run build --workspace=@launch/dashboard
 Landing:    npm run build --workspace=@launch/landing

================================================================================
 SETUP INICIAL
================================================================================

 make install          Instala tudo (Python + Node)
 make install-back     Apenas dependencias Python (uv)
 make install-front    Apenas dependencias Node (npm workspaces)
 make migrate          Roda migrations do Django
 make createsuperuser  Cria usuario admin

================================================================================
 DATABASE
================================================================================

 make migrate          Aplica migrations pendentes
 make makemigrations   Cria novas migrations
 make shell            Abre Django shell interativo

================================================================================
 IMPORTANTE
================================================================================

 - Python: SEMPRE use 'uv run' (nunca 'python' ou 'pip' direto)
 - Node: use 'npm' (nunca 'yarn' ou 'pnpm')
 - Variveis de ambiente: copie .env.example para .env e configure
 - Banco de dados: PostgreSQL deve estar rodando
 - Redis: necessario para Celery e cache

================================================================================
 DJANGO DEBUG TOOLBAR (DjDT)
================================================================================

 O DjDT esta ativo apenas em development (settings.development).

 ONDE APARECE POR PADRAO:
   /app/*          (dashboard)
   /admin/*        (admin)
   /auth/*         (autenticacao)
   /onboarding/*   (onboarding)

 ONDE NAO APARECE (por performance):
   Landing pages publicas (/inscrever-*, /obrigado-*, /suporte/, etc.)
   Essas rotas sao de alta performance e o DjDT adiciona overhead.

 FORCAR DjDT EM QUALQUER PAGINA:
   Adicione ?djdt=1 na URL. Exemplos:
     http://localhost:8844/inscrever-wh-rc-v3/?djdt=1
     http://localhost:8844/suporte/?djdt=1
     http://localhost:8844/obrigado-wh-rc-v3/?djdt=1

 NOTA TECNICA:
   O painel de Profiling esta desabilitado por conflito com Python 3.13
   (sys.monitoring vs cProfile). Os demais paineis (SQL, Cache, Signals,
   Templates, etc.) funcionam normalmente.
