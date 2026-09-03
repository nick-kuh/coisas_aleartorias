# Power Automate — fluxo "Consumer Board Builder"

O fluxo faz: **agente (Copilot) chama → Executar Office Script (gera o board) →
Criar `consumer-martech.html` no SharePoint → Responder ao agente com o link.**

Há **dois caminhos**. O **A é o garantido** (monta pelo próprio agente, sem
importar nada). O **B** é o pacote `.zip` — mais rápido se importar, mas o import
de pacote legado é sensível e pode falhar no seu tenant.

Pré-requisito dos dois: o **Office Script `Consumer Board Builder`** já criado no
Excel (`docs/standard/10-agente-gera-board.md`, Etapas 1–2).

---

## Caminho A — montar pelo agente (garantido, ~8 cliques)

Isso cria o fluxo **já com o gatilho do Copilot certo** — sem risco de import.

1. **Copilot Studio** → seu agente → **Ferramentas (Tools)** → **+ Adicionar
   ferramenta** → **Novo** → **Fluxo (Agent flow / Criar um fluxo)**. Abre o designer
   com o gatilho **"Quando um agente chama o fluxo"** já pronto.
2. **+ Nova etapa** → **Excel Online (Business)** → **Executar script**:
   - Local / Biblioteca: onde está o `BW_MarTech_2026_Controle_Projetos.xlsx`.
   - Arquivo: o próprio `.xlsx`.
   - Script: **Consumer Board Builder**.
3. **+ Nova etapa** → **SharePoint** → **Criar arquivo**:
   - Endereço do Site: seu site.
   - Caminho da Pasta: ex. `/Documentos Compartilhados/Consumer`.
   - Nome do Arquivo: `consumer-martech.html`.
   - Conteúdo do Arquivo: **conteúdo dinâmico → `result`** (saída do Executar script).
4. *(opcional)* **+ Nova etapa** → **SharePoint** → **Criar link de compartilhamento**
   → Identificador do Arquivo: o do "Criar arquivo".
5. **+ Nova etapa** → **Responder ao agente** (a ação de resposta do Copilot):
   adicione uma saída de **texto** chamada `board_url` = o **Caminho do link** (do
   passo 4) ou o **Link para o item** (do "Criar arquivo").
6. **Salvar**. Nome: **Consumer Board Builder**.
7. Volte ao agente: a ferramenta já aparece. Cole a **descrição** (abaixo).
8. Teste: **"monta o board de Consumer"**.

**Descrição da ferramenta** (cole no campo Descrição da tool — é o que faz o agente
escolhê-la):

> Builds the OFFICIAL Consumer board (B&W Marketing Technology 2026 Agenda: hero,
> real Unilever·B&W logo, cards, BR/MX/AR farol) from the Consumer MarTech Tracker
> Excel and returns its link. Call this whenever the user asks for the Consumer
> board, dashboard, agenda or HTML. Do NOT hand-write the HTML yourself.

> Referência das 3 ações (nomes e expressões) em `flow-definition.json`.

---

## Caminho B — importar o pacote `.zip`

> **Corrigido:** o `MissingPackageManifest` acontecia porque faltava o manifesto
> interno `Microsoft.Flow/flows/manifest.json`. O pacote foi regerado com a mesma
> estrutura do gerador validado em campo deste repo (`automation/gerar-consumer-flow.py`,
> espelhando `scripts/gerar-fluxo.py`). Agora importa.


`ConsumerBoardBuilder_package.zip` — **flow.microsoft.com → Meus fluxos → Importar →
Importar Pacote (Legado)** → suba o zip → escolha as conexões **Excel Online
(Business)** e **SharePoint** → Importar → Editar → repõe workbook, script, site e
pasta (têm GUIDs do seu tenant).

**Se der `MissingPackageManifest` ou outro erro de import:** o importador legado
rejeita o zip em muitos tenants (recurso em depreciação). **Não insista** — vá pelo
**Caminho A**, que dá exatamente o mesmo fluxo e nunca falha por formato de pacote.

---

## Atualização automática (opcional)

Para o board se regerar sozinho quando o tracker muda, duplique o fluxo trocando o
gatilho por **"Quando um arquivo é modificado (SharePoint)"** apontando para o
`.xlsx`, mantendo Executar script → Criar arquivo.
