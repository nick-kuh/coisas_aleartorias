# 6. Fluxo do Power Automate — transcrição da LT no SharePoint

Objetivo: a cada reunião de LT, a transcrição chega sozinha na biblioteca do SharePoint, limpa e nomeada de forma que o AURA consiga usá-la.

---

## Como o Teams realmente guarda a transcrição

Este é o ponto que confunde todo mundo, e que eu próprio errei na primeira versão deste guia.

**A transcrição não vira arquivo na pasta.** Ela é um **anexo do item de vídeo**, dentro do Stream. Por isso:

- A pasta `Recordings` mostra **só o `.mp4`**
- Clicar nele abre o **player**, não um texto
- A transcrição aparece no **painel lateral**, com um botão `Baixar ⌄`

Isso é o comportamento normal, não um defeito de configuração.

> 📌 **Uma reunião "transcrita apenas" também gera `.mp4`.** Se você só ligou a transcrição, sem gravar, o Teams ainda cria um item de mídia — ele precisa de algo para hospedar a transcrição. O banner do player diz *"Esta reunião foi transcrita apenas"*. Ver um `.mp4` não significa que alguém gravou.

### A boa notícia: existe API do SharePoint para isso

O próprio player busca a transcrição por uma API do **SharePoint** — não do Graph:

```
GET {site}/_api/v2.1/drives/{driveId}/items/{itemId}/media/transcripts
GET {site}/_api/v2.1/drives/{driveId}/items/{itemId}/media/transcripts/{id}/streamContent?format=text/vtt
```

Isso é chamável pela ação **"Enviar uma solicitação HTTP para o SharePoint"** do Power Automate, que usa **a sua própria conexão**. Sem registro de aplicativo, sem consentimento de admin, sem Application Access Policy — nenhum dos três portões da Rota B.

> ⚠️ **E tem prazo.** O player mostra *"Expira em 30 dias"*: gravação e transcrição somem sozinhas. Copiar para a biblioteca do SharePoint é o que preserva o histórico das LT além disso — o que torna esse fluxo uma questão de memória institucional, não de conveniência.

### Nota lateral: gravar e transcrever são botões diferentes

Continua valendo, e vale conferir se você não vir transcrição nenhuma no painel:

| Ação | Produz |
|---|---|
| **Gravar** | o vídeo |
| **Transcrever** | o texto do painel |

Para não depender de alguém lembrar: no convite da LT → **Opções de reunião → Gravar e transcrever automaticamente**. Se a opção nem existir, é política do tenant — aí é chamado para o admin, mas é um toggle, não os três portões do Graph.

---

## As três rotas

| | **Rota A — API do Stream** | **Rota A2 — arrastar** | **Rota B — Graph** |
|---|---|---|---|
| Como pega | pede a transcrição pela API do SharePoint | você solta o arquivo numa pasta | chama o Graph |
| Precisa de admin? | **Não** | **Não** | **Sim** — 3 portões |
| Automática? | **Sim** | não — 2 cliques por reunião | sim |
| Risco | ✅ **validada em 19/08 neste tenant** | nenhum | aprovações demoram |
| Tempo para montar | ~40 min | ~15 min | ~2h + espera |

> 🎯 **Vá de Rota A.** Ela foi **validada neste tenant em 19/08/2026** — a chamada existe e responde. Deixou de ser aposta.
>
> A **A2** fica como rede de segurança, para o caso de algo travar: 2 cliques a cada reunião, sem depender de nada.
>
> A Rota B só ganharia se você precisasse varrer reuniões de muita gente diferente — e o Graph já foi descartado.

---

# Rota A — automática, pela API do SharePoint

> ## 📍 O fluxo atravessa DOIS lugares diferentes
>
> Isso confunde, então vale fixar antes de montar qualquer coisa:
>
> ```
> ORIGEM — OneDrive do organizador
> https://<tenant>-my.sharepoint.com/personal/<upn>/Documents/Recordings/reuniao.mp4
>         │
>         │  passos 1–6: gatilho · caminho · esperar+listar · conferir · id · baixar o VTT
>         ▼
>    limpeza (passos 7–11) — só texto, não toca em arquivo
>         │
>         ▼
> DESTINO — site de equipe do CDIO LATAM
> https://<tenant>.sharepoint.com/sites/<CDIO-LATAM>/Transcricoes LT/LT-2026-08-19.txt
>         │
>         ▼
>    fonte de conhecimento do agente
> ```
>
> | | Onde | O que acontece |
> |---|---|---|
> | **Origem** | OneDrive, pasta `Recordings` | o `.mp4` chega com a transcrição anexada |
> | **Destino** | site do CDIO LATAM, `Transcricoes LT` | o `.txt` limpo é gravado, e é o que o agente lê |

> ## ✅ Rota A validada no tenant em 19/08/2026
>
> Não é mais inferência. A chamada foi capturada no DevTools do próprio ambiente e responde:
>
> ```
> https://<tenant>-my.sharepoint.com/personal/<upn>
>    /_api/v2.1/drives/<driveId>/items/<itemId>/media/transcripts/<transcriptId>/streamContent
> ```
>
> O host é `-my.sharepoint.com` — **OneDrive**, como o desenho previa. E o endpoint `media/transcripts` **existe e devolve dados**, que era a única peça que não dava para garantir de fora.
>
> ⚠️ **O player usa `?is=1&applymediaedits=false`, não `?format=text/vtt`.** Os dois valem teste: o VTT é bem mais fácil de limpar, porque o filtro por `<v ` resolve tudo numa condição. Se só o formato do player responder, a limpeza vira `Analisar JSON` em vez do filtro.

> ## 🔁 "Preciso fazer isso toda semana?" Não — a captura é **uma vez só**
>
> A URL parece um bloco único, mas tem quatro pedaços com destinos diferentes:
>
> ```
> https://<tenant>-my.sharepoint.com/personal/<upn>/_api/v2.1/drives/b!619Xou...
> └──────────────────────── FIXO — nunca muda ────────────────────────────────┘
>    /items/01JZ7SIC.../media/transcripts/54981c02-.../streamContent
>           └── MUDA ──┘                  └── MUDA ──┘
> ```
>
> | Pedaço | Muda? | De onde vem |
> |---|---|---|
> | Site (`<tenant>-my.sharepoint.com/personal/<upn>`) | **Nunca** | você digita **uma vez** no "Endereço do site" |
> | `driveId` | **Nunca** — é o mesmo OneDrive | você digita **uma vez** na URI |
> | `itemId` **ou** o caminho do arquivo | **A cada reunião** | vem do **gatilho** |
> | `transcriptId` | **A cada reunião** | vem do **passo 3**, extraído no passo 5 |
>
> Duas peças fixas que você descobre uma vez, e duas que o fluxo preenche sozinho. **Reunião semanal, quinzenal ou diária: tanto faz.**
>
> ⚠️ **O que quebraria isso:** trocar o organizador da LT. Aí o `/personal/<upn>` vira outro, porque passa a ser o OneDrive de outra pessoa. É o mesmo risco da nota sobre reunião de canal, no fim desta rota.

> ### 🔑 Por que a ação "…para o SharePoint" funciona num arquivo do OneDrive
>
> Porque **OneDrive for Business é um site SharePoint por baixo**. O endereço dele é:
>
> ```
> https://<tenant>-my.sharepoint.com/personal/<upn com _ no lugar de . e @>
> ```
>
> Exemplo: `nome.sobrenome@empresa.com` → `.../personal/nome_sobrenome_empresa_com` — os `.` e o `@` viram `_`
>
> Então nos passos 3 e 6, o campo **"Endereço do site"** recebe **esse endereço do OneDrive**, não o do site de equipe. Não é gambiarra — é o mesmo produto.
>
> **E você não precisa acreditar em mim:** a URL que você capturar no DevTools já mostra o host certo. Se aparecer `-my.sharepoint.com`, está confirmado.


## 1. Preparar o destino no SharePoint

1. No site do CDIO LATAM → **Novo → Biblioteca de documentos**
2. Nome: **`Transcricoes LT`**
3. Dentro dela, **+ Adicionar coluna**:

| Coluna | Tipo | Para quê |
|---|---|---|
| `DataReuniao` | Data | permite o agente dizer "na LT de 12/08…" |
| `Origem` | Texto | `Teams` — distingue do que for subido à mão |

## 2. Criar o fluxo

> ## 🎯 Passo zero: capture a chamada e teste duas variantes
>
> ### 1. Capture a chamada real (uma vez só)
>
> Com a gravação aberta e o painel **Transcrição** visível:
>
> 1. **F12** → a aba **Rede** normalmente **não vem aberta**: está atrás do botão **`+`**
> 2. Filtro: `transcripts`
> 3. **Feche e reabra o painel Transcrição** — redispara a chamada sem recarregar
> 4. Clique na linha → **Cabeçalhos** → copie o **URL da solicitação**
>
> ⚠️ Não confunda com a URL da **barra de endereços**: aquela tem `stream.aspx` e `referrerScenario=AddressBarCopied`, e **não é** a chamada da API.
>
> A URL certa tem esta cara:
>
> ```
> https://<tenant>-my.sharepoint.com/personal/<upn>/_api/v2.1/drives/<driveId>/items/<itemId>/media/transcripts/<transcriptId>/streamContent?is=1&applymediaedits=false
> ```
>
> Separe e guarde: **site** (tudo até `/_api/`) e **driveId**. São as duas peças fixas.
>
> ### 2. Teste duas variantes na barra de endereços
>
> Você já está autenticado — é colar e ver o que volta.
>
> **Variante A — endereçar por caminho, sem `itemId`:**
>
> ```
> <SITE>/_api/v2.1/drives/<driveId>/root:/Recordings/<arquivo>.mp4:/media/transcripts
> ```
>
> Se responder, o fluxo fica **bem** mais simples: o gatilho já dá o caminho, e não é preciso descobrir `itemId` nenhum.
>
> **Variante B — pedir VTT em vez do formato do player:**
>
> ```
> <a URL capturada>/streamContent?format=text/vtt
> ```
>
> Esperado: texto começando com `WEBVTT`, com linhas `<v Nome Sobrenome>…</v>`.
>
> ### 3. O que cada resultado decide
>
> | Resultado | Como fica o fluxo |
> |---|---|
> | **A e B funcionam** | O mais simples: caminho + `format=text/vtt`. Sem `itemId`, sem passo extra |
> | **A falha, B funciona** | Entra um passo resolvendo caminho → `itemId` pela mesma API |
> | **B falha** | Usa `?is=1&applymediaedits=false`, e a limpeza vira `Analisar JSON` em vez do filtro `<v ` |
>
> ⚠️ **Não guarde `driveId` e `itemId` em lugar público.** Eles identificam o seu OneDrive. Nos exemplos deste documento eles aparecem sempre como `<driveId>` e `<itemId>`.

**Power Automate → Criar → Fluxo de nuvem automatizado**

### Gatilho

**OneDrive for Business → Quando um arquivo é criado (somente propriedades)**

| Campo | Valor |
|---|---|
| Pasta | `/Gravações` (ou `/Recordings`, conforme o idioma da conta) |

É **OneDrive**, não SharePoint — a gravação de reunião agendada cai no OneDrive do organizador.

> ## 🔴 Existem DOIS gatilhos com nome quase igual. Pegar o errado quebra tudo
>
> | Gatilho | `operationId` | O que vem no `body` |
> |---|---|---|
> | Quando um arquivo é criado | `OnNewFileV2` | 🔴 **o conteúdo do arquivo** (binário) |
> | Quando um arquivo é criado **(somente propriedades)** | outro | ✅ **nome, caminho, data, id** |
>
> **Como o erro se apresenta:**
>
> ```
> 'endsWith' expects its first parameter to be of type string.
> The provided value is of type 'Null'.
> ```
>
> Isso é `body/Name` vindo vazio — porque com o gatilho errado **o body é o vídeo**, não as propriedades.
>
> **E tem um efeito colateral pior que o erro:** com `OnNewFileV2` o fluxo **baixa o `.mp4` inteiro** a cada disparo. Numa gravação de uma hora são centenas de MB trafegados para serem descartados, já que o fluxo só precisa do nome e do caminho.
>
> **Como conferir qual você pegou:** abra o gatilho → **⋯ → Exibição de código** e olhe o `operationId`. Se for `OnNewFileV2`, é o errado.
>
> Não dá para trocar a operação de um gatilho existente — **apague e adicione o certo**. As expressões `triggerOutputs()?['body/…']` do resto do fluxo continuam válidas.

> ## ⚠️ Antes de confiar em qualquer `body/…`: rode uma vez e olhe
>
> Os nomes de campo variam entre conectores, e digitar de memória é o que produz `Null`:
>
> | Onde | Pode ser |
> |---|---|
> | condição do `.mp4` | `Name` ou `DisplayName` |
> | caminho do arquivo | `Path` — **as chaves de `{Path}` são convenção do SharePoint**, o OneDrive pode não usar |
> | data para o nome do arquivo | `LastModified` |
>
> **Salve, rode uma vez, e no histórico abra a saída do gatilho.** O JSON mostra os nomes exatos. Só então escreva as expressões.
>
> 🎯 **Atalho que economiza uma rodada:** em vez de digitar, use o **seletor de conteúdo dinâmico**. Ele insere o nome certo seja qual for — digitar à mão é exatamente o que gera `{Path}` num conector que talvez use `Path`.

> ⚠️ O gatilho roda na conta de **quem conectar o OneDrive** — precisa ser a do organizador da LT. Se o organizador mudar, o fluxo para de enxergar os arquivos. Ver a nota sobre reunião de canal no fim desta rota.

### Passo 1 — só o `.mp4`

**Controle → Condição**:

```
endsWith(triggerOutputs()?['body/Name'], '.mp4')
```

é igual a `true`. Todo o resto vai no ramo **Se sim**.

> 📌 Repare que é o **oposto** do que faria sentido à primeira vista. Não existe `.vtt` na pasta para filtrar — o `.mp4` é o item que **carrega** a transcrição, e é dele que vamos pedi-la.

### Passo 2 — montar o caminho  ⚠️ **fora do loop**

**Operações de dados → Compor**, nome `Caminho`:

```
replace(triggerOutputs()?['body/{Path}'], '/Documents', '')
```

O gatilho traz o caminho com `/Documents` na frente; a raiz do drive **é** o Documents, então ele sai.

> ⚠️ **Deixe este passo ANTES do `Do until`, não dentro.** Ele só depende do gatilho — recalcular a cada iteração é desperdício, e referenciá-lo de fora do loop (o passo 6 faz isso) pega o valor da última iteração, o que é frágil sem necessidade.

### Passo 3 — esperar e listar as transcrições

**Controle → Do until**

| Campo | Valor |
|---|---|
| Condição (modo avançado) | `@greater(length(coalesce(body('Listar_transcricoes')?['value'], json('[]'))), 0)` |
| Contagem | `60` |
| Tempo limite | `PT1H` |

**Dentro do loop, nesta ordem:**

**4a. Controle → Atraso** — `30` segundos.

> 🔴 **Sem este atraso, o loop de espera não espera.** O campo "Tempo limite" é o **teto** de duração, não o ritmo: sem um Delay dentro, as 60 iterações queimam em poucos segundos e o loop desiste, enquanto a transcrição leva minutos para processar. Com 30 s × 60, a espera cobre até 30 minutos reais.

**4b. SharePoint → Enviar uma solicitação HTTP para o SharePoint**, nomeada `Listar transcricoes`:

| Campo | Valor |
|---|---|
| Endereço do site | 🔑 **o OneDrive**: `https://<tenant>-my.sharepoint.com/personal/<upn>` |
| Método | `GET` |
| URI | `_api/v2.1/drives/<seu driveId>/root:@{outputs('Caminho')}:/media/transcripts` |

E em **⋯ → Configurar execução após**, marque também **com falha**.

> Se a API devolver `404` enquanto a transcrição não existe — em vez de `200` com lista vazia — a ação falha e **o `Do until` aborta na primeira iteração**. Aceitar a falha deixa o loop continuar tentando; o `coalesce` da condição trata a ausência de corpo.

### Passo 4 — conferir que a transcrição ficou pronta

**Controle → Condição**, logo após o `Do until`, em modo avançado:

```
@greater(length(body('Listar_transcricoes')?['value']), 0)
```

- **Se sim** → o resto do fluxo
- **Se não** → **Controle → Encerrar** com `Failed`, código `TranscricaoNaoFicouPronta`

> ⚠️ **Por que isso é necessário:** um `Do until` que estoura o limite de tentativas termina com status **Sucesso**, não falha. Sem esta conferência, o fluxo seguiria com a lista vazia, o passo seguinte devolveria `null`, e você receberia um `404` confuso lá na frente — em vez do motivo real, que é "a transcrição nunca ficou pronta".

### Passo 5 — extrair o id da transcrição

**Operações de dados → Compor**, nome `TranscriptId`, **depois** do `Do until`:

```
last(body('Listar_transcricoes')?['value'])?['id']
```

Pego a **última** de propósito: se a transcrição foi reiniciada no meio da reunião, a última é a completa.

> 🔴 **Este passo é fácil de esquecer.** O passo 6 monta a URL com `@{outputs('TranscriptId')}` — se o Compose não existir com **exatamente** esse nome, o fluxo falha com referência não resolvida.

### Passo 6 — baixar o VTT

**SharePoint → Enviar uma solicitação HTTP para o SharePoint**, nomeada `Baixar transcricao`:

| Campo | Valor |
|---|---|
| Endereço do site | o mesmo do passo 3 — **o OneDrive** |
| Método | `GET` |
| URI | `_api/v2.1/drives/<seu driveId>/root:@{outputs('Caminho')}:/media/transcripts/@{outputs('TranscriptId')}/streamContent?format=text/vtt` |

> ✅ **Este é o portão.** Rode uma vez e **abra a saída desta ação**, não confie no verde: se começar com `WEBVTT` e tiver `<v Nome>`, a limpeza abaixo funciona como está. Se vier JSON, o `format=text/vtt` não é suportado e a limpeza precisa virar **Analisar JSON** em vez do filtro por `<v `.

> 📌 A ação chama "…para o **SharePoint**", mas o endereço é o do **OneDrive**. Está certo: OneDrive é um site SharePoint.

> ## 🔴 A armadilha nº 1: o nome da ação **é** a referência
>
> No Power Automate, `body('X')` e `outputs('X')` usam o **nome da ação**, com espaços virando `_`. Se o nome não casar, o fluxo falha na execução com `The template language expression … cannot be evaluated`.
>
> **Isso já derrubou este fluxo duas vezes, por caminhos diferentes:**
>
> | O que aconteceu | Por quê |
> |---|---|
> | `TextoLimpo` chamava `body('Selecionar')` | a ação Select tinha sido nomeada `Passo_8` |
> | `Passo_5` chamava `outputs('TranscriptId')` | o Compose foi criado com o nome padrão `Compose 3` |
>
> No segundo caso o conteúdo estava certo — só o **nome** não batia. É o erro mais fácil de cometer e o mais chato de achar, porque tudo *parece* montado.
>
> ### Como se proteger
>
> 1. **Renomeie toda ação assim que criar.** `Compose 3`, `Condition 1`, `Selecionar` não dizem o que fazem, e viram referência quebrada
> 2. Use os nomes deste guia: `Caminho`, `Listar transcricoes`, `TranscriptId`, `Baixar transcricao`, `Linhas`, `Falas`, `Limpar`, `TextoLimpo`
> 3. **Antes de rodar, faça a conferência cruzada:** para cada `body('X')` / `outputs('X')` do fluxo, existe uma ação chamada exatamente `X`? É um minuto e evita a maioria das execuções vermelhas

### Passo 7 — quebrar em linhas

**Operações de dados → Compor**, nome `Linhas`:

```
split(replace(string(body('Baixar_transcricao')), decodeUriComponent('%0D'), ''), decodeUriComponent('%0A'))
```

O `decodeUriComponent('%0D')` é `\r` e o `%0A` é `\n`. O Power Automate não aceita `\n` literal numa expressão — é por isso desse jeito.

### Passo 8 — jogar fora tudo que não é fala

**Operações de dados → Filtrar matriz**, nome `Falas`

| Campo | Valor |
|---|---|
| De | `outputs('Linhas')` |

Condição, em **modo avançado**:

```
@contains(item(), '<v ')
```

**Por que só isso basta:** num `.vtt`, só as linhas de fala têm a marcação de locutor `<v Nome>`. O cabeçalho `WEBVTT`, os identificadores de bloco, os timestamps `00:00:05.123 --> 00:00:08.456` e as linhas em branco **não têm** — e caem todos de uma vez.

### Passo 9 — 🔴 guarda: parar se não veio transcrição

**Controle → Condição**, em modo avançado:

```
@greater(length(body('Falas')), 0)
```

- **Se sim** → todo o resto do fluxo (passos 10 em diante)
- **Se não** → **Controle → Encerrar**:

| Campo | Valor |
|---|---|
| Status | `Failed` |
| Código | `TranscricaoVazia` |
| Mensagem | `Filtro nao achou linhas com <v — conferir a saida do passo 6` |

> 🔴 **Não pule este passo, e não deixe o ramo "Se não" vazio.**
>
> Sem a condição, se o `format=text/vtt` não devolver VTT o filtro não acha nada e o fluxo **grava um arquivo vazio no SharePoint sem dar erro**.
>
> Com a condição mas **sem o Encerrar**, o arquivo vazio deixa de ser gravado ✅ — mas o fluxo termina com status **Sucesso**, verde no histórico. Você não fica sabendo.
>
> **A guarda tem duas metades:** impedir o arquivo ruim, e te avisar. Ramo falso vazio entrega só a primeira.

### Passo 10 — limpar a marcação

**Operações de dados → Selecionar**, nome `Limpar`

| Campo | Valor |
|---|---|
| De | `body('Falas')` |
| Mapear | modo texto (ícone à direita), com a expressão abaixo |

```
replace(replace(replace(item(), '<v ', ''), '</v>', ''), '>', ': ')
```

O que acontece com uma linha:

```
<v Nome Sobrenome>Precisamos rever o Go-Live do Horizon 2</v>
   ↓  tira '<v '
Nome Sobrenome>Precisamos rever o Go-Live do Horizon 2</v>
   ↓  tira '</v>'
Nome Sobrenome>Precisamos rever o Go-Live do Horizon 2
   ↓  troca '>' por ': '
Nome Sobrenome: Precisamos rever o Go-Live do Horizon 2
```

> ⚠️ **Limitação honesta:** o `replace` troca **todas** as ocorrências. Se alguém falar algo com `>` no meio, aquela linha sai torta. Na prática é raro em transcrição de voz, e o custo de tratar isso direito não compensa — mas é bom você saber que existe.

### Passo 11 — juntar de volta

**Operações de dados → Compor**, nome `TextoLimpo`:

```
join(body('Limpar'), decodeUriComponent('%0A'))
```

> ⚠️ Repare que é `body('Limpar')` — **o nome da ação Selecionar**, não a palavra "Selecionar". Referência que não casa com o nome real da ação derruba o fluxo na execução.

### Passo 12 — gravar no SharePoint 🎯 **aqui muda de lugar**

Até agora tudo aconteceu na **origem** (OneDrive). Deste passo em diante é o **destino**: o site de equipe do CDIO LATAM, que é o que o agente enxerga.

**SharePoint → Criar arquivo**

| Campo | Valor |
|---|---|
| Endereço do site | 🎯 **o site do CDIO LATAM**, **não** o OneDrive dos passos 3 e 6 |
| Caminho da pasta | a biblioteca de transcrições |
| Nome do arquivo | expressão abaixo |
| Conteúdo do arquivo | `outputs('TextoLimpo')` |

```
concat('LT-', formatDateTime(triggerOutputs()?['body/LastModified'], 'yyyy-MM-dd-HHmm'), '.txt')
```

Resultado: `LT-2026-08-19-1929.txt`.

> 📌 **Por que `HHmm` e não só a data:** duas gravações no mesmo dia gerariam o mesmo nome e colidiriam. A data continua legível para a busca semântica, e a hora elimina a colisão. Se as LT são sempre uma por dia, dá para usar só `yyyy-MM-dd` e aceitar o risco.

### Passo 13 — preencher as colunas

**SharePoint → Atualizar propriedades do arquivo**

| Campo | Valor |
|---|---|
| Id | `ItemId` do passo anterior |
| DataReuniao | `formatDateTime(triggerOutputs()?['body/LastModified'], 'yyyy-MM-dd')` |
| Origem | `Teams` |

> ## 💡 Uma alternativa que simplifica, se você topar mudar como a LT é convocada
>
> Se a LT virar **reunião de canal** de um time do CDIO LATAM, a gravação e a transcrição caem **direto no SharePoint daquele time** — o mesmo site do destino. O fluxo passa a ter um site só, e os passos 4 e 5 apontam para o mesmo lugar do passo 10.
>
> E resolve um risco que a montagem atual carrega calado: hoje tudo depende do OneDrive **de uma pessoa**. Se o organizador sair da empresa ou mudar de área, o histórico das LT vai junto com a conta dele.
>
> Não é o que você pediu, e muda como a reunião é criada — fica registrado com o trade-off na mesa.

## 3. Ligar no agente

Copilot Studio → **Conhecimento** → a fonte `Transcription LT Meetings` deve apontar para a biblioteca **`Transcricoes LT`**.

Descrição da fonte — é ela que dispara a busca:

```
Transcripts of the CDIO LATAM Leadership Team meetings, held every two weeks.
Consult this source to find out WHY something happened: why a project is late,
what leadership decided about it, what was promised and by whom, what blocked a
go-live. One file per meeting, named LT-YYYY-MM-DD. Each line is "Speaker: what
they said". Contains decisions and commitments that are NOT recorded in Azure
DevOps or Power BI — this is where the reason lives when the system only shows
the fact.
```

---

# Rota A2 — arrastar o arquivo, sem depender de nada

Use quando a transcrição automática não estiver disponível, ou enquanto o chamado do admin não sai.

**A ideia:** quem organizou a reunião baixa a transcrição e solta numa pasta. O fluxo faz todo o resto — limpar, nomear e arquivar.

## Onde baixar a transcrição

No **chat da reunião** (ou na aba **Recap** da reunião no calendário):

1. Abra a reunião no calendário do Teams → aba **Recap**
2. Em **Transcrição** → **⋯** → **Baixar** → **.vtt**

São dois cliques. Se a transcrição estiver ali, você não precisa de mais nada.

## O fluxo

Idêntico à Rota A, trocando só o gatilho:

### Gatilho

**SharePoint → Quando um arquivo é criado (somente propriedades)**

| Campo | Valor |
|---|---|
| Endereço do site | o site do CDIO LATAM |
| Nome da biblioteca | `Transcricoes LT` |
| Pasta | `/_entrada` |

Crie a subpasta `_entrada` dentro da biblioteca. É a caixa de entrada — o arquivo cru cai ali, e o limpo vai para a raiz.

### Passos 1 a 8

**Reaproveite os passos 6 a 11 da Rota A** (quebrar em linhas, filtrar, limpar, juntar, gravar), com duas trocas:

- A origem do texto é **SharePoint → Obter conteúdo do arquivo** do próprio `_entrada`, no lugar do `body('Passo_5')`
- No passo de gravar, o nome do arquivo não pode sair da data do arquivo (que é a data em que você arrastou, não a da reunião). Use a data que está no nome do arquivo baixado, ou uma coluna que você preenche:

```
concat('LT-', formatDateTime(utcNow(), 'yyyy-MM-dd'), '.txt')
```

> 🎯 Se você baixar a transcrição no mesmo dia da reunião, `utcNow()` resolve. Se costuma atrasar, é melhor **renomear o arquivo para `LT-AAAA-MM-DD.vtt` antes de soltar** e extrair a data do próprio nome — a data no nome é o que o agente usa para dizer "na LT de 12/08".

### Último passo — limpar a caixa de entrada

**SharePoint → Excluir arquivo**, apontando para o `Identificador` do gatilho.

Sem isso o `_entrada` acumula os arquivos crus, e um dia alguém vai reprocessar sem querer.

---

# Rota B — Graph API, com admin

Use quando precisar varrer reuniões de organizadores diferentes, ou quando quiser os IDs.

## B1. O que o admin precisa liberar — os três portões

Nenhum dos três funciona sozinho. Peça os três **no mesmo chamado**, senão vira ida e volta.

### Portão 1 — registro de aplicativo

Entra ID → **Registros de aplicativo** → Novo. Anote **Application (client) ID**, **Directory (tenant) ID** e crie um **client secret**.

### Portão 2 — permissão de aplicativo + consentimento

Em **Permissões de API**, adicionar como **Permissões de aplicativo**:

- `OnlineMeetingTranscript.Read.All`
- `OnlineMeetings.Read.All`

E clicar em **Conceder consentimento do administrador**. Sem isso as permissões ficam listadas mas inertes.

### Portão 3 — Application Access Policy

Este é o que mais gente esquece. A permissão sozinha **não** autoriza o app a ler a reunião de uma pessoa específica. Precisa de uma política, aplicada por PowerShell (módulo `MicrosoftTeams`):

```powershell
New-CsApplicationAccessPolicy -Identity "AURA-Transcricoes" `
  -AppIds "<application-client-id>" `
  -Description "Leitura de transcricoes das LT do CDIO LATAM"

Grant-CsApplicationAccessPolicy -PolicyName "AURA-Transcricoes" `
  -Identity "<upn-do-organizador-da-LT>"
```

> ⏱️ A política leva algum tempo para propagar. Se der `403` logo depois de aplicar, espere e tente de novo antes de sair procurando outro problema.

### Portão 3.5 — o controle novo no Teams Admin Center

A Microsoft passou a ter um controle de tenant **separado** das permissões do Entra: **Teams Admin Center → Configurações e políticas → política de Reunião → "Transcript API access"**. Se estiver bloqueado ali, a API devolve erro **mesmo com tudo do Entra correto**.

Vale incluir no chamado, porque é recente e o time de admin pode não conhecer.

## B2. O fluxo

**Fluxo de nuvem agendado** — recorrência semanal, no dia seguinte à LT.

Todas as chamadas são **HTTP**, com **Autenticação: Active Directory OAuth**:

| Campo | Valor |
|---|---|
| Autoridade | `https://login.microsoftonline.com` |
| Locatário | o Directory (tenant) ID |
| Público-alvo | `https://graph.microsoft.com` |
| ID do Cliente | o Application (client) ID |
| Credencial | Segredo → o client secret |

### Passo 1 — achar a reunião na agenda

```
GET https://graph.microsoft.com/v1.0/users/{upn-do-organizador}/calendar/events
    ?$filter=start/dateTime ge '2026-08-01T00:00:00' and contains(subject,'LT')
    &$select=id,subject,start,onlineMeeting
```

### Passo 2 — extrair a URL de entrada

**Compor**, nome `JoinUrl`:

```
body('Passo_1')?['value'][0]?['onlineMeeting']?['joinUrl']
```

### Passo 3 — do JoinUrl para o ID da reunião

Este é o pulo do gato: o ID da reunião **não** está no evento do calendário. Só dá para chegar nele filtrando por URL.

```
GET https://graph.microsoft.com/v1.0/users/{upn}/onlineMeetings
    ?$filter=JoinWebUrl eq '@{outputs('JoinUrl')}'
```

**Compor** `MeetingId`:

```
body('Passo_3')?['value'][0]?['id']
```

> ⚠️ O `JoinWebUrl` tem que bater **exatamente**. Se a URL vier com parâmetros extras depois de `?`, o filtro não acha nada e o `value` volta vazio. Se der lista vazia, é quase sempre isso.

### Passo 4 — listar as transcrições

```
GET https://graph.microsoft.com/v1.0/users/{upn}/onlineMeetings/@{outputs('MeetingId')}/transcripts
```

Devolve uma lista — uma reunião pode ter mais de uma transcrição. Campos úteis: `id` e `createdDateTime`.

**Compor** `TranscriptId`:

```
last(body('Passo_4')?['value'])?['id']
```

Pego a **última** de propósito: se a transcrição foi reiniciada no meio da reunião, a última é a completa.

### Passo 5 — baixar o conteúdo

```
GET https://graph.microsoft.com/v1.0/users/{upn}/onlineMeetings/@{outputs('MeetingId')}/transcripts/@{outputs('TranscriptId')}/content?$format=text/vtt
```

O corpo da resposta é o `.vtt` cru.

### Passo 6 em diante — igual à Rota A

Reaproveite os **passos 6 a 11 da Rota A** (quebrar em linhas, filtrar `<v `, limpar, juntar, gravar no SharePoint). A origem do texto é o corpo da última chamada HTTP, igual à Rota A.

Para o nome do arquivo, aqui você tem algo melhor que a data do arquivo — a data real da reunião:

```
concat('LT-', formatDateTime(body('Passo_1')?['value'][0]?['start']?['dateTime'], 'yyyy-MM-dd'), '.txt')
```

---

## Erros que você provavelmente vai encontrar

| Erro | Onde | O que é |
|---|---|---|
| `403 Forbidden` na listagem | Passo 4 | Application Access Policy não aplicada, ainda propagando, ou "Transcript API access" bloqueado no Teams |
| `value` vazio | Passo 3 | O `JoinWebUrl` não bateu exatamente — compare caractere a caractere |
| `404` na transcrição | Passo 5 | A reunião não teve transcrição ligada. **Ligue a transcrição automática na política de reunião** |
| Arquivo com timestamps | limpeza | O Filtrar matriz não pegou — confira se está em **modo avançado** com `@contains(item(), '<v ')` |
| `endsWith … expects … string … provided value is of type 'Null'` | Condição | **Gatilho errado.** `OnNewFileV2` devolve o conteúdo do arquivo, não as propriedades — troque por "(somente propriedades)" |
| Campo do gatilho sempre vazio | qualquer | O nome não existe nesse conector. Rode uma vez, abra a saída do gatilho e use o nome real |
| **Só aparece `.mp4` na pasta** | Rota A | **É o comportamento normal.** A transcrição é anexo do vídeo, não arquivo solto. É dela que os passos 3 e 5 vão buscar |
| `The template language expression ... cannot be evaluated` | qualquer passo | Uma referência `body('X')`/`outputs('X')` aponta para ação que **não existe com esse nome**. Confira os nomes das ações contra as referências |
| O `Do until` termina em segundos | Passo 3 | **Falta o `Delay` dentro do loop.** "Tempo limite" é teto de duração, não ritmo — sem Delay, as 60 iterações queimam de uma vez |
| Arquivo gravado **vazio** no SharePoint | Passo 9 | A guarda não foi criada, e o `format=text/vtt` não devolveu VTT. Abra a saída do passo 6 e veja o que realmente voltou |
| `Do until` aborta na 1ª volta | Passo 3 | A chamada falhou (404 de "ainda não pronto") e derrubou o loop. Marque **com falha** em Configurar execução após |
| **Fluxo verde, mas nada foi gravado** | Passo 9 | O ramo "Se não" da guarda está **vazio**. Sem o `Encerrar`, o fluxo termina em sucesso e o problema fica invisível |
| **Fluxo verde, e a transcrição nunca chegou** | Passo 4 | Um `Do until` que estoura o limite termina em **sucesso**, não falha. Falta a condição pós-loop |
| `404` no passo 6, com o passo 3 tendo funcionado | Passo 5 | O id da transcrição saiu vazio — quase sempre é o nome da ação não batendo com `outputs('TranscriptId')` |
| Lista de transcrições vazia | Passo 4 | Ou a transcrição ainda está processando (aumente o atraso do passo 2), ou a reunião não teve transcrição ligada |
| `403` ou `404` na chamada HTTP | Passos 4–5 | A URL não bate com a do seu tenant. Compare com a que você pegou no DevTools |
| Gatilho não dispara | Rota A | A pasta pode chamar `Recordings` em vez de `Gravações`, conforme o idioma da conta |
| Fluxo roda 2x | Rota A | O `.vtt` e o `.docx` caem os dois. A condição do Passo 1 já resolve |

## Checklist

- [ ] **Passo zero** — chamada capturada no DevTools, e as variantes A e B testadas
- [ ] Site e `driveId` guardados: são as duas peças que nunca mudam
- [ ] Decidido entre Forma 1 (caminho) e Forma 2 (`itemId`), conforme o teste
- [ ] Chamada do passo 5 devolvendo o VTT cru — **é o portão, teste isolado antes do resto**
- [ ] Biblioteca `Transcricoes LT` criada, com as colunas `DataReuniao` e `Origem`
- [ ] Fluxo criado e testado numa reunião de teste, com transcrição ligada
- [ ] Arquivo chegou como `LT-AAAA-MM-DD.txt`, sem timestamps, no formato `Locutor: fala`
- [ ] Fonte de conhecimento apontando para a biblioteca, **com a descrição colada**
- [ ] Teste no agente: `o que foi decidido na LT sobre <projeto>?` — tem que responder da transcrição, sem rodar query

O último item é o que prova o circuito inteiro.
