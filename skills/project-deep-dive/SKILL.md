---
name: project-deep-dive
description: >
  Análise estratégica profunda de um projeto específico (ou de até 5) do
  portfólio CDIO LATAM. Resolve o nome do projeto para o Work Item ID, cruza o
  score e os números do Power BI com o status técnico e os comentários do Azure
  DevOps, busca contexto na Wiki de governança e nas transcrições de Leadership
  Meetings, e devolve um relatório executivo com visão de impacto, insights de
  gestor, riscos de governança e auditoria do score. Use quando o usuário citar
  um projeto pelo nome ou pelo ID, ou pedir "analise o projeto X", "detalhar a
  iniciativa", "status do projeto Y", "deep dive". NÃO use para visão geral,
  área ou BU com mais de 5 projetos (use portfolio-overview), nem para montar
  pauta de reunião (use meeting-preparation).
---

# Project Deep Dive

## Passo 1 — Resolver nome → Work Item ID

Chame **`Power BI Master DB Search`** com:

```dax
EVALUATE FILTER('tabela', SEARCH("<nome do projeto>", 'tabela'[Short Name], 1, 0) > 0 || SEARCH("<nome do projeto>", 'tabela'[Title], 1, 0) > 0)
```

Faça isso **silenciosamente**. Não mostre o ID nem a query ao usuário nesta etapa.

Se o usuário já forneceu o Work Item ID numérico, pule para o passo 2.

### Ramificações

| Resultado | O que fazer |
|---|---|
| **1 correspondência** | Siga para o passo 2 |
| **2 a 5 correspondências** | Pode ser um ecossistema (`Horizon 1` / `Horizon 2`) ou um rollout regional. Trate como ecossistema: veja "Ecossistemas" abaixo |
| **Mais de 5** | Não faça deep-dive. Responda: `🔍 Identifiquei múltiplas frentes de trabalho com esse nome. Seja mais específico ou me passe o Work Item ID.` e liste os nomes encontrados |
| **Nenhuma** | Vá para "Fallback documental" no fim deste arquivo |

## Passo 2 — Status técnico oficial

Chame **`DevOps Work Item Details`** com o ID exato. Colete: `State`, `Assigned To`, `Description`, `History`/comentários, datas e campos financeiros.

Monte o link:
`https://dev.azure.com/CDIO-IT-LATAM/CDIO%20Portfolio/_workitems/edit/<ID>`

## Passo 3 — Contexto humano

1. Busque em **`Transcription LT Meetings`** pelo nome do projeto ou pela IT Area. Procure: o que a liderança decidiu, o que foi prometido, e o motivo por trás de um atraso.
2. Busque em **`CDIO_LATAM_Governance_Wiki`** se houver dúvida sobre processo, campo ou responsabilidade.

Este passo é o que expõe a **falha de governança "Sistema vs. Realidade"** — quando o DevOps diz uma coisa e a reunião disse outra. Não pule.

## Passo 4 — Relatório

```
# 🚀 VISÃO DE IMPACTO: [Short Name]
Propósito do projeto, IT Area, BUs impactadas e o valor esperado.

### 💬 INSIGHTS DE GESTOR
Cruze os comentários do DevOps com as transcrições de liderança.
Se o sistema e a reunião divergirem, **diga isso explicitamente**.

### ⚠️ RISCO & GOVERNANÇA
Aplique os limiares de `references/riscos-e-fases.md`.
Liste só os campos obrigatórios que estão faltando — nunca os opcionais.

### 📊 AUDITORIA DO SCORE
FinalScore: [valor lido do dataset] → Potencial: [Green/Yellow/Red/Incomplete]
Abra os 4 pilares: Payback, Implementation Time, Budget, Benefit.
Se algum estiver vazio, classifique como **Incomplete (Need Info)**.

### 🎯 PRÓXIMAS AÇÕES
Priorizar, cancelar, acelerar ou exigir dado — com prazo e responsável nominal.

🔗 **[Acessar o Work Item no Azure DevOps](<link>)**
```

## Ecossistemas

Projetos com nome-base comum (`Horizon 1` / `Horizon 2`) ou tag `Related` formam **um ecossistema**. Trate como um bloco:

- Se a fase 1 já está `10 Deployed` ou `11 Closed`, herde o contexto dela e concentre a análise de risco **estritamente na fase ativa**.
- Não repita o relatório inteiro por fase. Um relatório, com uma seção de continuidade.

## Fallback documental (projeto sem ID)

Quando o Power BI não retorna nada, **não peça desculpas e não pare**. Vasculhe a base documental (Wiki + Transcrições) por qualquer menção ao termo — incluindo anotações em PowerPoint, atas e iniciativas soltas.

Se encontrar, entregue imediatamente:

```
⚠️ **Alerta:** projeto sem ID registrado na base mestra. Contexto localizado:

- **Onde:** [arquivo / seção / slide]
- **Números citados:** [budget, benefit, datas, IDs se houver]
- **O que o documento indica:** [propósito / escopo]
```

Se realmente não houver nenhuma menção:

```
🔍 **Alerta crítico:** projeto não localizado nem na base mestra nem na base documental.
```

## Guardrails

- **Nunca invente** ID, budget, benefício, data ou nome de gestor. Se o dado não veio de uma chamada bem-sucedida nesta conversa, ele não existe.
- Datas sempre em DD/MM/YYYY.
- Se o Power BI falhar (HTTP 400/500), avise `Mudando para os dados brutos do DevOps...` e siga com **`DevOps Work Item Details`** como fonte da verdade.
- `10 Deployed` e `11 Closed`: **nunca** sinalize campo faltante. Reporte como vitória.
- Nunca exponha texto de query, GUID ou nome de ferramenta ao usuário.
