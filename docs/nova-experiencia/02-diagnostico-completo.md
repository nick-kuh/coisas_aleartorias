# 2. Diagnóstico completo — o que exatamente se perdeu

Comparação componente a componente entre `botContent.yml` (clássico, que funcionava) e `Aura_Agent.yaml` (nova experiência, que não funciona). Os números de linha referenciam os arquivos originais que você enviou.

---

## 2.1 Placar geral

| | Clássico | Nova experiência |
|---|---|---|
| Tópicos com lógica | 25 (3 críticos ativos) | 0 (não existe mais o conceito) |
| Skills | — | 1 |
| Tools Power BI | 3 | 2 (uma delas quebrada) |
| Tools Azure DevOps | **5** | **0** |
| Tools Teams | 0 | 1 |
| Fontes de conhecimento | 2 | 2 ✅ |
| Variáveis globais | criadas em runtime pelos tópicos | 4 declaradas |

---

## 2.2 🔴 Azure DevOps: 5 ferramentas → 0

O YAML novo **não tem uma única ocorrência** de `shared_visualstudioteamservices`. Confirmação:

```
$ grep -c "visualstudioteamservices" Aura_Agent.yaml
0
```

O que existia no clássico e sumiu:

| Nome | `operationId` | Inputs fixos | Papel |
|---|---|---|---|
| `Devops Query (Knowledge)` (linha 2467) | `GetQueryResultsV2` | account `CDIO-IT-LATAM`, project `CDIO Portfolio`, **queryId `9aecac87-a35a-45be-b1f4-af64000189ca`** | Lista mestra do portfólio |
| `Query Devops IT Area` (linha 2516) | `GetQueryResultsV2` | account + project fixos, queryId **dinâmico** | Consulta por IT Area |
| `Query Devops BU` (linha 3036) | `GetQueryResultsV2` | account + project fixos, queryId **dinâmico** | Consulta por BU |
| `Obter os detalhes do item de trabalho` (linha 2516+) | `GetWorkItemDetails` | account, project, typeName `IT Project`, id dinâmico | Estado técnico + comentários |
| `Update Project` (linha 648) | `UpdateWorkItem` | account, project, type `IT Project`, id + `userEnteredFields` dinâmicos | **Atualização do work item** |

Sem elas, os passos 3 (LIVE STATUS) e a resiliência ("se o PBI falhar, use o DevOps como fonte da verdade") das suas instruções são **fisicamente impossíveis** — o agente lê a instrução, tenta obedecer e não encontra ferramenta.

---

## 2.3 🔴 Power BI: a `Master DB Search` está quebrada por falta de binding

No clássico (linha 2985), a tool `Power BI Master DB Search` tinha os três inputs travados:

```yaml
inputs:
  - kind: ManualTaskInput
    propertyName: groupid
    value: 4bd9bd39-a51b-4439-9248-805fd40a94a2
  - kind: ManualTaskInput
    propertyName: datasetid
    value: afe9436e-b892-45a8-a3c0-e816f3e13258
  - kind: ManualTaskInput
    propertyName: query
    value: EVALUATE 'Short Name'
```

No YAML novo (linhas 111–138), o componente termina assim:

```yaml
    dialog:
      kind: ConnectorTool
      authMode: Maker
      connectionReference: crdc4_auraagent_GW5of7.cr.shared_powerbi.812a...
      connectorId: /providers/Microsoft.PowerApps/apis/shared_powerbi
      operationId: ExecuteDatasetQuery
      # <- acabou aqui. NÃO existe bloco toolInputs.
```

Sem `toolInputs`, os três parâmetros ficam em "preencher dinamicamente com IA". O modelo **não tem como saber** os GUIDs do workspace e do dataset — eles não estão em lugar nenhum do contexto dele. Resultado: a chamada sai com `groupid` e `datasetid` inventados ou vazios e o Power BI devolve HTTP 400.

O detalhe cruel: **as variáveis com os valores certos existem no arquivo** (linhas 31–56 e 183–208), com os GUIDs corretos como `defaultValue`. Só não foram ligadas à tool. Compare com a tool `Inicio de Conversa` (linhas 139–182), que está certa:

```yaml
      toolInputs:
        - kind: AgentToolInput
          name: groupid
          value:
            kind: ContextVariableReference
            name: PowerBIMasterDBSearch.groupid
        - kind: AgentToolInput
          name: datasetid
          value:
            kind: ContextVariableReference
            name: PowerBIMasterDBSearch.datasetid
        - kind: AgentToolInput
          name: specification.query
          value:
            kind: ContextVariableReference
            name: IniciodeConversa.specification_query
```

**Essa é provavelmente a correção que sozinha destrava a maior parte dos seus erros de hoje.**

---

## 2.4 🔴 Power BI: a ferramenta mais importante não foi recriada

No clássico existia `Power BI Portfolio Database` (linha 3313), e ela era o motor do agente:

```yaml
- kind: AutomaticTaskInput          # <- o MODELO escreve a query
  propertyName: query
  name: DAX Query String
  description: |-
    Return ONLY the raw DAX string. DO NOT use markdown code blocks (```dax)...
    MUST start with EVALUATE. Table MUST ALWAYS be 'tabela'.
    Valid Columns: [Work Item Id], [Title], [Project IT Manager], [State],
    [Project Type], [IT Area], [BG or BU Engagement], [Specify Cross],
    [FinalScore], [Potencial], [StatusProjeto], [Business Benefit],
    [Budget Value], [Benefit Value], [Payback], [Implementation Time],
    [Country Deployed], [Portfolio Year].
    RULES: 1) Macro overview: use SUMMARIZECOLUMNS. 2) Specific/risk projects:
    use CALCULATETABLE. 3) NEVER invent columns.
```

Repare no design: `groupid` e `datasetid` **fixos**, `query` **livre para a IA**, e o dicionário de colunas embutido na descrição do input. Era isso que permitia "analise Make e Consumer", "quais são os watermelons", "top 3 big rocks" — qualquer pergunta virava DAX.

**Essa tool não existe no agente novo.** Sem ela o agente só tem duas queries fixas (`EVALUATE 'Short Name'` e `EVALUATE 'tabela_agente'`) e nenhuma capacidade analítica.

---

## 2.5 🔴 Lógica: 3 tópicos ativos → 1 skill

Estado dos tópicos no clássico:

| Tópico | Estado | Virou skill? |
|---|---|---|
| `Início da conversa` | Active | ✅ virou `inicio-de-conversa` (com defeitos, ver 2.6) |
| `Project Deep Dive` | Active | ❌ sumiu |
| `Meeting Preparation_` | Active | ❌ sumiu |
| `Update Project Devops` | **Inactive** | ❌ (já não rodava) |
| `BU's Query` / `Area's Query` / `AnalisePortol` / `ID to Title` / `Meeting Preparation` | Inactive | ❌ (já não rodavam) |

**Observação importante e positiva:** seu fluxo de update no DevOps que funcionava **não vinha do tópico** — o tópico `Update Project Devops` estava `Inactive`. Ele vinha da tool `Update Project` sendo escolhida pelo orquestrador a partir da `modelDescription` dela. Isso é exatamente o padrão da nova experiência. Você já estava construindo do jeito novo sem saber.

---

## 2.6 🟠 A skill `inicio-de-conversa` aponta para ferramentas inexistentes

A skill migrada (linhas 263–327) diz:

> **2.** Call the Power BI **detailed-query tool (PowerBI - Execute a query against a dataset)** to load the full portfolio into memory. Use this DAX query: `EVALUATE SUMMARIZECOLUMNS(...)`
>
> **3.** Call the Power BI **KPI/macro tool** (the pre-configured query that returns the "tabela_agente" table…)

Problemas:

1. Nenhuma tool do agente novo se chama "PowerBI - Execute a query against a dataset". Os nomes reais são `Power BI Master DB Search` e `Inicio de Conversa`.
2. O passo 2 exige uma tool com `query` livre — ou seja, exatamente a `Power BI Portfolio Database` que **não foi recriada**.
3. A tool se chama `Inicio de Conversa` e a skill se chama `inicio-de-conversa`. Dois componentes de tipos diferentes com o mesmo nome, num sistema onde o roteamento é por nome/descrição semântica. Confusão garantida.

---

## 2.7 🟠 As instruções migraram com lixo de formatação e uma referência morta

O texto foi colado por um editor que aplica escape de markdown. No YAML novo, dentro de `agentSettings.instructions.segments[0].value`:

| Linha (aprox.) | O que está lá | O que deveria ser |
|---|---|---|
| 15–21, 38–50 | `\* [N State]:` | `* [N State]:` |
| 28, 65 | `` \`IN\` `` e `` \`EVALUATE...\` `` | crases normais |
| 51, 62, 63 | `System\_State`, `Global.tabela\_pbi` | sem `\_` |
| 61–62 | Seção **"7. SILENT THINKING"** seguida de **"8. Parse intent -> 2. Write DAX"** | era `1. Parse intent` — o editor renumerou a lista |
| 67 | Outra seção **"8. REPORTING FORMATS"** | havia duas seções "8" |
| 12 | `use 'PBI MASTER DB SEARCH'  if user asks` (espaço duplo) | ali existia `{System.Bot.Components.Actions.'…'.DisplayName}` no clássico, que foi apagado |

E o pior, que não é cosmético:

```
- MEMORY ALREADY FILTERED: The internal memory 'Global.tabela_pbi' is ALREADY
  filtered for active/recent projects. Do not try to re-apply the GoLive date
  filters when reading from it.
```

`Global.tabela_pbi` era criada pelo nó `ParseValue` do tópico `Início da conversa` (linha 583 do clássico):

```yaml
- kind: ParseValue
  id: nCUuCi
  variable: Global.tabela_pbi
  valueType:
    kind: Table
  value: =Topic.firstTableRows
```

**Sem o tópico, a variável não existe.** O agente está sendo instruído a "ler de uma memória" que nunca é preenchida — ele vai alucinar que tem dados, ou travar.

---

## 2.8 🟠 Configurações do agente que mudaram sozinhas

| Config | Clássico | Novo | Efeito prático |
|---|---|---|---|
| `language` | `1046` (pt-BR) + `supportedLanguages: [1033, 1034, 21514]` | `1033` (en-US), sem idiomas extras | Respostas em português ficam piores; suas instruções mandam "output em português brasileiro" e brigam com a config |
| `contentModeration` | `High` | `Maximum` | Mais recusas. Seu agente faz cobrança dura ("Gestor Ofensor", "A Pergunta de €1 Milhão") — moderação máxima pode cortar isso |
| `useModelKnowledge` | `true` | ausente | Perde o conhecimento geral do modelo |
| `isFileAnalysisEnabled` | `true` | ausente | Perde análise de arquivo anexado |
| `isSemanticSearchEnabled` | `true` | ausente | Busca semântica no SharePoint (Wiki + Transcrições) pior |
| `optInUseLatestModels` | `true` | ausente | Não pega modelo novo automaticamente |
| `gptCapabilities.codeInterpreter` | `true` | ausente | **Perde cálculo determinístico** — o FinalScore de 4 pilares com pesos passa a ser conta "de cabeça" do modelo |
| `conversationStarters` | 1 no GptComponent + 3 `suggestedActions` no greeting | `[]` | Nenhum chip clicável |
| `enableMemory` | — | `true` | ✅ **ganho novo**: memória persistente entre conversas |
| `web.enableWebSearch` | — | `false` | Coerente (dado corporativo), mantenha |

---

## 2.9 ✅ O que sobreviveu bem

- **As 2 fontes de conhecimento SharePoint**, com as descrições longas intactas:
  - `CDIO_LATAM_Governance_Wiki` → `.../CDIO LATAM/CDIO Latam.pdf` (`targetKind: File`)
  - `Transcription LT Meetings` → `.../CDIO LATAM/Transcription LT Meetings` (`targetKind: Folder`)
- **O conteúdo estratégico das instruções** (persona, dicionário, acrônimos, states, riscos, campos de governança) — está tudo lá, só precisa de faxina.
- **O modelo**: `Opus48` nos dois.
- **A tool do Teams** `Postar mensagem em um chat ou canal` (`PostMessageToConversation`, `authMode: Invoker`) — **não existia no clássico**. É ganho, e é exatamente a peça que faltava para o agente avisar o gestor de um projeto atrasado.
- `accessControlPolicy: GroupMembership` e `authenticationMode: Integrated` idênticos.

---

## 2.10 Mapa de reconstrução

| Item do clássico | Onde vive na nova experiência |
|---|---|
| Tópico `Início da conversa` | Skill `inicio-de-conversa` + Settings › Greeting & prompts |
| Tópico `Project Deep Dive` | Skill `project-deep-dive` |
| Tópico `Meeting Preparation_` | Skill `meeting-preparation` |
| Tópicos `BU's Query` / `Area's Query` | Skill `portfolio-overview` (com a tabela de Query IDs em `references/`) |
| `SearchAndSummarizeContent` (nós de IA) | Vira texto de instrução na skill — o modelo já faz isso nativamente |
| `Question` + `ClosedListEntity` | Vira "pergunte ao usuário qual área, entre: …" na skill |
| `ConditionGroup` + Power Fx | Vira instrução condicional na skill (⚠️ perde determinismo — ver `03-manual`, seção sobre controle de acesso) |
| `SetVariable` / `ParseValue` / `Global.*` | Some. O contexto da conversa faz o papel; para persistir, use **Memory** |
| Ações (`TaskDialog`) | Viram **Tools** (`ConnectorTool`) — 1:1, mesma `operationId` |
| `ManualTaskInput` | Input com **"Valor personalizado"** (fixo) |
| `AutomaticTaskInput` | Input com **"Preencher dinamicamente com IA"** |
| `modelDescription` da ação | Descrição da tool (continua sendo o que faz o orquestrador escolher) |
| Tópicos de sistema (`Fallback`, `Escalonar`, `Saudação`…) | Somem. Comportamento vem das instruções |
| Triggers | Vivem em **Workflows**, fora do agente |

➡️ Continue em [`03-manual-nova-experiencia.md`](03-manual-nova-experiencia.md)
