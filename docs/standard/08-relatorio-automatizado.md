# 8. Relatório automatizado por IT Area

Dois fluxos do Power Automate e duas tools no agente. O primeiro devolve o portfólio de uma IT Area em JSON; o agente analisa; o segundo publica a página HTML no SharePoint com o texto que **o agente** escreveu. O relatório inteiro sai em **inglês**.

| | |
|---|---|
| Solução | [`flows/CDIORelatorioArea/`](../../flows/CDIORelatorioArea/) · empacote com `flows/build.sh` |
| Zip pronto | `dist/CDIORelatorioArea_1_2_0_4.zip` |
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
| **`PortfolioDataArea`** | `area`, `year` | consulta o DevOps e devolve JSON. Nenhum campo de texto livre para perguntar |
| **`PublishAreaReport`** | `area`, `year`, `exec_summary`, `analysis_html` | consulta, renderiza o HTML, publica no SharePoint, devolve o link |

Na primeira não sobra nada para o binder perguntar. Na segunda, a descrição de cada entrada agora **manda escrever** em vez de dizer "só no modo X" — e abre com `YOU write this - never ask the user for it`. Era a descrição que dizia ao modelo para deixar o campo vazio; era ela que precisava mudar.

`mode` e `full_html` deixaram de existir. Um escape hatch que custa uma pergunta em toda chamada não paga o que entrega.

> 💡 **Se ainda assim ele perguntar:** abra a tool no Copilot Studio, clique em `exec_summary` e procure um controle do tipo *"perguntar ao usuário quando o valor não for encontrado"*. No YAML exportado as entradas são `AutomaticTaskInput` idênticas, sem nada que as distinga — então ou esse controle só vive na UI, ou `shouldPromptUser: true` é o padrão do produto. Desmarcar, se existir, é o reforço.

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
- As descrições de `exec_summary` e `analysis_html` pedem **ENGLISH** em maiúsculas.
- O que ainda estava em português dentro do fluxo virou inglês: `Atraso Justificado` → **Delay Justification**, o texto de quando não há justificativa, o resumo automático de reserva, `Não informado` → **Not informed**, a mensagem de área vazia, o nome do arquivo (`..._CDIO_Report_Consumer.html`), e os números da tabela de BU passaram de `pt-BR` para `en-US`.

**A conversa com o agente continua em português.** Só o documento é inglês.

---

## 5. Importar

### Passo 1 · Pegar o zip

- **Baixar do GitHub:** abra [`dist/CDIORelatorioArea_1_2_0_4.zip`](https://github.com/nick-kuh/coisas_aleartorias/blob/claude/automated-html-report-section-rbmt60/dist/CDIORelatorioArea_1_2_0_4.zip) e clique em **Download raw file** (ícone ⤓ à direita). "Salvar como" na página salva HTML, não o zip.
- **Ou regerar:** `flows/build.sh`.

> ⚠️ **Não reempacote pelo Explorador do Windows.** O Power Automate exige `[Content_Types].xml`, `solution.xml` e `customizations.xml` **na raiz**; zipar a pasta cria um nível a mais e a importação recusa.

### Passo 2 · Importar

1. [make.powerautomate.com](https://make.powerautomate.com) → confira o **ambiente** no canto superior direito. É o mesmo do agente. Este é o erro que mais custa tempo.
2. **Soluções → Importar solução → Procurar** → o zip → **Avançar**.
3. A tela mostra `CDIORelatorioArea` versão `1.2.0.4`. Como a `1.1.x` já está lá, ele diz **Atualizar**.
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

> 🔴 **Solução importada chega com os fluxos DESLIGADOS.** É o passo que mais se pula, e o sintoma não parece com a causa: na lista, o ícone do fluxo ganha um pequeno **⃠** no canto — parece um fluxo "oculto" ou sem permissão, e é só desativado. O agente, ao chamar, devolve:
>
> ```
> Mensagem de Erro: O fluxo com a ID c8f5d2e1-... está desabilitado.
> Código do Erro: FlowDisabled
> ```

Na lista da solução, em cada um dos dois: **⋮ → Ativar**. O ⃠ some do ícone.

O 💎 ao lado do nome é outra coisa e é esperado: marca fluxo que vive dentro de uma solução.

### Passo 5 · Testar cada um sozinho

`PortfolioDataArea` → **Testar → Manualmente**, `area = Customer Dev`. Tem que voltar verde com `data` preenchido e `kpis.total` batendo com o Power BI. Esse teste nem toca no SharePoint: se passar, DevOps e filtros estão de pé.

`PublishAreaReport` → **Testar → Manualmente**, `area = Customer Dev`, `exec_summary = teste`, `analysis_html = <p style="font-size:12px;">teste</p>`. Tem que aparecer um `.html` na pasta e o `report_url` tem que abrir.

---

## 6. As duas tools no agente

Copilot Studio → agente → **Ferramentas → Adicionar uma ferramenta → Fluxo**, duas vezes.

### Tool 1

| | |
|---|---|
| Fluxo | `CDIO - Portfolio Data by Area` |
| **Renomear para** | **`Read Area Portfolio`** |

```
Returns the full portfolio of one CDIO LATAM IT Area as JSON - every active initiative plus the KPIs. Call this FIRST, whenever a report is asked for, and analyse what comes back. It creates no file.
```

### Tool 2

| | |
|---|---|
| Fluxo | `CDIO - Publish Area Report` |
| **Renomear para** | **`Publish Area Report`** |

```
Publishes the CDIO IT Portfolio LATAM executive report for one IT Area to SharePoint and returns the link. Call it only after Read Area Portfolio, passing the executive summary and the analysis YOU wrote in English. Never ask the user to write them.
```

> ⚠️ **Duas armadilhas neste passo.**
>
> **Renomeie mesmo.** O fluxo se chama `CDIO - Portfolio Data by Area`, a tool tem que se chamar `Read Area Portfolio` — é esse nome que o `§11` usa. Sem renomear, a instrução aponta para um nome que não existe.
>
> **As duas descrições são diferentes.** Copiar a mesma nas duas é fácil e quebra o roteamento: a de baixo diz *"Call this FIRST"* e *"It creates no file"* — numa tool que publica arquivo e é chamada por último, isso manda o modelo para o lado errado.

Confira que **todas as entradas** estão em **"Dinamicamente com IA"**. Entrada não declarada assim é entrada que o modelo não enxerga — o defeito repetido em [`02-correcao-das-tools.md`](02-correcao-das-tools.md), que reaparece a cada tool nova.

As descrições das entradas vêm prontas do gatilho de cada fluxo. **Não redigite.** As duas que fazem o trabalho pesado, para revisão:

**Descrição da entrada `exec_summary`:**  `425/1024`

```
YOU write this - never ask the user for it. The executive summary that opens the report, in ENGLISH, 3 to 5 sentences: money at stake, where risk concentrates, the decision you are asking leadership to make - in that order. Plain prose; only <strong> and <em> are allowed. Name every project as Name (1234). Every figure must come from the Portfolio Data call you just made. If you have not made that call yet, make it first.
```

**Descrição da entrada `analysis_html`** — é este texto que segura o desenho da página:  `928/1024`

```
YOU write this - never ask the user for it. Your analysis, in ENGLISH, as an HTML fragment placed in its own section of the report. YOU choose the sub-sections: nothing is mandatory, nothing is forbidden.
FRAGMENT only: no <html>, <head>, <body>, <style>, <script>, class= or id=. Use <p>, <div>, <table>, <tr>, <td>, <ul>, <li>, <strong>, <em>, <a>, each carrying an inline style=.
STYLE: font-family:'Segoe UI',sans-serif. Text #1e293b, muted #64748b, border #e2e8f0, soft background #f8fafc. Accents: #a855f7 decision, #06b6d4 section, #ef4444 risk, #10b981 win, #f59e0b watch. Block title 14px/800, body 12px/1.5, note 10px. Tables with border-collapse:collapse and padding:6px 10px.
PROJECTS: always Name (1234), linked to https://dev.azure.com/CDIO-IT-LATAM/CDIO%20Portfolio/_workitems/edit/1234. Money as EUR 1.4M.
FORBIDDEN: <img>, base64, any external URL, and any number that did not come from the Portfolio Data call.
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

Chama o fluxo de **publicação** direto, passando só `area` e `year`. Sem `exec_summary`, sem `analysis_html`, sem nunca ter lido o portfólio. O fluxo não quebra — o `coalesce` cobre os dois campos vazios — e é justamente esse o problema: sai uma página completa, bonita, com o resumo genérico de contagens e **sem o bloco de análise**. O relatório oco que esta arquitetura inteira existe para evitar.

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
2. `Publish Area Report` — same area and year, plus `exec_summary` and
   `analysis_html`, **written by you, in English**: the report is the one place §1
   does not apply. **Never ask the user for either**; their descriptions carry the
   contract.
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
| 1 | `PortfolioDataArea` manual, `area = Customer Dev` | JSON de volta; `kpis.total` bate com o Power BI; `noGoLiveDate > 0` numa área com projetos em `01 Idea` |
| 2 | Idem com uma área inexistente | resposta "No active initiative found", sem erro vermelho no histórico |
| 3 | `PublishAreaReport` manual com textos de teste | `.html` na pasta, quadro roxo "AURA — Analysis & Decisions" antes da tabela de BU |
| 0 | `Tópicos` no menu do agente | **não existe** um tópico `Create Report` ativo — ele atalha a arquitetura, ver §6.1 |
| 4 | Abrir cada tool e reler a descrição | a de `Publish Area Report` fala em publicar, **não** em "Call this FIRST" nem "creates no file" |
| 5 | No agente: *"faz o relatório de Customer Dev"* | ele chama `Read Area Portfolio`, **depois** `Publish Area Report`, e devolve o link — **sem pedir nada a você** |
| 6 | Ler a página | resumo e análise **em inglês**, cada projeto como `Nome (1234)` com link |
| 7 | Comparar os números do texto com o JSON do passo 1 | nenhum número inventado |
| 8 | Coluna ROI da tabela de BU | `2.10x`, não `€ 2,10`; vermelho abaixo de `1.00x`; `n/a` sem budget |
| 9 | Botão AURA no topo do relatório | abre o agente, não a home do Copilot Studio |
| 10 | Abrir o `report_url` num navegador anônimo | ou abre, ou baixa — e aí você sabe qual saída da §8 vai precisar |

O teste 5 é o que separa esta versão da anterior. Se ele parar e pedir o resumo, a correção não pegou: volte à caixa de aviso da §1.
