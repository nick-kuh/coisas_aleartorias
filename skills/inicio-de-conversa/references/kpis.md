# Referência — tabela `tabela_agente` e colunas do portfólio

Leia este arquivo apenas se um KPI vier vazio ou se precisar montar uma variação do dashboard.

## `tabela_agente` (Power BI KPI Agente)

Tabela de duas colunas, uma linha por indicador:

| `Value1` (rótulo) | `Value2` (valor) | Significado |
|---|---|---|
| `Total de Projetos` | número | Total de iniciativas no recorte ativo |
| `Benefit Value Total` | valor em € | Soma do benefício esperado |
| `Budget Value Total` | valor em € | Soma do budget total |
| `% On Schedule` | percentual | Percentual de projetos com Go-Live dentro do prazo |

Query fixa da tool: `EVALUATE 'tabela_agente'`

Se um rótulo não aparecer, é porque a medida foi renomeada no dataset. Não invente o valor — reporte a ausência.

## Colunas de `'tabela'` usadas no dashboard

| Coluna | Uso |
|---|---|
| `[Work Item Id]` | Chave para cruzar com o Azure DevOps |
| `[Short Name]` | Nome curto usado nas buscas por nome |
| `[IT Area]` | Consumer, Make, CD, Focus Market (+ áreas menores) |
| `[StatusProjeto]` | `Deployed`, `Delayed`, `In PGLS`, `Ending this Quarter`, `On Time`, `No Information` |
| `[FinalScore]` | Score numérico calculado no dataset — **leia, não recalcule** |
| `[Potencial]` | Green = alto · Yellow = médio · Red = baixo · vazio = Incomplete |
| `[Budget Formatado]` | Budget já formatado para exibição |
| `[Project Total Budget]` | Budget numérico, para contas |
| `[Benefit Value]` | Benefício esperado em € |
| `[Country Deployed]` | Países onde foi implantado |
| `[Payback in Months]` | Tempo de recuperação do investimento |
| `[Implemention Time in Months]` | Duração da construção até a entrega |
| `[N State]` | Fase numérica (10 = Deployed, 11 = Closed) |
| `[GoLive Date]` | Data de go-live |

## Sobre o filtro da query de abertura

```dax
FILTER('tabela',
  'tabela'[N State] < 10
  || ('tabela'[N State] = 10 && 'tabela'[GoLive Date] >= DATE(YEAR(TODAY()) - 1, 7, 1))
)
```

Traduzindo: **tudo que ainda está em andamento**, mais **o que foi entregue no último ciclo** (a partir de 1º de julho do ano anterior). Projetos `11 Closed` ficam de fora — já saíram do radar do CDIO.

Se o usuário pedir explicitamente projetos encerrados, rode uma nova query sem esse filtro na `Power BI Portfolio Database`.
