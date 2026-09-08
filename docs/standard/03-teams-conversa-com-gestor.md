# 3. Teams — o agente conversando com o gestor

Você perguntou: *"criei a ferramenta do Teams mas falta o campo Agent, e não aparece nada. Eu queria que fosse do próprio agente."*

A resposta está no próprio arquivo exportado, e o cenário que você quer **funciona** — em dois modos:

- **Modo sem publicação** (§3.0 abaixo) — funciona hoje mesmo, com dois trade-offs conhecidos. Escolha este se o publish ainda não é possível.
- **Modo publicado** (§3.1 em diante) — o cenário completo de mão dupla automática, mas exige agente publicado E instalado no Teams.

---

## 3.0 Modo sem publicação — quando o publish não é possível

Se por processo burocrático, política do tenant ou aprovação de admin o agente ainda não está publicado, você **não precisa esperar** para começar a usar o ciclo de cobrança. O modo "sem publicação" usa a **sua** conexão do Teams:

```
   AURA identifica atraso e monta o rascunho
              │
              ▼
   Teams · Post message
   poster    = Flow bot            ← o bot entrega
   location  = Chat with Flow bot  ← chat 1:1 do gestor com o Flow bot
   recipient = gestor@unilever.com ← e-mail, e é por isso que o location importa
              │
              ▼
   ┌──────────────────────────────────────────┐
   │  Chat 1:1 do gestor com o Flow bot       │
   │                                           │
   │  Flow bot: "Oi, tudo bem? O Nicolas      │
   │             pediu para eu lembrar sobre   │
   │             o Horizon 2 (12345)..."       │
   │                                           │
   │  Gestor responde ali — mas para o bot,   │
   │  não para você                            │
   └──────────────────────────────────────────┘
              │
              ▼   ← o gestor te avisa por outro canal, ou você pergunta
   Volte no agente e diga o que ele respondeu.
   O agente mostra o de-para e grava no DevOps
   depois da sua confirmação.
```

> ## 🔴 Por que não é `poster: User` + `location: Group chat`
>
> Era o que eu recomendava, e **devolve HTTP 404**. Comprovado no `botContent_76`.
>
> O schema da tool define o `recipient` assim:
>
> ```yaml
> recipient:
>   displayName: Group chat
>   description: Add conversation ID     # ← ID de conversa, não e-mail
> ```
>
> Com `location: Group chat`, o `recipient` tem que ser um **ID de conversa** (`19:...@thread.v2`) — algo que ninguém tem para um gestor arbitrário. O agente manda o e-mail, que é o certo para uma pessoa, e o conector não acha a conversa.
>
> O `descriptionForModel` do próprio `location` dá a regra: *"Use \"Chat with Flow bot\" only when poster is \"Flow bot\" or \"Power Virtual Agents\""*. É esse o destino que aceita e-mail.

### Configuração da tool nesse modo

| Entrada | `kind` | Valor | Aceita descrição? |
|---|---|---|---|
| `poster` | `ManualTaskInput` | **`Flow bot`** — escolher na lista | ❌ valor fixo, o modelo não lê |
| `location` | `ManualTaskInput` | **`Chat with Flow bot`** — só aparece depois do `poster` | ❌ idem |
| `body.bot` | — | **remover** — só existe com `poster: Power Virtual Agents` | — |
| `body.recipient` | `AutomaticTaskInput` | e-mail do gestor | ✅ **essencial** |
| `body.messageBody` | `AutomaticTaskInput` | texto aprovado | ✅ **essencial** |

> ⚠️ **Descrição só existe em `AutomaticTaskInput`.** Nos 30 inputs do agente: 6 de 6 dinâmicos têm descrição, 0 de 24 fixos têm. Descrever `poster: Flow bot` é escrever para ninguém.
>
> Sobre declarar `body.recipient` e `body.messageBody`: o log mostra que eles chegam ao conector **mesmo sem estarem declarados** — o orquestrador preenche pelo `dynamicInputSchema`. Mas declarar é melhor, porque é o que permite anexar a descrição. Os textos estão em [`02-correcao-das-tools.md`](02-correcao-das-tools.md#5a--modo-sem-publicação).

**O custo deste modo:** a mensagem sai do **Flow bot**, não de você. Por isso o texto precisa dizer quem está pedindo — é o que a §7 das instruções passou a exigir. E a resposta do gestor vai para o bot, não para você: o ciclo de volta continua manual.

`authMode: Invoker` continua certo — a mensagem sai com a **sua** conexão do Teams.

### Os dois trade-offs (leia com atenção)

**1. A volta é manual, não automática.** No modo publicado, o gestor responde no chat com o agente e essa resposta vira turno de conversa. Aqui a resposta vai para o **seu** chat com ele — você é o "canal" da volta. Isso significa:

- Você precisa **acompanhar** as respostas dos gestores no seu Teams.
- Quando quiser gravar, **volte no Copilot Studio** e diga `atualizar informação do projeto` (dispara o `respostadogestor`).
- O `respostadogestor` faz o trabalho: pergunta qual campo, valida o tipo, mostra de-para, confirma e grava.

**2. O gestor vê "Nicolas mandou", não "AURA Agent".** A mensagem sai como se você tivesse digitado — o gestor não sabe que foi um agente que compôs. Pode ser bom (mais engajamento, menos parece automação) ou ruim (menos transparência sobre o uso de IA). O rascunho é escrito em primeira pessoa (`"Oi, tudo bem?"`), sem se identificar como bot.

### Quando o publish sair, o que muda

Três campos na tool do Teams, e o `cobrancagestor` volta ao rascunho em terceira pessoa. Detalhes na **Correção 5B** de [`02-correcao-das-tools.md`](02-correcao-das-tools.md). O `respostadogestor` continua igual — mas passa a poder ser disparado automaticamente pela resposta do gestor.

---

## 3.1 Modo publicado — por que o dropdown está vazio

---

## 3.1.1 Por que o dropdown está vazio

No `botContent.yml` do AURA Agent, dentro do `dynamicInputSchema` da tool do Teams:

```yaml
bot:
  displayName: Agent
  description: Select your agent
  isRequired: true
  order: 0
  dynamicValuesConfig:
    capability: List      # ← dropdown populado por chamada ao conector
  type: String
```

`dynamicValuesConfig: capability: List` significa que o dropdown **não é uma lista fixa** — ele é preenchido por uma chamada ao conector do Microsoft Teams, que devolve **os agentes do Copilot Studio publicados no Teams**.

O seu AURA Agent foi criado em **13/08/2026** e nunca foi publicado no Teams. Por isso a lista volta vazia.

**Não é bug. É ordem de operações.** Você precisa publicar antes de conseguir selecionar.

E confirmando o que está no arquivo: `poster: Power Virtual Agents` e `location: powerva` são **exatamente** o par certo — correspondem a *Post as = Microsoft Copilot Studio agent* e *Post in = Chat with agent*, que é o que a Microsoft documenta para mensagem proativa. Você acertou essa parte.

---

## 3.2 Como popular o dropdown

Quatro pré-requisitos, nesta ordem:

| # | Onde | O quê |
|---|---|---|
| 1 | **Teams Admin Center** | Permitir apps personalizados no tenant. Depende do admin do Teams da Unilever — se estiver bloqueado, para aqui |
| 2 | **Copilot Studio → Canais** | Ligar o canal **Microsoft Teams** para o AURA Agent |
| 3 | **Copilot Studio → Publicar** | Publicar o agente. Sem versão publicada, o canal não vale |
| 4 | **Teams** | Instalar o agente como app (**Abrir agente** / **Adicionar ao Teams**). Dependendo da política, pode exigir aprovação do admin |

Feito isso, volte na tool → entrada **Agent** → o AURA Agent aparece no dropdown.

> ⚠️ **A tool e o agente precisam estar no mesmo ambiente do Power Platform.** A mensagem proativa só funciona dentro do mesmo ambiente.

---

## 3.3 A mecânica que faz virar conversa de mão dupla

Este é o ponto que destrava o seu cenário.

A mensagem proativa **só pode ir para o chat pessoal do gestor com o agente** — não vai para canal, não vai para chat em grupo. Isso parece limitação, mas é justamente o que faz o resto funcionar:

```
   AURA detecta atraso no work item #12345
              │
              ▼
   Teams · Post message
   poster    = Microsoft Copilot Studio agent
   location  = Chat with agent
   bot       = AURA Agent
   recipient = gestor@unilever.com
              │
              ▼
   ┌──────────────────────────────────────┐
   │  Chat 1:1 do GESTOR com o AURA Agent │
   │                                       │
   │  AURA:   "O Horizon 2 (#12345) está   │
   │           com Go-Live vencido. Qual   │
   │           a nova data?"               │
   │                                       │
   │  Gestor: "30/11/2026"    ← ele responde AQUI
   └──────────────────────────────────────┘
              │
              ▼
   A resposta chega ao AURA como um TURNO NORMAL de conversa.
   O agente valida a data, confirma, e chama Update Project.
              │
              ▼
   Azure DevOps: Custom.GoLiveDate = 30/11/2026
```

**Por que funciona:** a mensagem cai dentro de um chat *com o agente*. Tudo que o gestor escrever ali é entregue ao agente como mensagem de usuário comum. Você não precisa de webhook, polling, nem de ler a caixa de e-mail dele. O canal de volta já existe por construção.

**O que você precisa construir:** o agente não sabe *por que* mandou a mensagem quando a resposta chega. Duas formas de resolver, e a segunda é a boa:

1. **Contexto no texto.** Colocar `#12345` na mensagem e torcer para o modelo relacionar. Frágil.
2. **Um tópico dedicado** que dispara quando alguém responde com uma data, pede o ID se não souber, valida o formato, confirma e grava. Determinístico.

⛔ **Descontinuado.** O tópico segue em [`topics/cobranca-gestor.yaml`](../../topics/cobranca-gestor.yaml) como histórico, mas a cobrança passou a ser feita pelas instruções — [`05-arquitetura-3-camadas.md`](05-arquitetura-3-camadas.md).

---

## 3.4 Requisitos do lado do gestor

| Requisito | Se não atender |
|---|---|
| Ter o AURA Agent instalado no Teams | A ação falha. O schema tem `installedError` para escolher entre **Fail** e **Succeed with status code** |
| Estar no mesmo tenant | Não entrega |
| Ter permissão de uso do agente (`accessControlPolicy: GroupMembership`) | Recebe a mensagem mas o agente não responde |

👉 **Consequência prática:** antes de rodar cobrança para valer, os gestores precisam ter o agente instalado. Na primeira rodada, mande você mesmo o link de instalação para eles — ou peça ao admin do Teams para **pré-instalar** o app via política de setup.

Configure `installedError` = **Succeed with status code**, para que uma cobrança em lote não morra inteira porque um gestor não instalou.

---

## 3.5 A escolha de autenticação

Hoje a tool está com `mode: Invoker` (credencial do usuário final).

| Modo | O que significa | Quando usar |
|---|---|---|
| **Invoker** (hoje) | A chamada ao conector usa a conexão do Teams **de quem está falando com o agente** | Cada pessoa precisa autorizar a própria conexão na primeira vez |
| **Maker** | Usa a **sua** conexão para todos | Cobrança de governança disparada pelo time de estratégia — mais previsível |

Note que isso é diferente de quem **assina** a mensagem: `poster = Microsoft Copilot Studio agent` faz a mensagem sair como **o AURA Agent** nos dois casos. O modo só decide de quem é a conexão que faz a chamada.

**Recomendação:** trocar para **Maker**. Assim a cobrança não depende de cada usuário ter conectado o Teams, e o comportamento é o mesmo para todo mundo.

---

## 3.6 Se quiser automatizar de vez

Hoje a cobrança é disparada por você, na conversa. Para virar rotina — *"toda segunda 8h, varra o portfólio e cobre quem está atrasado"* — o desenho é um **fluxo do Power Automate**:

```
Gatilho de recorrência (segunda, 8h)
   └─> Power BI · executar DAX  → lista de projetos atrasados
   └─> Aplicar a cada           → para cada projeto
         └─> Teams · Post message (poster = Copilot Studio agent,
                                   location = Chat with agent,
                                   bot = AURA Agent,
                                   recipient = gestor)
```

O fluxo precisa estar **no mesmo ambiente** do agente. E atenção aos limites de throttling do conector do Teams em lote grande — mandando para dezenas de gestores de uma vez, você bate limite e recebe erro.

---

## 3.7 Troubleshooting

| Sintoma | Causa | Solução |
|---|---|---|
| `400 · Label for notification value needs to be Yes or No` | `body.attribution` gravado como **texto** contra um input tipado `Boolean` — o runtime descarta o campo e o conector exige | [`09-erro-400-label-as-notification.md`](09-erro-400-label-as-notification.md) |
| Agente diz **✅ enviada** mas o gestor não recebeu | `installedError = Succeed with status code` + gestor sem o app instalado | Ponha `Fail` para depurar; §3.4 |
| Dropdown **Agent** vazio | Agente não publicado no Teams | §3.2, os 4 passos |
| `We couldn't find your bot` | Agente e fluxo/tool em ambientes diferentes, ou agente despublicado | Confirme o ambiente; republique |
| Ação falha para um gestor específico | Ele não tem o agente instalado | Peça instalação, ou use `installedError = Succeed with status code` |
| Mensagem entregue mas o agente não responde à resposta | Gestor fora do grupo de acesso | Revise `accessControlPolicy: GroupMembership` |
| Erro 502 / BadGateway | Falha transitória conhecida no conector | Repita; se persistir, recrie a conexão do Teams |
| Erro de throttling em lote | Limite do conector do Teams | Espace os envios, ou processe em lotes menores |
| Quer mandar para canal | **Não é suportado** | Proativa só vai para chat pessoal com o agente |

---

## Fontes

- [Send proactive Microsoft Teams messages — Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-copilot-studio/advanced-proactive-message)
- [Connect and configure an agent for Teams and Microsoft 365 Copilot](https://learn.microsoft.com/en-us/microsoft-copilot-studio/publication-add-bot-to-microsoft-teams)
- [Publish agents to channels and clients](https://learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/channels)
- [Quickstart: create a classic agent and publish it to Microsoft Teams](https://learn.microsoft.com/en-us/microsoft-copilot-studio/fundamentals-get-started-teams)
- [Send a message in Teams using Power Automate](https://learn.microsoft.com/en-us/power-automate/teams/send-a-message-in-teams)

➡️ ⛔ O tópico foi **descontinuado**. O protocolo de cobrança vive agora na §7 das [instruções](../../agent/instructions-standard.md); o tópico fica como histórico em [`topics/`](../../topics/README.md).
