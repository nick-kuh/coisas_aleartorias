# 0. Comece aqui — o que fazer, na ordem

> ## 🟢 Status em 17/08/2026 — o agente FUNCIONA
>
> O `botContent_73` confirma: análise de portfólio rodando ponta a ponta, com o modelo escrevendo DAX sozinho (`autoFilledArguments: ["query"]`). Zero exceptions.
>
> **Blocos A (quase todo) e D: ✅ feitos.** Restam **duas entradas de tool**, ~5 minutos:
>
> | Pendência | Onde | Efeito de não ter |
> |---|---|---|
> | `userEnteredFields` | `Update Project` | Não grava nada no DevOps |
> | `body.recipient` + `body.messageBody`, e **remover** `body.bot` | `Teams — Postar mensagem` | Não envia mensagem |
>
> Detalhes: [`01-diagnostico-aura-agent.md`](01-diagnostico-aura-agent.md), seção "Estado atual". Textos para colar: [`02-correcao-das-tools.md`](02-correcao-das-tools.md), Correções 1 e 5A.

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
| **B** | Publicar no Teams + completar a tool | ~20 min | **Bloco 0 aprovado** *(opcional — ver abaixo)* |
| **C** | Migrar para a arquitetura de 3 camadas | ~20 min | Bloco A |
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

# 📢 BLOCO B — Teams 🟡 **2 itens pendentes** (~5 min)

> ✅ **Você já está no modo sem publicação** — `poster: User` e `location: Group chat` estão configurados. Não precisa publicar nada.

Faltam três ajustes na tool `Postar mensagem em um chat ou canal`:

- [ ] 🔴 **REMOVER** a entrada `body.bot` — hoje está declarada como Valor personalizado **sem valor**. Ela só existe quando `poster: Power Virtual Agents`; com `poster: User` é inerte no melhor caso, e obrigatório-vazio no pior. **É a causa provável do erro que você viu.**
- [ ] 🔴 **Adicionar** `body.recipient` → **Dinamicamente com IA** + descrição ([Correção 5A](02-correcao-das-tools.md#5a--modo-sem-publicação-recomendado-enquanto-o-publish-não-sair))
- [ ] 🔴 **Adicionar** `body.messageBody` → **Dinamicamente com IA** + descrição
- [ ] Trocar a descrição da tool (a atual, "Posta uma mensagem em um chat ou canal", é genérica e o orquestrador pode chamar sem querer)

### ✅ Terminei o Bloco B?

- [ ] `cobrar o gestor` → ID de teste → **seu próprio e-mail** → **Enviar** → a mensagem chega no seu Teams

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

## Onde estão as outras coisas

| Quero… | Vá para |
|---|---|
| Entender **por que** está quebrado | [`01-diagnostico-aura-agent.md`](01-diagnostico-aura-agent.md) |
| O texto exato de cada correção | [`02-correcao-das-tools.md`](02-correcao-das-tools.md) |
| Entender o Teams a fundo | [`03-teams-conversa-com-gestor.md`](03-teams-conversa-com-gestor.md) |
| Decidir sobre Work IQ | [`04-work-iq.md`](04-work-iq.md) |
| Entender a **arquitetura de 3 camadas** | [`05-arquitetura-3-camadas.md`](05-arquitetura-3-camadas.md) |
| As **instruções** para colar | [`agent/instructions-standard.md`](../../agent/instructions-standard.md) |
| O **playbook** do SharePoint | [`AURA_Playbook_Analitico.md`](../../playbook/AURA_Playbook_Analitico.md) |
| Os tópicos antigos (histórico) | [`topics/README.md`](../../topics/README.md) |
| Receitas de DAX | [`dax-cookbook.md`](../../skills/portfolio-overview/references/dax-cookbook.md) |
| Nomes dos campos `Custom.*` | [`campos-devops.md`](../../skills/update-devops/references/campos-devops.md) |
