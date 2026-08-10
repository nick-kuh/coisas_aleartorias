---
name: portfolio-overview
description: >
  Visão macro do portfólio CDIO LATAM — o portfólio inteiro, uma IT Area
  (Consumer, Make, CD, Focus Market) ou uma Business Unit (BW, PC, HC, Foods,
  Cross, BPC, HPC, HPF). Devolve um dashboard conciso com saúde do portfólio,
  breakdown por área, watermelons e Big Rocks, sem análise individual projeto a
  projeto. Use quando pedirem "visão geral", "como está o portfólio",
  "analise a área X", "projetos de BW", "watermelons", "top big rocks",
  "projetos em risco", ou sempre que o recorte tiver mais de 5 projetos.
  NÃO use para um projeto único ou um punhado nomeado (use project-deep-dive)
  nem para montar pauta de reunião (use meeting-preparation).
---

# Visão macro do portfólio

## Passo 1 — Entenda o recorte

Identifique o que foi pedido:

| Pedido | Recorte |
|---|---|
| "visão geral", "o portfólio" | Tudo |
| "Make", "Consumer", "CD", "Focus Market", "business ops", "supply chain", "marketing", "customer development" | IT Area |
| "BW", "B&W", "beauty", "PC", "personal care", "HC", "home care", "Foods", "Cross" | Business Unit |
| "BPC", "HPC", "HPF" | Combinação de BUs — traduza antes (ver abaixo) |

**Acrônimos combinados:** `BPC` = BW **e** PC · `HPC` = HC **e** PC · `HPF` = HC, PC **e** Foods.

Ao filtrar por BU, sempre inclua os projetos marcados como `Cross` cuja coluna `[Specify Cross]` mencione a BU:

```dax
FILTER('tabela',
  'tabela'[BG or BU Engagement] = "PC"
  || ('tabela'[BG or BU Engagement] = "Cross" && SEARCH("PC", 'tabela'[Specify Cross], 1, 0) > 0)
)
```

## Passo 2 — Busque os dados

Use **`Power BI Portfolio Database`** com uma query `SUMMARIZECOLUMNS` para o recorte. Receitas prontas em `references/dax-cookbook.md`.

Se precisar do estado técnico oficial ou do histórico, complemente com **`DevOps Query by Area or BU`** usando o Query ID da tabela em `references/query-ids.md`.

**Foco:** priorize `Consumer`, `Make`, `CD` e `Focus Market`. Ignore áreas menores (Tax Reform, Commercial…) em visões gerais, a menos que peçam explicitamente.

## Passo 3 — Formato de saída

Concisão é a regra. **Nunca faça análise individual aqui.**

```
**📊 SAÚDE DO PORTFÓLIO**
Entregues (10 Deployed + 11 Closed): X | Em andamento (06–09): Y | Em escopo (01–05): Z
Em risco: N projetos

**🏢 BREAKDOWN POR IT AREA**
| IT Area | Projetos | Budget | Benefício | Em risco |
(apenas as áreas core)

**🍉 WATERMELONS**
Projetos com status verde por fora e vermelho por dentro — benefício zerado,
Go-Live estourado, ou parado além do limite da fase.
Formato: **[Short Name]** — [ID] — [o que está errado]

**🪨 TOP BIG ROCKS**
As 3 maiores iniciativas por Budget + Benefício, com o risco de cada uma.

**🎯 DIRETRIZ PARA OS PRÓXIMOS 30 DIAS**
Um veredito claro e a ação corretiva que a liderança deve cobrar de quem.
```

## Regras de risco

Consulte `references/riscos-e-fases.md` para os limiares completos. Os principais:

- Parado >60 dias em `02 Scoping` → **Alto**
- Chegou em `05 Cost Approv` sem Budget ou sem Benefit → **CRÍTICO**
- Parado >30 dias em `08 UAT` → **Alto**
- PGLS infinito (>3 meses) → **Médio**
- Watermelon (verde com €0 de benefício ou atrasado por dentro) → **CRÍTICO**
- Um único owner com >5 Big Rocks → **Alto**
- `10 Deployed` e `11 Closed` → **nunca sinalize por campo faltante.** Reporte como vitória

## ⛔ Regra anti-alucinação

Só cite nome de projeto que veio de uma chamada bem-sucedida **nesta conversa**, com `[Title]` e `[Work Item Id]` reais.

Se você só tem agregados macro, escreva exatamente:

> Tenho apenas os agregados macro neste momento. Peça uma IT Area ou um projeto específico para eu trazer nomes e outliers.

**Nunca invente nome, ID, budget, benefício ou data para preencher uma lista.**
