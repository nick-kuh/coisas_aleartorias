# 9. O erro do Teams — `HTTP 400 · Label for notification`

> **Status:** causa-raiz identificada e provada no log. Correção de 1 campo.
> **Evidência:** `botContent__20260908T140500` (`dialog.json`, conversa `01234a6e-10e4-419d-8b7a-e969eee538d7`, 08/09/2026 16:35 UTC).

---

## A frase que o agente devolveu

```
Mensagem de Erro: O conector 'Microsoft Teams' retornou um erro HTTP com o código 400.
Erro Interno: Label for notification value needs to be Yes or No under Advanced option
RequestId : 5c7c5944-a697-429c-968e-840e00ec92c5
Código do Erro: ConnectorRequestFailure
```

Não é o `poster`. Não é o `location`. Não é o `bot`. Não é permissão, não é publish, não é o gestor sem o app instalado.
É **um** campo avançado da tool: **`body.attribution`** — *"Rotular como notificação" / "Label as notification"*.

---

## A prova

O `DynamicPlanStepBindUpdate` aparece **duas vezes** por chamada de tool: o bind inicial e o bind final que vai para o conector.

Em toda chamada que **funcionou** na mesma conversa, os dois binds são **byte a byte idênticos**:

| Passo | Tool | Bind 1 | Bind 2 | Resultado |
|---|---|---|---|---|
| `[2]`/`[3]` | Power BI (dashboard) | 3 args | **3 args, iguais** | ✅ |
| `[5]`/`[6]` | Power BI (`tabela_agente`) | 3 args | **3 args, iguais** | ✅ |
| `[19]`/`[20]` | Power BI (busca TAX Reform) | 3 args | **3 args, iguais** | ✅ |
| `[34]`/`[35]` | **Teams · Post message** | **7 args** | **6 args — some `attribution`** | ❌ 400 |

Bind 1 — atividade `[34]`:

```json
"body": {
  "activeChat": "Send",
  "attribution": "No",              ←  presente
  "bot": "crdc4_AURAAgent",
  "installedError": "Succeed",
  "messageBody": "Oi, tudo bem? O Nicolas me pediu...",
  "recipient": "lucas.barbosa2@unilever.com"
}
```

Bind 2 — atividade `[35]`, o que efetivamente saiu:

```json
"body": {
  "activeChat": "Send",
                                    ←  attribution SUMIU
  "bot": "crdc4_AURAAgent",
  "installedError": "Succeed",
  "messageBody": "Oi, tudo bem? O Nicolas me pediu...",
  "recipient": "lucas.barbosa2@unilever.com"
}
```

É a única diferença entre os dois binds, na única chamada que falhou. Não há ambiguidade.

---

## Por que o campo é descartado

Confronte o valor com o tipo declarado. No `DynamicPlanReceived` (`[31]`), a própria definição de tool que o orquestrador recebeu:

```json
{
  "$kind": "ToolInput",
  "name": "Label as notification",
  "description": "Sender name",
  "type": { "$kind": "Boolean" },     ←  BOOLEANO
  "propertyName": "body.attribution",
  "order": 1
}
```

E no `botContent.yml`:

```yaml
- kind: ManualTaskInput
  propertyName: body.attribution
  value: Yes                          ←  STRING
```

A sequência completa:

1. O input é tipado **`Boolean`** no `dynamicInputSchema` do conector.
2. O valor gravado na tool é a **string** `"No"` (hoje `"Yes"`) — não `true`/`false`.
3. `attribution` **não** está marcado `isRequired: true` no schema (diferente de `bot`, `recipient` e `messageBody`, que estão).
4. A coerção string → boolean falha. Por ser opcional aos olhos do Copilot Studio, o runtime **descarta o parâmetro em silêncio** em vez de erguer erro. Daí o bind 2 mais curto.
5. O conector do Teams, do lado do servidor, **exige** o campo. Recebe o body sem ele e devolve `400 · Label for notification value needs to be Yes or No under Advanced option`.

O silêncio do passo 4 é o que torna o erro difícil de ler: a mensagem fala de um campo que o agente nem chegou a enviar.

---

## ⚠️ A edição das 16:50 não resolve

Cronologia extraída do próprio export:

| UTC | O quê | De onde |
|---|---|---|
| 16:35:29 | Chamada falha com o 400 | `dialog.json` `[36]` |
| 16:36:46 | Agente publicado | `entity.publishedOn` |
| **16:50:30** | **Tool do Teams editada** | `auditInfo.modifiedTimeUtc` da tool |
| 17:05 | Export gerado | nome do zip (14:05 BRT) |

A tool foi mexida depois da falha e hoje está com `value: Yes` em vez de `No`. **Isso vai falhar exatamente igual**: continua sendo uma string, e o problema nunca foi *qual* string — foi *ser* string.

Dois agravantes:

- O serializador do arquivo **cita quando precisa** (`displayName: "Entrar "` está entre aspas). `Yes` saiu como token nu, sem virar `true`. É string.
- `publishedOn` (16:36:46) é **anterior** a `modifiedTimeUtc` da tool (16:50:30) — a alteração **ainda não foi publicada**. Mesmo que estivesse certa, não estaria valendo.

---

## A correção

### Opção A — arrumar o campo na tool (5 min, é a certa)

1. Copilot Studio → **Ferramentas** → *Microsoft Teams · Postar mensagem em um chat ou canal*.
2. Abrir **Opções avançadas** / *Advanced*.
3. Em **Rotular como notificação** (*Label as notification*): **selecionar no dropdown**, não digitar. O controle é booleano — tem que gravar `true`/`false`, não o texto `Yes`/`No`.
   - Se o campo estiver com o texto colado, **limpe-o** e escolha na lista.
   - Se ele aceitar fórmula, `=false` também serve. `"No"` entre aspas, não.
4. **Publicar** o agente. Sem isso a correção não sai do rascunho.
5. Teste de aceite: `cobrar o gestor do 1256 sobre o go-live` → aprovar → a resposta tem que trazer `messageLink`, não `ConnectorRequestFailure`.

`Não` = mensagem normal do agente. `Sim` = prefixo *"Notificação via…"* antes do nome do agente. Para cobrança de governança, **Não** é o certo.

### Opção B — tirar o envio da tool e pôr num fluxo (se A não pegar)

O bug é de **coerção de tipo na camada de tool do Copilot Studio**, não do conector. Dentro de um fluxo do Power Automate o mesmo campo é um dropdown nativo, serializado corretamente pelo designer — o problema não existe. O desenho é o do §3.6, e o repositório já tem `flows/` para isso.

Custo: perde o binding direto e a chamada passa a ser um fluxo. Ganho: imune a esta classe de defeito.

---

## O resto da tool do Teams — auditoria campo a campo

| Campo | Valor hoje | Veredito |
|---|---|---|
| `poster` | `Power Virtual Agents` | ✅ certo (= *Microsoft Copilot Studio agent*) |
| `location` | `powerva` | ✅ certo (= *Chat with agent*). **Não é o culpado**: a request chegou a ser validada no corpo pelo backend do Teams, ou seja passou pelo roteamento. Um `location` inválido morre antes disso |
| `body.bot` | `crdc4_AURAAgent` | ✅ resolvido — o dropdown populou depois do publish (era o problema do §3.1) |
| `body.attribution` | `Yes` (string) | 🔴 **o defeito** |
| `body.activeChat` | `Send` | ✅ |
| `body.installedError` | `Succeed` | 🟡 **armadilha** — ver abaixo |
| `body.recipient` | `AutomaticTaskInput` | 🟡 descrição contradiz o comportamento — ver abaixo |
| `body.messageBody` | `AutomaticTaskInput` | ✅ |
| `connectionProperties.mode` | `Invoker` | 🟡 recomendação do §3.5 continua de pé: trocar para `Maker` |

### 🟡 `installedError: Succeed` — o falso positivo que vem depois

Traduz para *"Se o agente não estiver instalado: **êxito com código de status**"*. Combinado com o `SendActivity` de confirmação, produz isto:

> ✅ Mensagem enviada do seu chat com **lucas.barbosa2@unilever.com** no Teams…

…quando o Lucas **não recebeu nada**, porque nunca instalou o AURA Agent. A doc da Microsoft é explícita: mensagem proativa só chega a quem tem o agente instalado; quem desinstala ou bloqueia deixa de receber.

**Assim que o 400 sair do caminho, este é o próximo sintoma** — e é pior, porque não gera erro nenhum.

**Enquanto estiver depurando: ponha `Fail`.** Você precisa que ele grite. Depois de validado ponta a ponta com um gestor real que já instalou o app, volte para `Succeed` — aí o motivo do §3.4 (cobrança em lote não morrer inteira por causa de um gestor) passa a valer.

### 🟡 `recipient` — a regra que o agente não cumpriu

A descrição do input manda:

> `NEVER ask the user who to send to. NEVER guess or construct an address`

No log, o agente **perguntou** (`[12]`), o usuário respondeu `lucas.barbosa2` (`[15]`), o agente identificou que o gestor registrado é outro — **Rafael Silotto** — ofereceu a Opção B e mandou para o indicado pelo usuário (`[22]`, `[25]`, `[26]`).

O agente se comportou bem: detectou a divergência, avisou, registrou. Mas a descrição do input diz o oposto do que o §7 das instruções permite. **Alinhe os dois textos** — hoje a tool proíbe o que a instrução autoriza, e é sorte que o modelo tenha escolhido a leitura sensata.

---

## O que a mesma conversa mostra funcionando

Vale registrar, porque delimita o problema:

- Dashboard de abertura ponta a ponta — 429 iniciativas, €456.507 Mi de benefício, 64% on schedule (`[8]`).
- Power BI escrevendo DAX sozinho, `autoFilledArguments: ["query"]` (`[19]`) — a camada de descrição de input está fazendo o trabalho dela.
- Desambiguação de projeto: achou as duas fases de TAX Reform, mostrou a tabela, recomendou a Fase 2 por estar `Delayed` (`[22]`).
- Rascunho da mensagem no formato certo, com link `_workitems/edit/1256` e não `_apis/wit/` (`[26]`).
- Protocolo de aprovação respeitado: não chamou a tool antes do `pode enviar` (`[29]` → `[33]`).

**Toda a cadeia funciona. Ela quebra no último centímetro**, num campo avançado que o próprio runtime joga fora sem avisar.

---

## Dois achados laterais

### O `OnError` esconde o erro em produção

```yaml
condition: =System.Conversation.InTestMode = true
   → mostra {System.Error.Message}    ← detalhe completo
elseActions
   → "Ocorreu um erro. Código do erro: {System.Error.Code}"   ← só o código
```

Você só leu `Label for notification…` porque estava no painel de teste. **No Teams e no M365 Copilot o usuário vê apenas `ConnectorRequestFailure`** — que não diz nada.

Enquanto o ciclo de cobrança não estiver estável, **jogue `{System.Error.Message}` também no ramo `else`**. Depois tire.

### `Project Deep Dive` aponta para fontes que não existem

O tópico (ativo) chama `SearchAndSummarizeContent` contra `'base mestra'` e *"a base de documentos do SharePoint"*. As fontes de conhecimento cadastradas no agente são outras: `CDIO_LATAM_Governance_Wiki`, `Transcription LT Meetings`, `Consumer MarTech Tracker`, `AURA_Playbook_Analitico.docx` e um `.svg`.

Pior: essas chamadas **não têm `mode: Restricted`** (o `cobrancagestor` tem, em todas). Sem restrição, a busca pode cair no conhecimento do modelo — e um `ID` e um `Score` inventados atravessam o `SetVariable` até virarem chamada ao DevOps.

O mesmo tópico ainda monta o link final com `Topic.url` — exatamente o que a §9 das instruções proíbe (*"never the `url` a DevOps tool returns — it opens raw JSON"*).

---

## Ordem de ataque

| # | O quê | Tempo | Prova de que acabou |
|---|---|---|---|
| 1 | `attribution` → booleano pelo dropdown | 2 min | O bind 2 no log passa a ter 7 args |
| 2 | `installedError` → `Fail` (temporário) | 1 min | — |
| 3 | `{System.Error.Message}` no ramo `else` do `OnError` | 2 min | — |
| 4 | **Publicar** | 3 min | `publishedOn` > `modifiedTimeUtc` da tool |
| 5 | Teste com um gestor que **tem** o app instalado | 5 min | Retorna `messageLink` e a mensagem chega |
| 6 | `mode` → `Maker` (§3.5) | 2 min | Outra pessoa consegue cobrar |
| 7 | Reverter 2 e 3 | 2 min | — |
| 8 | `Project Deep Dive`: `mode: Restricted` + trocar `Topic.url` | 10 min | Projeto inexistente devolve alerta, não invenção |

O passo 1 é o que destrava. Os passos 2 e 3 existem para você **ver** o que acontecer depois dele.

---

## Fontes

- [Send proactive Microsoft Teams messages — Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-copilot-studio/advanced-proactive-message)
- [Use connectors in Copilot Studio agents — Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-copilot-studio/advanced-connectors)
- [Connect and configure an agent for Teams and Microsoft 365 Copilot](https://learn.microsoft.com/en-us/microsoft-copilot-studio/publication-add-bot-to-microsoft-teams)
- ["We couldn't find your bot" when posting to a Copilot Studio agent from a cloud flow](https://rajeevpentyala.com/2026/07/06/we-couldnt-find-your-bot-when-posting-to-a-copilot-studio-agent-from-a-cloud-flow/)
