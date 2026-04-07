# ADR-0001: Definir a Fronteira Oficial de Captura de Lead

**Status**: Accepted
**Data**: 2026-04-05
**Decisao**: O sistema considera um lead oficialmente capturado apenas no `submit valido` da landing.

## Contexto

O fluxo atual de captura comeca antes do envio do formulario.

Hoje o sistema ja cria ou enriquece dados em momentos anteriores ao submit:

- `page load`: cria/recupera `Identity` anonima e grava `PAGE_VIEW`
- `fp-resolve`: vincula `FingerprintIdentity` a sessao
- `capture-intent`: pode salvar `email_hint`, `phone_hint` e ate criar contatos pendentes

Isso gera ambiguidade de produto e de engenharia:

- um visitante identificado nao e necessariamente um lead
- um hint salvo nao e necessariamente uma conversao
- um contato pendente nao e necessariamente um cadastro concluido

Ao mesmo tempo, o negocio precisa de uma fronteira clara para:

- conversao
- analytics
- CRM
- automacoes externas
- metas operacionais

## Drivers de Decisao

- produto precisa de um momento unico e claro de conversao
- engenharia precisa separar `tracking tecnico` de `captura oficial`
- analytics precisa evitar contar prelead como lead
- operacao precisa saber quando N8N, Meta e CRM devem ser considerados consequencias da captura

## Opcoes Consideradas

### Opcao A — Considerar lead desde o `page load`

**Pros**

- maximo volume de dados desde o primeiro contato

**Cons**

- infla conversao
- mistura visita com captura real
- inviabiliza leitura confiavel de funil

### Opcao B — Considerar lead a partir do `capture-intent`

**Pros**

- aproveita abandono parcial
- antecipa sinais de interesse

**Cons**

- ainda nao existe consentimento claro de envio final
- usuario pode sair sem concluir
- contato pendente nao representa lead consolidado

### Opcao C — Considerar lead apenas no `submit valido`

**Pros**

- fronteira simples e auditavel
- alinha UX, produto e operacao
- evita contaminar analytics de conversao
- deixa `capture-intent` como enriquecimento e recuperacao, nao como conversao

**Cons**

- parte do valor de prelead fica fora da metrica oficial de captura

## Decisao

Adotar a **Opcao C**.

### Regra oficial

```text
Visitante identificado   != Lead capturado
Hint salvo              != Conversao
Contato pendente        != Cadastro concluido
Submit valido           == Momento oficial da captura de lead
```

## Consequencias

### Produto

- a conversao oficial da landing passa a ser o `submit valido`
- `capture-intent` continua existindo, mas como sinal de prelead
- pagina de obrigado continua sendo a manifestacao visual do sucesso

### Engenharia

- o fluxo deve garantir que todo `submit valido` consolide a identidade do lead
- o sistema deve diferenciar claramente estados de visitante, prelead e lead
- `CaptureSubmission` deve ser tratado como registro esperado do submit valido

### Analytics

- `PAGE_VIEW` e `FORM_INTENT` continuam no funil, mas fora da conversao final
- `FORM_SUCCESS` passa a ser o evento de referencia da captura
- metricas de lead nao devem usar `capture-intent` como proxy de conversao

### Operacao

- N8N, Meta CAPI e outras integracoes passam a ser efeitos assincronos do submit valido
- falha em integracao externa nao muda o fato de que a captura ocorreu
- observabilidade precisa acompanhar a entrega dessas integracoes separadamente

## Implicacoes Imediatas

1. `capture-intent` deve ser interpretado como enriquecimento progressivo, nao como captura final.
2. `CaptureSubmission` deve se tornar universal em submits validos de producao.
3. Landings de producao devem convergir para configuracao via `CapturePage` no banco.
4. Dashboards e relatorios devem distinguir claramente:
   - visitante
   - prelead
   - lead capturado

## Riscos

- se `CaptureSubmission` continuar opcional em algumas campanhas, a decisao fica correta conceitualmente, mas incompleta na implementacao
- se times operacionais tratarem `capture-intent` como lead, voltamos a gerar ambiguidade

## Mitigacoes

- fechar o gap tecnico que impede `CaptureSubmission` em 100% dos submits validos
- documentar a taxonomia oficial do funil
- refletir essa regra nos dashboards e automacoes

## Referencias

- `../lead-capture-workflow.md`
- `src/apps/landing/views.py`
- `src/apps/landing/services/capture.py`
- `src/apps/contacts/identity/services/resolution_service.py`
- `src/core/tracking/identity_middleware.py`
