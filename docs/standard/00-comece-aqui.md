# 0. Comece aqui — o que fazer, na ordem

> ## 🟢 Status em 19/08/2026 — o Teams foi resolvido
>
> O `botContent_77` confirma: `poster: Flow bot` + `location: Chat with Flow bot`, **zero erros no log**. E o schema do conector mudou sozinho, que é a prova de que pegou:
>
> ```yaml
> recipient:
>   displayName: Recipient                        # era "Group chat"
>   description: Enter a name or email address    # era "Add conversation ID"
> ```
>
> Ele agora pede **nome ou e-mail** — exatamente o que o agente manda. O 404 acabou.
>
> **Abertos agora:**
>
> | O quê | Onde | Gravidade |
> |---|---|---|
> | `Create Project` sem `title` — não cria nada | [`07`](07-criar-e-remover-projeto.md) | 🔴 a tool não funciona |
> | `Remove Project` aponta para `DeleteWorkItemLinkAsync` — **não apaga projeto** | [`07`](07-criar-e-remover-projeto.md) | 🔴 faz outra coisa |
> | Fluxo das transcrições da LT | [`06`](06-fluxo-transcricoes.md) | 🟠 novo |

> ### 🔄 18/08/2026 — mudança de arquitetura
>
> Os dois tópicos foram **descontinuados**. O agente passa a decidir sozinho, guiado por três camadas: instruções enxutas + descrição de input + playbook no SharePoint. O **Bloco C mudou de assunto** — não cole mais os tópicos.
>
> Motivo curto: as instruções antigas estavam **na fronteira do limite** (8.096 caracteres, com o teto documentado na faixa de 8.000) e cheias de repetição, e tópico prende o agente num fluxo determinístico. O desenho completo: [`05-arquitetura-3-camadas.md`](05-arquitetura-3-camadas.md).

Este é o único documento que você precisa abrir para trabalhar. Os outros são referência, e este remete a eles na hora certa.

Divisão por **dependência**, não por assunto: o Bloco A você faz sozinho hoje; o Bloco B depende de outra pessoa.

| Bloco | O quê | Tempo | Depende de |
|---|---|---|---|
| **0** | Pedir liberação no Teams Admin Center | 2 min | — (mas destrava o B) |
| **A** | 4 correções de tool | ~40 min | ninguém ✅ |
| **B** | Corrigir `poster`/`location` da tool do Teams | ~3 min | ninguém ✅ |
| **C** | Migrar para a arquitetura de 3 camadas | ~20 min | Bloco A |
| **D** | Polimento (opcional) | ~15 min | ninguém |
| **E** | As duas tools novas | ~15 min | ninguém |
| **F** | Transcrições da LT | ~20 min | ninguém |

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

### A1 · `Update Project` 🟡 **1 item pendente**

Esta tool ainda **não grava nada**: recebe o `id` e não tem onde receber *o que* mudar.

- [x] ~~Adicionar `type` → **Valor personalizado** → `IT Project`~~ ✅ feito
- [x] ~~Adicionar a descrição da entrada `id`~~ ✅ feito
- [ ] 🔴 **Adicionar `userEnteredFields`** → **Dinamicamente com IA** → colar a descrição ([Correção 1](02-correcao-das-tools.md#correção-1--update-project--mais-urgente))

> Detalhe que ajuda a achar: a descrição da própria tool já cita `userEnteredFields` em 3 das 4 regras críticas. O modelo lê a regra e não encontra o campo.

### A2 · `Power BI Portfolio Database` ✅ **CONCLUÍDA**

- [x] ~~Adicionar `query` → Dinamicamente com IA → dicionário de colunas~~ ✅

**Comprovada em runtime:** o log mostra `autoFilledArguments: ["query"]` e o modelo escreveu um DAX com filtro Cross-BU correto. Foi a correção de maior impacto.

### A3 · `Obter os detalhes do item de trabalho` ✅ **CONCLUÍDA**

- [x] ~~Adicionar `id` → Dinamicamente com IA + descrição~~ ✅
- [x] ~~Trocar a descrição da tool pelo texto `SILENT TOOL...`~~ ✅

### A4 · `Query Devops BU` e `Query Devops IT Area` ✅ **CONCLUÍDA**

- [x] ~~`Query Devops BU`: adicionar `queryId` + tabela de GUIDs por BU~~ ✅
- [x] ~~`Query Devops IT Area`: descrição do `queryId` com os GUIDs por área~~ ✅

### ✅ Terminei o Bloco A?

| # | Digite | Esperado | Status |
|---|---|---|---|
| 1 | `mude o Note do work item <id de teste> para "teste AURA"` | Confirma e grava | 🔴 **falha** — falta `userEnteredFields` |
| 2 | `quais são os projetos watermelon?` | Roda uma query DAX nova e responde | ✅ **funciona** |
| 3 | `me traz os detalhes do work item 376` | Traz os campos, sem JSON cru | ✅ |
| 4 | `me lista os projetos de Personal Care` | Usa o Query ID de PC | ✅ |

> ⚠️ No teste 1, use um **work item de teste**, nunca um projeto real. É a única tool que grava.

---

# 📢 BLOCO B — Teams ✅ **CONCLUÍDO**

Configuração final, confirmada no `botContent_77`:

| Entrada | Valor |
|---|---|
| `poster` | `Flow bot` |
| `location` | `Chat with Flow bot` |
| `body.recipient` | dinâmico, com descrição |
| `body.messageBody` | dinâmico, com descrição |
| `body.bot` | removido |

> 📌 **O que deu errado no caminho, para não repetir:** eu tinha recomendado `poster: User` + `location: Group chat`. Esse par devolve **404**, porque com `Group chat` o `recipient` precisa ser um **ID de conversa**, e o agente manda e-mail. O histórico completo está em [`02-correcao-das-tools.md`](02-correcao-das-tools.md#5a--modo-sem-publicação).

**Falta só o teste de ponta a ponta:**

- [ ] `consegue mandar um teams para <gestor>` → `pode mandar` → chega no Teams, vindo do Flow bot


**Como a mensagem chega:** do **Flow bot**, no chat 1:1 do gestor com o Flow bot — não de você. Por isso a §7 das instruções manda **dizer quem está pedindo** ("o Nicolas pediu para eu lembrar…"), em vez de escrever em primeira pessoa.

### ✅ Terminei o Bloco B?

- [ ] `consegue mandar um teams para <gestor>` → `pode mandar` → a mensagem chega no Teams, **sem erro 404**
- [ ] O texto recebido diz quem está pedindo

---

## Bloco B alternativo — modo publicado (para o futuro)

> 🛑 **Só faz sentido depois** que o chamado do Bloco 0 for aprovado e o agente for publicado + instalado no Teams. O modo sem publicação acima já resolve o ciclo.

**Por que o dropdown `Agent` fica vazio antes disso:** ele é preenchido por uma chamada que lista **agentes publicados no Teams**. Não é bug — é ordem de operações.

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

# 🧠 BLOCO C — migrar para a arquitetura de 3 camadas (~20 min)

> ⛔ **Os dois tópicos foram descontinuados. Não cole mais `cobranca-gestor.yaml` nem `resposta-do-gestor.yaml`.** Eles seguem no repositório como histórico e caminho de volta.

**O que muda:** em vez de prender o agente num fluxo, você dá a ele instruções que cabem, restrições no lugar certo e um playbook profundo para consultar. O porquê de cada camada está em [`05-arquitetura-3-camadas.md`](05-arquitetura-3-camadas.md).

| Camada | Onde vive | Orçamento | Garantia |
|---|---|---|---|
| Instruções | Copilot Studio → Instruções | ~8.000 *(usando 6.367)* | ✅ carrega sempre |
| Descrição de input | Ferramentas → Entradas | **1.024 por entrada** | ✅ carrega quando a tool é considerada |
| Playbook | SharePoint → fonte de conhecimento | sem limite prático | ⚠️ busca semântica, sob demanda |

### C1 · Colar as instruções novas

1. Copilot Studio → AURA Agent → **Instruções**
2. **Apagar tudo** e colar o conteúdo de [`agent/instructions-standard.md`](../../agent/instructions-standard.md)
3. Salvar

São **6.367 caracteres**, contra **8.096** das antigas — 21% mais enxutas, com a mesma cobertura de regra.

- [ ] Instruções substituídas

### C2 · Atualizar as duas descrições de input

Elas absorveram o que saiu das instruções — as 13 fases válidas, os formatos de escrita e a regra Cross-BU.

- [ ] `Update Project` → entrada `userEnteredFields` → descrição nova de [`02-correcao-das-tools.md`](02-correcao-das-tools.md#correção-1--update-project--mais-urgente)
- [ ] `Power BI Portfolio Database` → entrada `query` → descrição nova de [`02-correcao-das-tools.md`](02-correcao-das-tools.md#correção-2--power-bi-portfolio-database--destrava-a-análise)

### C3 · Subir o playbook no SharePoint

1. Subir [`playbook/AURA_Playbook_Analitico.docx`](../../playbook/AURA_Playbook_Analitico.docx) na biblioteca do CDIO LATAM
2. Copilot Studio → **Conhecimento** → **+ Adicionar conhecimento** → SharePoint → apontar para o arquivo
3. **Colar a descrição da fonte** — o texto está em [`05-arquitetura-3-camadas.md`](05-arquitetura-3-camadas.md#a-descrição-da-fonte-de-conhecimento)

> ⚠️ A descrição da fonte **é o que dispara a busca**. Se ela for genérica, o playbook nunca é consultado. Não pule este passo.

- [ ] `.docx` subido
- [ ] Fonte cadastrada **com a descrição colada**

### C4 · Remover os tópicos do agente (se já colou)

Copilot Studio → **Tópicos** → `cobrancagestor` e `respostadogestor` → **⋯** → Excluir.

Se ainda não colou nenhum dos dois, não há nada a fazer aqui.

- [ ] Tópicos removidos, ou nunca colados

### ✅ Terminei o Bloco C?

| # | Pergunte | Esperado |
|---|---|---|
| 1 | `analise o projeto <nome>` | Relatório com **🎯 decisão recomendada**. **Sem** seção de matemática de score |
| 2 | `quais projetos estão em risco?` | Fala de valor em risco e de há quanto tempo está parado — não "score 86 = verde" |
| 3 | *(depois de uma análise que exponha gap)* | O agente **oferece** cobrar o gestor, sem você pedir |
| 4 | Aceitar a oferta | Mostra o rascunho e **espera aprovação** antes de enviar |
| 5 | `mude o State do work item <teste> para 07 Design Build` | Mostra o de-para, espera confirmação, grava |
| 6 | `como o FinalScore é calculado?` | **Aí sim** explica a matemática — sob demanda |
| 7 | `o que é um watermelon?` | Responde direto, **sem rodar query** |

O teste 7 é o que prova que o SharePoint está sendo recuperado. Se falhar, o lugar de mexer é a **descrição da fonte de conhecimento**, não o playbook.

Os testes 4 e 5 são os que mais merecem atenção: eram garantidos por `ConditionGroup` de tópico, que *executa*, e agora dependem de instrução, que é seguida quase sempre. Se algum dia uma escrita indevida acontecer, o caminho de volta é recriar o `resposta-do-gestor` — [`topics/README.md`](../../topics/README.md).

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

# 🆕 BLOCO E — as duas tools novas (~15 min)

Detalhe e textos para colar: [`07-criar-e-remover-projeto.md`](07-criar-e-remover-projeto.md)

### E1 · `Create Project` 🔴 hoje não cria nada

Falta o `title`, que é **obrigatório** no schema do conector — é o mesmo defeito que a `Update Project` tinha.

- [ ] `title` → Dinamicamente com IA + descrição
- [ ] `description` → Dinamicamente com IA + descrição
- [ ] `userEnteredFields` (aparece como **"Other Fields"**, em Advanced) → Dinamicamente com IA + descrição
- [ ] Trocar a descrição da tool

### E2 · `Remove Project` 🔴 não faz o que o nome diz

```yaml
modelDisplayName: Remove Project
operationId: DeleteWorkItemLinkAsync    # ← apaga um LINK entre itens, não o item
```

- [ ] **Apagar a tool**
- [ ] Usar `00 Cancelled` via `Update Project` para retirar projeto do portfólio

Preserva histórico, auditoria e a série do Power BI — e não precisa de ferramenta nova. O porquê e a alternativa (se você quiser deleção real mesmo assim) estão no [`07`](07-criar-e-remover-projeto.md).

---

# 🎙️ BLOCO F — transcrições da LT no SharePoint (~15 min + ~40 min)

Guia completo, passo a passo: [`06-fluxo-transcricoes.md`](06-fluxo-transcricoes.md)

> **Dois pontos que confundem:**
>
> 1. A transcrição **não vira arquivo na pasta**. É anexo do vídeo dentro do Stream — por isso `Recordings` mostra só o `.mp4`, e clicar abre o player. É normal, não é defeito.
> 2. O fluxo atravessa **dois lugares**: a gravação está no **OneDrive** do organizador, e o texto limpo vai para o **site do CDIO LATAM**. Nos passos que leem a transcrição, o "Endereço do site" é o do **OneDrive** — que também é um site SharePoint (`<tenant>-my.sharepoint.com/personal/<upn>`).
>
> E ela **expira em 30 dias**. Copiar para o SharePoint é o que preserva o histórico das LT.

> ✅ **A rota automática foi validada no tenant em 19/08.** A chamada da API de mídia do SharePoint existe e responde — deixou de ser aposta.

**Ordem recomendada:**

### F1 · Rota A2, manual (~15 min) — rede de segurança

- [ ] Criar a pasta `Transcription LT Meetings` com as colunas `DataReuniao` e `Origem`, e a subpasta `_entrada`
- [ ] Fluxo: gatilho no `_entrada` → limpar → gravar como `LT-AAAA-MM-DD.txt`
- [ ] A cada LT: no player, **Baixar ⌄ → .vtt** e soltar no `_entrada`. Dois cliques

Com isso a LT da próxima semana já entra no SharePoint, sem depender de nada dar certo.

### F2 · Rota A, automática (~40 min) ✅ **validada**

Usa a **API de mídia do SharePoint** — não o Graph. Sem registro de aplicativo, sem consentimento de admin.

- [ ] Capturar a chamada no DevTools (F12 → `+` → **Rede** → filtro `transcripts`) e guardar **site** e **driveId**
- [ ] Testar as duas variantes: por caminho, e com `?format=text/vtt` — decidem a forma do fluxo
- [ ] Montar o fluxo: gatilho no `.mp4` → esperar → listar transcrições → baixar VTT → limpar → gravar

### F3 · Ligar no agente

- [ ] Fonte `Transcription LT Meetings` apontando para a biblioteca, **com a descrição colada**
- [ ] Testar: `o que foi decidido na LT sobre <projeto>?`

A Rota B (Graph) fica documentada para quando precisar varrer reuniões de vários organizadores — mas depende de três liberações de admin.

---

## Onde estão as outras coisas

| Quero… | Vá para |
|---|---|
| Entender **por que** está quebrado | [`01-diagnostico-aura-agent.md`](01-diagnostico-aura-agent.md) |
| O texto exato de cada correção | [`02-correcao-das-tools.md`](02-correcao-das-tools.md) |
| Entender o Teams a fundo | [`03-teams-conversa-com-gestor.md`](03-teams-conversa-com-gestor.md) |
| Decidir sobre Work IQ | [`04-work-iq.md`](04-work-iq.md) |
| Entender a **arquitetura de 3 camadas** | [`05-arquitetura-3-camadas.md`](05-arquitetura-3-camadas.md) |
| Montar o fluxo das **transcrições** | [`06-fluxo-transcricoes.md`](06-fluxo-transcricoes.md) |
| **Replicar** o fluxo para as outras áreas e contas | [`08-gerar-os-fluxos.md`](08-gerar-os-fluxos.md) |
| Ajustar **Create / Remove Project** | [`07-criar-e-remover-projeto.md`](07-criar-e-remover-projeto.md) |
| As **instruções** para colar | [`agent/instructions-standard.md`](../../agent/instructions-standard.md) |
| O **playbook** do SharePoint | [`AURA_Playbook_Analitico.md`](../../playbook/AURA_Playbook_Analitico.md) |
| Os tópicos antigos (histórico) | [`topics/README.md`](../../topics/README.md) |
| Receitas de DAX | [`dax-cookbook.md`](../../skills/portfolio-overview/references/dax-cookbook.md) |
| Nomes dos campos `Custom.*` | [`campos-devops.md`](../../skills/update-devops/references/campos-devops.md) |
