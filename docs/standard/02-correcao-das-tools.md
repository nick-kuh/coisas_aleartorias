# 2. Correção das tools — o que abrir e o que colar

> ⚠️ **Cada descrição de entrada tem teto de 1.024 caracteres.** Os textos abaixo já vêm medidos, com a folga anotada. Se você editar algum, meça antes de colar — `python3 scripts/validate-topics.py` faz isso.

> 📌 **Este é o documento de referência.** Se você quer a ordem de execução — o que fazer primeiro, o que depende de terceiros e quando testar — comece por [`00-comece-aqui.md`](00-comece-aqui.md) e volte aqui para pegar os textos.

Cinco tools a corrigir, em ordem de impacto. Cada uma tem o texto pronto para colar e o teste de aceite.

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

> ## 🔴 Corrigido em 18/08 — o `botContent_76` provou que a configuração anterior estava errada
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

| Entrada | Preencher usando | Valor |
|---|---|---|
| `poster` | **escolher na lista** | **`Flow bot`** 🔴 *(trocar de "User")* |
| `location` | **escolher na lista** | **`Chat with Flow bot`** 🔴 *(trocar de "Group chat")* — a opção só aparece depois de trocar o `poster` |
| `body.bot` | — | **REMOVER a entrada** — só existe quando `poster` = Microsoft Copilot Studio agent |
| `body.recipient` | Dinamicamente com IA | ✅ **já funciona, não mexer** |
| `body.messageBody` | Dinamicamente com IA | ✅ **já funciona, não mexer** |

> ⚠️ **Escolha pelos dropdowns, nunca digite o texto.** Os dois campos são `dynamicValuesConfig: capability: List` — o valor gravado é interno, não o rótulo da tela. Prova no seu próprio histórico: quando você escolheu "Chat with agent", o export gravou `location: powerva`.

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

**Descrição da tool** (trocar a "Posta uma mensagem em um chat ou canal"):  `379/1024`

```
Sends a Microsoft Teams message to a Project IT Manager, delivered by the Flow
bot into the manager's 1:1 chat. The message must say who is asking, because it
arrives from a bot and not from the requesting user. Use ONLY after the user has
reviewed and explicitly approved the draft. Typical use: asking a manager for a
new Go-Live date on a delayed project. NEVER call this tool to answer a question
or to display information to the current user.
```

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

**`body.recipient`:** `The email address of the Project IT Manager who must receive the message. Take it from [Project IT Manager] in Power BI or from Assigned To in Azure DevOps. NEVER guess an email address.`

**`body.messageBody`:** `The message text, already reviewed and approved by the requesting user. Must open by naming WHO is asking, because it arrives from the Flow bot and not from that person. Must state the project name, the Work Item ID, the concrete problem and what is expected, and include the work item link.`

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
