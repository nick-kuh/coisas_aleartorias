# 8. Relatório automatizado por IT Area

O fluxo `GerarRelatorioArea` lê o portfólio de uma IT Area no Azure DevOps, monta uma página HTML e publica no SharePoint. Este documento faz três coisas: **audita a versão que você exportou** (`CDIORelatorioArea_1_0_0_6`), **entrega a versão corrigida** (`1.1.0.1`, em [`flows/`](../../flows/)) e explica **como tirar o relatório do modo "tópico" e deixar o agente escrever a análise**.

| | |
|---|---|
| Solução corrigida | [`flows/CDIORelatorioArea/`](../../flows/CDIORelatorioArea/) · empacote com `flows/build.sh` |
| Zip pronto | `dist/CDIORelatorioArea_1_1_0_1.zip` |
| Seção nas instruções | `§11` de [`agent/instructions-standard.md`](../../agent/instructions-standard.md) |

> ⚠️ **Nada aqui foi executado contra o seu tenant.** O JSON foi validado estruturalmente (parênteses, aspas, referências entre ações, placeholders do template), não em runtime. Os testes de aceite do final existem por isso.

---

## 1. O diagnóstico, em uma frase

O fluxo está **bem desenhado e mal blindado**: a lógica de negócio está certa, mas quatro expressões quebram no primeiro projeto sem data, dois filtros não filtram nada, e o SharePoint ainda está com placeholder. Ele provavelmente **nunca chegou a rodar até o fim** numa área real.

### Os achados

| # | Onde | O quê | Gravidade |
|---|---|---|---|
| 1 | `F_QPrio`, `F_DeployedQ`, `F_TL_Big/Reg/Sml` | `formatDateTime('')` numa iniciativa sem Go-Live **e** sem PGLS → a ação falha | 🔴 quebra o fluxo |
| 2 | `Criar_arquivo_SharePoint` | `https://SEU_TENANT.sharepoint.com/sites/SEU_SITE` — placeholder literal, e enterrado dentro da ação | 🔴 quebra o fluxo |
| 3 | WIQL | `[System.State] <> 'Closed'` — o valor real é `11 Closed`, então **nada é excluído** | 🟠 números errados |
| 4 | `Items` / `bu` | BU adivinhada por substring do título, ignorando `BG or BU Engagement` e `Specify Cross` | 🟠 números errados |
| 5 | `Details_ByBudget/ByDate` | `workitems?ids=` aceita **200 ids**; sem corte e sem guarda para lista vazia | 🟠 quebra em área grande |
| 6 | `Responder_Erro` | só cobre a falha do SharePoint — se o WIQL falhar, ninguém responde e o agente trava | 🟠 sem saída |
| 7 | `Init_Year` | `coalesce(..., '2026')` — ano fixo no código | 🟡 envelhece sozinho |
| 8 | `% On Schedule` | denominador inclui projetos **sem** Go-Live, que nunca entram no numerador | 🟡 KPI pessimista |
| 9 | Tabela BU, coluna ROI | mostra `(benefício − budget) / budget` com prefixo `€` — é razão, não dinheiro | 🟡 rótulo errado |
| 10 | `F_HP_Eligible` | `stateNum >= 6` e `<> 11` deixa `12 On Holding` entrar como "elegível a High Potential" | 🟡 |
| 11 | `S_*Cards` / `flag` | `if()` com `formatDateTime` e `Flags?[...]` no ramo falso — risco em país fora dos 5 | 🟡 |
| 12 | `bizDesc` | imprime `Business Benefit` (domínio fechado: `Compliance` \| `Value Added`) onde o layout espera uma frase | 🟡 conteúdo pobre |

### O achado 1, com detalhe — é ele que derruba o fluxo

`and()` no Power Automate **não faz curto-circuito**: ele avalia todos os argumentos antes de decidir. Então isto

```
and( or(not(empty(pgls)), not(empty(golive))),
     equals(concat('Q', ... formatDateTime(if(empty(pgls), golive, pgls),'MM') ...), Quarter_Next) )
```

não é protegido pela guarda da esquerda. Numa iniciativa em `01 Idea` — sem Go-Live e sem PGLS, o caso mais comum do portfólio — o segundo argumento chama `formatDateTime('')` e a ação **falha**.

A correção não é escrever a guarda melhor: é **tirar a data do filtro**. A `Select Items` passa a calcular, por linha, um campo `eq` com o rótulo do trimestre, usando uma **data-sentinela** (`1900-01-01`) quando não há data nenhuma:

```
edateSafe = if(empty(if(empty(pgls), golive, pgls)), '1900-01-01T00:00:00Z', if(empty(pgls), golive, pgls))
eq        = concat('Q', string(add(div(sub(int(formatDateTime(edateSafe,'MM')),1),3),1)), ' ', formatDateTime(edateSafe,'yyyy'))
```

Nenhum ramo pode lançar (só `if` e `coalesce` sobre literais), `formatDateTime` sempre recebe data válida, e `Q1 1900` nunca casa com um trimestre real. Os filtros viram comparação de string pura:

```
F_QPrio      →  @and(equals(item()?['ptype'],'Big Rock'), equals(item()?['eq'], outputs('Quarter_Next')))
F_DeployedQ  →  @and(contains(toLower(item()?['state']),'deployed'), equals(item()?['eq'], outputs('Quarter_Curr')))
F_TL_Big     →  @and(equals(item()?['ty'], outputs('Init_Year')), equals(item()?['ptype'],'Big Rock'))
```

O mesmo truque resolve o achado 11: os cartões usam `goliveSafe`, e o ramo `'TBD'` continua sendo o escolhido quando não há data.

---

## 2. O ponto principal: onde está a costura

Sua pergunta era como **parar de montar o relatório por tópico e deixar o agente analisar tudo**. Vale separar duas coisas que parecem uma só.

**O template não é o problema.** Cabeçalho, cartões de KPI, timeline, tabela de BU — isso é *cromo*: precisa ser exato, barato e nunca alucinado. O Power Automate faz isso melhor que qualquer modelo, e faz de graça.

**O problema é que a análise também está no template.** Hoje o `{{EXEC_SUMMARY}}` é um `concat` de contagens:

> *"Portfolio de Consumer em 2026: 47 iniciativas ativas — 12 Big Rock, 20 Regular e 15 Small…"*

Isso não é análise, é a legenda dos cartões que já estão logo acima. E não existe **nenhum lugar** na página onde caiba um julgamento — quais projetos concentram risco, o que a LT decidiu, o que a liderança precisa aprovar nesta semana.

### A arquitetura: uma tool, duas chamadas

Em vez de dois fluxos, o `1.1.0.1` ganha uma entrada `mode` e roda duas vezes:

```
1)  mode = data     →  fluxo devolve o portfólio inteiro da área em JSON + os KPIs que ele calculou
                       (o agente lê tudo, cruza com transcrição da LT e wiki, aplica as quatro lentes)

2)  mode = report   →  fluxo renderiza a página, injetando exec_summary e analysis_html
                       escritos pelo agente, e devolve o link do SharePoint
```

O que cada lado passa a fazer:

| | Fluxo | Agente |
|---|---|---|
| KPIs, contagens, percentuais | ✅ calcula | ❌ nunca inventa |
| Cartões, timeline, tabela de BU | ✅ renderiza | — |
| **O que o relatório diz** | ❌ | ✅ escreve |
| Quais projetos merecem destaque | ❌ | ✅ decide |
| Por que algo atrasou | ❌ (não vê a LT) | ✅ cruza a transcrição |
| Qual decisão pedir, de quem, até quando | ❌ | ✅ |

**Por que não deixar o agente cuspir o HTML inteiro?** Porque a página completa passa de 25 KB. Pedir isso a cada relatório significa (a) estourar o limite de resposta do Copilot Studio, (b) pagar token por markup que nunca muda, e (c) aceitar que um `<td>` esquecido quebre o layout — sem ninguém para conferir. A costura acima dá **a mesma liberdade editorial** com uma fração do risco: o agente escreve prosa e tabelas, o template garante que a página continua sendo a página.

Para o caso raro em que o usuário quer algo realmente fora do padrão, existe a saída de emergência `full_html`: se vier preenchido, o fluxo ignora o template e salva aquele HTML como o relatório inteiro.

### O que o `mode=data` devolve

```json
{
  "area": "Consumer", "year": "2026", "generatedAt": "...",
  "quarterCurr": "Q3 2026", "quarterNext": "Q4 2026",
  "kpis": { "total": 47, "bigRock": 12, "regular": 20, "small": 15,
            "inProgress": 31, "inProgressWithGoLive": 27, "noGoLiveDate": 4,
            "onSchedule": 17, "delayed": 10, "hasFinancials": 22, "profitable": 14,
            "hpEligible": 19, "highPotential": 8 },
  "ids": { "delayed": [...], "noGoLiveDate": [...], "highPotential": [...],
           "deployedCurrentQuarter": [...], "nextQuarterBigRocks": [...] },
  "projects": [ { "id": 1234, "title": "...", "state": "07 Design Build", "ptype": "Big Rock",
                  "itArea": "...", "bu": "...", "country": "...", "golive": "...", "pgls": "...",
                  "budget": 0, "benefit": 0, "payback": -1, "impl": -1,
                  "bizDesc": "Value Added", "manager": "...", "note": "..." } ]
}
```

Repare que `projects` **não** carrega o campo `flag` — ele é um `<img src="data:image/png;base64,…">` de 1 KB por linha, que serve ao HTML e só gastaria contexto do modelo.

> 📏 **Teto prático.** Uma IT Area de ~120 iniciativas dá algo entre 30 e 60 KB de JSON, dependendo do tamanho dos `Note`. Cabe. **O portfólio inteiro (422 iniciativas) não cabe** — se um dia quiser o consolidado LATAM, é um relatório por área e um agregador por cima, não uma chamada só.

---

## 3. O que mudou, ação por ação

| Ação | Antes | Depois |
|---|---|---|
| `Init_Year` | `coalesce(..., '2026')` | `formatDateTime(utcNow(),'yyyy')` quando vazio |
| `Init_Mode`, `Init_ExecSummary`, `Init_Analysis`, `Init_FullHtml` | — | novas entradas do gatilho |
| `WIQL_ByBudget/ByDate` | `<> 'Closed'` | `<> '11 Closed'` · área com aspas escapadas |
| `Ids_ByBudget/ByDate` | `join(select(...))` | `join(take(select(...), 200), ',')` |
| `If_Sem_Itens` | — | responde "nenhuma iniciativa" e encerra, em vez de dar 400 |
| `Items` | BU pelo título | BU por `BG or BU Engagement` + `Specify Cross` · campos `eq`, `ty`, `goliveSafe`, `tdateSafe` |
| `Items_Lean` | — | versão sem HTML, para o `mode=data` |
| `F_InProgress_Dated`, `F_NoDate` | — | separa "sem Go-Live" de "atrasado" |
| `F_OnSchedule` / `% On Schedule` | denominador `F_InProgress` | denominador `F_InProgress_Dated` · card ganha "SEM DATA" |
| `F_HP_Eligible` | `>= 6` e `<> 11` | `6 ≤ stateNum ≤ 10` (tira `12 On Holding`) |
| `F_QPrio`, `F_DeployedQ`, `F_TL_*` | `formatDateTime` no `where` | comparação de string (`eq`, `ty`) |
| `Apply_to_each_BU` | uma expressão com 8 `xpath` repetidos | `BU_Rows` → `BU_Benefit` → `BU_Budget` → `BU_Roi` |
| Coluna ROI | `€ (benefício−budget)/budget` | `2,10x`, vermelho abaixo de `1,00x`, `n/d` sem budget |
| `Html_4_Analise` | — | injeta `exec_summary` e `analysis_html` |
| `Criar_arquivo_SharePoint` | sempre `Html_Final` | `full_html` sobrepõe quando vier |
| `CONFIG_SiteUrl`, `CONFIG_Pasta` | endereço fixo dentro da ação do SharePoint | duas caixas no topo do fluxo — os únicos dois campos que você edita |
| `report_url` | `body/{Link}`, que a ação **Criar arquivo** não devolve | `CONFIG_SiteUrl` + `body/Path`, com espaços em `%20` |
| `Scope_Principal` + `Responder_Erro` | erro só no SharePoint | qualquer falha do fluxo vira resposta ao agente |
| `Responder_Dados` | — | o ramo `mode=data` |

O `Template` também mudou em dois pontos: o cartão **% On Schedule** ganhou a célula `SEM DATA`, e nasceu um `{{ANALYSIS_BLOCK}}` logo antes da tabela de BU — o quadro roxo onde a análise do agente entra. Quando `analysis_html` vem vazio, o bloco inteiro some da página.

---

## 4. Importar — passo a passo

### Passo 1 · Pegar o zip

Três caminhos; escolha um.

- **Baixar do GitHub** (mais direto se você não usa git na máquina): abra [`dist/CDIORelatorioArea_1_1_0_1.zip`](https://github.com/nick-kuh/coisas_aleartorias/blob/claude/automated-html-report-section-rbmt60/dist/CDIORelatorioArea_1_1_0_1.zip) na branch `claude/automated-html-report-section-rbmt60` e clique em **Download raw file** (o ícone ⤓ à direita). Não use "Save as" na página do GitHub — isso salva HTML, não o zip.
- **Se você já tem o repositório:** `git pull` e o arquivo está em `dist/`.
- **Regerar do JSON:** `flows/build.sh`. É o que você faz depois de qualquer edição no JSON.

> ⚠️ **Não abra e re-zipe o arquivo pelo Explorador do Windows.** O Power Automate exige `[Content_Types].xml`, `solution.xml` e `customizations.xml` **na raiz** do zip; zipar a pasta cria um nível a mais e a importação falha com "arquivo de solução inválido". Se precisar re-empacotar, use `flows/build.sh`.

### Passo 2 · Importar no Power Automate

1. [make.powerautomate.com](https://make.powerautomate.com) → confira no canto superior direito que você está no **ambiente certo** (o mesmo onde o agente vive). Este é o erro que mais custa tempo.
2. Menu esquerdo → **Soluções**.
3. Botão **Importar solução** → **Procurar** → escolha o zip → **Avançar**.
4. A tela mostra `CDIORelatorioArea`, versão `1.1.0.1`, publicador `UnileverCoPilotStudioPOC`. Como você já importou a `1.0.0.6`, ele vai dizer **"Atualizar"** — é o que você quer: mantém o mesmo fluxo, mesmo ID, e as tools que já apontam para ele continuam apontando.
5. **Conexões**: vão aparecer as duas referências — `CDIO Relatorio - Azure DevOps` e `CDIO Relatorio - SharePoint`. Escolha a conexão existente em cada dropdown. Se alguma estiver vazia, clique em **+ Nova conexão**, autentique, volte e selecione (a lista não atualiza sozinha — recarregue o dropdown).
6. **Importar**. Leva de 1 a 3 minutos.

> Se aparecer **"Uma solução gerenciada não pode ser sobrescrita"**, a `1.0.0.6` entrou como gerenciada. Aí desinstale-a primeiro (**Soluções → ... → Excluir**) e importe de novo — você perde o fluxo antigo, que é justamente o que queremos substituir.

### Como saber qual build você tem

Abra o fluxo e olhe a sequência no topo. **Entre `Init FullHtml` e `Init Now` têm que existir dois nós: `CONFIG SiteUrl` e `CONFIG Pasta`.**

- **Estão lá** → é a `1.1.0.1`. Siga para o Passo 3.
- **`Init FullHtml` emenda direto em `Init Now`** → você tem um build anterior, em que o endereço do SharePoint ficava enterrado dentro da ação `Criar arquivo SharePoint` e ainda existia uma ação `Propriedades do arquivo` pedindo o GUID da biblioteca. **Reimporte a `1.1.0.1`** em vez de consertar à mão: são três edições espalhadas, uma delas numa expressão.

### Passo 3 · Preencher os dois campos de configuração

O fluxo importado **não funciona ainda**: o endereço do SharePoint é placeholder. Abra a solução → clique no fluxo `CDIO - Gerar Relatorio por Area` → **Editar**.

As duas primeiras ações depois de `Init_FullHtml` são caixas de texto simples. Só isso:

| Ação | Valor atual | Trocar por |
|---|---|---|
| **`CONFIG_SiteUrl`** | `https://SEU_TENANT.sharepoint.com/sites/SEU_SITE` | a URL do site, **sem barra no final** — ex.: `https://unilever.sharepoint.com/sites/ITBWLatam` |
| **`CONFIG_Pasta`** | `/Documentos Compartilhados/Relatorios CDIO` | o caminho real da pasta, **começando com barra** |

Sobre a pasta: o nome depende do idioma do site. Em site em inglês é `/Shared Documents/...`; em português, `/Documentos Compartilhados/...`. Para não chutar — abra a biblioteca no navegador e olhe a URL: o trecho entre o nome do site e o resto é o que vai aqui. **A pasta precisa existir**; o fluxo não a cria.

Salve. Nenhum outro campo precisa ser tocado.

### Passo 4 · Ligar e testar sozinho, antes do agente

Ainda no fluxo: **Testar → Manualmente → Testar**, e preencha só duas coisas:

```
area = Consumer
mode = data
```

O que provar:

- terminou **verde**, sem ação vermelha no histórico;
- a saída da ação `Responder_Dados` tem `data` preenchido, com `kpis.total` batendo com o que o Power BI mostra para Consumer;
- se falhou, o histórico mostra **qual** ação e com que erro — é para isso que existe o `Scope_Principal`.

Depois repita com `mode = report`. Agora tem que aparecer um `.html` na pasta do SharePoint, e o `report_url` da resposta tem que abrir esse arquivo.

### Passo 5 · Plugar no agente

Copilot Studio → seu agente → **Ferramentas → Adicionar uma ferramenta → Fluxo** → escolha `CDIO - Gerar Relatorio por Area`.

1. Renomeie para **`Relatório da Área`** — é o nome que §11 das instruções usa.
2. Cole a descrição da tool (§6 abaixo).
3. Confira que **todas as 6 entradas** estão em **"Dinamicamente com IA"**. Entrada que não está declarada assim é entrada que o modelo não enxerga — é o defeito repetido em [`02-correcao-das-tools.md`](02-correcao-das-tools.md), e ele reaparece toda vez que uma tool é adicionada.
4. As descrições das entradas já vêm prontas do gatilho do fluxo. **Não redigite.**

---

## 5. O detalhe chato: `.html` no SharePoint costuma **baixar**, não abrir

Boa parte dos tenants roda a biblioteca em **Browser File Handling: Strict**, e nesse modo o SharePoint devolve `.html` como anexo — o usuário clica no link do relatório e ganha um download. Três saídas, em ordem de preferência:

1. **Converter para PDF.** Acrescente a ação **"Converter arquivo"** (OneDrive/SharePoint) depois do `Criar_arquivo_SharePoint`, salve o `.pdf` ao lado e devolva o link dele. O template já foi escrito para isso — tem `page-break-after` entre as partes. Custo: as bandeirinhas em `data:` URI podem não sobreviver ao conversor; teste com uma área que tenha Brasil e México.
2. **Pedir ao admin** `Browser File Handling: Permissive` na biblioteca (Configurações do site → Configurações avançadas). Resolve de vez, mas é chamado para terceiro.
3. **Mandar o HTML por e-mail/Teams** em vez de link. Funciona, mas perde a página como artefato durável — e o Outlook ignora metade do CSS.

Enquanto isso não estiver decidido, o `report_url` é um link de download. Vale o agente avisar.

> 📎 O `report_url` é montado como `CONFIG_SiteUrl` + o `Path` que o SharePoint devolve, com espaços em `%20`. A ação **Criar arquivo** **não** devolve `{Link}` — quem devolve é **Obter propriedades do arquivo**, que exige o GUID da biblioteca e o `ItemId`. Montar a URL custa uma expressão e não custa nem uma ação nem um placeholder a mais.

---

## 6. A tool no agente

**Ferramentas → Adicionar → Fluxo → `CDIO - Gerar Relatorio por Area`.** Renomeie para **`Relatório da Área`** — é o nome que §11 das instruções usa.

Descrição da tool:

```
Gera o Relatorio Executivo do CDIO IT Portfolio LATAM para uma IT Area. Chame duas vezes: primeiro com mode=data para receber o portfolio da area em JSON e analisar, depois com mode=report passando o resumo executivo e a analise que voce escreveu, para publicar a pagina e receber o link.
```

As seis entradas vêm prontas do gatilho do fluxo — **não precisa redigitar nenhuma descrição**. Confira só que todas estão marcadas **"Dinamicamente com IA"**, que é o defeito repetido em [`02-correcao-das-tools.md`](02-correcao-das-tools.md): entrada não declarada é entrada que o modelo não enxerga.

As três que fazem o trabalho pesado, para referência e revisão:

**Descrição da entrada `mode`:**  `285/1024`

```
Como chamar o fluxo. "data" devolve o portfolio inteiro da IT Area em JSON, sem gerar arquivo nenhum - e o que voce usa para analisar. "report" publica o relatorio em HTML no SharePoint e devolve o link. Padrao: report. SEMPRE chame "data" primeiro, analise, e so entao chame "report".
```

**Descrição da entrada `exec_summary`:**  `309/1024`

```
So em mode=report. Seu resumo executivo em pt-BR, 3 a 5 frases, no topo da pagina: dinheiro em jogo, risco concentrado, decisao pedida - nessa ordem. Texto corrido; so <strong> e <em> sao aceitos. Cite projetos como Nome (1234). Se vier vazio, o fluxo escreve um resumo generico so com contagens - evite isso.
```

**Descrição da entrada `analysis_html`** — é este texto que segura o desenho da página:  `869/1024`

```
So em mode=report. Sua analise, em HTML, inserida como secao propria do relatorio. VOCE escolhe as sub-secoes: nada e obrigatorio, nada e proibido.
FRAGMENTO apenas: sem <html>, <head>, <body>, <style>, <script>, class= ou id=. Use <p>, <div>, <table>, <tr>, <td>, <ul>, <li>, <strong>, <em>, <a>, com style= inline em cada tag.
ESTILO: font-family:'Segoe UI',sans-serif. Texto #1e293b, secundario #64748b, borda #e2e8f0, fundo suave #f8fafc. Destaques: #a855f7 decisao, #06b6d4 secao, #ef4444 risco, #10b981 ganho, #f59e0b atencao. Titulo de bloco 14px/800, corpo 12px/1.5, nota 10px. Tabela com border-collapse:collapse e padding:6px 10px.
PROJETO: sempre Nome (1234) com link para https://dev.azure.com/CDIO-IT-LATAM/CDIO%20Portfolio/_workitems/edit/1234. Dinheiro como €1,4M.
PROIBIDO: <img>, base64, URL externa, e qualquer numero que nao tenha vindo do mode=data.
```

---

## 7. A seção nas instruções — e o que ela custou

`§11` entrou em [`agent/instructions-standard.md`](../../agent/instructions-standard.md):

```
# 11. THE AREA REPORT
The report tool (§2) runs **twice**. `mode=data` returns the whole IT Area (exact
string, §3) as JSON: read it all, cross with §10 and the wiki, run the four lenses.
Then `mode=report` publishes the page with the `exec_summary` and `analysis_html`
**you** wrote — you choose what it says; their input descriptions carry the HTML
contract. Return the `report_url` with three lines on what it concludes; offer §7
per gap. Interpret the page's KPIs, never repeat them.
```

> 🔴 **As instruções estão no teto.** O campo aceita **8.000 caracteres**, e cada menção a uma tool vira uma referência `{{System.Bot.Components.Actions...}}` que infla o texto em ~92 caracteres. Com §11 e a nona menção de tool, o arquivo fica em **7.156 chars → ~7.984 no agente: 16 de folga.**
>
> Para caber, §11 ficou com **um** parágrafo e o contrato de HTML foi para a descrição de entrada da tool — que é exatamente onde ele rende mais, porque o modelo o lê no momento de preencher o campo. Isso é a mesma tese de [`05-arquitetura-3-camadas.md`](05-arquitetura-3-camadas.md).
>
### O que foi cortado para caber

Nada de regra saiu, mas duas frases foram embora e vale saber:

| Onde | Saiu | Por quê é aceitável |
|---|---|---|
| §10, última linha | *"Offer the user a Teams recap of what is pending, with links."* | 🟠 **é a única perda real de comportamento** — o agente deixa de oferecer o resumo por Teams no fim de uma reconciliação. §7 continua cobrindo a cobrança projeto a projeto. Se fizer falta, é o primeiro candidato a voltar |
| §9 | *"Everywhere: dashboards, deep dives, Teams drafts, confirmations"* → *"Everywhere"* | a regra é a mesma; a enumeração era ênfase |
| §4, §5, §7, §8 | reescritas mais curtas | mesma regra, menos palavras |

> **A próxima seção não cabe sem cortar outra.** `python3 scripts/validate-topics.py` mede antes de você colar; o produto trunca em silêncio, e o corte come o fim do texto.

---

## 8. Testes de aceite

| # | O que fazer | O que provar |
|---|---|---|
| 1 | Testar manualmente: `area = Consumer`, `mode = data` | responde JSON; `kpis.total` bate com o Power BI; `noGoLiveDate > 0` numa área com projetos em `01 Idea` |
| 2 | Mesma coisa com `area = Tax Reform` (área pequena) ou uma área inexistente | resposta "nenhuma iniciativa ativa", sem erro vermelho no histórico |
| 3 | `mode = report`, sem `exec_summary` nem `analysis_html` | página sai completa, com o resumo genérico e **sem** o quadro roxo |
| 4 | `mode = report` com `analysis_html = <p style="font-size:12px;">teste</p>` | quadro roxo "AURA — Análise e Decisões" aparece antes da tabela de BU |
| 5 | No agente: *"faz o relatório de Consumer"* | ele chama `data`, **depois** `report`, e devolve o link — não pula direto para `report` |
| 6 | Ler a página gerada | nenhum número no texto do agente que não esteja no JSON do passo 1 |
| 7 | Conferir a coluna ROI da tabela de BU | mostra `2,10x`, não `€ 2,10`; vermelho abaixo de `1,00x` |
| 8 | Abrir o `report_url` num navegador anônimo | ou abre a página, ou baixa — e aí você já sabe qual das três saídas da §5 vai precisar |

O teste 5 é o que separa esta arquitetura da anterior. Se o agente chamar direto `mode=report`, a página sai com o resumo genérico — tecnicamente um sucesso, e exatamente o relatório que você não quer.
