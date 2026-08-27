# 8. Relatório automatizado por IT Area

Dois fluxos do Power Automate e duas tools no agente. O primeiro devolve o portfólio de uma IT Area em JSON; o agente analisa; o segundo publica a página HTML no SharePoint com o texto que **o agente** escreveu. O relatório inteiro sai em **inglês**.

| | |
|---|---|
| Solução | [`flows/CDIORelatorioArea/`](../../flows/CDIORelatorioArea/) · empacote com `flows/build.sh` |
| Zip pronto | `dist/CDIORelatorioArea_1_4_1_0.zip` |
| Seção nas instruções | `§11` de [`agent/instructions-standard.md`](../../agent/instructions-standard.md) |

> ⚠️ **Nada aqui foi executado contra o tenant.** `scripts/validate-flows.py` valida os dois JSON — aninhamento de `InitializeVariable`, `Response` dentro de laço, parênteses e aspas, referências entre ações, placeholders do template e o limite de 1.024 por descrição de entrada. Estrutura, não runtime; os testes de aceite do final existem por isso.

---

## 1. Por que a versão de uma tool só travava

Na primeira tentativa isto era **um** fluxo com uma entrada `mode`. O agente chamava, e em vez de rodar, perguntava ao usuário:

> *"Por favor, forneça o resumo executivo em português, contendo de 3 a 5 frases…"*

O transcript mostra o mecanismo exato. O plano foi montado certo — o `thought` registrado era *"Primeiro puxo o portfolio completo da área para analisar"* — e o binding preencheu três entradas sozinho:

```json
arguments: { "area": "Customer Dev", "mode": "data", "year": "2026" }
autoFilledArguments: ["area", "mode", "year"]
```

Mas a definição da tool que o orquestrador recebe traz, **nas seis entradas**:

```
exec_summary   isRequired=false   isAutomatic=true   shouldPromptUser=true
```

E o Copilot Studio resolve **todas** as entradas da tool antes de executar — não só as que importam para aquela chamada. Na quarta, a descrição que eu tinha escrito dizia *"Só em mode=report"*, e ele estava chamando com `mode=data`. Ele concluiu, corretamente, que não tinha valor para pôr ali. **`shouldPromptUser` transforma "não tenho valor" em "pergunta ao humano".** Não existe evento `StepFinished` depois: o fluxo nunca rodou.

Repare que o mesmo mecanismo foi ótimo no `area` — a resposta com a tabela das sete IT Areas, quando o pedido veio sem área, nasceu daí. **Perguntar a área é certo; perguntar o resumo é fatal.**

O erro de projeto foi meu: eu assumi que entrada opcional vazia simplesmente não seria enviada.

### O que a correção muda

Dois fluxos, cada um com o seu conjunto de entradas:

| Fluxo | Entradas | Faz |
|---|---|---|
| **`PortfolioDataArea`** | `scope_label`, `wiql_filter`, `year` | consulta o DevOps e devolve JSON. Nenhum campo de texto livre para perguntar |
| **`PublishAreaReport`** | `scope_label`, `wiql_filter`, `year`, `report_html` | consulta, renderiza o HTML, publica no SharePoint, devolve o link |

Na primeira não sobra nada para o binder perguntar. Na segunda, a descrição de cada entrada agora **manda escrever** em vez de dizer "só no modo X" — e abre com `YOU write this - never ask the user for it`. Era a descrição que dizia ao modelo para deixar o campo vazio; era ela que precisava mudar.

`mode` e `full_html` deixaram de existir. Um escape hatch que custa uma pergunta em toda chamada não paga o que entrega.

> 💡 **Se ainda assim ele perguntar:** abra a tool no Copilot Studio, clique em `report_html` e procure um controle do tipo *"perguntar ao usuário quando o valor não for encontrado"*. No YAML exportado as entradas são `AutomaticTaskInput` idênticas, sem nada que as distinga — então ou esse controle só vive na UI, ou `shouldPromptUser: true` é o padrão do produto. Desmarcar, se existir, é o reforço.

---

## 2. Onde está a costura

O template **não** é o problema. Cabeçalho, cartões de KPI, timeline, tabela de BU são cromo: precisam ser exatos e baratos, e o Power Automate faz isso melhor que qualquer modelo.

O problema era que a análise também estava no template. O `{{EXEC_SUMMARY}}` era um `concat` de contagens — a legenda dos cartões que já estão logo acima — e não havia lugar nenhum na página para um julgamento.

| | Fluxo | Agente |
|---|---|---|
| KPIs, contagens, percentuais | ✅ calcula | ❌ nunca inventa |
| Cartões, timeline, tabela de BU | ✅ renderiza | — |
| **O que o relatório diz** | ❌ | ✅ escreve |
| Quais projetos merecem destaque | ❌ | ✅ decide |
| Por que algo atrasou | ❌ (não vê a LT) | ✅ cruza a transcrição |
| Qual decisão pedir, de quem, até quando | ❌ | ✅ |

**Por que não pedir o HTML inteiro ao modelo.** A página passa de 25 KB. Seria estourar o limite de resposta do Copilot Studio, pagar token por markup que nunca muda, e aceitar que um `<td>` esquecido quebre o layout sem ninguém para conferir. A costura dá a mesma liberdade editorial com uma fração do risco.

### O que o `PortfolioDataArea` devolve

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

`projects` não carrega o campo `flag` — ele é um `<img src="data:image/png;base64,…">` de 1 KB por linha, que serve ao HTML e só gastaria contexto do modelo.

> 📏 **Teto prático.** Uma IT Area de ~120 iniciativas dá entre 30 e 60 KB de JSON, dependendo do tamanho dos `Note`. Cabe. **O portfólio inteiro (423 iniciativas) não cabe** — o consolidado LATAM é um relatório por área mais um agregador por cima, não uma chamada só.

---

## 3. O caso que prova a arquitetura

O relatório `Relatorio_LATAM_Customer_Dev_4_1.html`, gerado antes desta mudança, tem um Executive Summary bem escrito. Compare com os próprios cartões da mesma página:

| O resumo diz | A página mostra |
|---|---|
| "thirteen initiatives in flight" | **3 Projects** |
| "benefit pool above €150M" | Benefit **0,000 Mi** nas duas linhas da tabela de BU |
| "the majority already in Deployed state" | **"No Deployed Projects."** |
| TPM Brazil, NRM BPC, EDDGIE Brazil, TPM Stabilization | os três cards são NRM Lever 3 PC (1221), Hermes AI (1222), EDDGIE Horizon 2 (1229) |

O resumo fala do portfólio de um gestor; os dados são de três projetos filtrados por área e ano. Nenhum projeto citado no resumo traz o work item ID, que o §9 exige.

É uma melancia de relatório: verde por fora, vazio por dentro. Um executivo lê o parágrafo e guarda "€150M e 13 iniciativas" — número que não existe na página nem no DevOps. **É exatamente o que a passada de dados impede:** o resumo agora tem que sair do JSON daquela execução, e a descrição da entrada diz isso com todas as letras.

O cromo daquele arquivo, esse sim, era melhor — e foi portado: o botão **AURA** com o deep link do agente e o logo embutido (no template antigo ele apontava para a home genérica do Copilot Studio), o balão `i` de tooltip no título da timeline, os ícones 🪨 ⚙️ 🔹 com o rótulo ao lado, e a sombra no cartão de atrasado.

---

## 4. O relatório em inglês

O cromo do template sempre foi inglês — *Monthly Automation Report*, *KPI Snapshot*, *Main Priorities*. O resumo saía em português por causa do §1, que manda responder sempre em pt-BR. Duas regras se contradizendo é o modelo escolhendo sozinho a cada execução.

Agora está resolvido nos dois lados:

- `§11` abre a exceção explícita: *"the report is the one place §1 does not apply"*.
- A descrição de `report_html` pede **ENGLISH** em maiúsculas.
- O que ainda estava em português dentro do fluxo virou inglês: `Atraso Justificado` → **Delay Justification**, o texto de quando não há justificativa, o resumo automático de reserva, `Não informado` → **Not informed**, a mensagem de área vazia, o nome do arquivo (`..._CDIO_Report_Consumer.html`), e os números da tabela de BU passaram de `pt-BR` para `en-US`.

**A conversa com o agente continua em português.** Só o documento é inglês.

---

## 5. Importar

### Passo 1 · Pegar o zip

- **Baixar do GitHub:** abra [`dist/CDIORelatorioArea_1_4_1_0.zip`](https://github.com/nick-kuh/coisas_aleartorias/blob/claude/automated-html-report-section-rbmt60/dist/CDIORelatorioArea_1_4_1_0.zip) e clique em **Download raw file** (ícone ⤓ à direita). "Salvar como" na página salva HTML, não o zip.
- **Ou regerar:** `flows/build.sh`.

> ⚠️ **Não reempacote pelo Explorador do Windows.** O Power Automate exige `[Content_Types].xml`, `solution.xml` e `customizations.xml` **na raiz**; zipar a pasta cria um nível a mais e a importação recusa.

### Passo 2 · Importar

1. [make.powerautomate.com](https://make.powerautomate.com) → confira o **ambiente** no canto superior direito. É o mesmo do agente. Este é o erro que mais custa tempo.
2. **Soluções → Importar solução → Procurar** → o zip → **Avançar**.
3. A tela mostra `CDIORelatorioArea` versão `1.4.1.0`. Como a `1.1.x` já está lá, ele diz **Atualizar**.
4. Mapeie as duas conexões: `CDIO Relatorio - Azure DevOps` e `CDIO Relatorio - SharePoint`.
5. **Importar.** Agora a solução tem **dois** fluxos.

> A `1.1.x` tinha um fluxo só, chamado `GerarRelatorioArea`. Ele é substituído por `PublishAreaReport` — mesmo GUID, então a tool que já apontava para ele continua apontando. `PortfolioDataArea` é novo.

### Passo 3 · Conferir o SharePoint (só no `PublishAreaReport`)

As duas caixas depois de `Init Analysis` **já vêm com os valores reais** desde a `1.2.0.1`:

| Ação | Valor |
|---|---|
| **`CONFIG SiteUrl`** | `https://unilever.sharepoint.com/sites/ITBWLatam` |
| **`CONFIG Folder`** | `/Shared Documents/CDIO LATAM/Agent Report` |

Só confira. `CDIO LATAM` é maiúsculo, e o caminho da pasta vai **sem** `/sites/ITBWLatam`, que já está no `SiteUrl`. Se um dia o site mudar, é aqui — e só aqui.

O `PortfolioDataArea` não toca no SharePoint: nada para configurar nele.

### Passo 4 · Ligar os dois

> 🔴 **Ativar é onde o fluxo inválido aparece.** O Power Automate aceita salvar e importar um fluxo que ele depois recusa executar — a validação só roda no **Ativar**, e a mensagem vem crua:
>
> ```
> Turn on failed. ... 'InvalidVariableInitialization' ... The variable action
> 'Var_BU_Rows' of type 'InitializeVariable' cannot be nested in an action of
> type 'Scope_Main'.
> ```
>
> Esse era real e foi corrigido na `1.2.0.1`: **`InitializeVariable` só existe na raiz do fluxo** — nunca dentro de Scope, Condition ou Foreach.
>
> E logo atrás dele veio o segundo, só no fluxo de dados:
>
> ```
> Turn on failed. ... 'InvalidTemplate' ... The workflow parameters
> '$authentication' are not valid; they are not declared in the definition ...
> The only declared parameters for this definition are '$connections'.
> ```
>
> Um gatilho `kind: Skills` roda com **dois** parâmetros injetados pelo runtime, `$connections` e `$authentication`, e a definição precisa declarar os dois. O gerador tinha reescrito o bloco `parameters` desse fluxo deixando só `$connections`. Corrigido na `1.2.0.2`.
>
> As duas checagens entraram no `scripts/validate-flows.py`, junto com `Response` dentro de laço, que tem a mesma natureza. **Rode antes de empacotar** — as três só apareceriam no `Ativar`.

> 🔴 **E depois de ativar veio o terceiro, que nem o `Ativar` pega.** Os dois fluxos rodaram e falharam dentro do `Scope_Main`, em ~4s, devolvendo ao agente o texto do `Respond_Error`.
>
> A causa está no `Custom.ProjectITManager`. Neste projeto ele volta como **string** — `"Deffendi, Vinicius <Vinicius.Deffendi@unilever.com>"` — e não como objeto de identidade. O `Select Items` fazia `?['displayName']` em cima disso, e seleção de propriedade sobre string **lança** em runtime.
>
> Um campo de identidade do DevOps volta em uma das duas formas conforme a API e a projeção usadas, então a correção da `1.2.0.3` normaliza as duas sem `?[...]`:
>
> ```
> if(contains(RAW, 'displayName'),
>    trim(first(split(last(split(RAW, '"displayName":"')), '"'))),
>    trim(first(split(RAW, '<'))))
> ```
>
> No mesmo passe caiu o `stateNum`, que fazia `substring(state, 0, 1)` protegido por um `length > 2` à esquerda de um `and()` — e `and()` não faz curto-circuito. Agora o texto é preenchido com `'xx'` antes do `substring`, e o `if` escolhe entre **dois literais** dentro do `int()`, de modo que nenhum ramo pode lançar.
>
> `validate-flows.py` passou a recusar qualquer `?['fields']?['X']?['y']`.

> 🔴 **E o quarto, que é a raiz de tudo.** Com a `1.2.0.3` no ar, o histórico finalmente mostrou a ação vermelha:
>
> ```
> InvalidTemplate. Unable to process template language expressions in action
> 'Ids_ByBudget': 'The template function 'select' is not defined or not valid.'
> ```
>
> **`select()` e `filter()` não são funções de expressão no Power Automate.** São **ações** — `Select` e `Filter array`. Escrever `select(...)` dentro de um `@{}` importa, salva e ativa sem uma palavra, e só quebra ao rodar.
>
> Esse trecho veio do fluxo original, não foi coisa que eu inventei — o que também responde uma pergunta que ficou aberta a sessão inteira: **o fluxo `1.0.0.6` nunca funcionou ponta a ponta.** O `Ids_ByBudget` dele tinha exatamente a mesma expressão, e é a terceira ação de todas.
>
> Na `1.2.0.4` cada uso virou ação de verdade: dois `Select` para as listas de IDs, cinco para os conjuntos do payload, um para as BUs, e dentro do laço de BU um `Filter array` mais dois `Select`. O fluxo de dados foi de 32 para 38 ações e o de publicação de 65 para 70 — todas do tipo que o produto reconhece.
>
> `validate-flows.py` ganhou a checagem que teria pego isso no primeiro dia: **toda função citada numa expressão é conferida contra a lista da Workflow Definition Language**, ignorando o que está dentro de aspas (senão `rgba(...)` de um estilo CSS viraria falso positivo). Uma fixture reintroduz os quatro erros desta sessão e ele pega os quatro.

> 🔴 **O quinto, e o último da série.** Com o `select()` resolvido, o fluxo de dados passou a funcionar — devolveu `total: 11, bigRock: 6, regular: 4, small: 1` para Customer Dev 2026. O de publicação foi mais longe e parou no laço de BU:
>
> ```
> InvalidTemplate ... action 'BU_Benefit' ... The template language function 'xml'
> parameter is not valid. The provided value cannot be converted to XML:
> 'This document already has a 'DocumentElement' node.'
> ```
>
> O truque de somar um array em Power Automate passa por `xpath(xml(json(...)))`, e o array **precisa estar embrulhado num objeto**. Com `{"v":[1,2,3]}` o `xml()` gera três elementos na raiz e recusa o documento. A forma canônica é:
>
> ```
> xpath(xml(json(concat('{"root":{"v":', string(array), '}}'))), 'sum(/root/v)')
> ```
>
> Repare no `{"root":{...}}` e no `'}}'` fechando os dois. Também veio do fluxo original, e é a razão de a tabela de BU nunca ter saído. Corrigido na `1.2.0.5`, com a checagem correspondente no validador.

### Duas entradas de texto livre eram uma a mais

Com os cinco erros de expressão fora do caminho, o agente voltou a travar — desta vez pedindo:

> *"Por favor, forneça a análise em HTML para o relatório executivo."*

O plano estava certo e o `Read Area Portfolio` tinha devolvido as 11 iniciativas. O que o binding mostra é o problema:

```
autoFilled: ['area', 'exec_summary']
exec_summary  (5956 chars)
analysis_html  —
```

O modelo escreveu **tudo** dentro do `exec_summary` — 5.956 caracteres, onde a descrição pedia 3 a 5 frases — e chegou no `analysis_html` sem nada para pôr. Entrada de texto livre que fica vazia vira pergunta ao usuário, e a gente já tinha visto esse filme na §1.

Duas entradas longas obrigam o modelo a **repartir** o que escreveu, e ele reparte quando quer. Na `1.3.0.0` existe **uma só**: `report_html`, com todo o texto do relatório, caindo na caixa do topo — que virou `Executive Summary & Analysis`, branca e mais larga, e recebe blocos (`<div>`, `<table>`) em vez de um `<p>` que o navegador fecharia sozinho no primeiro `<div>`. O quadro roxo separado saiu.

Ela é **opcional**: se vier vazia, a página sai com a contagem automática e uma linha em âmbar dizendo que ninguém escreveu a análise. Relatório degradado e visivelmente degradado é melhor que conversa travada.

### `round()` também não existe

Passado o laço de BU, o `Html_1_KPIs` parou com a mesma família de erro:

```
InvalidTemplate ... action 'Html_1_KPIs' ... The template function 'round'
is not defined or not valid.
```

A Workflow Definition Language tem `add`, `sub`, `mul`, `div`, `mod`, `min`, `max`, `rand` e `range` — e **não tem `round`**. Arredondar para inteiro é `formatNumber(x, 'F0')`, que já devolve string, então o `string()` em volta também sai:

```
string(round(div(mul(a,100), b)))     →     formatNumber(div(mul(a,100), b), 'F0')
```

Três lugares: as duas percentagens do `Html_1_KPIs`, as três da timeline e o `summary` da resposta. Corrigido na `1.3.0.1`.

Pior: eu tinha **adicionado `round` à whitelist do validador** um turno antes, quando ele acusou a função e eu presumi falso positivo. O validador estava certo e eu o ensinei errado.

### As 47 funções, auditadas de uma vez

Depois desse, parei de corrigir uma por vez e listei **todas as funções usadas nos dois fluxos**: 47 distintas. Só `round` era inválida; as outras 46 são reais. A lista, para referência:

```
add and base64 base64ToBinary body coalesce concat contains div empty equals
first float formatDateTime formatNumber greater greaterOrEquals if int item
items join json last length less lessOrEquals mul not or outputs replace
split string sub substring take toLower triggerBody trim union utcNow
variables workflow xml xpath
```

Esse levantamento é reprodutível — é o mesmo caminho que o `validate-flows.py` percorre, e vale repetir a cada mudança grande.

### 1.4.0.0 — o filtro deixa de ser só IT Area

O primeiro relatório publicado revelou o limite do desenho. O pedido era *"somente os projetos de Amanda Papucci de Make"*; o agente **achou** os 80 projetos dela via DAX no Power BI, escreveu a análise sobre eles — e na hora de publicar só conseguiu passar `area: 'Make (Business Operation)'`. A página saiu com as 63 iniciativas da área inteira. A tool não tinha vocabulário para dizer "gerente".

Trocamos a entrada `area` por três:

| Entrada | Para quê |
|---|---|
| `wiql_filter` | as cláusulas `AND` que **o agente escreve** — área, gerente, país, tipo, orçamento, ou nada |
| `scope_label` | o rótulo que vai no cabeçalho e no nome do arquivo |
| `year` | 4 dígitos, vazio = ano corrente, `all` = sem filtro de ano |

É o mesmo padrão que já funciona no `Power BI Portfolio Database`: a descrição da entrada carrega o dicionário de campos e o modelo escreve a consulta. O que o fluxo continua garantindo sozinho é o team project e a exclusão de `00 Cancelled` e `11 Closed`.

Três exemplos do WIQL que sai:

```sql
-- scope_label: "Customer Dev"        wiql_filter: AND [Custom.ITArea] = 'Customer Dev'
... AND [Custom.PortfolioYear] = 2026 AND [Custom.ITArea] = 'Customer Dev'

-- scope_label: "Amanda Papucci"      wiql_filter: AND [Custom.ProjectITManager] CONTAINS 'Papucci'
... AND [Custom.PortfolioYear] = 2026 AND [Custom.ProjectITManager] CONTAINS 'Papucci'

-- scope_label: "Whole portfolio"     wiql_filter: (vazio)      year: all
... AND [System.State] <> '00 Cancelled' AND [System.State] <> '11 Closed'
```

**O risco novo é a divergência entre as duas chamadas.** Se o agente analisar um recorte e publicar outro, a página fica coerente por dentro e mentirosa por fora. Três defesas: a descrição manda passar a string **idêntica** nas duas; o `§11` repete (*"the same three, verbatim"*); e o `summary` da chamada de dados devolve literalmente *"Pass the SAME scope_label, wiql_filter and year to Publish Area Report"*, para o agente copiar em vez de reescrever.

O `{{AREA}}` do template virou `{{SCOPE}}`, e o nome do arquivo sai do rótulo com parênteses, barras e vírgulas removidos — o primeiro relatório gerou `..._Make_(Business_Operation).html`, com parênteses na URL.

**Descrição da entrada `wiql_filter`** — é este texto que ensina o agente a escrever WIQL:  `936/1024`

```
Extra WIQL WHERE clauses, each starting with AND. Leave empty for the whole portfolio.
Already applied by the flow: the team project, State <> '00 Cancelled', State <> '11 Closed', and the year.
FIELDS: [Custom.ITArea] [Custom.ProjectITManager] [Custom.CountryDeployed] [Custom.ProjectType] [Custom.BGorBUEngagement] [Custom.SpecifyCross] [Custom.BusinessBenefit] [Custom.ProjectTotalBudget] [Custom.ProjectBenefitValue] [Custom.GoLiveDate] [Custom.PGLSEndDate] [System.State] [System.AssignedTo] [System.Title]
OPERATORS: = <> > < >= <= CONTAINS IN. Strings in single quotes, numbers and dates bare.
EXAMPLES:
AND [Custom.ITArea] = 'Customer Dev'
AND [Custom.ProjectITManager] CONTAINS 'Papucci'
AND [Custom.ITArea] = 'Make (Business Operation)' AND [Custom.CountryDeployed] CONTAINS 'Brazil'
AND [Custom.ProjectType] = 'Big Rock' AND [Custom.ProjectTotalBudget] > 100000
Never invent a field. Pass the EXACT same string to both tools.
```

**Descrição da entrada `scope_label`:**  `344/1024`

```
Short English label for the report header and the file name, describing what you filtered. Examples: "Customer Dev", "Make (Business Operation) - Brazil", "Amanda Papucci - all areas", "Big Rocks above EUR 100k", "Whole portfolio". Under 60 characters. It must describe the same set the wiql_filter selects, and be identical in both tool calls.
```

### 1.4.1.0 — opcional demais é tão ruim quanto obrigatório demais

A `1.4.0.0` marcou todas as entradas como opcionais, para nunca mais travar pedindo texto ao usuário. O resultado foi o oposto do esperado:

```
41 TRIG CDIO-PortfolioDatabyArea
42 BIND {}
46 TRIG CDIO-PublishAreaReport
47 BIND {}
```

**Zero argumentos nas duas chamadas.** Os defaults entraram, e o relatório saiu como `Whole portfolio, year 2026: 139 iniciativas`, com onze gerentes e várias áreas — quando o pedido era a carteira de uma gestora só.

Entre o binder **perguntar** e o binder **calar e reportar o escopo errado**, perguntar é infinitamente melhor: a pergunta é visível e recuperável, o escopo errado é uma página que parece certa e mente. Então `scope_label`, `wiql_filter` e `report_html` voltaram a ser **obrigatórios**; só `year` continua opcional, porque tem default honesto.

A descrição do `wiql_filter` passou a abrir com o aviso — *"NEVER omit this — an empty value silently reports the whole portfolio"* — e a dar o valor literal para quando o portfólio inteiro **é** a intenção: `AND [System.Id] > 0`. Assim "sem filtro" deixa de ser indistinguível de "esqueci o filtro".

### O code interpreter competindo com o fluxo

No mesmo teste, o pedido *"consegue criar em html por favor"* levou o orquestrador para outro lugar:

```
29 TRIG P:CodeTool
30 BIND {'input': 'Create a standalone, self-contained HTML executive report file named "Relatorio_Amanda_Papucci.html"...'}
```

Ele escreveu uma página inteira do zero, com `<style>`, classes e layout próprios — bonita, e **com os dados corretos**: conferi os 17 projetos citados contra as 77 linhas que o DAX devolveu, e todos são da Amanda. Mas não é o template, não passa pelo fluxo, não tem KPI calculado nem timeline, e não vai para o SharePoint.

O `codeInterpreter` está ligado no agente e responde bem a "gere um html". Duas defesas: o `§11` ganhou **"Never build the page yourself — no code interpreter, no hand-written HTML"**, e a descrição da tool de publicação passou a dizer que ela **é dona** da página. Se ainda assim ele desviar, o desligamento do code interpreter (Configurações → IA generativa) é a opção definitiva — ao custo de perder a análise ad-hoc que ele faz bem.

---

### E o último: um `replace()` manco

```
The template language function 'replace' expects three string parameters ...
The function was invoked with '1' parameter(s).
```

Esse não veio do fluxo original: **foi dano de cirurgia minha**. Para tirar a camada do `{{EXEC_SUMMARY}}` do `Html_Final`, um regex removeu `, alvo, valor)` e pôs `)` no lugar. Remover uma camada de `replace()` exige tirar **duas** coisas — o `replace(` da frente e todo o `, alvo, valor)` de trás, parêntese incluído. Eu tirei uma e meia.

O detalhe cruel: **os parênteses continuavam balanceados**. A checagem de balanceamento passava, o fluxo importava, salvava e ativava, e a expressão era `replace(x)`.

Por isso o validador ganhou a checagem 12: **aridade**. Ele conta os argumentos de cada chamada, respeitando aspas e aninhamento, e confere contra a tabela das funções de contrato fixo — `replace` são 3, `if` são 3, `split` são 2, `substring` são 2 ou 3, `concat` é 1 ou mais. Editar expressão longa à mão é exatamente onde se perde um argumento sem perceber.

> 🔴 **Solução importada chega com os fluxos DESLIGADOS.** É o passo que mais se pula, e o sintoma não parece com a causa: na lista, o ícone do fluxo ganha um pequeno **⃠** no canto — parece um fluxo "oculto" ou sem permissão, e é só desativado. O agente, ao chamar, devolve:
>
> ```
> Mensagem de Erro: O fluxo com a ID c8f5d2e1-... está desabilitado.
> Código do Erro: FlowDisabled
> ```

Na lista da solução, em cada um dos dois: **⋮ → Ativar**. O ⃠ some do ícone.

O 💎 ao lado do nome é outra coisa e é esperado: marca fluxo que vive dentro de uma solução.

### Passo 5 · Testar cada um sozinho

`PortfolioDataArea` → **Testar → Manualmente**, `scope_label = Customer Dev` e `wiql_filter = AND [Custom.ITArea] = 'Customer Dev'`. Tem que voltar verde com `data` preenchido e `kpis.total` batendo com o Power BI. Esse teste nem toca no SharePoint: se passar, DevOps e filtros estão de pé.

`PublishAreaReport` → **Testar → Manualmente**, os mesmos `scope_label` e `wiql_filter`, mais `report_html = <p style="font-size:13px;">teste</p>`. Tem que aparecer um `.html` na pasta e o `report_url` tem que abrir.

---

## 6. As duas tools no agente

Copilot Studio → agente → **Ferramentas → Adicionar uma ferramenta → Fluxo**, duas vezes.

### Tool 1

| | |
|---|---|
| Fluxo | `CDIO - Portfolio Data by Area` |
| **Renomear para** | **`Read Area Portfolio`** |

```
Returns one slice of the CDIO LATAM portfolio as JSON - every matching initiative plus the KPIs. YOU write the wiql_filter: IT Area, manager, country, project type, budget, or any combination of them. Call this FIRST whenever a report is asked for, or whenever a portfolio question needs project-level data. It creates no file.
```

### Tool 2

| | |
|---|---|
| Fluxo | `CDIO - Publish Area Report` |
| **Renomear para** | **`Publish Area Report`** |

```
Publishes the CDIO IT Portfolio LATAM executive report to SharePoint and returns the link. This tool OWNS the report page: never build the HTML yourself and never use the code interpreter for it. Call it only after Read Area Portfolio, passing the SAME scope_label, wiql_filter and year, plus the report_html YOU wrote in English.
```

> ⚠️ **Duas armadilhas neste passo.**
>
> **Renomeie mesmo.** O fluxo se chama `CDIO - Portfolio Data by Area`, a tool tem que se chamar `Read Area Portfolio` — é esse nome que o `§11` usa. Sem renomear, a instrução aponta para um nome que não existe.
>
> **As duas descrições são diferentes.** Copiar a mesma nas duas é fácil e quebra o roteamento: a de baixo diz *"Call this FIRST"* e *"It creates no file"* — numa tool que publica arquivo e é chamada por último, isso manda o modelo para o lado errado.

Confira que **todas as entradas** estão em **"Dinamicamente com IA"**. Entrada não declarada assim é entrada que o modelo não enxerga — o defeito repetido em [`02-correcao-das-tools.md`](02-correcao-das-tools.md), que reaparece a cada tool nova.

As descrições das entradas vêm prontas do gatilho de cada fluxo. **Não redigite.** As duas que fazem o trabalho pesado, para revisão:

**Descrição da entrada `report_html`** — é este texto que segura o desenho da página:  `976/1024`

```
YOU write this, always - never ask the user for it. It is the whole written part of the report, in ENGLISH.
SHAPE: open with 3-5 sentences of executive summary - money at stake, where risk sits, the decision you want from leadership. Then your analysis, in as many sub-sections as you like; nothing is mandatory.
FRAGMENT only: no <html>, <head>, <body>, <style>, <script>, class= or id=. Use <p>, <div>, <table>, <tr>, <td>, <ul>, <li>, <strong>, <em>, <a>, each with inline style=.
STYLE: font-family:'Segoe UI',sans-serif. Text #1e293b, muted #64748b, border #e2e8f0. Accents: #a855f7 decision, #06b6d4 section, #ef4444 risk, #10b981 win, #f59e0b watch. Section title 14px/800, body 13px/1.6. Tables border-collapse:collapse, padding:6px 10px.
PROJECTS: always Name (1234), linked to https://dev.azure.com/CDIO-IT-LATAM/CDIO%20Portfolio/_workitems/edit/1234. Money as EUR 1.4M.
FORBIDDEN: <img>, base64, external URLs, and any number the Portfolio Data call did not return.
```

---

## 6.1 O tópico que atalha a arquitetura

Existe no agente um tópico `Create Report`, `OnRecognizedIntent`, com doze frases de gatilho (`relatorio da area`, `gerar relatorio de`, `monta o relatorio de`…). Ele é anterior a esta versão e **precisa sair** — desative ou apague.

O que ele faz:

```yaml
- kind: InvokeFlowAction
  flowId: b7e3a1c4-5d92-4f08-9a61-3c8de40f27b5     # PublishAreaReport
  input:
    binding:
      area: =Topic.SelectedArea
      year: "2026"
```

Chama o fluxo de **publicação** direto, passando só `area` e `year` — entradas que nem existem mais desde a `1.4.0.0`. Sem `report_html`, sem nunca ter lido o portfólio. O fluxo não quebra — o `coalesce` cobre o campo vazio — e é justamente esse o problema: sai uma página completa, bonita, com o resumo genérico de contagens e **sem o bloco de análise**. O relatório oco que esta arquitetura inteira existe para evitar.

Três defeitos menores no mesmo tópico, todos irrelevantes depois de apagá-lo, mas que valem como registro:

- `year: "2026"` fixo no código, o mesmo defeito que o `Init_Year` do fluxo já não tem;
- a área sai de um `If` de Power Fx sobre o texto cru, e `"CD" in Upper(...)` casa dentro de **CDIO** — qualquer pedido que mencione a organização e nenhuma área vira `Customer Dev`;
- e o pior: **é uma corrida.** Às vezes o tópico ganha, às vezes o orquestrador ganha. O mesmo pedido produz o relatório completo ou o oco, sem nada na conversa explicando a diferença.

É a tese do [`05-arquitetura-3-camadas.md`](05-arquitetura-3-camadas.md) aparecendo de novo: tópico prende o agente num fluxo determinístico e disputa com o orquestrador. Os outros dois tópicos já foram desativados por isso; este entrou depois e passou despercebido.

---

## 7. As instruções

> 🔴 **O agente está rodando as instruções antigas.** O export mostra **8.217 caracteres**, com as seções numeradas até `# 10. THE AREA REPORT` e **sem** a seção de reconciliação com a reunião da LT. O texto do §9 lá é a redação do primeiro export, não a deste repositório: o **Bloco C nunca foi feito**. O que aconteceu foi colar o bloco novo por cima do texto que já estava no agente, numerado como 10 — e por isso ele manda "cross with §10", apontando para si mesmo. E 8.217 está acima do teto de 8.000.

A correção é colar o [`agent/instructions-standard.md`](../../agent/instructions-standard.md) **inteiro, substituindo tudo**. Não acrescentar.

> **7.051 chars no arquivo → ~7.971 no agente, 29 de folga.** Cada menção a uma tool vira uma referência `{{System.Bot.Components.Actions...}}` que infla o texto em ~92 caracteres, e agora são dez menções. `python3 scripts/validate-topics.py` mede antes de você colar; o produto trunca em silêncio, e o corte come o fim do texto.

O `§11`, para conferência depois de colar:

```
# 11. THE AREA REPORT
Two tools, in order; the analysis between them is the report.

1. `Read Area Portfolio` + IT Area (exact string, §3) + year → the area as JSON.
   Read it all, cross with §10 and the wiki, run the four lenses.
2. `Publish Area Report` — same area and year, plus `report_html`: the whole
   written report, **by you, in English** — the one place §1 does not apply.
   **Never ask the user for it**; its description carries the contract.
3. Return the `report_url` with three lines on what it concludes; offer §7 per gap.

Interpret the page's KPIs, never repeat them. No figure the data call did not return.
```

---

## 8. O detalhe chato: `.html` no SharePoint costuma **baixar**, não abrir

Boa parte dos tenants roda a biblioteca em **Browser File Handling: Strict**, e aí o SharePoint devolve `.html` como anexo — o usuário clica no link e ganha um download. Três saídas, em ordem de preferência:

1. **Converter para PDF.** Acrescente **"Converter arquivo"** (OneDrive/SharePoint) depois do `Create File SharePoint`, salve o `.pdf` ao lado e devolva o link dele. O template foi escrito para isso — tem `page-break-after` entre as partes. Teste com uma área que tenha Brasil e México: as bandeirinhas em `data:` URI podem não sobreviver ao conversor.
2. **Pedir ao admin** `Browser File Handling: Permissive` na biblioteca. Resolve de vez, mas depende de terceiro.
3. **Mandar por e-mail/Teams** em vez de link. Funciona, mas perde a página como artefato durável, e o Outlook ignora metade do CSS.

> 📎 O `report_url` é `CONFIG_SiteUrl` + o `Path` que o SharePoint devolve, com espaços em `%20`. A ação **Criar arquivo** **não** devolve `{Link}` — quem devolve é **Obter propriedades do arquivo**, que exige o GUID da biblioteca e um `ItemId` que a Criar arquivo também não garante. Montar a URL custa uma expressão e não custa nem uma ação nem um placeholder.

---

## 9. Testes de aceite

| # | O que fazer | O que provar |
|---|---|---|
| 1 | `PortfolioDataArea` manual, `scope_label = Customer Dev`, `wiql_filter = AND [Custom.ITArea] = 'Customer Dev'` | JSON de volta; `kpis.total` bate com o Power BI |
| 2 | Idem com um filtro que não casa com nada | resposta "No initiative matched", ecoando o filtro usado, sem erro vermelho |
| 2b | Idem com `wiql_filter` vazio e `year = all` | portfólio inteiro, todos os anos |
| 3 | `PublishAreaReport` manual com um `report_html` de teste | `.html` na pasta, com o texto na caixa `Executive Summary & Analysis` do topo |
| 0 | `Tópicos` no menu do agente | **não existe** um tópico `Create Report` ativo — ele atalha a arquitetura, ver §6.1 |
| 4 | Abrir cada tool e reler a descrição | a de `Publish Area Report` fala em publicar, **não** em "Call this FIRST" nem "creates no file" |
| 5 | No agente: *"faz o relatório de Customer Dev"* | ele chama `Read Area Portfolio`, **depois** `Publish Area Report`, e devolve o link — **sem pedir nada a você** |
| 6 | Ler a página | resumo e análise **em inglês** na caixa do topo, cada projeto como `Nome (1234)` com link |
| 7 | Comparar os números do texto com o JSON do passo 1 | nenhum número inventado |
| 8 | Coluna ROI da tabela de BU | `2.10x`, não `€ 2,10`; vermelho abaixo de `1.00x`; `n/a` sem budget |
| 9 | Botão AURA no topo do relatório | abre o agente, não a home do Copilot Studio |
| 10 | Abrir o `report_url` num navegador anônimo | ou abre, ou baixa — e aí você sabe qual saída da §8 vai precisar |

O teste 5 é o que separa esta versão da anterior. Se ele parar e pedir o resumo, a correção não pegou: volte à caixa de aviso da §1.
