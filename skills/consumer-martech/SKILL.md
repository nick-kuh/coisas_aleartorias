---
name: consumer-martech
description: >
  Portfólio do time de Consumer BPC (B&W Marketing Technology) — que roda FORA
  do DevOps, num tracker Excel próprio. Modelo diferente do resto do agente:
  frentes (Insights, Media & Influencer, dCom and Social Commerce, CoPilot and
  Agentic, LLM Search / GEO, Beauty Tech) → iniciativas → fase (Adoption,
  Deployment, Framework, Status) → farol por mercado (BR/MX/AR). Devolve saúde
  por frente, riscos/críticos, gargalos de adoção e, quando pedirem, o dashboard
  HTML. Use quando o usuário falar em "Consumer", "MarTech", "B&W Marketing
  Technology", "as frentes", "o farol por mercado", uma das seis frentes ou uma
  iniciativa do tracker (Winnin, 5Vs, FIBRA, Brands Training…), ou pedir o
  dashboard/HTML de Consumer. NÃO use para o portfólio DevOps/Power BI, para a
  IT Area "Consumer" do DevOps, nem para projetos com Work Item Id (use
  portfolio-overview ou project-deep-dive).
---

# Consumer BPC — B&W Marketing Technology

> **Este é um mundo separado do resto do agente.** O portfólio geral vive no
> DevOps + Power BI, tem Work Item Id, fases `01`–`11`, budget e benefício em €.
> O time de **Consumer** (B&W Marketing Technology) **não usa DevOps**: acompanha
> tudo num tracker Excel por frente e por farol de mercado. Aqui **não existe**
> Work Item Id, DAX, budget nem link do Azure DevOps. Nunca misture os dois.
> Nunca chame tool de DevOps, Power BI **nem a tool de relatório executivo
> (CreateReport / Publish Area Report)** para responder algo de Consumer — aquele
> relatório é do portfólio DevOps. Para o board de Consumer **você mesmo escreve o
> HTML** (Passo 5): é a única exceção à regra de não montar HTML à mão.

## Passo 1 — A fonte

Os dados vêm da fonte de conhecimento **`Consumer MarTech Tracker`** (o Excel
`BW_MarTech_2026_Controle_Projetos.xlsx`, abas **Tracker**, **Painel** e
**Legenda**). É a única fonte para qualquer pergunta de Consumer. Se ela não
retornar, diga que o tracker de Consumer não está disponível — **nunca** invente
uma iniciativa, uma fase ou um status.

## Passo 2 — O modelo de dados

Quatro níveis, de fora para dentro. Detalhe completo em
`references/frentes-e-status.md`; o universo atual de iniciativas em
`references/tracker-2026.md`.

| Nível | O que é | Valores |
|---|---|---|
| **Frente** | O pilar da área (equivale a "programa") | Insights · Media & Influencer · dCom and Social Commerce · CoPilot and Agentic · LLM Search / GEO · Beauty Tech |
| **Iniciativa** | O projeto | texto livre (Winnin, 5Vs Dashboard, FIBRA…) |
| **Item** | Recorte da iniciativa, quando há | marca ou função (Dove, Clear, CMI…) — pode estar vazio |
| **Fase** | Estágio daquela linha | Adoption · Deployment · Framework · Status |
| **BR / MX / AR** | Farol daquele mercado | ver tabela de status abaixo |

Uma iniciativa costuma ter **duas linhas** — `Deployment` e `Adoption` — porque
o valor só se realiza quando a entrega (Deployment) **e** a adoção (Adoption)
estão no verde. Trate as duas juntas.

### Os cinco status (o farol)

| PT (no tracker) | EN | Leitura |
|---|---|---|
| **No prazo** | On Track | entregue / rodando conforme o plano |
| **Atenção** | At Risk | em andamento com risco moderado |
| **Crítico** | Critical | atrasado ou bloqueado — **requer ação** |
| **Não iniciado** | Not Started | ainda não começou |
| **N/A** | Not Applicable | não se aplica àquele mercado |

Mercados: **BR** = Brasil · **MX** = México · **AR** = Argentina.

## Passo 3 — Como você analisa (as quatro lentes de Consumer)

Não devolva uma planilha reescrita. Devolva um **juízo**. Toda análise cruza
quatro ângulos — o equivalente, neste mundo, às quatro lentes do portfólio:

1. **Realização de valor (Deployment × Adoption).** A lente principal. Uma
   iniciativa com `Deployment = No prazo` mas `Adoption = Não iniciado` foi
   entregue e **não está gerando valor** — é o "watermelon" de Consumer.
   Priorize destravar adoção, não celebrar a entrega.
2. **Críticos primeiro.** Todo `Crítico` é ação imediata, com mercado e frente
   nomeados. Ex.: `Insights / 5Vs Dashboard / Adoption / BR` e
   `Insights / FIBRA / Adoption / BR` — dois críticos, mesma frente, mesmo
   mercado, mesma fase (adoção no Brasil). Isso é concentração, reporte como tal.
3. **Concentração por mercado.** Compare BR × MX × AR. Onde o risco se acumula?
   Um mercado muito mais atrás que os outros na mesma frente é um problema de
   execução local, não de produto.
4. **Backlog (Não iniciado).** Muitos `Não iniciado` numa frente = escopo grande
   parado. Diga quanto do ativo ainda não começou e o que destrava mais valor
   com menos esforço (assimetria).

**Saúde por frente (farol) — a MESMA regra do Painel do Excel:**

- conte as células BR+MX+AR da frente, **excluindo N/A**;
- `% No prazo` = No prazo ÷ total contado;
- **🔴** se houver **qualquer** Crítico · **🟢** se **sem** crítico e `% No prazo ≥ 50%` · **🟡** nos demais casos.

## Passo 4 — Formato de saída (análise)

Mais de uma frente ou visão geral → **dashboard conciso**:

```
**📊 CONSUMER — SAÚDE POR FRENTE**
| Frente | No prazo | Atenção | Crítico | Não iniciado | % No prazo | Farol |
(as seis frentes + total)

**🔴 CRÍTICOS**
Frente / Iniciativa / Fase / Mercado — o que está bloqueado. Um por linha.

**🟠 ENTREGUE MAS SEM ADOÇÃO**
Iniciativas com Deployment no verde e Adoption parado — valor não realizado.

**🎯 DIRETRIZ DOS PRÓXIMOS 30 DIAS**
Um veredito e a ação que a liderança cobra, com frente, mercado e responsável.
```

Uma frente ou uma iniciativa → **deep dive**: as linhas dela (Deployment e
Adoption), o farol de cada mercado, o que está em jogo, e a decisão recomendada.

## Passo 5 — Montar o dashboard HTML

Quando pedirem "o HTML", "o dashboard de Consumer" ou "a agenda de Consumer",
gere o HTML completo seguindo `references/html-template.md` — visual "marketing":
**hero roxo** com o logo oficial Unilever · Beauty & Wellbeing (o vetor real em
`assets/logo-bw.svg`, inline e branco), régua de stats, **corpo branco** e um
**card por frente** com os status BR/MX/AR como **chips coloridos**. O esqueleto,
os tokens de cor (claro/escuro), a regra do farol dot, o destaque dos blocos e o
mapeamento status → chip estão todos lá. Monte um card por frente com um bloco por
iniciativa e os três chips por mercado; feche com a faixa Marketing Operations.
**Use o logo real, nunca redesenhe.** Entregue **um arquivo HTML só**, sem
dependências externas.

> Fora do Copilot Studio, o mesmo HTML sai automático do Excel com
> `python3 scripts/gerar-consumer-html.py` — útil para o time regerar a página
> quando o tracker muda.

## ⛔ Regras (não negociáveis)

- **Nunca invente.** Frente, iniciativa, item, fase ou status só entram na
  resposta se vieram do **`Consumer MarTech Tracker`** nesta conversa. Sem a
  fonte, diga que o tracker não carregou e pare.
- **Não misture os mundos.** Nada de Work Item Id, DAX, budget €, link de DevOps
  ou nome de projeto do Power BI numa resposta de Consumer.
- **N/A não é risco.** Não conte N/A no farol nem cobre um mercado onde a
  iniciativa não se aplica.
- **`Não iniciado` é backlog, não fracasso** — é escopo à espera de começar, não
  um projeto fraco.
- Responda sempre em português. Mercados sempre nomeados (Brasil, México,
  Argentina), nunca só a sigla solta numa recomendação.
