# Receitas de DAX — `Power BI Portfolio Database`

Tabela: sempre `'tabela'`. Toda query começa com `EVALUATE`. Devolva só a string DAX crua, sem cercas de markdown.

---

## Colunas válidas

`[Work Item Id]` · `[Title]` · `[Short Name]` · `[Project IT Manager]` · `[State]` · `[N State]` · `[StatusProjeto]` · `[Project Type]` · `[IT Area]` · `[BG or BU Engagement]` · `[Specify Cross]` · `[FinalScore]` · `[Potencial]` · `[Business Benefit]` · `[Budget Formatado]` · `[Project Total Budget]` · `[Budget Value]` · `[Benefit Value]` · `[Payback in Months]` · `[Implemention Time in Months]` · `[Country Deployed]` · `[GoLive Date]` · `[PGLS End Date]` · `[Portfolio Year]`

**Nunca invente coluna.** Se precisar de algo que não está aqui, diga que o dado não existe no dataset.

### Domínios fechados

| Coluna | Valores |
|---|---|
| `[IT Area]` | `Consumer`, `Customer Dev`, `Make (Business Operation)`, `Focus Market (Cust Ops)`, `Commercial Exp`, `Tech Services`, `Tax Reform` |
| `[BG or BU Engagement]` | `BW`, `PC`, `HC`, `Foods`, `1UL`, `Cross` |
| `[StatusProjeto]` | `Deployed`, `Delayed`, `In PGLS`, `Ending this Quarter`, `On Time`, `No Information` (= sem GoLive Date) |
| `[Business Benefit]` | `Compliance`, `Value Added` |
| `[Potencial]` | Green (alto), Yellow (médio), Red (baixo) |
| `[Project Type]` | `Big Rock` (singular — **não** `Big Rocks`), `Regular`, `Small Project`. Filtro padrão `Big Rock` |

---

## 1. Panorama por IT Area

```dax
EVALUATE
SUMMARIZECOLUMNS(
    'tabela'[IT Area],
    "Projetos", COUNTROWS('tabela'),
    "Budget Total", SUM('tabela'[Project Total Budget]),
    "Benefit Total", SUM('tabela'[Benefit Value])
)
```

## 2. Projetos de uma IT Area

```dax
EVALUATE
CALCULATETABLE(
    SUMMARIZECOLUMNS('tabela'[Work Item Id], 'tabela'[Short Name], 'tabela'[State],
        'tabela'[StatusProjeto], 'tabela'[Project IT Manager], 'tabela'[FinalScore],
        'tabela'[Potencial], 'tabela'[Project Total Budget], 'tabela'[Benefit Value],
        'tabela'[GoLive Date]),
    'tabela'[IT Area] = "Make (Business Operation)"
)
```

## 3. Recorte por Business Unit (com Cross)

Sempre inclua o `Cross` que menciona a BU:

```dax
EVALUATE
FILTER(
    'tabela',
    'tabela'[BG or BU Engagement] = "PC"
    || ('tabela'[BG or BU Engagement] = "Cross" && SEARCH("PC", 'tabela'[Specify Cross], 1, 0) > 0)
)
```

Para múltiplas BUs (`BPC` = BW + PC):

```dax
EVALUATE
FILTER(
    'tabela',
    'tabela'[BG or BU Engagement] IN {"BW", "PC"}
    || ('tabela'[BG or BU Engagement] = "Cross"
        && (SEARCH("BW", 'tabela'[Specify Cross], 1, 0) > 0
            || SEARCH("PC", 'tabela'[Specify Cross], 1, 0) > 0))
)
```

## 4. Watermelons — verde por fora, vermelho por dentro

```dax
EVALUATE
FILTER(
    'tabela',
    'tabela'[N State] < 10
    && (
        ISBLANK('tabela'[Benefit Value]) || 'tabela'[Benefit Value] = 0
        || 'tabela'[StatusProjeto] = "Delayed"
        || 'tabela'[StatusProjeto] = "No Information"
    )
)
```

## 5. Governança — chegou em Cost Approv sem os números

```dax
EVALUATE
FILTER(
    'tabela',
    'tabela'[N State] >= 5 && 'tabela'[N State] < 10
    && (ISBLANK('tabela'[Project Total Budget]) || ISBLANK('tabela'[Benefit Value]))
)
```

## 6. Top Big Rocks por benefício

```dax
EVALUATE
TOPN(
    3,
    FILTER('tabela', 'tabela'[Project Type] = "Big Rock" && 'tabela'[N State] < 10),
    'tabela'[Benefit Value], DESC
)
```

## 7. Carga por owner (detectar quem tem >5 Big Rocks)

```dax
EVALUATE
SUMMARIZECOLUMNS(
    'tabela'[Project IT Manager],
    "Big Rocks", CALCULATE(COUNTROWS('tabela'),
        'tabela'[Project Type] = "Big Rock", 'tabela'[N State] < 10)
)
```

## 8. Buscar projeto por nome

```dax
EVALUATE
FILTER('tabela',
    SEARCH("<nome>", 'tabela'[Short Name], 1, 0) > 0
    || SEARCH("<nome>", 'tabela'[Title], 1, 0) > 0)
```

> Esta é a query da tool `Power BI Master DB Search`. **Nunca** use `EVALUATE 'tabela'` puro para buscar por nome — traz a tabela inteira.

## 9. Projetos sem Go-Live definida

```dax
EVALUATE
FILTER('tabela', 'tabela'[N State] < 10 && ISBLANK('tabela'[GoLive Date]))
```

---

## Regras gerais

1. Visão macro → `SUMMARIZECOLUMNS`. Recorte específico ou risco → `CALCULATETABLE` ou `FILTER`.
2. `[FinalScore]` e `[Potencial]` são **calculados no dataset**. Leia. Nunca recalcule.
3. Se `[Payback in Months]`, `[Implemention Time in Months]`, `[Project Total Budget]` ou `[Benefit Value]` estiver vazio, o potencial é `Incomplete` — não estime.
4. Datas do sistema vêm em DD/MM/YYYY.
5. Se a query falhar (HTTP 400/500), avise o usuário e caia para o Azure DevOps como fonte da verdade.
