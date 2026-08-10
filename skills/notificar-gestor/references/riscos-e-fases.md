# Fases, riscos e regras de governança

## As 13 fases oficiais

| `N State` | Nome oficial | Grupo |
|---|---|---|
| 0 | `00 Cancelled` | Encerrado |
| 1 | `01 Idea` | Escopo |
| 2 | `02 Scoping` | Escopo |
| 3 | `03 Scope Approv` | Escopo |
| 4 | `04 Costing` | Escopo |
| 5 | `05 Cost Approv` | Escopo |
| 6 | `06 Plan Analyze` | Construção |
| 7 | `07 Design Build` | Construção |
| 8 | `08 UAT` | Construção |
| 9 | `09 PGLS` | Construção |
| 10 | `10 Deployed` | Sucesso |
| 11 | `11 Closed` | Sucesso |
| 12 | `12 On Holding` | Parado |

### A diferença entre 10 e 11 (crítica)

- **`10 Deployed`** — sucesso técnico. O projeto foi entregue e está sob cuidado do CDIO para hypercare, adoção e ajustes antes do hand-off. **Nunca sinalize por campo faltante.** É vitória.
- **`11 Closed`** — marco final. Transferido oficialmente para o time de Produto/Negócio. Concluído e fora do radar do CDIO. **Nunca sinalize.**

## Limiares de risco

| Situação | Severidade |
|---|---|
| Parado >60 dias em `02 Scoping` | 🔴 Alto |
| Chegou em `05 Cost Approv` sem Budget ou sem Benefit | 🔴 **CRÍTICO** |
| Parado >30 dias em `08 UAT` | 🔴 Alto |
| PGLS infinito (>3 meses em `09 PGLS`) | 🟡 Médio |
| **Watermelon**: status verde mas €0 de benefício, ou atrasado por dentro | 🔴 **CRÍTICO** |
| Um owner com >5 Big Rocks ativos | 🔴 Alto |
| `[StatusProjeto]` = `No Information` (sem GoLive Date) | 🟡 Médio |
| `12 On Holding` sem justificativa registrada | 🟡 Médio |
| `10 Deployed` / `11 Closed` | ✅ nunca sinalizar — reportar como vitória |

## Campos obrigatórios (auditoria estrita)

**Nunca sinalize campo que não esteja nesta lista.** `Security Assessment`, `Clarity ID`, `Note` e `Tags` são 100% opcionais.

### Obrigatórios sempre

Title · State · Assigned To · Description · Project Type · Business Benefit · Business Product Domain · BG or BU Engagement · IT Manager · IT Area · Country · Year · Implementation Time

### Condicionais

| Campo | Obrigatório quando |
|---|---|
| `Specify Cross` | `BG or BU Engagement` = `Cross` |
| `Budget` | a partir de `06 Plan Analyze` |
| `Benefit Value` | a partir de `05 Cost Approv`. Opcional se `Business Benefit` ≠ `Value Added` |
| `Payback` | a partir de `06 Plan Analyze` |
| `GoLive Date` | a partir de `06 Plan Analyze` |
| `PGLS End Date` | a partir de `06 Plan Analyze` |

## FinalScore e Potencial

O `[FinalScore]` é calculado **no dataset** a partir de exatamente 4 pilares, cada um com peso próprio:

1. `[Payback in Months]`
2. `[Implemention Time in Months]`
3. `[Project Total Budget]`
4. `[Benefit Value]`

`[Potencial]` classifica pela cor: **Green** = alto · **Yellow** = médio · **Red** = baixo.

⚠️ **Se qualquer um dos 4 pilares estiver vazio, o cálculo falha e a classificação é `Incomplete` (Need Info).** Sempre leia `[FinalScore]` e `[Potencial]` do dataset — nunca recalcule nem estime.

## Ecossistemas

Projetos que compartilham nome-base (`Horizon 1` e `Horizon 2`) ou carregam tag `Related` formam **um ecossistema**. Se a fase 1 já foi entregue, herde o contexto dela e concentre a análise de risco estritamente na fase 2 ativa.
