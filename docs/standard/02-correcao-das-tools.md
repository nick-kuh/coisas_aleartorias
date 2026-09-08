# 2. Correção das tools — o que abrir e o que colar

> ⚠️ **Cada descrição de entrada tem teto de 1.024 caracteres.** Os textos abaixo já vêm medidos, com a folga anotada. Se você editar algum, meça antes de colar — `python3 scripts/validate-topics.py` faz isso.

> 📌 **Este é o documento de referência.** Se você quer a ordem de execução — o que fazer primeiro, o que depende de terceiros e quando testar — comece por [`00-comece-aqui.md`](00-comece-aqui.md) e volte aqui para pegar os textos.

Cinco tools a corrigir, em ordem de impacto. Cada uma tem o texto pronto para colar e o teste de aceite.

> ## 📋 O que ainda não está no agente — medido no `botContent_78`, 21/08
>
> Exportei o agente e comparei com o que está escrito neste repositório. Quatro coisas seguem por aplicar, em ordem de impacto no comportamento:
>
> | # | O quê | Como está no agente hoje | O que acontece por causa disso |
> |---|---|---|---|
> | 1 | 🔴 Descrição da fonte `Transcription LT Meetings` | promete `Each line is "Speaker: what they said"` | **o modelo inventa locutor** para caber na promessa — texto novo em [`06`](06-fluxo-transcricoes.md#3-ligar-no-agente) |
> | 2 | 🔴 Descrição de `Power BI Portfolio Database` | a genérica do conector, sem os valores válidos | ele inventa `Big Rocks` e `Make (Business Ops)`, que não existem — texto na Correção 2 |
> | 3 | 🟠 Instruções do agente | versão anterior, sem o §8 de criar/cancelar e sem o §10 | pode alegar que apagou um work item; não sabe reconciliar reunião × DevOps |
> | 4 | 🟡 `modelDisplayName` / `modelDescription` da tool do Teams | os padrão do conector | o modelo tem menos sinal de quando usar e o que mandar |
>
> ✅ Já aplicados e confirmados: as descrições de `Update Project`, `Create Project`, `Devops Query`, `Query Devops IT Area/BU`, `DevOps Work Item Details`, e a configuração `Flow bot` + `Chat with Flow bot` do Teams. A tool `Remove Project` foi removida, como combinado.

**Onde:** Copilot Studio → AURA Agent → **Ferramentas** → clique na tool → **Entradas**.

Para cada entrada há a coluna **"Preencher usando"**:
- **Valor personalizado** = fixo, você digita (`ManualTaskInput`)
- **Preencher dinamicamente com IA** = o modelo preenche (`AutomaticTaskInput`) — e a **descrição da entrada** é o único lugar onde o modelo aprende o formato

> ⚠️ Se uma entrada não aparece na lista, clique em **"+ Adicionar entrada"** / expanda **"Mostrar todas as entradas"**. É exatamente aí que os inputs se perderam.

---

## Correção 1 — `Update Project` 🔴 mais urgente

Hoje esta tool **não consegue atualizar nada**: recebe o `id` e não tem onde receber o que mudar.

### Entradas

| Entrada | Preencher usando | Valor |
|---|---|---|
| `account` | Valor personalizado | `CDIO-IT-LATAM` ✅ já está |
| `project` | Valor personalizado | `CDIO Portfolio` ✅ já está |
| `id` | Dinamicamente com IA | ✅ já está — só adicione a descrição abaixo |
| **`type`** | Valor personalizado | `IT Project` 🔴 **adicionar** |
| **`userEnteredFields`** | Dinamicamente com IA | 🔴 **adicionar** + descrição abaixo |

**Descrição da entrada `id`:**  `179/1024`

```
The unique numeric ID of the Azure DevOps Work Item (e.g., 12345). Use the
'Power BI Master DB Search' tool to resolve a project name to its Work Item ID
before calling this tool.
```

**Descrição da entrada `userEnteredFields`** — cole literalmente:  `996/1024`

```
A JSON object whose keys are FULL Azure DevOps reference names and whose values are the new values. Examples: "System.State", "System.AssignedTo", "Custom.GoLiveDate", "Custom.ProjectTotalBudget", "Custom.ProjectBenefitValue", "Custom.Note".
Include ONLY the field(s) the user asked to change.
"System.State" accepts ONLY these 13 strings: "00 Cancelled", "01 Idea", "02 Scoping", "03 Scope Approv", "04 Costing", "05 Cost Approv", "06 Plan Analyze", "07 Design Build", "08 UAT", "09 PGLS", "10 Deployed", "11 Closed", "12 On Holding". Never invent, abbreviate or drop the numeric prefix.
FORMATS: dates as YYYY-MM-DD. Money and months as plain numbers, no symbol, no separator.
NEVER send read-only fields: System.CreatedBy, System.CreatedDate, System.ChangedBy, System.ChangedDate, System.TeamProject, System.WorkItemType, or any Microsoft.VSTS.Common audit field. The PATCH fails.
NEVER call this tool before showing the user the exact before -> after change and getting explicit confirmation.
```

📎 Lista completa e conferida dos reference names `Custom.*`: [`skills/update-devops/references/campos-devops.md`](../../skills/update-devops/references/campos-devops.md)

✅ **Teste:** num work item **de teste**, peça `mude o Note do work item <id> para "teste AURA"`. Hoje não acontece nada.

---

## Correção 2 — `Power BI Portfolio Database` 🔴 destrava a análise

O dashboard de abertura funciona porque o tópico passa a query. Fora dele, o modelo não tem como escrever DAX.

### Entradas

| Entrada | Preencher usando | Valor |
|---|---|---|
| `groupid` | Valor personalizado | `4bd9bd39-a51b-4439-9248-805fd40a94a2` ✅ já está |
| `datasetid` | Valor personalizado | `afe9436e-b892-45a8-a3c0-e816f3e13258` ✅ já está |
| **`query`** | Dinamicamente com IA | 🔴 **adicionar** + descrição abaixo |

**Descrição da entrada `query`** — é este texto que ensina o modelo a escrever DAX válido:  `989/1024`

```
Return ONLY raw DAX, no markdown fences. MUST start with EVALUATE. Table is always 'tabela'.
Columns: [Work Item Id], [Title], [Short Name], [Project IT Manager], [State], [N State], [StatusProjeto], [Project Type], [IT Area], [BG or BU Engagement], [Specify Cross], [FinalScore], [Potencial], [Business Benefit], [Project Total Budget], [Budget Value], [Benefit Value], [Payback in Months], [Implemention Time in Months], [Country Deployed], [GoLive Date], [PGLS End Date], [Portfolio Year].
RULES: 1) Overview: SUMMARIZECOLUMNS. 2) Specific/risk: CALCULATETABLE or FILTER. 3) NEVER invent columns. 4) Default [Project Type] is 'Big Rock'. 5) Active projects are [N State] < 10. 6) BU acronyms: BPC = BW + PC, HPC = HC + PC, HPF = HC + PC + Foods. 7) A BU filter MUST also catch Cross projects naming it in [Specify Cross], via SEARCH.
Domains: [StatusProjeto] = Deployed | Delayed | In PGLS | Ending this Quarter | On Time | No Information. [Business Benefit] = Compliance | Value Added.
```

### Descrição da tool `Power BI Portfolio Database`  `960/1024`

Hoje é genérica e não diz **quais strings** são válidas num filtro. É por isso que o agente inventa valor de IT Area e recebe zero linhas sem entender por quê.

```
Use for any portfolio question: analysis, status, Big Rocks, risks, budgets, project details. Runs DAX against the live CDIO LATAM dataset.
Filter values must be written EXACTLY as below. A wrong string returns ZERO rows silently — it does not fail, it just looks like there is no data.
[IT Area] = Consumer | Customer Dev | Make (Business Operation) | Focus Market (Cust Ops) | Commercial Exp | Tech Services | Tax Reform
[Project Type] = Big Rock | Regular | Small Project
[BG or BU Engagement] = BW | PC | HC | Foods | 1UL | Cross
[Business Benefit] = Value Added | Compliance
[StatusProjeto] = Deployed | Delayed | In PGLS | Ending this Quarter | On Time | No Information
[State] = 00 Cancelled | 01 Idea | 02 Scoping | 03 Scope Approv | 04 Costing | 05 Cost Approv | 06 Plan Analyze | 07 Design Build | 08 UAT | 09 PGLS | 10 Deployed | 11 Closed | 12 On Holding
Two traps: "Big Rock" not "Big Rocks"; "Make (Business Operation)" not "Make (Business Ops)".
```

> ⚠️ As listas vieram do que o Power BI **devolveu** em execuções reais, não de memória. Duas correções que saíram daí: é `Big Rock` (singular) e `Make (Business Operation)` — não `Big Rocks` nem `Make (Business Ops)`.

📎 Receitas prontas (watermelons, big rocks, governança, filtro Cross-BU): [`skills/portfolio-overview/references/dax-cookbook.md`](../../skills/portfolio-overview/references/dax-cookbook.md)

✅ **Teste:** em conversa nova, depois do dashboard, pergunte `quais são os projetos watermelon?`. Ele tem que rodar uma query nova. Hoje ele improvisa em cima do que já está em `Global.tabela_pbi`, ou trava.

---

## Correção 3 — `Obter os detalhes do item de trabalho` 🔴

### Entradas

| Entrada | Preencher usando | Valor |
|---|---|---|
| `account` | Valor personalizado | `CDIO-IT-LATAM` ✅ |
| `project` | Valor personalizado | `CDIO Portfolio` ✅ |
| `typeName` | Valor personalizado | `IT Project` ✅ |
| **`id`** | Dinamicamente com IA | 🔴 **adicionar** |

**Descrição da entrada `id`:**  `156/1024`

```
The unique numeric ID of the Azure DevOps Work Item. Resolve the project name to
its Work Item ID with 'Power BI Master DB Search' before calling this tool.
```

### E restaure a descrição da tool

Hoje é `Obter os detalhes de um único item de trabalho`. Troque por:

```
SILENT TOOL. Fetches raw JSON data for a single Azure DevOps work item using its
unique ID. It returns technical fields, financial data and status. DO NOT
generate text, summaries or recommendations when using this tool. Only retrieve
the data for the system's internal reasoning.
The `url` field in the response is an API address (_apis/wit/workItems/) that
returns JSON. NEVER show it to the user. The human link is
https://dev.azure.com/CDIO-IT-LATAM/CDIO%20Portfolio/_workitems/edit/<id>
```

O `SILENT TOOL … DO NOT generate text` é o que impede o agente de despejar JSON cru na conversa.

✅ **Teste:** `me traz os detalhes do work item 376` — esse ID aparece no seu próprio log de conversa (`ANDEAN - Project - IT IC Demerge Ecuador`).

---

## Correção 4 — `Query Devops BU` 🟠

### Entradas

| Entrada | Preencher usando | Valor |
|---|---|---|
| `account` | Valor personalizado | `CDIO-IT-LATAM` ✅ |
| `project` | Valor personalizado | `CDIO Portfolio` ✅ |
| **`queryId`** | Dinamicamente com IA | 🔴 **adicionar** + descrição abaixo |

**Descrição da entrada `queryId`:**  `365/1024`

```
The GUID of the saved Azure DevOps query for a Business Unit. Pick from:
Foods = e15d1af6-0238-4e26-93ba-1f456b6258a9;
HC/Home Care = 61e1da44-eb44-4f0f-8ff7-385d045f397c;
PC/Personal Care = bf99b079-207d-4027-97c2-6573129c5400;
BW/Beauty & Wellbeing = 472b3677-9bd9-4289-8367-c61826219f3d;
anything else = 590e44b1-fdb4-4e3b-bd2e-32813b771443.
NEVER invent a GUID.
```

Faça o mesmo na **`Query Devops IT Area`** (o input `queryId` já existe, só falta a descrição):

```
The GUID of the saved Azure DevOps query for an IT Area. Pick from:
Make/Business Ops/Supply Chain = 8b53a319-c304-4d55-be7e-0e3b8e2c2d03;
Consumer/Marketing = 95581604-d21e-4268-a1fa-ca5bd59185f9;
CD/Customer Development = 10271fab-00ff-44c6-98d7-241877e53ee7;
Focus Market/Customer Operations = 236b80a4-395a-40cd-a962-8b3284fce608;
anything else = 590e44b1-fdb4-4e3b-bd2e-32813b771443.
NEVER invent a GUID.
```

📎 Tabela completa: [`skills/portfolio-overview/references/query-ids.md`](../../skills/portfolio-overview/references/query-ids.md)

✅ **Teste:** `me lista os projetos de Personal Care`.

---

## Correção 5 — `Teams — Postar mensagem` 🔴

Duas versões: escolha a que corresponde à sua situação hoje.

👉 **Guia completo com trade-offs:** [`03-teams-conversa-com-gestor.md`](03-teams-conversa-com-gestor.md) e [`../../topics/README.md`](../../topics/README.md), seção "Modo sem publicação"

### 5A — Modo SEM PUBLICAÇÃO

> ## ✅ RESOLVIDO em 19/08 — confirmado no `botContent_77`
>
> `poster: Flow bot` + `location: Chat with Flow bot` aplicados, **zero erros no log**. E o schema do conector se reescreveu sozinho, que é a prova: o `recipient` deixou de pedir `Add conversation ID` e passou a pedir `Enter a name or email address`.
>
> O que está abaixo fica como histórico do diagnóstico.

> ## 🔴 O erro que existia — o `botContent_76` provou que a configuração anterior estava errada
>
> Eu recomendava `poster: User` + `location: Group chat`. **Isso devolve HTTP 404.** O log mostra o agente enviando o par correto do ponto de vista dele:
>
> ```json
> { "poster": "User", "location": "Group chat",
>   "body": { "recipient": "Nicolas.Kuhnast@unilever.com", "messageBody": "Oi, tudo bem? ..." } }
> ```
>
> E o conector respondendo `404 · NotFound · ConnectorRequestFailure`, duas vezes.
>
> **A causa está no schema da própria tool:**
>
> ```yaml
> recipient:
>   displayName: Group chat
>   description: Add conversation ID     # ← ID de conversa, não e-mail
> ```
>
> Com `location: Group chat`, o `recipient` tem que ser um **ID de conversa** (`19:...@thread.v2`). O agente mandou um e-mail — certo para uma pessoa, errado para esse destino. O conector procurou um group chat com aquele nome e não achou.

Mensagem sai do **Flow bot**, no chat 1:1 do gestor com o Flow bot. Não depende de publicar o agente.

| Entrada | `kind` no YAML | Preencher usando | Valor / descrição |
|---|---|---|---|
| `poster` | `ManualTaskInput` | **escolher na lista** | **`Flow bot`** 🔴 *(trocar de "User")* |
| `location` | `ManualTaskInput` | **escolher na lista** | **`Chat with Flow bot`** 🔴 *(trocar de "Group chat")* — só aparece depois de trocar o `poster` |
| `body.bot` | — | — | **REMOVER a entrada** — só existe com `poster` = Microsoft Copilot Studio agent |
| `body.recipient` | `AutomaticTaskInput` | Dinamicamente com IA | declarar **+ colar a descrição** abaixo |
| `body.messageBody` | `AutomaticTaskInput` | Dinamicamente com IA | declarar **+ colar a descrição** abaixo |

> ### Quais entradas aceitam descrição — e quais não
>
> Contando os 30 inputs declarados no seu agente, o padrão é absoluto:
>
> | `kind` | Quantos | Com `description` | Com `value` fixo |
> |---|---|---|---|
> | `AutomaticTaskInput` | 6 | **6 de 6** ✅ | 0 |
> | `ManualTaskInput` | 24 | **0 de 24** | 23 |
>
> **Descrição só existe em `AutomaticTaskInput`.** Um `ManualTaskInput` tem valor fixo que você digitou — o modelo nunca preenche nem lê. Descrever `poster: User` é escrever para ninguém.
>
> Ou seja: em `poster` e `location`, **não perca tempo**. Em `body.recipient` e `body.messageBody`, a descrição é a **única** coisa que guia o modelo — é a mesma camada que fez o DAX passar a sair certo. Declarados e sem descrição, os dois são preenchidos às cegas.

> ### ⚠️ `poster` e `location`: escolha na lista, nunca edite o YAML
>
> Os dois são `dynamicValuesConfig: capability: List`, e o valor gravado **não é o rótulo da tela**. O seu próprio histórico mostra que os casos se comportam diferente:
>
> | O que você escolheu | O que o export gravou |
> |---|---|
> | "Chat with agent" | `powerva` — **não** o rótulo |
> | "Group chat" | `Group chat` — literal |
>
> Não dá para saber qual literal o "Chat with Flow bot" grava, e chutar quebra a tool. Escolher na lista resolve sozinho.
>
> Já os dois `AutomaticTaskInput` são texto livre — descrição pode ser editada à vontade.

> ### ✅ Duas coisas que este export desmentiu
>
> Eu vinha afirmando as duas, e o log mostra o contrário:
>
> | Eu dizia | O log mostra |
> |---|---|
> | "Faltam `body.recipient` e `body.messageBody` como entradas" | **Estão sendo enviados normalmente**, mesmo sem estarem declarados em `inputs:`. O orquestrador preenche pelo `dynamicInputSchema`. **Não há nada a adicionar.** |
> | "`body.bot` vazio é a causa provável do erro" | Não é. A causa é o par `location`/`recipient`. Remover o `body.bot` continua valendo, mas é limpeza, não correção. |

> ### 🎯 O teste que destrava tudo
>
> Troque o `poster` para **Flow bot** e abra o dropdown de `location`. **Se "Chat with Flow bot" aparecer**, o Flow bot está liberado no seu tenant e o caminho está aberto.
>
> **Se não aparecer**, o Flow bot está bloqueado por política e o único caminho é publicar o agente — vá para o **5B**. O Flow bot é first-party e existe onde há Power Automate, mas alguns tenants bloqueiam o app. Não tenho como verificar isso daqui.

**Descrição da tool** (trocar a "Posta uma mensagem em um chat ou canal"):  `586/1024`

```
Sends a Microsoft Teams message to a Project IT Manager, delivered by the Flow bot into the manager's 1:1 chat. Resolve the recipient YOURSELF from the project data ([Project IT Manager], falling back to Assigned To) — never ask the user who to send to. The message must say who is asking, because it arrives from a bot, not from the requesting user. Use ONLY after the user has reviewed and explicitly approved the draft. Typical use: asking a manager for a new Go-Live date on a delayed project. NEVER call this tool to answer a question or to display information to the current user.
```

> 🎯 **A frase `Resolve the recipient YOURSELF … never ask the user who to send to` é a que você pediu:** o agente pega o `[Project IT Manager]` sozinho e não pergunta "para quem envio". A trava `Use ONLY after … approved the draft` fica — a aprovação do rascunho continua obrigatória.

### 5B — Modo PUBLICADO (quando o publish sair)

Mensagem sai como o AURA Agent, no chat 1:1 do gestor com o agente. Fecha o ciclo de mão dupla — a resposta do gestor volta ao agente.

| Entrada | Preencher usando | Valor |
|---|---|---|
| `poster` | Valor personalizado | `Microsoft Copilot Studio agent` *(trocar de "User")* |
| `location` | Valor personalizado | `Chat with agent` *(trocar de "Group chat")* |
| **`body.bot`** (Agent) | Valor personalizado | selecionar **AURA Agent** — dropdown fica populado depois de publicar |
| `body.recipient` | Dinamicamente com IA | idem |
| `body.messageBody` | Dinamicamente com IA | idem |

**Descrição da tool no modo publicado:**  `331/1024`

```
Sends a Microsoft Teams message from the AURA Agent to a Project IT Manager.
Use ONLY after the requesting user has reviewed and explicitly approved the
message draft. Typical use: asking a manager for a new Go-Live date on a
delayed project. NEVER call this tool to answer a question or to display
information to the current user.
```

### Descrições das duas entradas dinâmicas (valem nos dois modos)

**Descrição da entrada `body.recipient`**  `330/1024`

```
Email of the Project IT Manager who must receive the message. Resolve it YOURSELF: call Power BI Master DB Search or DevOps Work Item Details and read [Project IT Manager], falling back to Assigned To. NEVER ask the user who to send to. NEVER guess or construct an address — if the field is empty in both sources, say so and stop.
```

> Esta entrada é `AutomaticTaskInput` (dinâmica) — a descrição é lida pelo modelo. É aqui que o "pegar o IT Manager sozinho, sem perguntar" realmente pega. O `NEVER guess … if the field is empty, say so and stop` é o guardrail: sem e-mail no sistema, ele para em vez de inventar.

**Descrição da entrada `body.messageBody`**  `297/1024`

```
The message text, already shown to and explicitly approved by the requesting
user. Open by naming WHO is asking — it arrives from the Flow bot, not from that
person. State the project as Name (1234), the concrete gap, what is expected
back, and include the link as
https://dev.azure.com/CDIO-IT-LATAM/CDIO%20Portfolio/_workitems/edit/<id> — never an
_apis/wit/ address. Max 5 lines.
```

---

## Correções opcionais, mas baratas

### O quinto KPI

A `tabela_agente` devolve `% High Potencial` (6% no seu log) e o tópico não mostra. Em `Início da conversa`, duplique um `SetVariable`:

```yaml
- kind: SetVariable
  id: setVar_HighPotencial
  variable: Topic.high_potencial
  value: =LookUp(Topic.TabelaPronta, 'tabela_agente[Value1]' = "% High Potencial").'tabela_agente[Value2]'
```

E acrescente a linha no `SendActivity`: `- **Projetos de Alto Potencial:** {Topic.high_potencial}`

### A saudação em português

O agente é pt-BR e as instruções mandam responder em português, mas a saudação do tópico está em inglês. Em `Início da conversa` → `sendMessage_Greeting`:

```
**{System.Bot.Name}  |**  _See Beyond_

Olá {System.User.FirstName}. Um instante enquanto eu cruzo os dados do portfólio para montar o dashboard executivo de hoje...
```

E o `SendActivity` do resumo, que também está em inglês.

### O typo nas instruções

Procure `[Project Total Budget**€**)]` e troque por `[Project Total Budget (**€**)]`.

### Capacidades do agente

Em **Configurações → Recursos generativos**:

- **Navegação na web:** hoje `true`. Num agente de dado corporativo isso convida o modelo a buscar na web pública e misturar com o portfólio. Considere **desligar** (o antigo tinha `false`).
- **Interpretador de código:** hoje ausente; o antigo tinha `true`. Se existir o toggle, **ligue** — é o que dá conta determinística. Enquanto não tiver, a mitigação já está nas instruções: sempre **ler** `[FinalScore]` do dataset, nunca recalcular.

### `Project Deep Dive` procura numa base que não existe

O tópico manda buscar na `'base mestra'`, que não é fonte de conhecimento nenhuma do agente. Substitua o primeiro `SearchAndSummarizeContent` (`findProjectID`) por uma chamada à tool `Power BI Master DB Search`, que é feita exatamente para resolver nome → ID. É a mudança que mais melhora a precisão do Deep Dive.

---

## Verificação

### Ordem de teste

| # | Digite | Esperado | Hoje |
|---|---|---|---|
| 1 | (abra conversa nova) | Dashboard com os 4 KPIs | ✅ já funciona |
| 2 | `quais são os projetos watermelon?` | Roda DAX nova e responde | ❌ |
| 3 | `me traz os detalhes do work item 376` | Traz os campos, sem JSON cru | ❌ |
| 4 | `me lista os projetos de Personal Care` | Usa o Query ID de PC | ❌ |
| 5 | `mude o Note do work item <teste> para "teste AURA"` | Confirma e grava | ❌ |
| 6 | `analise o projeto <nome real>` | Deep Dive com os 4 blocos | ✅ parcial |

### Teste das fontes de conhecimento

O tipo mudou para busca de site e a do Wiki aponta para um `.pdf`. Confirme:

| Pergunta | Esperado |
|---|---|
| `o que é a fase 09 PGLS?` | Resposta vinda do Wiki, com citação |
| `o que a liderança de Make decidiu na última reunião?` | Resposta vinda das Transcrições |

Se vier vazio ou genérico: em **Conhecimento**, remova a fonte e adicione de novo pela opção de **arquivo/pasta do SharePoint** (não a de busca em site) — para o Wiki, apontando o PDF; para as Transcrições, apontando a pasta.
