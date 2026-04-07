# Docusaurus Docs Bootstrap

Esta pasta foi criada para concentrar a documentacao navegavel do projeto.

Estado atual:

- a estrutura inicial de docs ja existe em `frontends/docusaurus/docs/`
- ainda nao existe `package.json` nem app Docusaurus executavel
- isso foi intencional para nao alterar o monorepo agora, porque o root usa `workspaces: ["frontends/*"]`

Primeiro documento iniciado:

- `docs/lead-capture-workflow.md`

Objetivo imediato:

- registrar o workflow completo de captura de lead
- diferenciar fluxo real x fluxo esperado
- documentar onde cada dado e persistido
- servir de base para ADRs e para os proximos ajustes de implementacao

Proximo passo natural quando quisermos transformar isso em um app Docusaurus real:

1. adicionar `package.json` proprio
2. criar `docusaurus.config.ts` e `sidebars.ts`
3. integrar scripts de dev/build sem quebrar os workspaces atuais
