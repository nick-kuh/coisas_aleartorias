# 10. O agente gera o board EXATO quando o usuário pede

Objetivo: o usuário pede "monta o board de Consumer" na conversa e recebe o
**modelo aprovado** (hero roxo, logo real Unilever·B&W, Poppins, cards, chips,
tom claro) — não uma tabela genérica.

**Por que não é o agente que desenha:** o board exige o logo real (~48 KB) e a
fonte (~43 KB) reproduzidos byte a byte. Um modelo de linguagem não faz isso — ele
improvisa. A solução é o agente **chamar uma ferramenta** (um fluxo do Power
Automate) que roda um **Office Script** determinístico e devolve o HTML/link exato.

```
Usuário: "monta o board de Consumer"
   → Agente reconhece (skill consumer-martech) e chama a TOOL "Consumer Board Builder"
      → Power Automate: Executar Office Script (lê o Tracker, gera o HTML EXATO)
      → salva consumer-martech.html no SharePoint  → devolve o link
   → Agente responde com o link do board
```

O Office Script está em `automation/consumer-board-office-script.ts` (validado: gera
os mesmos números do Painel — 103 células, 47% no prazo, 2 críticos).

---

## Etapa 1 — Hospedar o logo branco (2 min)

1. Suba **`assets/logo-bw-white.svg`** (logo em branco, para o hero roxo) numa
   biblioteca do SharePoint que o time acessa.
2. Copie a URL direta do arquivo.

## Etapa 2 — Criar o Office Script (3 min)

1. Abra o **`BW_MarTech_2026_Controle_Projetos.xlsx`** no **Excel na web**.
2. **Automatizar → Novo Script**, apague o exemplo e cole todo o conteúdo de
   `automation/consumer-board-office-script.ts`.
3. No topo do script, preencha `LOGO_URL` com a URL da Etapa 1 (entre aspas).
   Se deixar vazio, o logo cai para um lockup de texto (ainda funciona).
4. **Salvar** com o nome **`Consumer Board Builder`**.

> O script lê a aba **Tracker** e devolve o HTML como texto (valor de retorno).

## Etapa 3 — Fluxo no Power Automate (10 min)

Crie um fluxo (**flow.microsoft.com → Criar → Fluxo de nuvem instantâneo**):

1. **Gatilho:** "Executar um fluxo a partir do Copilot" (ou "Power Apps / Botão") —
   é o que permite o agente chamar. (Para atualização automática semanal, use
   também um segundo fluxo com gatilho **"Quando um arquivo é modificado (SharePoint)"**
   apontando para o `.xlsx`.)
2. **Ação — Excel Online (Business) → Executar script:**
   - Localização/Biblioteca/Arquivo: o `BW_MarTech_2026_Controle_Projetos.xlsx`.
   - Script: **Consumer Board Builder**.
   - A saída `result` é o HTML.
3. **Ação — SharePoint → Criar arquivo:**
   - Pasta: onde o board deve morar.
   - Nome: `consumer-martech.html`.
   - Conteúdo: `result` (a saída do script).
   *(Se já existir, use "Atualizar arquivo" ou substitua.)*
4. **Ação — SharePoint → Criar link de compartilhamento** (opcional) para ter uma
   URL pronta.
5. **Ação — Responder ao Copilot** (quando o gatilho é do Copilot): devolva a URL do
   arquivo/link como saída de texto `board_url`.

## Etapa 4 — Ligar o fluxo como ferramenta do agente (3 min)

1. No Copilot Studio → **Ferramentas (Tools) → Adicionar ferramenta → Fluxo** →
   escolha o fluxo **Consumer Board Builder**.
2. **Descrição da ferramenta** (é o que faz o agente escolhê-la) — cole:

   > Builds the OFFICIAL Consumer board (the approved B&W Marketing Technology 2026
   > Agenda: hero, real Unilever·B&W logo, cards, BR/MX/AR farol) from the Consumer
   > MarTech Tracker Excel and returns its link. Call this whenever the user asks for
   > the Consumer board, dashboard, agenda or HTML. Do NOT hand-write the HTML yourself.

3. Uma linha nas **instruções** (dentro do `# 0.`, trocando a parte do HTML):

   > To build the Consumer board/dashboard/HTML, call the **Consumer Board Builder**
   > flow and return its link — never hand-write that HTML yourself.

## Melhorias confirmadas em campo

Valores reais do fluxo montado pela UI (para referência):

- **Gatilho do Copilot:** `manual` / `kind: Skills`.
- **Run script:** `operationId RunScriptProd`; a saída do board vem em
  `@outputs('Run_script')?['body/result']`.
- **Create file → Nome (com data, para histórico):**
  `@concat('consumer-', formatDateTime(addHours(utcNow(),-3),'yyyy-MM-dd-HHmm'), '.html')`
  → gera `consumer-2026-09-03-2107.html` (UTC−3). **Sempre com `.html`**, senão não
  abre como página.
- **Respond to the agent:** devolva uma saída de texto `board_url` = *Link to item*
  do Create file (`@outputs('Create_file')?['body/{Link}']`), para o agente
  responder com o link.

## O fluxo não aparece na lista de ferramentas do agente?

O agente só lista, em **Ferramentas → Fluxos de trabalho**, os fluxos que estão na
**mesma solução (Solution)** dele. Na lista de fluxos, os que estão em solução têm
um **losango 💎** ao lado do nome; um fluxo criado solto em "Meus fluxos" **não
aparece** no agente — mesmo no ambiente certo e com o gatilho do Copilot.

**Correção:** make.powerapps.com → **Soluções** → abra a solução do agente →
**+ Adicionar existente → Automação → Fluxo de nuvem** → selecione o fluxo →
volte ao Copilot Studio → Ferramentas → Adicionar → Fluxos de trabalho → agora ele
aparece → **Publique** o agente. (Se pedir para converter conexões em "referências
de conexão", aceite.)

## O fluxo roda e cria o arquivo, mas o agente "não acha" o board?

O agente **não lê a pasta** do SharePoint — ele mostra o valor de `board_url` que o
**fluxo devolve**. Se a ação **"Respond to the agent" / "Return value(s) to Copilot"**
estiver com o corpo vazio (só `statusCode: 200`), `board_url` vem vazio e o agente
diz que não achou o board — mesmo com o arquivo criado.

**Correção (no fluxo):** abra o fluxo → última ação **Respond to the agent** →
**Adicionar uma saída** → **Texto** → nome **exatamente `board_url`** → valor =
uma expressão que monta a URL a partir do caminho do Create file:
`concat('https://<tenant>.sharepoint.com/sites/<Site>', replace(outputs('Create_file')?['body/Path'], ' ', '%20'))`  ← inclua o `/sites/<Site>`; o `body/Path` é relativo ao SITE. Nem toda versão do Create file traz `{Link}`.
→ Salvar. (A lista do Create file não traz "Link to item"; o campo é `body/Path`.
Se o link abrir "não encontrado", adicione **Create sharing link** (com `body/ItemId`)
e devolva o campo **"Sharing Link"** dela — é a URL clicável.) Conectar o agente à pasta é desnecessário; o link vem do fluxo.

## O agente insiste em chamar o fluxo "antigo" (não atualiza)?

Duas causas de plataforma, ambas reais:

1. **Fluxo dentro de um solution GERENCIADO (managed).** Solution managed é
   congelado/somente-leitura — editar o fluxo por fora **não gruda**, e o agente
   segue rodando a versão congelada. (No caso real, o ConsumerReport estava dentro
   do `CDIORelatorioArea` managed, ainda usando `body/{Link}` e sem o Create
   sharing link.)
2. **Snapshot do contrato da tool.** O Copilot Studio guarda as entradas/saídas do
   fluxo no momento em que a tool é adicionada; mudar o fluxo não atualiza o
   snapshot sozinho.

**Correção:**
- **Power Automate → abra o fluxo → "Salvar como"** → cópia **não-gerenciada**
  (flowId novo, editável). Ajuste as ações nela.
- **Copilot Studio → Ferramentas → REMOVA a tool do fluxo → ADICIONE o novo fluxo**
  (re-mapeia `board_url`) → **Publique**. Isso troca o flowId e o contrato.

**Permissões como o CDIO:** deixe a tool em `mode: Invoker` (padrão de agent flow) e
o fluxo usando **connection references** (Excel + SharePoint) — as mesmas do CDIO,
se quiser idêntico. Fora de um solution editável, connection reference não se
configura; por isso o fluxo precisa estar não-gerenciado.

## Procedimento LIMPO (quando o fluxo estava preso no managed)

1. **Power Automate → "Salvar como"** o fluxo → cópia não-gerenciada. Renomeie
   (`Consumer Report v2`).
2. **Religue as conexões** (Save As derruba): Run script (workbook + script),
   Create file (site + pasta + Nome dated .html + Conteúdo=result), Create sharing
   link (Id=`body/ItemId`, View, Organização), Respond (`board_url` = **Sharing Link**).
3. **Salvar → Testar (▶)**: run verde, arquivo criado, o link do Sharing Link abre
   o board.
4. **Copilot Studio → Ferramentas → Adicionar → Fluxos de trabalho** → a cópia nova
   → Descrição → confirmar saída `board_url` → **Publicar**.
5. Permissões como CDIO: tool em **Invoker** (padrão) → pede consentimento na 1ª vez.
6. **Desative** (Turn off) o fluxo antigo do managed, para não existir dois.

## Erro `sharingDisabled` no Create sharing link

`{"error":{"code":"notAllowed","innerError":{"code":"sharingDisabled"}...}` = o site
tem **compartilhamento por link desativado** (política do tenant). A ação **Create
sharing link não funciona** nesse site — **remova-a**.

**Use o link direto do arquivo** (não precisa de compartilhamento): em
**Respond to the agent → `board_url`**, expressão:
`outputs('Create_file')?['body/{Link}']`
(É o `{Link}` = "Link to item" do Create file — não aparece na lista de conteúdo
dinâmico, mas na expressão funciona. É o mesmo que o fluxo do CDIO usa.)

> Se ao abrir o link o navegador **baixar** o `.html` em vez de mostrar: é a config
> "Browser File Handling" do site (Strict). Um admin muda para Permissive, ou abra
> com `?web=1` no fim da URL.

## URL vazia e "solicitar acesso" (site privado + sharing desativado)

**URL vazia:** algumas versões do Create file **não** têm `{Link}`, e o `body/Path`
é relativo ao **site** (não ao domínio). `board_url` (expressão):
`concat('https://<tenant>.sharepoint.com/sites/<Site>', replace(outputs('Create_file')?['body/Path'], ' ', '%20'))`.
Ex.: site `ITBWLatam` + Path `/Shared Documents/CDIO LATAM/Agent Report/x.html`.

**"Solicitar acesso":** o site é grupo privado e o sharing por link está desativado
(`sharingDisabled`), então não há "público via link". Dê acesso **no local**:
- (A) SharePoint → pasta do board → **Gerenciar acesso** → adicionar o grupo do
  público (ou "Todos, exceto usuários externos") como **Pode exibir**; ou
- (B) gravar o board numa biblioteca de um site que o público **já** acessa
  (aponte o Create file para lá).

## Fazer o link BAIXAR o arquivo (em vez de abrir no SharePoint)

Acrescente `?download=1` no fim da URL: o SharePoint entrega o `.html` como
**download** e o usuário abre localmente (o board renderiza no navegador dele),
contornando o bloqueio de exibir HTML no site. No `board_url`:
`concat('https://<tenant>.sharepoint.com/sites/<Site>', replace(outputs('Create_file')?['body/Path'], ' ', '%20'), '?download=1')`
(Ainda precisa de acesso de leitura ao arquivo — ver seção de acesso acima.)

## Etapa 5 — Testar

Peça ao agente: **"monta o board de Consumer"**. Ele deve **chamar o fluxo** e
responder com o link do `consumer-martech.html` — abrindo o board no modelo exato,
com o logo real. Sem tabela genérica, sem inventar dado.

---

## Resumo

| Peça | Papel |
|---|---|
| `automation/consumer-board-office-script.ts` | Gera o HTML exato dentro do Excel (determinístico) |
| `assets/logo-bw-white.svg` | Logo branco para o hero (hospedado no SharePoint) |
| Fluxo **Consumer Board Builder** | Roda o script, salva o HTML, devolve o link |
| Ferramenta no agente | Deixa o agente disparar o fluxo quando o usuário pede |

Assim o agente é o gatilho (on-demand) **e** o resultado é sempre o nosso modelo —
os dois objetivos ao mesmo tempo. Quando o tracker muda, o board sai atualizado
(na próxima chamada, ou automático pelo fluxo de "arquivo modificado").
