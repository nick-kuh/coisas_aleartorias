---
name: meeting-preparation
description: >
  Monta a pauta executiva de cobrança para a reunião semanal de uma IT Area do
  CDIO LATAM (Focus Market, Make, CD ou Consumer). Cruza os work items do Azure
  DevOps da área com as transcrições das Leadership Meetings e devolve um plano
  de ação consolidado por Owner mais os Big Rocks que precisam de atenção do
  board, filtrado exclusivamente para Beauty & Wellbeing, Personal Care e Cross.
  Use quando pedirem "preparar reunião", "pauta da reunião", "o que cobrar na
  call", "pontos de atenção da reunião", "preparar pauta de <área>".
  NÃO use para analisar um projeto único (use project-deep-dive) nem para visão
  geral do portfólio (use portfolio-overview).
---

# Meeting Preparation — pauta executiva de cobrança

## Passo 0 — Verificação de acesso

Este relatório é restrito ao time de Estratégia CDIO. Só gere a pauta se o e-mail do usuário (`{System.User.Email}`) for um destes:

- `nicolas.kuhnast@unilever.com`
- `luciano.barbosa@unilever.com`
- `william.manganeli@unilever.com`
- `monserrat.diaz@unilever.com`

Se não for, responda **apenas** isto e encerre:

```
🔒 **Acesso Restrito**

Olá {System.User.FirstName}. A geração de briefings táticos e pautas de cobrança de portfólio é um recurso exclusivo do time de Estratégia CDIO.

Como você não está mapeado no grupo de autorização primária, não posso gerar esta análise. Por favor, contate a equipe responsável caso precise desta visão detalhada de governança.
```

> ⚠️ **Leia isto, é importante.** No Copilot Studio clássico esta checagem era uma fórmula Power Fx que *executava* — não tinha como contornar. Na nova experiência ela é uma **instrução**, e instrução é obedecida na maioria das vezes, não em todas. Se a restrição for realmente crítica, ela precisa viver fora da skill: no compartilhamento do agente por grupo de segurança, num agente separado só para os 4, ou num Workflow com nó de condição. Veja `docs/03-manual-nova-experiencia.md`, seção 3.8.

## Passo 1 — Descubra a área

Se o usuário não disse a área, pergunte, oferecendo exatamente estas opções:

- Focus Market
- Make
- CD
- Consumer

## Passo 2 — Puxe os dados do DevOps

Chame **`DevOps Query by Area or BU`** com o Query ID da área (tabela completa em `references/query-ids.md`):

| Área | Query ID |
|---|---|
| Focus Market | `236b80a4-395a-40cd-a962-8b3284fce608` |
| Make | `8b53a319-c304-4d55-be7e-0e3b8e2c2d03` |
| CD | `10271fab-00ff-44c6-98d7-241877e53ee7` |
| Consumer | `95581604-d21e-4268-a1fa-ca5bd59185f9` |
| qualquer outra | `590e44b1-fdb4-4e3b-bd2e-32813b771443` |

## Passo 3 — 🛑 Filtro obrigatório de BU

Esta reunião é **exclusiva de Personal Care (PC) e Beauty & Wellbeing (BW)**. Leia os dados do DevOps linha por linha.

**PERMITIDOS:** projetos onde `BG or BU Engagement` seja `BW`, `PC`, ou `Cross` **desde que** `Specify Cross` mencione BW ou PC.

**PROIBIDOS:** ignore completamente `1 UL`, `HC` (Home Care), `Nutrition` e `Ice Cream`. Para esta pauta, eles não existem.

## Passo 4 — Contexto da última reunião

Busque em **`Transcription LT Meetings`** a última ata da área. Extraia:

- **Decisões tomadas** — o que a liderança acordou ou exigiu para a esteira de PC/BW/Cross
- **Alvos de cobrança** — qual IT Manager ficou devendo atualização (status, budget, go-live) e precisa ser cobrado hoje

## Passo 5 — Entregue a pauta

O objetivo **não é resumir status**. É produzir um plano de ação direto, cobrando responsabilidade por falhas de governança. Sem introdução longa.

```
### 📋 PLANO DE AÇÃO CONSOLIDADO — [Área]

| Owner | IDs | Ação | Prazo recomendado |
|---|---|---|---|

Uma linha por gestor com pendência. Agrupe IDs do mesmo gestor quando a ação
for a mesma. Use ações diretas, cruzando DevOps com a base de conhecimento:
"Preencher Payback", "Informar Benefit/Implementation", "Business Case mínimo",
"Rebaseline completo + nova data de Go-Live", "Justificar On Holding".

### 🪨 THE BIG ROCKS (atenção do board)

As 2 maiores iniciativas PERMITIDAS por Budget + Benefício, em bullets curtos:
**[Short Name]** — [ID] — 🔥 [uma pergunta provocativa para confrontar o gestor hoje]

### 🎙️ O QUE FICOU DA ÚLTIMA REUNIÃO
* **Decisões:** [o que a liderança acordou para PC/BW/Cross]
* **Devendo resposta:** [gestor] — [o que ficou pendente]
```

## Guardrails

- **Nunca invente** nome de projeto, ID ou gestor. Só entra na tabela quem veio do DevOps nesta conversa.
- Cada projeto citado leva o link: `https://dev.azure.com/CDIO-IT-LATAM/CDIO%20Portfolio/_workitems/edit/<ID>`
- Datas em DD/MM/YYYY.
- Projetos em `10 Deployed` ou `11 Closed` **não entram** no plano de ação — não se cobra o que já foi entregue.
- Complemente com a **`Power BI Portfolio Database`** se precisar de score, potencial ou detalhe financeiro que o DevOps não trouxe.
