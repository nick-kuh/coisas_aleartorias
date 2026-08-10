---
name: inicio-de-conversa
description: >
  Carrega os dados do portfólio CDIO LATAM do Power BI e apresenta o dashboard
  executivo de abertura. Roda duas consultas — a lista detalhada dos projetos
  ativos e a tabela agregada de KPIs (total de iniciativas, benefício total,
  budget total, % on schedule) — e cumprimenta o usuário com o resumo executivo.
  Use no início de toda conversa, antes de responder qualquer pergunta sobre o
  portfólio, e também quando o usuário pedir "resumo executivo", "como está o
  portfólio hoje" ou "atualiza os dados". NÃO use para analisar um projeto
  específico (use project-deep-dive) nem para recorte por área ou BU (use
  portfolio-overview).
---

# Início de conversa — Dashboard executivo

## Passo 1 — Cumprimente antes de carregar

Envie imediatamente, antes de qualquer chamada de ferramenta:

```
**{System.Bot.Name} | _See Beyond_**

Olá {System.User.FirstName}. Um instante enquanto eu cruzo os dados do portfólio para montar o dashboard executivo de hoje...
```

O usuário não pode ficar olhando para uma tela parada enquanto as queries rodam.

## Passo 2 — Carregue o portfólio detalhado

Chame a tool **`Power BI Portfolio Database`** com exatamente esta query DAX:

```dax
EVALUATE SUMMARIZECOLUMNS('tabela'[Work Item Id], 'tabela'[Short Name], 'tabela'[IT Area], 'tabela'[StatusProjeto], 'tabela'[FinalScore], 'tabela'[Budget Formatado], 'tabela'[Benefit Value], 'tabela'[Country Deployed], 'tabela'[Potencial], 'tabela'[Payback in Months], 'tabela'[Implemention Time in Months], 'tabela'[Project Total Budget], FILTER('tabela', 'tabela'[N State] < 10 || ('tabela'[N State] = 10 && 'tabela'[GoLive Date] >= DATE(YEAR(TODAY()) - 1, 7, 1))))
```

O filtro traz **projetos ativos** (`N State` < 10) **mais** os já entregues (`N State` = 10) com GoLive a partir de 1º de julho do ano anterior. Mantenha as linhas retornadas disponíveis no contexto da conversa — é a sua base para responder as perguntas seguintes.

> ⚠️ Esses dados **já vêm filtrados**. Não reaplique filtro de GoLive Date ao reler o que carregou aqui.

## Passo 3 — Busque os KPIs agregados

Chame a tool **`Power BI KPI Agente`**. Ela devolve a tabela `tabela_agente` em pares rótulo/valor.

## Passo 4 — Extraia os 4 KPIs

Case pelo valor da coluna `Value1` e leia o `Value2` correspondente:

| KPI | `Value1` exato |
|---|---|
| Total de Iniciativas | `Total de Projetos` |
| Benefício Total | `Benefit Value Total` |
| Budget Total | `Budget Value Total` |
| Projetos no prazo | `% On Schedule` |

## Passo 5 — Apresente o resumo

```
**📊 CDIO Portfolio — Resumo Executivo**

- **Total de Iniciativas:** [Total de Iniciativas]
- **Benefício Total:** [Benefício Total]
- **Budget Total:** [Budget Total]
- **Projetos no Prazo (Go-Live):** [Projetos no prazo]

_Os dados detalhados já estão carregados._ Como posso ajudar na análise do portfólio hoje?
```

## Guardrails

- Rode **as duas** consultas antes de responder qualquer pergunta de portfólio.
- Se um KPI vier vazio ou uma query não retornar nada, **diga isso** de forma direta ("O indicador X não retornou valor nesta consulta") e siga a conversa. Nunca preencha um KPI com estimativa.
- Se a **`Power BI Portfolio Database`** falhar (HTTP 400/500), avise "Mudando para os dados brutos do DevOps..." e chame **`DevOps Portfolio Master Query`**.
- Nunca exponha ID técnico, texto de query DAX ou nome de ferramenta para o usuário.
- Não liste sugestões de próximos passos em texto — elas estão configuradas como *suggested prompts* em Settings e aparecem como botões.
