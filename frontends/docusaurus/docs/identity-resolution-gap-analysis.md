---
title: Identity Resolution Gap Analysis
description: Analise crítica do que falta para reconhecer a mesma pessoa ao longo do tempo, entre devices e entre sessões.
---

# Identity Resolution Gap Analysis

## Pergunta central

O que falta para que o sistema saiba, **sempre**, que duas visitas pertencem à mesma pessoa?

Resposta curta:

**nada no software, sozinho, consegue garantir isso sempre**.

O sistema atual consegue chegar a um nível bom de reconciliação quando existe ao menos um identificador forte ou um elo compartilhado entre sessões/dispositivos. O que ele **não** consegue fazer é reconhecer a mesma pessoa entre dispositivos e ao longo do tempo quando não existe nenhum identificador persistente em comum.

Então a análise correta precisa separar:

1. o que o sistema já faz bem
2. o que ainda falta modelar/operar melhor
3. o que é estruturalmente impossível sem novos sinais ou novos passos do usuário

---

## Regra de Realidade

```text
Mesma pessoa humana != sempre observável pelo sistema

O sistema só consegue unificar com segurança quando existe pelo menos um elo:

- mesma sessão
- mesmo fingerprint estável
- mesmo email
- mesmo telefone
- mesmo cookie de PII hash
- mesma conta autenticada
- mesmo identificador externo estável
```

Sem elo compartilhado, o máximo que existe é **heurística**, não verdade.

---

## O que o sistema já faz bem hoje

## 1. Cria identidade desde a primeira visita

O visitante não precisa enviar o formulário para entrar no grafo de identidade.

Isso é forte porque permite:

- preservar histórico pré-submit
- linkar fingerprint depois
- manter continuidade por sessão

Código principal:

- `backend/src/core/tracking/identity_middleware.py`

## 2. Conecta fingerprint à sessão quando ele chega depois

Quando o `visitorId` chega, o sistema consegue:

- criar/reusar `FingerprintIdentity`
- anexar à `Identity` da sessão
- atualizar `PAGE_VIEW`
- detectar divergência de identidade e enfileirar merge

Código principal:

- `backend/src/apps/landing/views.py#fp_resolve`
- `backend/src/core/tracking/identity_middleware.py#_link_fingerprint_to_identity`

## 3. Faz resolução forte no submit

No submit válido, o sistema consolida por:

- fingerprint
- email
- phone

e consegue:

- criar nova identity
- reutilizar identity existente
- fundir identities múltiplas
- fundir a identity anônima da sessão na identity final

Código principal:

- `backend/src/apps/landing/services/capture.py#process_lead`
- `backend/src/apps/contacts/identity/services/resolution_service.py`
- `backend/src/apps/contacts/identity/services/merge_service.py`

## 4. Mantém continuidade cross-session para visitantes convertidos

Depois do submit, o sistema seta cookies hashados:

- `_em`
- `_ph`

Depois, se a sessão sumir, ele tenta recuperar a `Identity` por esses hashes.

Isso é um ponto bem forte para continuidade temporal.

Código principal:

- `backend/src/apps/landing/views.py#_set_hashed_pii_cookies`
- `backend/src/core/tracking/identity_middleware.py#_recover_identity_from_hashed_cookies`

---

## O que ainda falta para ficar muito melhor

## 1. Ponte explícita entre `User` e `Identity`

Hoje:

- `identity.User` = conta autenticável
- `contacts.identity.Identity` = pessoa/lead do funil

Esses mundos estão separados, e isso é coerente.

Mas se o lead virar comprador/aluno e depois operar em áreas autenticadas, falta uma ponte canônica do tipo:

```text
UserIdentityLink
ou
user.identity FK
ou
identity.user FK
```

Sem isso, você pode até saber que o lead e o aluno parecem a mesma pessoa, mas não existe verdade institucional explícita ligando os dois domínios.

### Impacto

- dificulta visão 360 de lead -> comprador -> aluno
- dificulta cruzar marketing + billing + produto autenticado

### Recomendação

Criar uma ponte explícita, mas só quando as regras de domínio estiverem claras:

- 1 user para 1 identity?
- 1 identity pode ter múltiplos users?
- um operador interno pode ou não coincidir com um lead/comprador?

---

## 2. Estratégia explícita de `Identity Confidence`

Hoje já existe `confidence_score`, mas o sistema ainda não parece expor isso como contrato operacional forte para decisão automática.

O que falta:

- política de limiar por tipo de evidência
- política de auto-merge vs review manual
- política de quando a ligação é “forte” ou apenas “provável”

### Exemplo de camada de decisão

```text
Confidence < 0.50   -> apenas correlacionado
0.50 - 0.84         -> mesma pessoa provável
0.85 - 0.94         -> merge automatizável se não houver conflito
>= 0.95             -> mesma pessoa com alta confiança
```

Hoje o sistema já calcula confiança, mas não está claro no runtime que isso governa o nível de automação.

---

## 3. Sobrevivência mais forte entre devices

Hoje, cross-device acontece muito bem quando há:

- mesmo email
- mesmo telefone
- cookies `_em` / `_ph`

O gap é o caso clássico:

- device A sem login
- device B sem login
- sessões diferentes
- sem cookie compartilhado
- sem submit com o mesmo email/telefone ainda

Nesse caso, não existe verdade suficiente.

### Recomendação

Se você quiser aumentar a chance de unificação entre devices ao longo do tempo, os caminhos reais são:

1. deep links autenticados para fluxos importantes
2. magic links por email
3. OTP de telefone
4. alguma ação autenticada ou semiautenticada do usuário
5. parâmetros de continuidade entre campanhas e canais próprios

Sem isso, o sistema ficará preso à coincidência de sinais fracos.

---

## 4. Relação explícita entre `CaptureIntent` e `CaptureSubmission`

Hoje o intent é fechado por `capture_token`, o que é bom.

Mas ainda faltaria, para visão operacional completa:

- trilha de conversão intent -> submission mais navegável
- consultas diretas do tipo:
  - quantos intents viraram capture
  - quantos ficaram abandonados
  - quantos foram reconciliados em outra sessão/device

### Recomendação

Adicionar, se fizer sentido para analytics:

- um vínculo explícito no intent para a submission final
- ou uma materialized view / projection de lifecycle do intent

---

## 5. Similarity / review lane humana

O código já tem `AnalysisService.find_similar_identities(...)`.

Isso é um ótimo começo, mas hoje parece mais ferramenta analítica do que trilha operacional.

### O que falta

- surface admin/operação para “possible duplicates”
- fila de revisão humana
- ação segura de merge manual assistido

### Por quê isso importa

Porque sempre haverá cenários em que o sistema não deve auto-mergear, mas deveria **sugerir** fortemente que duas identities parecem a mesma pessoa.

---

## O que é impossível garantir só com a arquitetura atual

## Cenário impossível 1

Mesma pessoa, dois devices, nenhuma sessão compartilhada, nenhum fingerprint compartilhado, nenhum email/phone compartilhado ainda.

Exemplo:

- no celular a pessoa só lê a landing
- no notebook volta semanas depois
- nenhum cookie é aproveitado
- nenhum submit foi feito antes

Resultado:

- o sistema não tem como saber que é a mesma pessoa

## Cenário impossível 2

Mesma pessoa com múltiplos emails/telefones, sem evento de ligação entre eles.

Exemplo:

- numa campanha usa email A
- em outra usa email B
- nunca usa o mesmo telefone
- nunca autentica

Resultado:

- sem elo comum, o sistema não tem verdade suficiente para unificar automaticamente

## Cenário impossível 3

Dois humanos diferentes dividindo device/browser/fingerprint em contexto extremo.

Resultado:

- fingerprint não é prova humana definitiva
- é evidência de dispositivo, não de pessoa

---

## Estratégia realista por camadas

Se a meta é “quase sempre descobrir que é a mesma pessoa”, a estratégia correta não é tentar um truque único. É empilhar camadas de certeza.

## Camada 1 — Sessão

Já existe.

Valor:

- continuidade de curtíssimo prazo

## Camada 2 — Fingerprint

Já existe.

Valor:

- continuidade por navegador/dispositivo

Limite:

- não resolve humano cross-device sozinho

## Camada 3 — Canais fortes

Já existe.

Valor:

- email e phone são o principal mecanismo de unificação real

## Camada 4 — Cookies hashados pós-conversão

Já existe.

Valor:

- continuidade cross-session para convertidos

## Camada 5 — Vínculo autenticado

Ainda falta como ponte explícita `User <-> Identity`.

Valor:

- fecha o ciclo lead -> comprador -> aluno

## Camada 6 — Similaridade assistida

Ainda falta superfície operacional forte.

Valor:

- resolve os casos limítrofes que não merecem auto-merge

---

## Visual amplo — Deveria vs Faz Hoje

```text
╔══════════════════════════════════════╦════════════════════════════════════════════════════════════╗
║ Situação                            ║ Sistema deveria fazer / sistema faz hoje                 ║
╠══════════════════════════════════════╬════════════════════════════════════════════════════════════╣
║ mesma sessão                        ║ deveria: continuar a mesma pessoa                         ║
║                                      ║ hoje: faz                                                 ║
╠══════════════════════════════════════╬════════════════════════════════════════════════════════════╣
║ mesmo device/fingerprint            ║ deveria: continuar a mesma pessoa                         ║
║                                      ║ hoje: faz bem, com merge async quando diverge            ║
╠══════════════════════════════════════╬════════════════════════════════════════════════════════════╣
║ nova sessão, mesma pessoa convertida║ deveria: recuperar a mesma pessoa                         ║
║                                      ║ hoje: faz via _em/_ph                                    ║
╠══════════════════════════════════════╬════════════════════════════════════════════════════════════╣
║ cross-device com mesmo email/phone  ║ deveria: unificar                                         ║
║                                      ║ hoje: faz no submit                                       ║
╠══════════════════════════════════════╬════════════════════════════════════════════════════════════╣
║ cross-device sem elo forte          ║ deveria: no máximo sugerir, nunca afirmar                 ║
║                                      ║ hoje: não consegue garantir                               ║
╠══════════════════════════════════════╬════════════════════════════════════════════════════════════╣
║ lead vira comprador/aluno           ║ deveria: continuar a mesma pessoa em domínios diferentes  ║
║                                      ║ hoje: falta ponte explícita User <-> Identity            ║
╚══════════════════════════════════════╩════════════════════════════════════════════════════════════╝
```

## O que eu classificaria como faltas reais

### Falta 1 — Ponte canônica `User <-> Identity`

Essa é a maior lacuna de ciclo de vida.

### Falta 2 — Similar duplicate review lane

O sistema sabe bastante, mas ainda não institucionalizou a revisão humana de duplicatas prováveis.

### Falta 3 — Política explícita de confidence thresholds

Já há score, mas ainda falta transformá-lo em contrato operacional claro.

### Falta 4 — Estratégia de identificação forte cross-device

Isso não se resolve só com software backend. Exige jornada de produto:

- magic link
- OTP
- login
- eventos autenticados

## Conclusão

Se a exigência for:

> “sempre vamos descobrir que é a mesma pessoa”

a resposta exata é:

**não com o que temos hoje, e nem com qualquer arquitetura puramente passiva baseada só em sessão + fingerprint + contato eventual.**

Se a exigência for:

> “quase sempre, quando houver sinais suficientes, vamos consolidar corretamente”

a resposta é:

**o sistema já está relativamente bem encaminhado**, e o que falta de verdade é:

1. ponte `User <-> Identity`
2. lane operacional de possíveis duplicatas
3. política explícita de confidence / auto-merge
4. mecanismos de identificação forte cross-device ao longo da jornada

## Próximos passos recomendados

1. definir o modelo oficial `User <-> Identity`
2. criar surface operacional de `possible duplicates`
3. explicitar thresholds de confidence no domínio
4. desenhar a jornada de identificação forte para comprador/aluno
