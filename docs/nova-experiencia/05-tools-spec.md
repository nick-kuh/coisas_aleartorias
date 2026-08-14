# 5. Ficha técnica das 8 tools

Tudo aqui foi extraído do `botContent.yml` original. **Nenhum GUID, `operationId` ou nome de campo foi inventado.**

Legenda da coluna *Preencher usando*:
- **Valor personalizado** = fixo, você digita (era `ManualTaskInput`)
- **Dinamicamente com IA** = o modelo preenche (era `AutomaticTaskInput`)

---

## Constantes do ambiente

| Constante | Valor | Vem de |
|---|---|---|
| Power BI — workspace (`groupid`) | `4bd9bd39-a51b-4439-9248-805fd40a94a2` | `botContent.yml` L164, L3010, L3338 |
| Power BI — dataset (`datasetid`) | `afe9436e-b892-45a8-a3c0-e816f3e13258` | L168, L3014, L3342 |
| Power BI — tabela principal | `'tabela'` | descrição do input DAX (L3355+) |
| Power BI — tabela de KPIs | `'tabela_agente'` (colunas `Value1` / `Value2`) | L172 |
| Power BI — query da Master Search | `EVALUATE 'Short Name'` | L3018 |
| Azure DevOps — `account` | `CDIO-IT-LATAM` | L673, L1941, L2492, L2541, L3061 |
| Azure DevOps — `project` | `CDIO Portfolio` | L677, L1945, L2496, L2545, L3065 |
| Azure DevOps — `type` / `typeName` | `IT Project` | L681, L2552 |
| URL de work item | `https://dev.azure.com/CDIO-IT-LATAM/CDIO%20Portfolio/_workitems/edit/{id}` | L2921, L1746 |

### Query IDs do Azure DevOps

| Escopo | Query ID | Vem de |
|---|---|---|
| **Master** (portfólio inteiro) | `9aecac87-a35a-45be-b1f4-af64000189ca` | L1949 |
| IT Area — Make / Business Ops / Supply Chain | `8b53a319-c304-4d55-be7e-0e3b8e2c2d03` | L305 |
| IT Area — Consumer / Marketing | `95581604-d21e-4268-a1fa-ca5bd59185f9` | L306 |
| IT Area — CD / Customer Development | `10271fab-00ff-44c6-98d7-241877e53ee7` | L307 |
| IT Area — Focus Market / Customer Operations | `236b80a4-395a-40cd-a962-8b3284fce608` | L308 |
| BU — Foods | `e15d1af6-0238-4e26-93ba-1f456b6258a9` | L88 |
| BU — HC / Home Care | `61e1da44-eb44-4f0f-8ff7-385d045f397c` | L90 |
| BU — PC / Personal Care | `bf99b079-207d-4027-97c2-6573129c5400` | L92 |
| BU — BW / Beauty & Wellbeing | `472b3677-9bd9-4289-8367-c61826219f3d` | L94 |
| **Default / Others** | `590e44b1-fdb4-4e3b-bd2e-32813b771443` | L96 |

> 🐛 **Bug encontrado no clássico:** no tópico `BU's Query` (o mais recente, L2215) a linha do BW foi corrompida para `"" in Upper(System.Activity.Text) Or "personal care" in ...`. Como `"" in qualquer coisa` é sempre verdadeiro, essa condição capturava **qualquer** BU que não fosse Foods/HC/PC e devolvia a query de BW. A versão correta está na cópia anterior `BU's Query_` (L94) e é a que está na tabela acima. Se as consultas por BU vinham estranhas, aqui está o motivo.

---

# TOOL 1 — `Power BI Portfolio Database` 🆕 **criar do zero**

A ferramenta mais importante. É o motor analítico do agente.

| | |
|---|---|
| Conector | Power BI |
| Operação | **Executar uma consulta em um conjunto de dados** (`ExecuteDatasetQuery`) |
| Autenticação | **Maker-provided** |

**Descrição (cole no campo Descrição):**

```
ALWAYS use this tool when the user asks for portfolio analysis, project status,
Big Rocks, risks, budgets, watermelons, scores or specific project details from
CDIO LATAM. It executes DAX queries against the portfolio dataset and returns
real-time data. This is the primary analytical engine of the agent.
```

**Inputs:**

| Input | Preencher usando | Valor |
|---|---|---|
| `groupid` (Workspace) | **Valor personalizado** | `4bd9bd39-a51b-4439-9248-805fd40a94a2` |
| `datasetid` (Conjunto de dados) | **Valor personalizado** | `afe9436e-b892-45a8-a3c0-e816f3e13258` |
| `query` (Texto da consulta) | **Dinamicamente com IA** | — (descrição abaixo) |

**Descrição do input `query`** — este texto é o que ensina o modelo a escrever DAX. Cole literalmente:

```
Return ONLY the raw DAX string. DO NOT use markdown code blocks (```dax) or any
other formatting. MUST start with EVALUATE. Table MUST ALWAYS be 'tabela'.
Valid Columns: [Work Item Id], [Title], [Short Name], [Project IT Manager],
[State], [N State], [StatusProjeto], [Project Type], [IT Area],
[BG or BU Engagement], [Specify Cross], [FinalScore], [Potencial],
[Business Benefit], [Budget Formatado], [Project Total Budget], [Budget Value],
[Benefit Value], [Payback in Months], [Implemention Time in Months],
[Country Deployed], [GoLive Date], [PGLS End Date], [Portfolio Year].
RULES: 1) Macro overview: use SUMMARIZECOLUMNS. 2) Specific/risk projects: use
CALCULATETABLE or FILTER. 3) NEVER invent columns. 4) Default [Project Type]
filter is 'Big Rock' unless the user asks otherwise.
```

> ⚠️ Note que `[Project Type]`, `[Business Benefit]` e `[StatusProjeto]` têm domínios fechados. Valores válidos de `[StatusProjeto]`: `Deployed`, `Delayed`, `In PGLS`, `Ending this Quarter`, `On Time`, `No Information` (= sem GoLive Date). `[Business Benefit]`: `Compliance` ou `Value Added`.

---

# TOOL 2 — `Power BI Master DB Search` 🔧 **corrigir a existente**

Já existe no agente. **Não recrie — abra e conserte os inputs.**

| | |
|---|---|
| Conector | Power BI |
| Operação | `ExecuteDatasetQuery` |
| Autenticação | **Maker-provided** |

**Descrição (manter a que já está):**

```
CRITICAL: ALWAYS use this FIRST to search by project name. It queries the Power
BI dataset and returns a LIST/ARRAY of numerical 'Work Item IDs' and their
baseline data (Area, Assigned To, Budget, Benefit). If the query returns
multiple items (like regional rollouts), you MUST capture ALL IDs in the list.
```

**Inputs — é AQUI que está o defeito:**

| Input | Está hoje | Tem que ficar | Valor |
|---|---|---|---|
| `groupid` | ❌ IA | **Valor personalizado** | `4bd9bd39-a51b-4439-9248-805fd40a94a2` |
| `datasetid` | ❌ IA | **Valor personalizado** | `afe9436e-b892-45a8-a3c0-e816f3e13258` |
| `query` | ❌ IA sem descrição | **Dinamicamente com IA** + descrição abaixo | — |

**Descrição do input `query`:**

```
Return ONLY the raw DAX string, no markdown fences. To resolve a project name
to its Work Item ID you MUST use exactly this pattern:
EVALUATE FILTER('tabela', SEARCH("<project name>", 'tabela'[Short Name], 1, 0) > 0
  || SEARCH("<project name>", 'tabela'[Title], 1, 0) > 0)
NEVER use a plain EVALUATE 'tabela'.
```

✅ **Teste de aceite:** no painel de teste da tool, ela tem que devolver linhas. Hoje devolve HTTP 400.

---

# TOOL 3 — `Power BI KPI Agente` ✏️ **renomear a existente**

Hoje se chama `Inicio de Conversa` — o mesmo nome da skill, o que confunde o orquestrador. Renomeie.

| | |
|---|---|
| Conector | Power BI · `ExecuteDatasetQuery` · Maker-provided |

**Descrição nova:**

```
SILENT TOOL. Returns the pre-aggregated KPI table 'tabela_agente' with
label/value pairs (Value1 = label, Value2 = value) for the CDIO portfolio:
"Total de Projetos", "Benefit Value Total", "Budget Value Total",
"% On Schedule". Use ONLY to build the executive KPI header. DO NOT analyze or
comment on the raw output.
```

**Inputs (os três já estão corretos, só confirme):**

| Input | Preencher usando | Valor |
|---|---|---|
| `groupid` | Valor personalizado | `4bd9bd39-a51b-4439-9248-805fd40a94a2` |
| `datasetid` | Valor personalizado | `afe9436e-b892-45a8-a3c0-e816f3e13258` |
| `query` | Valor personalizado | `EVALUATE 'tabela_agente'` |

---

# TOOL 4 — `DevOps Portfolio Master Query` 🆕

| | |
|---|---|
| Conector | Azure DevOps |
| Operação | **Obter resultados da consulta** (`GetQueryResultsV2`) |
| Autenticação | **Maker-provided** |

**Descrição (a original, que funcionava):**

```
SILENT TOOL. Retrieves a static list of work items from the master CDIO
Portfolio Query. Returns raw arrays of project data. DO NOT analyze, summarize,
or talk to the user after running this tool. Pass the raw output to the system
variables.
```

| Input | Preencher usando | Valor |
|---|---|---|
| `account` | Valor personalizado | `CDIO-IT-LATAM` |
| `project` | Valor personalizado | `CDIO Portfolio` |
| `queryId` | Valor personalizado | `9aecac87-a35a-45be-b1f4-af64000189ca` |

---

# TOOL 5 — `DevOps Query by Area or BU` 🆕

Consolida as duas tools do clássico (`Query Devops IT Area` + `Query Devops BU`). Eram idênticas — mesma operação, mesmos inputs fixos, `queryId` dinâmico. Uma tool só reduz a chance de o orquestrador escolher errado.

| | |
|---|---|
| Conector | Azure DevOps · `GetQueryResultsV2` · Maker-provided |

**Descrição:**

```
SILENT TOOL. Dynamically retrieves the list of Azure DevOps work items for a
given saved Query ID (one per IT Area or per Business Unit). Returns critical
fields such as State, GoLive Date, Budgets, Assigned To and History. The caller
MUST supply the queryId from the official mapping table. DO NOT generate any
user-facing response, analysis or summary from this tool. Return the raw JSON
array to the internal reasoning only.
```

| Input | Preencher usando | Valor |
|---|---|---|
| `account` | Valor personalizado | `CDIO-IT-LATAM` |
| `project` | Valor personalizado | `CDIO Portfolio` |
| `queryId` | **Dinamicamente com IA** | descrição abaixo |

**Descrição do input `queryId`:**

```
The GUID of the saved Azure DevOps query. Pick it from the official mapping:
Make/Business Ops/Supply Chain = 8b53a319-c304-4d55-be7e-0e3b8e2c2d03;
Consumer/Marketing = 95581604-d21e-4268-a1fa-ca5bd59185f9;
CD/Customer Development = 10271fab-00ff-44c6-98d7-241877e53ee7;
Focus Market/Customer Operations = 236b80a4-395a-40cd-a962-8b3284fce608;
Foods = e15d1af6-0238-4e26-93ba-1f456b6258a9;
HC/Home Care = 61e1da44-eb44-4f0f-8ff7-385d045f397c;
PC/Personal Care = bf99b079-207d-4027-97c2-6573129c5400;
BW/Beauty & Wellbeing = 472b3677-9bd9-4289-8367-c61826219f3d;
anything else = 590e44b1-fdb4-4e3b-bd2e-32813b771443.
NEVER invent a GUID.
```

---

# TOOL 6 — `DevOps Work Item Details` 🆕

| | |
|---|---|
| Conector | Azure DevOps |
| Operação | **Obter os detalhes do item de trabalho** (`GetWorkItemDetails`) |
| Autenticação | **Maker-provided** |

**Descrição (a original):**

```
SILENT TOOL. Fetches raw JSON data for a single Azure DevOps work item using
its unique ID. It returns technical fields, financial data and status. DO NOT
generate text, summaries or recommendations when using this tool. Only retrieve
the data for the system's internal reasoning.
```

| Input | Preencher usando | Valor |
|---|---|---|
| `account` | Valor personalizado | `CDIO-IT-LATAM` |
| `project` | Valor personalizado | `CDIO Portfolio` |
| `typeName` | Valor personalizado | `IT Project` |
| `id` | **Dinamicamente com IA** | "The unique numeric Work Item ID. Resolve the project name to its ID with `Power BI Master DB Search` before calling this tool." |

**Outputs a expor:** `fields`, `id`, `rev`, `url`.

---

# TOOL 7 — `DevOps Update Work Item` 🆕 ⚠️ escrita

Única tool que **grava**. Trate com cuidado.

| | |
|---|---|
| Conector | Azure DevOps |
| Operação | **Atualizar um item de trabalho** (`UpdateWorkItem`) |
| Autenticação | **Maker-provided** |

**Descrição (a original, que já era boa):**

```
USE THIS TOOL when a user explicitly requests to modify, change the status,
update descriptions, financial metrics or custom metadata within an existing
Azure DevOps work item.
BEFORE calling this tool, you MUST use 'DevOps Work Item Details' to fetch the
current state of the work item and confirm the change with the user.
CRITICAL RULES:
1. Only send the SPECIFIC field(s) the user wants to change in userEnteredFields.
2. NEVER send read-only fields (CreatedBy, CreatedDate, ChangedBy, ChangedDate,
   StateChangeDate, TeamProject, WorkItemType).
3. Use full reference names as keys (e.g. "Custom.Note" not "Note").
4. After the update succeeds, confirm the change to the user showing the field
   name and the new value.
```

| Input | Preencher usando | Valor |
|---|---|---|
| `account` | Valor personalizado | `CDIO-IT-LATAM` |
| `project` | Valor personalizado | `CDIO Portfolio` |
| `type` | Valor personalizado | `IT Project` |
| `id` | **Dinamicamente com IA** | ID numérico do work item |
| `userEnteredFields` | **Dinamicamente com IA** | descrição abaixo |

**Descrição do input `userEnteredFields`:**

```
A JSON object of key-value pairs where each key is the FULL Azure DevOps field
reference name and each value is the new value to set.
Examples of valid keys: "System.State", "Custom.BusinessBenefit", "Custom.Note",
"Custom.ProjectTotalBudget", "Custom.Stages".
ONLY include the specific field(s) the user asked to change.
Do NOT include unchanged fields.
Do NOT include read-only fields like System.CreatedBy, System.CreatedDate,
System.ChangedBy, System.ChangedDate, Microsoft.VSTS.Common.StateChangeDate,
System.TeamProject or System.WorkItemType.
```

📎 A lista completa e verificada dos reference names está em [`skills/update-devops/references/campos-devops.md`](../../skills/update-devops/references/campos-devops.md).

---

# TOOL 8 — `Teams — Postar mensagem` ✅ **já existe, manter**

| | |
|---|---|
| Conector | Microsoft Teams |
| Operação | **Postar mensagem em um chat ou canal** (`PostMessageToConversation`) |
| Autenticação | **End user** (`authMode: Invoker`) — ✅ mantenha assim |

Manter credencial do usuário final é a decisão certa: a cobrança sai **como você**, não como um bot anônimo. Efeito colateral: cada pessoa que usar essa capacidade precisa autorizar a própria conexão do Teams na primeira vez.

**Descrição nova (a atual, "Posta uma mensagem em um chat ou canal", é genérica demais e o orquestrador pode chamar sem querer):**

```
Sends a Microsoft Teams message on behalf of the current user. Use ONLY after
the user has explicitly reviewed and approved the message draft. Typical use:
notifying a Project IT Manager about a delayed project or a governance gap.
NEVER call this tool to answer a question or to display information to the
current user.
```

**Inputs:** `poster`, `location` e `body` são dinâmicos por natureza (o `body` do conector é `UnresolvedDynamicType`).

| Input | Observação |
|---|---|
| `poster` | Opções: `User`, `Flow bot`, `Microsoft Copilot Studio agent`. Para cobrança use **`User`** |
| `location` | Opções: `Group chat`, `Channel`, `Chat with Flow bot`. Para DM 1:1 com o gestor, teste **`Chat with Flow bot`** e **`Group chat`** — a combinação varia por tenant |
| `body` | Destinatário (e-mail do gestor) + texto da mensagem |

> ⚠️ **Passo de verificação obrigatório:** teste esta tool isoladamente no painel de teste, mandando uma mensagem **para você mesmo**, antes de ligar a skill `notificar-gestor`. A combinação `poster`/`location` que funciona no seu tenant precisa ser confirmada na prática — não dá para determinar isso pelo arquivo. Quando descobrir, trave `poster` e `location` em **Valor personalizado** e deixe só o `body` dinâmico.

---

## Resumo: 8 tools

| # | Nome | Ação | Grava? |
|---|---|---|---|
| 1 | `Power BI Portfolio Database` | 🆕 criar | não |
| 2 | `Power BI Master DB Search` | 🔧 corrigir inputs | não |
| 3 | `Power BI KPI Agente` | ✏️ renomear | não |
| 4 | `DevOps Portfolio Master Query` | 🆕 criar | não |
| 5 | `DevOps Query by Area or BU` | 🆕 criar | não |
| 6 | `DevOps Work Item Details` | 🆕 criar | não |
| 7 | `DevOps Update Work Item` | 🆕 criar | ⚠️ **sim** |
| 8 | `Teams — Postar mensagem` | ✅ manter + ajustar descrição | ⚠️ **envia** |
