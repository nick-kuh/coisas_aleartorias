# Frentes, fases e status — Consumer BPC (B&W MarTech)

Referência de vocabulário do tracker de Consumer. Tudo aqui vem do Excel
`BW_MarTech_2026_Controle_Projetos.xlsx` (abas Tracker / Painel / Legenda).
Nada é DevOps: não há Work Item Id, DAX, budget nem link do Azure.

## As seis frentes (pilares da área)

Ordem canônica — use sempre nesta ordem em dashboards e tabelas:

1. **Insights**
2. **Media & Influencer**
3. **dCom and Social Commerce**
4. **CoPilot and Agentic**
5. **LLM Search / GEO**
6. **Beauty Tech**

"Frente" é o pilar/programa da área. Cada frente agrupa várias **iniciativas**
(os projetos). Uma iniciativa pode ter uma coluna **Item** (recorte por marca ou
função — Dove, Clear, CMI…) quando faz sentido quebrá-la.

## As quatro fases

A fase diz em que estágio aquela **linha** da iniciativa está. Cada iniciativa
costuma aparecer em duas linhas (Deployment + Adoption).

| Fase | Significado |
|---|---|
| **Deployment** | Colocar a solução no ar / entregar a capacidade |
| **Adoption** | Fazer os times de fato usarem a solução entregue |
| **Framework** | Estruturar o modelo/processo repetível (ainda não é entrega nem adoção) |
| **Status** | Linha única de acompanhamento — usada quando a iniciativa não se separa em Deployment/Adoption (ex.: treinamentos de marca, agentes) |

**Deployment sem Adoption = valor não realizado.** Entregar não é adotar. A
frente só "vale" quando a adoção acompanha a entrega.

## Os cinco status (farol) e o mapeamento EN

| PT (no tracker) | EN | Classe da pill (HTML) | Cor Excel (origem) | Leitura |
|---|---|---|---|---|
| **No prazo** | On Track | `good` | verde `C6EFCE` | entregue / rodando conforme o plano |
| **Atenção** | At Risk | `warn` | amarelo `FFEB9C` | em andamento com risco moderado |
| **Crítico** | Critical | `bad` | vermelho `FFC7CE` | atrasado ou bloqueado — requer ação |
| **Não iniciado** | Not Started | `idle` | cinza `E2E2E2` | ainda não começou |
| **N/A** | Not Applicable | `na` | cinza claro `F5F5F5` | não se aplica àquele mercado |

## Mercados

| Sigla | País |
|---|---|
| **BR** | Brasil |
| **MX** | México |
| **AR** | Argentina |

Cada iniciativa carrega um farol por mercado. Um mercado pode ser `N/A` (a
iniciativa não roda ali) sem afetar os outros.

## Regra de saúde por frente (idêntica à aba Painel)

Para cada frente:

1. Conte as células de status **BR + MX + AR**, **excluindo N/A** (e vazias).
2. `Total ativo` = soma de No prazo + Atenção + Crítico + Não iniciado.
3. `% No prazo` = No prazo ÷ Total ativo.
4. Farol:
   - **🔴 Crítico** → existe **qualquer** célula Crítico na frente;
   - **🟢 Verde** → **nenhum** crítico **e** `% No prazo ≥ 50%`;
   - **🟡 Amarelo** → todos os demais casos (sem crítico, `% No prazo < 50%`).

O mesmo vale para o total geral do portfólio de Consumer.

## As quatro lentes de análise de Consumer

Espelham as quatro lentes do portfólio DevOps, traduzidas para este mundo:

| Lente | Pergunta | Sinal de alerta |
|---|---|---|
| **Realização de valor** | A adoção acompanha a entrega? | Deployment verde + Adoption `Não iniciado`/`Crítico` |
| **Críticos** | O que está bloqueado agora? | Qualquer `Crítico`, nomeado por frente/iniciativa/fase/mercado |
| **Concentração** | O risco se acumula onde? | Um mercado, uma frente ou uma fase concentrando os piores status |
| **Assimetria / backlog** | O que destrava mais valor com menos esforço? | Muito `Não iniciado` numa frente de alto retorno |

Regra de ouro: **nunca reporte um número cru — reporte um juízo e uma ação.**
