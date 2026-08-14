# 0. Comece aqui — o que fazer, na ordem

Este é o único documento que você precisa abrir para trabalhar. Os outros são referência, e este remete a eles na hora certa.

Divisão por **dependência**, não por assunto: o Bloco A você faz sozinho hoje; o Bloco B depende de outra pessoa.

| Bloco | O quê | Tempo | Depende de |
|---|---|---|---|
| **0** | Pedir liberação no Teams Admin Center | 2 min | — (mas destrava o B) |
| **A** | 4 correções de tool | ~40 min | ninguém ✅ |
| **B** | Publicar no Teams + completar a tool | ~20 min | **Bloco 0 aprovado** |
| **C** | Colar os 2 tópicos | ~10 min | Blocos A e B |
| **D** | Polimento (opcional) | ~15 min | ninguém |

> ⚡ **Faça o Bloco 0 agora e o Bloco A em seguida.** O Bloco 0 fica rodando em paralelo com terceiros enquanto você trabalha.

---

# ⚡ BLOCO 0 — faça isto primeiro (2 minutos)

Abra o chamado para o time de Teams / IT da Unilever pedindo:

> Liberação de **app personalizado (custom app)** no Microsoft Teams Admin Center, para publicar um agente do Copilot Studio no Teams.

**Por que agora:** sem isso o Bloco B **não acontece**, e liberação de política de tenant costuma levar dias. Se você deixar para pedir depois de terminar as tools, perde a semana.

- [ ] Chamado aberto

Enquanto espera, siga para o Bloco A — ele não depende disso.

---

# 🔧 BLOCO A — as 4 correções de tool (~40 min)

**É aqui que o agente destrava.** Nenhuma destas depende de admin, de publicação, nem do Teams.

**Onde:** Copilot Studio → AURA Agent → **Ferramentas** → clique na tool → **Entradas**.

Em cada entrada existe a coluna **"Preencher usando"**:
- **Valor personalizado** = fixo, você digita
- **Preencher dinamicamente com IA** = o modelo preenche — e a **descrição da entrada** é o único lugar onde ele aprende o formato

> ⚠️ Se uma entrada não aparece na lista, procure por **"+ Adicionar entrada"** ou expanda **"Mostrar todas as entradas"**. Foi exatamente aí que os inputs se perderam.

Os textos completos para colar estão em [`02-correcao-das-tools.md`](02-correcao-das-tools.md) — abra ao lado.

### A1 · `Update Project` 🔴 a mais urgente

Hoje esta tool **não atualiza nada**: recebe o `id` e não tem onde receber o que mudar.

- [ ] Adicionar `type` → **Valor personalizado** → `IT Project`
- [ ] Adicionar `userEnteredFields` → **Dinamicamente com IA** → colar a descrição ([Correção 1](02-correcao-das-tools.md#correção-1--update-project--mais-urgente))
- [ ] Adicionar a descrição da entrada `id` (ela já existe, só está sem descrição)

### A2 · `Power BI Portfolio Database` 🔴 destrava a análise

A abertura funciona porque o tópico passa a query. Fora dela, o modelo não tem como escrever DAX.

- [ ] Adicionar `query` → **Dinamicamente com IA** → colar o dicionário de colunas ([Correção 2](02-correcao-das-tools.md#correção-2--power-bi-portfolio-database--destrava-a-análise))

### A3 · `Obter os detalhes do item de trabalho` 🔴

- [ ] Adicionar `id` → **Dinamicamente com IA** → colar a descrição
- [ ] Trocar a descrição da tool pelo texto `SILENT TOOL...` ([Correção 3](02-correcao-das-tools.md#correção-3--obter-os-detalhes-do-item-de-trabalho)) — é o que impede o agente de despejar JSON cru

### A4 · `Query Devops BU` e `Query Devops IT Area` 🟠

- [ ] Em `Query Devops BU`: adicionar `queryId` → **Dinamicamente com IA** → colar a tabela de GUIDs por BU
- [ ] Em `Query Devops IT Area`: o `queryId` já existe, só colar a descrição com os GUIDs por área

### ✅ Terminei o Bloco A?

No painel de teste, estas 4 perguntas têm que funcionar. **Hoje as quatro falham.**

| # | Digite | Esperado |
|---|---|---|
| 1 | `mude o Note do work item <id de teste> para "teste AURA"` | Confirma e grava — **este é o teste decisivo** |
| 2 | `quais são os projetos watermelon?` | Roda uma query DAX nova e responde |
| 3 | `me traz os detalhes do work item 376` | Traz os campos, sem JSON cru |
| 4 | `me lista os projetos de Personal Care` | Usa o Query ID de PC |

> ⚠️ No teste 1, use um **work item de teste**, nunca um projeto real. É a única tool que grava.

---

# 📢 BLOCO B — Teams (~20 min, depois da aprovação)

> 🛑 **PARE AQUI SE** o chamado do Bloco 0 ainda não foi aprovado. Sem app personalizado liberado no tenant, o dropdown continua vazio por mais que você tente.

**Por que o dropdown `Agent` está vazio hoje:** ele é preenchido por uma chamada que lista **agentes publicados no Teams**. O seu nunca foi publicado. Não é bug — é ordem de operações.

Nesta sequência exata:

- [ ] **1.** Teams Admin Center: app personalizado liberado (Bloco 0) ✅
- [ ] **2.** Copilot Studio → **Canais** → ligar **Microsoft Teams**
- [ ] **3.** Copilot Studio → **Publicar**
- [ ] **4.** Teams → instalar o agente (**Abrir agente** / **Adicionar ao Teams**)
- [ ] **5.** Voltar em **Ferramentas → Teams — Postar mensagem** → entrada **Agent** → agora o **AURA Agent** aparece → selecionar
- [ ] **6.** Adicionar `body.recipient` → **Dinamicamente com IA** → descrição em [Correção 5](02-correcao-das-tools.md#correção-5--teams--postar-mensagem)
- [ ] **7.** Adicionar `body.messageBody` → **Dinamicamente com IA** → descrição em Correção 5
- [ ] **8.** Trocar a descrição da tool (a atual, "Posta uma mensagem em um chat ou canal", é genérica demais e o orquestrador chama sem querer)

**Recomendado:** trocar a autenticação de **Invoker** para **Maker**, para a cobrança não depender de cada pessoa ter conectado o Teams. Detalhes em [`03-teams-conversa-com-gestor.md`](03-teams-conversa-com-gestor.md), §3.5.

### ✅ Terminei o Bloco B?

- [ ] O **AURA Agent** aparece no dropdown **Agent** e está selecionado

---

# 📋 BLOCO C — os dois tópicos (~10 min)

**Sim, são dois tópicos separados.** Um arquivo = um tópico. **Não cole os dois no mesmo.**

Eles são as duas metades do mesmo ciclo:

```
cobranca-gestor      →  a IDA    (você manda a cobrança)
resposta-do-gestor   ←  a VOLTA  (o gestor responde e o agente grava no DevOps)
```

**Caminho, para cada um dos dois arquivos:**

1. Copilot Studio → AURA Agent → **Tópicos**
2. **+ Adicionar um tópico** → **Do zero**
3. Canto superior direito → menu **⋯** → **Abrir editor de código**
4. Apagar tudo que estiver lá e **colar o conteúdo do `.yaml`**
5. **Salvar**

- [ ] Tópico 1 colado: [`topics/cobranca-gestor.yaml`](../../topics/cobranca-gestor.yaml)
- [ ] Tópico 2 colado: [`topics/resposta-do-gestor.yaml`](../../topics/resposta-do-gestor.yaml)

### ✅ Terminei o Bloco C?

Teste ponta a ponta **com você mesmo como destinatário**. Repare na ordem: cancele antes de aprovar, para validar o portão antes de validar o envio.

| # | Onde | Ação | Esperado |
|---|---|---|---|
| 1 | Painel de teste | `cobrar o gestor` | Pergunta o Work Item ID |
| 2 | | `376` | Lê o DevOps, sugere um e-mail, pede confirmação |
| 3 | | **seu próprio** e-mail | Mostra o rascunho e pergunta se pode enviar |
| 4 | | **Cancelar** | Não envia nada ✅ |
| 5 | | repetir e escolher **Enviar** | Chega no seu Teams, no chat com o AURA Agent |
| 6 | Teams | `a nova data é 30/11/2026` | Dispara o segundo tópico, pede o ID |
| 7 | | `376` | Mostra o de-para e pede confirmação |
| 8 | | **Confirmar** | Grava — confira no DevOps |

Só depois de tudo isso passar, teste com um gestor real.

> 📎 Dois pontos que podem precisar de ajuste na primeira execução (binding dos campos do Teams e formato da data): [`topics/README.md`](../../topics/README.md), seção "Dois pontos que eu não consigo verificar daqui".

---

# ✨ BLOCO D — polimento (~15 min, opcional)

Nada aqui é bloqueante. Tudo está detalhado em [`02-correcao-das-tools.md`](02-correcao-das-tools.md#correções-opcionais-mas-baratas).

- [ ] **5º KPI de graça** — a `tabela_agente` já devolve `% High Potencial` (6%) e o dashboard não mostra. Um `SetVariable` no tópico `Início da conversa`
- [ ] **Saudação em português** — o agente é pt-BR mas a saudação está em inglês
- [ ] **Typo nas instruções** — `[Project Total Budget**€**)]` → `[Project Total Budget (**€**)]`
- [ ] **Desligar navegação na web** — hoje está ligada; num agente de dado corporativo isso convida o modelo a misturar web pública com o portfólio
- [ ] **`Project Deep Dive`** — hoje busca numa "base mestra" que não existe como fonte de conhecimento. Trocar por uma chamada à `Power BI Master DB Search`. É a mudança que mais melhora a precisão do Deep Dive
- [ ] **Testar as fontes de conhecimento** — mudaram de tipo; a do Wiki aponta um `.pdf` num campo que espera site. Teste: `o que é a fase 09 PGLS?`

---

## Se algo der errado

| Sintoma | Causa provável |
|---|---|
| "Não tenho ferramenta para isso" | A entrada não foi adicionada, ou ficou como Valor personalizado em branco |
| HTTP 400 no Power BI | `groupid`/`datasetid` saíram de Valor personalizado |
| Agente despeja JSON cru | Faltou o `SILENT TOOL... DO NOT generate text` na descrição (A3) |
| Update "funciona" mas nada muda | `userEnteredFields` não foi adicionado (A1) |
| Dropdown **Agent** vazio | Agente não publicado no Teams — Bloco B, passos 1 a 4 |
| `We couldn't find your bot` | Agente e tool em ambientes diferentes, ou agente despublicado |
| Mensagem chega mas o agente não responde à resposta | O gestor está fora do grupo de acesso do agente |

Mais casos: [`03-teams-conversa-com-gestor.md`](03-teams-conversa-com-gestor.md), §3.7.

---

## Onde estão as outras coisas

| Quero… | Vá para |
|---|---|
| Entender **por que** está quebrado | [`01-diagnostico-aura-agent.md`](01-diagnostico-aura-agent.md) |
| O texto exato de cada correção | [`02-correcao-das-tools.md`](02-correcao-das-tools.md) |
| Entender o Teams a fundo | [`03-teams-conversa-com-gestor.md`](03-teams-conversa-com-gestor.md) |
| Decidir sobre Work IQ | [`04-work-iq.md`](04-work-iq.md) |
| Receitas de DAX | [`dax-cookbook.md`](../../skills/portfolio-overview/references/dax-cookbook.md) |
| Nomes dos campos `Custom.*` | [`campos-devops.md`](../../skills/update-devops/references/campos-devops.md) |
