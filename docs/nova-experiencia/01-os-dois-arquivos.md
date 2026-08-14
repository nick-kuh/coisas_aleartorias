# 1. O que são os dois arquivos

Os dois arquivos são **o mesmo agente (Aura Agent / CDIO Agent), exportado de duas gerações diferentes do Copilot Studio**. Não é uma versão "melhor" e outra "pior" do mesmo formato — são formatos incompatíveis entre si.

---

## `botContent_68.zip` — o agente CLÁSSICO (o que funcionava)

Ao descompactar:

```
botContent.yml   (492 KB, 13.574 linhas)
dialog.json      (138 KB)
```

Marcadores que identificam a geração:

```yaml
entity:
  schemaName: copilots_header_a950a
  cdsBotId: dec9721d-16fd-f011-8406-000d3a467d39
  template: default-2.1.0            # <- geração clássica
  language: 1046                     # <- pt-BR como idioma primário
  supportedLanguages: [1033, 1034, 21514]
  configuration:
    settings:
      GenerativeActionsEnabled: true
    aISettings:
      useModelKnowledge: true
      isFileAnalysisEnabled: true
      isSemanticSearchEnabled: true
      contentModeration: High
      optInUseLatestModels: true
    recognizer:
      kind: GenerativeAIRecognizer   # <- orquestrador clássico
```

**Conteúdo real (36 componentes):**

| Tipo | Qtd | O que são |
|---|---|---|
| `DialogComponent` com `beginDialog` (tópicos) | 25 | Fluxos de conversa: `Início da conversa`, `Project Deep Dive`, `Meeting Preparation_`, `Update Project Devops`, `BU's Query`, `Area's Query`, `ID to Title`, + tópicos de sistema (`Fallback`, `Escalonar`, `Saudação`, `Tchau`, `Recomeçar`…) |
| `DialogComponent` com `kind: TaskDialog` (ações/tools) | 8 | 3 Power BI (`ExecuteDatasetQuery`) + 5 Azure DevOps (`GetQueryResultsV2` ×3, `GetWorkItemDetails`, `UpdateWorkItem`) |
| `GptComponent` | 1 | O cérebro: `displayName: Aura Agent`, `metadata.instructions` (as 10 seções de persona/regras), `conversationStarters`, `gptCapabilities.codeInterpreter: true`, `aISettings.model.modelNameHint: Opus48` |
| `KnowledgeSourceComponent` | 2 | `CDIO_LATAM_Governance_Wiki` (PDF no SharePoint) e `Transcription LT Meetings` (pasta no SharePoint) |

O resto do arquivo (linhas ~3.800 até 13.500) é o **swagger dos conectores** Power BI e Azure DevOps — descrição de todas as operações disponíveis. Não é conteúdo seu, é catálogo do conector.

---

## `Aura_Agent.yaml` — o agente na NOVA experiência (o que não funciona)

Um único arquivo YAML, 13.810 linhas. Marcadores da geração:

```yaml
entity:
  schemaName: crdc4_auraagent_GW5of7
  cdsBotId: 514835e4-92b9-49f4-9381-a93abfb93502
  template: cliagent-1.0.0           # <- nova experiência
  language: 1033                     # <- en-US (mudou!)
  runtimeProvider: PowerVirtualAgents
  configuration:
    aISettings:
      contentModeration: Maximum     # <- subiu de High
    recognizer:
      kind: CLICopilotRecognizer     # <- novo orquestrador
    agentSettings:
      kind: AgentSettings
      version: "1.0"
      model:
        series: Opus48
      instructions:
        segments:
          - kind: StaticSegment
            value: |-  ...            # <- as instruções agora vivem aqui
      enableMemory: true             # <- capacidade nova
      web:
        enableWebSearch: false
      conversationStarters: []       # <- vazio!
```

**Conteúdo real (11 componentes):**

| Tipo | Qtd | Quais |
|---|---|---|
| `DialogComponent` → `kind: ConnectorTool` | 3 | `Power BI Master DB Search`, `Inicio de Conversa` (Power BI), `Postar mensagem em um chat ou canal` (Teams) |
| `DialogComponent` → `kind: InlineAgentSkill` | 1 | `inicio-de-conversa` — a skill nova, com `content:` em markdown + frontmatter |
| `GlobalVariableComponent` | 4 | `PowerBIMasterDBSearch.groupid`, `.datasetid`, `.specification_query`, `IniciodeConversa.specification_query` |
| `KnowledgeSourceComponent` | 2 | as mesmas 2 fontes SharePoint — **estas migraram intactas** |
| `ConnectionReference` | 2 | Power BI (com `connectionId`) e Teams (sem `connectionId`, porque usa credencial do usuário final) |

De novo, ~11.000 das 13.810 linhas são swagger de conector (Power BI a partir da linha 369, Microsoft Teams a partir da 2769). Só ~330 linhas são conteúdo seu.

---

## A diferença estrutural, em uma frase

| Clássico | Nova experiência |
|---|---|
| Você desenha **fluxos** (tópicos) com nós: `Question`, `ConditionGroup`, `SetVariable`, `ParseValue`, `BeginDialog`, `SendActivity`, `SearchAndSummarizeContent`, tudo com fórmulas **Power Fx** | Você escreve **instruções em linguagem natural** + **skills** (arquivos Markdown) + **tools**, e um orquestrador decide o que chamar |
| Controle determinístico: o `If` roda do jeito que você escreveu | Controle probabilístico: o modelo escolhe a skill pela `description` e segue as instruções |
| `OnConversationStart`, `OnRecognizedIntent` com `triggerPhrases` | Sem tópicos, sem trigger phrases. Ativação por descrição semântica |
| Child agents | Connected agents (agentes reais separados) |
| Triggers dentro do agente | Triggers vivem em **Workflows** |

A Microsoft anunciou em junho/2026 que **tópicos e child agents não são mais suportados** na nova experiência, e **não existe conversor** entre as duas — nem de ida nem de volta. Um agente clássico continua clássico; um agente novo tem que ser construído do zero na nova experiência.

Ou seja: o que aconteceu com você não foi erro de configuração. Foi uma troca de arquitetura, e o que a ferramenta trouxe automaticamente para o agente novo foi só uma fração do antigo — com alguns defeitos de configuração no caminho, que o documento seguinte detalha.

➡️ Continue em [`02-diagnostico-completo.md`](02-diagnostico-completo.md)
