# 1. Diagnóstico do AURA Agent (standard)

Auditoria do `botContent_69.zip` — agente `crdc4_AURAAgent`, criado em 13/08/2026, reconstruído na experiência **standard/clássica**.

---

## 🟢 Estado atual — `botContent_73` (17/08/2026)

**O agente funciona.** O diagnóstico abaixo foi confirmado em produção: aplicadas as correções, o comportamento previsto apareceu.

### A prova, do `dialog.json`

Usuário digitou *"traga para o portfolio de make de bpc"*. O agente chamou a `Power BI Portfolio Database` com:

```json
{"arguments": {"query": "EVALUATE FILTER('tabela', ...)"},
 "autoFilledArguments": ["query"]}
```

**`autoFilledArguments: ["query"]`** — antes era `[]`. O modelo escreveu o DAX sozinho, que é exatamente o que a Correção 2 destravou. A query que ele produziu:

```dax
EVALUATE FILTER('tabela', 'tabela'[IT Area] = "Make (Business Operation)"
  && (('tabela'[BG or BU Engagement] = "BW" || 'tabela'[BG or BU Engagement] = "PC")
  || ('tabela'[BG or BU Engagement] = "Cross"
      && (SEARCH("BW", 'tabela'[Specify Cross], 1, 0) > 0
       || SEARCH("PC", 'tabela'[Specify Cross], 1, 0) > 0))))
```

Três regras das instruções seguidas à risca:
- **Acrônimo:** traduziu `BPC` → `BW` + `PC`
- **Cross-BU:** incluiu `Cross` com `SEARCH` em `[Specify Cross]`
- **Anti-alucinação:** só colunas válidas, nenhuma inventada

O relatório resultante nomeou projetos reais com ID e valor — South Pole (546) com ROI -80%, MIRAI Make (1252) Big Rock sem budget, Automatic Goods Receipt (202) High Potential travado em On Holding — e terminou oferecendo cobrar a gestora via Teams. **Zero exceptions no log.**

### Placar das correções

| Correção | Status |
|---|---|
| **A2** `Power BI Portfolio Database` | ✅ completa — **comprovada em runtime** |
| **A3** `Obter detalhes do work item` | ✅ `id` + descrição, e SILENT TOOL restaurado |
| **A4** `Query Devops BU` / `IT Area` | ✅ ambas com `queryId` + descrição |
| **A1** `Update Project` | 🟡 `type` ✅, `id`+desc ✅ — **falta `userEnteredFields`** |
| **A5** `Teams` | 🟡 `poster: User` ✅, `location: Group chat` ✅ — **faltam `body.recipient` e `body.messageBody`**, e `body.bot` sobrou |

### Configurações (Bloco D) — aplicadas

| Config | Antes | Agora |
|---|---|---|
| `contentModeration` | `Low` | ✅ `High` |
| `optInUseLatestModels` | `false` | ✅ `true` |
| `codeInterpreter` | ausente | ✅ `true` — cálculo determinístico recuperado |

### As 2 pendências

**1. `userEnteredFields` na `Update Project`.** É o campo que diz *o que* mudar. Sem ele a tool recebe só o `id` e não grava nada. Detalhe: a `modelDescription` da tool **já cita** `userEnteredFields` em 3 das 4 regras críticas — o modelo lê a instrução e não encontra o campo.

**2. `body.bot` sobrando na tool do Teams.** Está declarado como `ManualTaskInput` **sem valor**:

```yaml
- kind: ManualTaskInput
  propertyName: body.bot     # ← sem value
```

Esse campo só existe quando `poster: Power Virtual Agents`. Com `poster: User` ele é inerte no melhor caso, e um obrigatório vazio no pior — provável causa do erro observado. **Remover a entrada** e adicionar `body.recipient` + `body.messageBody`.

Textos prontos em [`02-correcao-das-tools.md`](02-correcao-das-tools.md), Correções 1 e 5A.

### Backlog (nada bloqueia)

- 5º KPI `% High Potencial` não exibido no dashboard
- Saudação do tópico ainda em inglês
- Typo `[Project Total Budget**€**)]` nas instruções
- `webBrowsing: true` — considerar desligar num agente de dado corporativo
- `Project Deep Dive` ainda busca numa `'base mestra'` que não existe como fonte de conhecimento
- `conversationStarters` vazio

---

## Diagnóstico original (`botContent_69`)

---

## 1.1 O veredito

Esta reconstrução está **muito melhor** do que a tentativa na experiência nova, e **já funciona parcialmente**. O `dialog.json` que veio junto é a prova.

O que voltou e está correto:

| | Status |
|---|---|
| `template: default-2.1.0` + `recognizer: GenerativeAIRecognizer` | ✅ clássico, o motor que funcionava |
| `language: 1046` (pt-BR) | ✅ corrigido (na experiência nova tinha virado en-US) |
| 5 tools do Azure DevOps | ✅ todas de volta |
| 3 tools do Power BI | ✅ |
| Tool do Teams | ✅ criada |
| 2 fontes de conhecimento SharePoint | ✅ (com uma ressalva, §1.5) |
| Tópicos `Início da conversa` e `Project Deep Dive` | ✅ |
| `Global.tabela_pbi` sendo criada pelo `ParseValue` | ✅ — a instrução que a lê voltou a fazer sentido |
| Instruções sem os escapes `\*` / `\_` | ✅ |
| `{System.Bot.Components.Actions.'…_dJR'.DisplayName}` | ✅ resolve, e aponta para a tool certa (Master DB Search) |

## 1.2 A prova de que a abertura funciona

Do `dialog.json`, atividade 3:

```json
{"taskDialogId": "crdc4_AURAAgent.action.PowerBI-Executarumaconsultaemumconjuntosdedados_lkk",
 "arguments": {
   "groupid":   "4bd9bd39-a51b-4439-9248-805fd40a94a2",
   "datasetid": "afe9436e-b892-45a8-a3c0-e816f3e13258",
   "query":     "EVALUATE SUMMARIZECOLUMNS('tabela'[Work Item Id], … )"
 },
 "autoFilledArguments": []}
```

A query passou, o Power BI respondeu, e a atividade 5 mostra `Global.tabela_pbi` populada com linhas reais (Work Item Id 376, `ANDEAN - Project - IT IC Demerge Ecuador`, IT Area `Commercial Exp`…). A atividade 9 é o dashboard renderizado:

> **Total Initiatives:** 422 · **Total Benefit:** €412,637 Mi · **Total Budget:** €311,092 Mi · **Projects on Schedule:** 61%

Guarde o detalhe **`"autoFilledArguments": []`**. Ele é a chave do diagnóstico inteiro.

---

## 1.3 🔴 O defeito central: inputs não declarados

No classic, a lista `inputs:` de uma tool define **o que o orquestrador generativo consegue preencher**.

Um **tópico** consegue passar um argumento por binding mesmo que ele não esteja declarado — foi exatamente o que aconteceu acima: a `_lkk` não tem `query` na sua lista de inputs, mas o tópico `Início da conversa` fez `input.binding.query` e funcionou. Por isso `autoFilledArguments` veio vazio: **nada foi preenchido pelo modelo, tudo veio do tópico.**

O **modelo**, por outro lado, só enxerga o que está declarado como `AutomaticTaskInput`. O que não está declarado, para ele não existe.

### Comparação com o agente que funcionava

| Tool | Agente antigo (funcionava) | AURA Agent (hoje) | Falta |
|---|---|---|---|
| `Power BI Portfolio Database` | groupid, datasetid, **query (IA + descrição-dicionário)** | groupid, datasetid | 🔴 `query` |
| `Power BI Master DB Search` | groupid, datasetid, query (fixo) | idem | ✅ |
| `Inicio de Conversa` | groupid, datasetid, query (fixo) | idem | ✅ |
| `Obter os detalhes do item de trabalho` | account, project, **id (IA)**, typeName | account, project, typeName | 🔴 `id` |
| `Query Devops IT Area` | account, project, queryId (IA) | idem | ✅ |
| `Query Devops BU` | account, project, **queryId (IA)** | account, project | 🔴 `queryId` |
| `Devops Query (Knowledge)` | account, project, queryId (fixo) | idem | ✅ |
| `Update Project` | account, project, **type**, id (IA+desc), **userEnteredFields (IA+desc)** | account, project, id (IA) | 🔴 `type`, `userEnteredFields` |
| `Teams — Postar mensagem` | (não existia) | poster, location, **body.bot vazio** | 🔴 `body.bot`, `body.recipient`, `body.messageBody` |

### Por que isso importa em cada caso

Só 3 das 9 tools são chamadas por algum tópico. As outras 6 dependem **inteiramente** do orquestrador:

| Tool | Chamada por tópico | Consequência prática |
|---|---|---|
| `Power BI Portfolio Database` | `Início da conversa` (L1828) | A abertura funciona ✅. Mas quando você pergunta "quais são os watermelons?", o modelo **não tem parâmetro de query para preencher** → não consegue rodar DAX próprio. **Morre toda a análise sob demanda** — e é a tool descrita como "ALWAYS use this tool when the user asks for portfolio analysis" |
| `Obter os detalhes do item de trabalho` | `Project Deep Dive` (L297) | Deep Dive funciona ✅. Mas "me traz o work item 376" fora do tópico não funciona — sem `id`, o modelo não consegue chamar |
| `Query Devops BU` | ❌ ninguém | Inútil. A descrição promete filtrar por BU Query ID e não existe onde passar o ID |
| `Update Project` | ❌ ninguém | **Não atualiza nada.** O modelo consegue mandar o `id` e mais nada — não há campo para dizer o que mudar |
| `Teams — Postar mensagem` | ❌ ninguém | Não envia. Ver §1.4 |
| `Query Devops IT Area`, `Devops Query (Knowledge)`, `Master DB Search`, `Inicio de Conversa` | ❌ ninguém, mas completas | ✅ funcionam |

## 1.4 🔴 A tool do Teams está pela metade

```yaml
inputs:
  - kind: ManualTaskInput
    propertyName: poster
    value: Power Virtual Agents     # = "Microsoft Copilot Studio agent" ✅
  - kind: ManualTaskInput
    propertyName: location
    value: powerva                  # = "Chat with agent" ✅
  - kind: ManualTaskInput
    propertyName: body.bot          # ← declarado e SEM value
```

`body.bot` é obrigatório (`isRequired: true`) e está vazio. E `body.recipient` e `body.messageBody`, também obrigatórios, não foram declarados de forma alguma.

As duas primeiras escolhas estão **certas** — `poster` e `location` são exatamente o par que a Microsoft documenta para mensagem proativa. O que falta é o agente, o destinatário e o texto. O porquê do dropdown vazio e como resolver estão em [`03-teams-conversa-com-gestor.md`](03-teams-conversa-com-gestor.md).

## 1.5 🟠 Descrições que se perderam

Três textos que faziam trabalho pesado sumiram junto com os inputs:

| Onde | O que era | Efeito de não ter |
|---|---|---|
| Input `query` da `Power BI Portfolio Database` | O dicionário de colunas válidas + regras (`SUMMARIZECOLUMNS` para macro, `CALCULATETABLE` para específico, `'tabela'` obrigatória, nunca inventar coluna) | Mesmo depois de recriar o input, sem esse texto o modelo escreve DAX inválido |
| Input `userEnteredFields` da `Update Project` | O formato JSON com reference names e a lista de campos read-only proibidos | Update falha, ou pior: manda campo read-only e o PATCH quebra |
| `modelDescription` da `Obter os detalhes do item de trabalho` | `SILENT TOOL. Fetches raw JSON… DO NOT generate text, summaries, or recommendations` — hoje é só "Obter os detalhes de um único item de trabalho" | O agente despeja JSON cru na cara do usuário em vez de usar o dado internamente |

## 1.6 🟠 Configurações do agente

| Config | Agente antigo | AURA Agent | Comentário |
|---|---|---|---|
| `gptCapabilities.codeInterpreter` | `true` | **ausente** | Perde cálculo determinístico. Mitigação: sempre **ler** `[FinalScore]` do dataset, nunca recalcular |
| `gptCapabilities.webBrowsing` | `false` | **`true`** | Inverteu. Num agente de dado corporativo, busca na web pública convida alucinação — considere desligar |
| `contentModeration` | `High` | `Low` | Mais permissivo. Serve à cobrança dura, mas é uma escolha consciente a fazer |
| `optInUseLatestModels` | `true` | `false` | Não adota modelo novo automaticamente |
| `conversationStarters` | 1 | **nenhum** | Os 3 atalhos existem como `suggestedActions` no tópico ✅, mas o starter do agente sumiu |
| `useModelKnowledge` / `isFileAnalysisEnabled` / `isSemanticSearchEnabled` | `true` | `true` | ✅ mantidos |

## 1.7 🟠 Fontes de conhecimento — mudou o tipo

| | Agente antigo | AURA Agent |
|---|---|---|
| Tipo | `SharePointKnowledgeSource` + `targetKind: File` / `Folder` | `SharePointSearchSource` + `site:` |
| Wiki | `.../CDIO LATAM/CDIO Latam.pdf` (`targetKind: File`) | `.../CDIO%20LATAM/CDIO%20Latam.pdf` no campo **`site`** |
| Transcrições | `.../Transcription LT Meetings` (`targetKind: Folder`) | mesma URL no campo **`site`** |

São duas opções diferentes na UI: uma indexa **arquivos e pastas específicos**, a outra faz **busca sobre um site/biblioteca**. Apontar a busca de site para um **arquivo `.pdf`** é no mínimo suspeito.

**Não afirmo que está quebrado — mas precisa de teste.** O teste está em [`02-correcao-das-tools.md`](02-correcao-das-tools.md), §Verificação.

## 1.8 🟡 Defeitos herdados (já existiam no agente antigo)

Não foram introduzidos agora, mas vale corrigir:

1. **`Project Deep Dive` procura numa "base mestra" que não existe.** O tópico faz `SearchAndSummarizeContent` mandando "varra TODAS as linhas da tabela no arquivo 'base mestra'" — mas não há fonte de conhecimento com esse nome. As fontes são o Wiki (PDF) e as Transcrições. Ou seja, o passo `SINGLE/MULTIPLE/NOT_FOUND` é adivinhação. Deveria usar a tool `Power BI Master DB Search`, que é feita exatamente para isso.
2. **`Power BI Master DB Search` tem a query travada em `EVALUATE 'Short Name'`.** As instruções mandam usar `EVALUATE FILTER('tabela', SEARCH(...))` — impossível, porque o input é fixo. Funciona na marra (traz a tabela inteira e o modelo acha o ID), mas é caro e frágil.
3. **Typo nas instruções:** `[Project Total Budget**€**)]` — falta o `(` de abertura.
4. **Falta a seção 6** nas instruções: vai da 5 direto para a 7.
5. **A saudação do tópico está em inglês** ("Hello {System.User.FirstName}. Please wait a moment…") num agente pt-BR cujas instruções mandam responder em português.
6. **`Meeting Preparation` não foi recriada** — estava `Active` no agente antigo.

## 1.9 🟢 Um KPI de graça

O `dialog.json` mostra que a `tabela_agente` devolve **5** indicadores, e o tópico só usa 4:

| `Value1` | `Value2` | Usado? |
|---|---|---|
| `Total de Projetos` | 422 | ✅ |
| `Benefit Value Total` | €412,637 Mi | ✅ |
| `Budget Value Total` | €311,092 Mi | ✅ |
| `% On Schedule` | 61% | ✅ |
| `% High Potencial` | 6% | ❌ **não exibido** |

Um `SetVariable` a mais no tópico e o dashboard ganha um quinto KPI sem custo de query.

---

➡️ Correção de cada tool, com os textos prontos: [`02-correcao-das-tools.md`](02-correcao-das-tools.md)
