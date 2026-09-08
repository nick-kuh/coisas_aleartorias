# 10. Prompts sugeridos — a biblioteca do AURA Agent

> Escritos a partir das tools, das fontes de conhecimento e das frases-gatilho reais do `crdc4_AURAAgent`. Cada prompt roteia para uma capacidade que existe.
> **Limite do produto:** até **10 prompts sugeridos** aparecem nos cards do Teams / M365 Copilot. A seleção está em [§ Os 10 para os cards](#os-10-para-os-cards).

---

## ⚠️ Antes de escrever qualquer prompt — as frases proibidas

Tópico tem prioridade sobre a orquestração generativa. Se um prompt sugerido usar uma frase-gatilho de tópico, ele **desvia** do agente e cai num script.

### 🔴 `Project Deep Dive` (ATIVO — e quebrado)

| Frase-gatilho | Nunca use em prompt sugerido |
|---|---|
| `analise o projeto` | 🔴 |
| `quero ver o projeto` | 🔴 |
| `detalhar a iniciativa` | 🔴 |
| `status da iniciativa específica` | 🔴 |
| `informações detalhadas da iniciativa` | 🔴 |

O tópico busca em `'base mestra'` e numa "base de documentos do SharePoint" — **nenhuma das duas é fonte de conhecimento cadastrada** no agente. E as chamadas não têm `mode: Restricted`, então a busca pode cair no conhecimento do modelo: um `ID` inventado atravessa o `SetVariable` e vira chamada ao DevOps.

**"Analise o projeto X" é o prompt mais natural do mundo — e é o único que você não pode sugerir.** Toda a biblioteca abaixo contorna isso.

### 🟡 `Escalonar` (ATIVO)

Cuidado com `Preciso que um gerente me contate` e `Preciso que um gerente entre em contato comigo` — são gatilhos do escalonamento para humano, não da cobrança de gestor. Ficam perto demais da linguagem de portfólio.

### ⚪ Sem risco

`cobrancagestor` e `respostadogestor` estão `Inactive` (intencional, §5). Frases como `a nova data é` ou `cobrar o gestor` **não** disparam tópico — vão para a orquestração generativa, que é onde você quer.

---

## 1. Relatórios

**Por trás:** `Read Area Portfolio` → você escreve a análise → `Publish Area Report` → devolve `report_url`. Duas tools, em ordem.

```
Gera o relatório executivo de Make (Business Operation) do portfólio 2026 e me manda o link.
```
```
Quero o relatório publicado só dos Big Rocks com Go-Live vencido no Brasil.
```
```
Monta o relatório do portfólio sob o Rafael Silotto e me passa a página.
```

> 💡 **Peça a página explicitamente** — "relatório", "publicado", "link", "board". Sem isso o agente responde no chat e nunca chama a segunda tool. É comportamento correto dele, não falha.

> ⚠️ **Consumer tem board próprio.** `Consumer Report 1` devolve `board_url` e sai do Excel, não do DevOps. Nunca misture no mesmo pedido.

---

## 2. Analisar um projeto específico

**Por trás:** Power BI resolve o nome → ID, DevOps traz o estado vivo, as transcrições explicam o porquê.

```
Me dá um deep dive do CB TAX Reform [Phase 2] (1256): onde está o risco e o que eu decido.
```
```
O que está travando o 1256? Cruza o DevOps com o que ficou registrado na última LT.
```
```
Faz a auditoria de governança do work item 1256 — o que falta para ele estar compliant.
```

> 💡 Sempre `Nome (1234)` ou o ID puro. O agente é obrigado a citar assim de volta (§9), e passar o ID economiza uma ida ao Power BI.

---

## 3. Analisar o portfólio inteiro

**Por trás:** Power BI Portfolio Database com DAX escrito pelo próprio agente. As 4 lentes: valor em risco · momento · concentração · assimetria.

```
Como está o portfólio CDIO LATAM hoje? Visão executiva com os outliers.
```
```
Onde está o maior valor em risco do portfólio agora, e o que eu faço a respeito?
```
```
Quais são os watermelons? Projetos verdes com benefit zerado ou Go-Live vencido.
```
```
Me mostra a assimetria: pouco esforço, muito valor. O que está barato de destravar?
```

> ⚠️ **"Portfólio inteiro" obriga a incluir Consumer** (§0 das instruções) — a seção Consumer vem do Excel, por frente e farol, sem €budget. Se a resposta não trouxer Consumer, a instrução foi ignorada e vale reportar.

---

## 4. Analisar o portfólio de uma área

**IT Areas exatas:** `Consumer` · `Customer Dev` · `Make (Business Operation)` · `Focus Market (Cust Ops)`. Menores: `Commercial Exp` · `Tech Services` · `Tax Reform`.

```
Panorama do Customer Dev: saúde, quebra por fase e onde eu olho primeiro.
```
```
Focus Market (Cust Ops) — algum gestor com mais de 5 Big Rocks ativos?
```
```
Make (Business Operation): lista o que está parado há mais de 60 dias em 02 Scoping.
```
```
Quanto de budget o Customer Dev tem preso em projetos sem Benefit preenchido?
```

**Consumer é outro idioma** — nunca ID, nunca budget, nunca DevOps:

```
Como está o Consumer? Visão por frente, com o farol BR/MX/AR e onde o valor não está sendo realizado.
```

---

## 5. Dúvidas sobre a Unilever (vocabulário e estrutura)

**Por trás:** o dicionário de BUs e a regra Cross-BU vivem nas próprias instruções (§3).

```
O que é BPC e o que entra nele quando eu filtro o portfólio?
```
```
Como funciona a regra de Cross-BU? Se eu pedir PC, o que mais entra na conta?
```
```
Quais são as IT Areas do CDIO LATAM e o que cada uma cobre?
```
```
O que conta como um ecossistema aqui, e por que Horizon 1 e Horizon 2 são a mesma iniciativa?
```

> 🔴 **Limite honesto:** o agente **não tem fonte sobre a Unilever corporativa** — RH, políticas, benefícios, organograma, resultados financeiros. Com `useModelKnowledge: true` e `webBrowsing: true` ligados, ele **vai responder mesmo assim**, do conhecimento do modelo ou da web, sem citar de onde.
>
> Duas saídas: (a) não sugerir esse tipo de pergunta e deixar claro que AURA é portfólio; (b) desligar `useModelKnowledge` para ele admitir que não sabe. **Recomendo (b)** — num agente que fala de €456 Mi, uma resposta inventada sobre política interna custa mais do que a conveniência vale.

---

## 6. Como funciona o CDIO (governança)

**Por trás:** `CDIO_LATAM_Governance_Wiki` + `AURA_Playbook_Analitico.docx`. Pergunta conceitual não gera query nem dashboard (§9).

```
Quais campos são obrigatórios para um projeto passar de 05 Cost Approv?
```
```
Explica as 13 fases do CDIO — o que cada uma exige antes de avançar.
```
```
O que é PGLS, e quando um projeto pode sair dessa fase?
```
```
Quando Specify Cross vira obrigatório?
```
```
Como o FinalScore é calculado?
```

> 💡 O `FinalScore` é insumo de triagem, nunca manchete (§4). O agente só abre a matemática **se você perguntar como** — é exatamente o que este último prompt faz.

---

## 7. Pedir para atualizar um projeto

**Por trás:** `Update Project` no DevOps. Protocolo §8: lê o valor atual → mostra **de → para** → espera confirmação explícita → grava → confirma. Ele não encadeia isso sozinho.

```
Preciso atualizar o Go-Live do 1256. A nova data é 30/11/2026.
```
```
O budget do 1256 mudou para €4,5 Mi. Pode atualizar?
```
```
Muda o state do 1256 para 08 UAT.
```
```
O gestor confirmou o benefit do 1256 em €12 Mi — grava isso.
```

> ⚠️ **Aposentar um projeto é mudar o State para `00 Cancelled`**, o que preserva o histórico e a série do Power BI. **Nenhuma tool apaga work item** — se o agente disser que apagou, mentiu (§8).

---

## 8. Criar um projeto

**Por trás:** `Create Work Item`. Só com pedido explícito, rascunho completo na tela, cria depois do sim. Novo projeto nasce em `01 Idea`.

```
Quero criar um projeto novo no portfólio. Me guia pelos campos obrigatórios.
```
```
Cria um work item: nome "<Nome>", IT Area Customer Dev, BU PC, Brasil, Big Rock, ano 2026.
```
```
Vou abrir uma iniciativa nova de Focus Market. O que você precisa de mim antes de criar?
```

> 💡 O agente **nunca inventa título** — ele pergunta. O primeiro prompt é o melhor para quem nunca criou: ele conduz o preenchimento.

---

## 9. Bônus — reconciliar uma reunião de LT

**Por trás:** `Transcription LT Meetings`, arquivos `LT-<Área>-AAAA-MM-DD-HHmm`. A busca ignora recência, então **diga a área e a data**.

```
Compara a LT de Consumer de 02/09 com o DevOps e me diz o que está desatualizado.
```
```
Na última LT de Make, o que foi comprometido que ainda não apareceu no portfólio?
```

---

## 10. Bônus — cobrar o gestor 🔴 bloqueado hoje

Os prompts abaixo estão certos, mas o envio **falha com HTTP 400** até a correção do `body.attribution` ser publicada — ver [`09-erro-400-label-as-notification.md`](09-erro-400-label-as-notification.md). **Não coloque nos cards antes disso.**

```
Cobra o gestor do 1256 pedindo a nova data de Go-Live.
```
```
Manda uma mensagem para o responsável do 1256 pedindo o Benefit Value.
```

---

## Os 10 para os cards

Uma por capacidade, cobrindo o caminho inteiro sem repetir tool. Título curto + prompt.

| # | Título do card | Prompt |
|---|---|---|
| 1 | **Visão do portfólio** | `Como está o portfólio CDIO LATAM hoje? Visão executiva com os outliers.` |
| 2 | **Onde está o risco** | `Onde está o maior valor em risco do portfólio agora, e o que eu faço a respeito?` |
| 3 | **Panorama de uma área** | `Panorama do Customer Dev: saúde, quebra por fase e onde eu olho primeiro.` |
| 4 | **Consumer** | `Como está o Consumer? Visão por frente, com o farol BR/MX/AR.` |
| 5 | **Deep dive de projeto** | `Me dá um deep dive do <Nome do Projeto> (<ID>): onde está o risco e o que eu decido.` |
| 6 | **Watermelons** | `Quais são os watermelons? Projetos verdes com benefit zerado ou Go-Live vencido.` |
| 7 | **Relatório publicado** | `Gera o relatório executivo de <Área> do portfólio 2026 e me manda o link.` |
| 8 | **Regras de governança** | `Quais campos são obrigatórios para um projeto passar de 05 Cost Approv?` |
| 9 | **Atualizar um dado** | `Preciso atualizar o Go-Live do <ID>. A nova data é DD/MM/AAAA.` |
| 10 | **Criar iniciativa** | `Quero criar um projeto novo no portfólio. Me guia pelos campos obrigatórios.` |

Quando a cobrança do Teams voltar, ela substitui o card **6** — watermelon já aparece dentro do **2**.

---

## Colunas reais do dataset

Para escrever prompts novos que o DAX consiga responder. Extraídas de uma resposta real da tool:

`Area Path` · `Assigned to` · `BG or BU Engagement` · `Benefit Formatado` · `Benefit Value` · `Budget Formatado` · `Budget Value` · `Business Benefit` · `Business Products Domain` · `ColorRule` · `Compliance Status` · `Country Deployed` · `Created Date` · `DiasRestantes` · `FinalScore` · `GoLive Date` · `IT Area` · `Implemention Time in Months` · `N State` · `Num Proj Type` · `OrdemPotencial` · `PGLS End Date` · `Payback in Months` · `Portfolio Year` · `Potencial` · `Project Approved` · `Project IT Budget` · `Project IT Manager` · `Project Total Budget` · `Project Type` · `ROI (%)` · `Sem Informação?` · `Short Name` · `Specify Cross` · `State` · `StatusProjeto` · `Title` · `Titulo com Emoji` · `Work Item Id` · `Work Item Type`

Duas que rendem prompt bom e ninguém usa: **`DiasRestantes`** (negativo = atrasado) e **`Sem Informação?`** (a lacuna de governança já calculada no modelo).

```
Quantos projetos estão com DiasRestantes negativo e ainda não chegaram em 10 Deployed?
```

---

## Fontes

- [Configure suggested prompts for Teams and Microsoft 365 — Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-copilot-studio/configure-starter-prompts)
