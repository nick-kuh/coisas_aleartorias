# 3. Manual da nova experiência do Copilot Studio

Este é o "manual" que faltava: o que existe hoje, o que sumiu, e como cada peça funciona — com foco no que o Aura Agent precisa. Links das fontes no fim.

---

## 3.1 O modelo mental novo

No clássico você era **desenhista de fluxo**. Na nova experiência você é **redator de comportamento**. Toda a arquitetura se resume a cinco camadas:

```
┌─────────────────────────────────────────────────────┐
│ INSTRUCTIONS  – quem o agente é e as regras sempre  │  sempre no contexto
│                  ativas                              │
├─────────────────────────────────────────────────────┤
│ SKILLS        – "como fazer a tarefa X"             │  carregadas sob demanda
│                  (arquivos Markdown)                 │
├─────────────────────────────────────────────────────┤
│ TOOLS         – ações concretas (conector, MCP,     │  chamadas quando preciso
│                  agent flow, API)                    │
├─────────────────────────────────────────────────────┤
│ KNOWLEDGE     – documentos, SharePoint, Dataverse,  │  buscadas quando preciso
│                  Microsoft IQ / Fabric IQ            │
├─────────────────────────────────────────────────────┤
│ MEMORY        – o que persiste entre conversas      │  novo
└─────────────────────────────────────────────────────┘
        ↑
   ORQUESTRADOR decide o que usar, quando, em que ordem
```

O que **acabou**: tópicos, child agents inline, trigger phrases, nós de fluxo (`Question`, `ConditionGroup`, `SetVariable`, `ParseValue`, `SendActivity`), e triggers dentro do agente.

O que **surgiu**: skills, memory, connected agents (agentes de verdade, não inline), workflows com o designer novo, e Microsoft IQ / Fabric IQ como fonte de conhecimento.

> **Não existe migração automática.** As duas experiências usam arquiteturas diferentes e a conversão não é suportada em nenhuma direção. Agente clássico fica clássico; agente novo precisa ser construído na nova.

---

## 3.2 SKILLS — a parte que você não sabia fazer

### O que é

Uma skill é **um arquivo Markdown com frontmatter YAML**. Só isso. Ela contém um conjunto de instruções auto-contido para uma tarefa específica, e é carregada **só quando o orquestrador decide que é relevante** (isso se chama *progressive disclosure*). É o substituto direto do tópico.

O formato é o **Agent Skills**, padrão aberto criado originalmente pela Anthropic e adotado pela Microsoft — o mesmo formato funciona no Copilot Studio, no GitHub Copilot, no Visual Studio e no VS Code.

### Anatomia de um `SKILL.md`

```markdown
---
name: project-deep-dive
description: Análise profunda de UM projeto específico do portfólio CDIO...
             Use quando o usuário citar o nome ou o ID de um projeto...
             NÃO use para visão macro do portfólio (use portfolio-overview).
---

# Project Deep Dive

## Quando esta skill está ativa

1. Faça isto
2. Depois isto
...

## Formato de saída
...

## Casos de borda
...
```

### As regras que a Microsoft impõe

| Campo | Regra |
|---|---|
| `name` | **kebab-case**: só minúsculas, números e hífen. Não pode começar nem terminar com hífen. ≤ 64 caracteres. `Project Deep Dive` ❌ · `project-deep-dive` ✅ |
| `description` | ≤ 1024 caracteres. É o **contrato de ativação** — é ela, e só ela, que o orquestrador lê para decidir se carrega a skill. Precisa dizer *o que faz*, *quando usar* e *quando NÃO usar* |
| corpo | Markdown livre. Recomendação: manter o `SKILL.md` abaixo de ~500 linhas |
| `references/` | Material pesado (tabelas de GUID, dicionário de campos, receitas de DAX) vai em arquivos separados, e o `SKILL.md` diz **quando** ler cada um |

### A `description` é 90% do resultado

Este é o erro nº 1 de quem vem do mundo dos tópicos. No clássico, o gatilho era literal: `triggerPhrases: ["preparar reunião", "pauta para a reunião"]`. Na nova experiência **não existe trigger phrase** — a ativação é semântica, comparando a intenção do usuário com a `description`.

❌ Ruim: `description: Prepara reuniões.`
✅ Bom:

```yaml
description: >
  Gera a pauta executiva de cobrança para a reunião semanal de uma IT Area do
  CDIO LATAM (Focus Market, Make, CD ou Consumer). Cruza os work items do Azure
  DevOps da área com as transcrições de Leadership Meetings e devolve um plano
  de ação por Owner + os Big Rocks. Use quando pedirem "preparar reunião",
  "pauta", "o que cobrar na call", "pontos de atenção da reunião de <área>".
  NÃO use para análise de um projeto único (use project-deep-dive) nem para
  visão geral do portfólio (use portfolio-overview).
```

Repare no padrão: **o que faz + com que dados + quando usar + quando NÃO usar**. O "quando não usar" evita que duas skills briguem pela mesma pergunta.

### Como a skill chama uma tool

A skill **não** tem sintaxe de invocação. Ela referencia a tool **pelo nome visível**, em texto:

```markdown
2. Chame a tool **`Power BI Portfolio Database`** com a query DAX:
   EVALUATE FILTER('tabela', SEARCH("<nome>", 'tabela'[Short Name], 1, 0) > 0)
```

São *ponteiros suaves*. Consequências práticas:

- **O nome da tool tem que bater exatamente** com o que está configurado no agente. Foi por isso que a sua skill `inicio-de-conversa` não funcionou: ela cita "PowerBI - Execute a query against a dataset", que não é o nome de nenhuma tool sua.
- **Nunca dê a uma skill o mesmo nome de uma tool.** Hoje você tem a tool `Inicio de Conversa` e a skill `inicio-de-conversa`. Renomeie a tool.
- Se a tool não existir, o agente não dá erro — ele **improvisa**, que é pior.

### Como criar uma skill na UI

Menu **Skills → Adicionar skill**, com três caminhos:

1. **Criar do zero** — a UI pede nome, descrição e instruções. (Foi o que você usou: o marcador `<!-- bic:source=blank -->` na sua skill denuncia isso.)
2. **Carregar arquivo** — sobe um `.md` com frontmatter, ou um `.zip` contendo `SKILL.md` + arquivos de apoio. **É assim que você vai instalar as skills deste repositório.** Só o `.zip` suporta `references/`.
3. **Descrever em linguagem natural** — a IA redige a skill para você.

Skills são reutilizáveis: cria uma vez, usa em vários agentes.

---

## 3.3 INSTRUCTIONS — o que fica sempre ligado

As instruções ficam sempre no contexto, então **cada palavra custa**. A regra: instruções guardam o que vale para *toda* interação; o resto vai para skill.

| Vai nas Instructions | Vai numa Skill |
|---|---|
| Persona, tom, objetivo | Passo a passo de uma tarefa |
| Vocabulário/acrônimos do negócio | Formato de um relatório específico |
| Regras inegociáveis (anti-alucinação, formato de data) | Queries, GUIDs, mapeamentos |
| Roteamento de alto nível ("para dado numérico use PBI, para status use DevOps") | Dicionários de campo, receitas de DAX |

Há limite de caracteres (na faixa de ~8.000). As suas instruções atuais estão pesadas justamente porque carregam receita de DAX, lista de campos e lista de estados — coisas que pertencem a `references/` de skill.

---

## 3.4 TOOLS — o que mudou na prática

Uma tool é uma ação concreta: operação de **conector** (Power BI, Azure DevOps, Teams…), **MCP server**, **agent flow**, **API/REST** ou **prompt**.

### Configuração de cada input

Para cada parâmetro você escolhe o **"Preencher usando"**:

| Opção | Equivalente clássico | Quando usar |
|---|---|---|
| **Preencher dinamicamente com IA** (padrão) | `AutomaticTaskInput` | O modelo deduz do contexto. Ex.: a query DAX, o `id` do work item |
| **Valor personalizado** | `ManualTaskInput` | Fixo ou fórmula Power Fx. Ex.: `groupid`, `datasetid`, `account`, `project` |

> ⚠️ **O padrão é "preencher com IA".** É por isso que a sua `Power BI Master DB Search` quebrou: ao recriar a tool, ninguém travou `groupid`/`datasetid` em "Valor personalizado", e o modelo não tem como adivinhar GUID.

Power Fx ainda existe — mas **só** dentro de "Valor personalizado" de input de tool. Não existe mais Power Fx para condicional de fluxo.

### Descrição da tool = roteamento

A descrição continua sendo o que faz o orquestrador escolher a ferramenta. As suas descrições clássicas eram boas e devem ser mantidas:

> `SILENT TOOL. Fetches raw JSON data for a single Azure DevOps work item using its unique ID. (...) DO NOT generate text, summaries, or recommendations when using this tool.`

Esse "SILENT TOOL / DO NOT generate text" é o que impede o agente de despejar JSON cru na cara do usuário.

### Autenticação

| Modo | No YAML | Significado |
|---|---|---|
| **Maker-provided** | `authMode: Maker` | Roda com a SUA conexão. Todo mundo enxerga o mesmo dado. É o caso do Power BI e do DevOps do Aura |
| **End user** (padrão) | `authMode: Invoker` | Cada usuário conecta a própria conta. É o caso da sua tool do Teams — e é o certo: a mensagem de cobrança sai como a pessoa, não como um bot |

---

## 3.5 KNOWLEDGE

Suas 2 fontes SharePoint migraram intactas e continuam funcionando igual. Novidades que valem para você:

- **Fabric IQ / Power BI semantic model como conhecimento.** Hoje você fala com o Power BI por DAX via conector. Existe agora o caminho de plugar o *semantic model* como fonte de conhecimento (Microsoft IQ ficou GA no Copilot Studio), o que dispensaria escrever DAX para perguntas comuns. **Não estou propondo isso agora** — trocar o motor de dados no mesmo momento em que você reconstrói o agente é acumular duas variáveis. Fica como evolução depois que o agente estiver estável.
- **Work IQ** traz contexto organizacional do Microsoft 365.

---

## 3.6 MEMORY — capacidade nova, já ligada no seu agente

`enableMemory: true` já está no seu YAML. Memory dá contexto persistente entre interações: preferências, padrões, contexto recorrente.

Cuidado importante: **memory não substitui a `Global.tabela_pbi`**. Aquela variável guardava o resultado de uma query dentro de uma conversa. Memory é sobre preferências duráveis do usuário ("Nicolas sempre quer ver BW/PC primeiro"), não sobre cache de dataset. Por isso a instrução que manda ler `Global.tabela_pbi` tem que ser **removida**, não readaptada.

---

## 3.7 TRIGGERS e WORKFLOWS — onde foi parar a automação

Triggers **saíram de dentro do agente**. Se você quer comportamento autônomo ("toda segunda 8h, varra o portfólio e avise quem está atrasado"), o desenho é:

```
Workflow (trigger de recorrência / SharePoint / Forms / HTTP)
   └─> nó de Agente  ─> chama o Aura Agent
   └─> nó de ação    ─> posta no Teams
```

O designer de workflows foi refeito (maio/2026) e suporta início manual, recorrência agendada, HTTP e triggers de conector. Agentes entram como **nó** dentro do workflow.

Isso importa para você em dois pontos:

1. **A cobrança automática de gestores** que você pediu pode virar, no futuro, um workflow agendado em vez de algo que você dispara na conversa.
2. **O controle de acesso da Meeting Preparation** — ver abaixo.

---

## 3.8 ⚠️ O que você perde de verdade: determinismo

Este é o ponto que ninguém fala e que você precisa saber antes de reconstruir.

No clássico, a restrição da `Meeting Preparation` era código:

```powerfx
=Or(
  "nicolas.kuhnast@unilever.com" in Lower(System.User.Email),
  "luciano.barbosa@unilever.com" in Lower(System.User.Email),
  "william.manganeli@unilever.com" in Lower(System.User.Email),
  "monserrat.diaz@unilever.com" in Lower(System.User.Email)
)
```

Isso **executava**. Não tinha como contornar.

Numa skill, a mesma regra vira texto: "só gere a pauta se o e-mail do usuário estiver nesta lista". Um modelo obedece na maioria das vezes — mas é uma instrução, não um portão. Alguém insistente pode contornar.

**Três formas de recuperar o determinismo, em ordem de esforço:**

1. **Compartilhamento do agente por grupo de segurança** (o `accessControlPolicy: GroupMembership` já está ligado). Controla quem fala com o agente. Simples, mas é tudo-ou-nada: não dá para liberar o agente para todos e a pauta para quatro.
2. **Agente separado** só para a pauta executiva, compartilhado apenas com os 4. Recomendado se a informação for realmente sensível.
3. **Workflow** com o teste de e-mail num nó de condição (determinístico) e o agente como nó seguinte. Mais trabalho, controle real.

Vou entregar a instrução dentro da skill **e** deixar registrado que ela não é um portão. A decisão é sua.

Regra geral para o resto do agente: **onde havia `ConditionGroup` com regra de negócio crítica, tem que existir uma pergunta de confirmação ou um workflow.** É por isso que a skill `update-devops` e a `notificar-gestor` obrigam confirmação explícita antes de gravar/enviar — é a forma de recolocar um portão onde o Power Fx sumiu.

---

## 3.9 Azure DevOps: conector vs MCP

Você escolheu reconstruir com o **conector** — é o caminho certo agora: é o que já funcionava, está 100% suportado, e você mantém `account`/`project`/`typeName` fixos.

Como evolução futura existe o **MCP Server do Azure DevOps** (`microsoft/azure-devops-mcp`), que exporia todas as APIs do DevOps de uma vez em vez de uma tool por operação. Copilot Studio suporta MCP em **Tools → Adicionar ferramenta → Model Context Protocol**, mas o MCP do Azure DevOps **não está na lista pronta** — precisaria ser hospedado como MCP remoto (Azure Container Apps / App Service) e isso exige alguém com acesso ao Azure. Fica registrado, não é para agora.

---

## 3.10 Checklist mental na hora de decidir onde algo vai

```
É quem o agente é, ou regra que vale sempre?      → INSTRUCTIONS
É "como executar a tarefa X"?                     → SKILL
É "chamar o sistema Y"?                           → TOOL
É documento para consultar?                       → KNOWLEDGE
É preferência que dura entre conversas?           → MEMORY
É "quando acontecer Z, faça"?                     → WORKFLOW
É tabela/GUID/dicionário que só uma skill usa?    → references/ da skill
```

---

## Fontes

- [Skills overview for agents — Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/skills-overview)
- [Create a skill for an agent — Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/skills-create)
- [Add an existing skill to an agent — Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/skills-add-existing)
- [Manage and delete skills — Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/skills-manage)
- [Add a tool to an agent (preview) — Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/add-tools-custom-agent)
- [Build an agent (preview) — Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/build-overview)
- [Memory (preview) — Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/memory-overview)
- [Settings (preview) — Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/settings-overview)
- [Add MCP components to an agent — Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-copilot-studio/mcp-add-components-to-agent)
- [What's new in Copilot Studio (maio/2026): workflows e computer-using agents](https://www.microsoft.com/en-us/microsoft-copilot/blog/copilot-studio/new-and-improved-computer-using-agents-a-new-workflows-experience-and-real-time-voice-experiences/)
- [Skills como substituto de tópicos e child agents — Reshmee Auckloo](https://reshmeeauckloo.com/posts/copilotstudio-skills-referencingtools/)
- [Copilot Studio Reimagined: orquestrador, SKILL.md — Holger Imbery](https://holgerimbery.blog/copilot-studio-reimagined)
- [Agents Have Skills Now — The Custom Engine (Microsoft)](https://microsoft.github.io/mcscatblog/posts/modern-mcs-agent-skills/)
- [microsoft/azure-devops-mcp](https://github.com/microsoft/azure-devops-mcp)

➡️ Continue em [`04-passo-a-passo.md`](04-passo-a-passo.md)
