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

> ## ✅ O que a execução de 21/08 provou em campo
>
> Segunda rodada de validação, agora com o fluxo montado e rodando de verdade:
>
> | Evidência na execução | O que fica confirmado |
> |---|---|
> | `Listar transcricoes` verde em **0,3 s** | o caminho montado a partir do `Name`, o `driveId`, o endereçamento `root:…:` e o `%20` — a API achou o arquivo |
> | `Do until` verde em **31 s** | o `Delay` está no lugar certo e o loop espera de verdade (1 volta de 30 s) |
> | A condição pós-loop entrou no ramo **Se sim** | `length(…['value']) > 0` — **a listagem devolveu transcrição** |
>
> Toda a metade "achar o arquivo e localizar a transcrição" está fechada. O que segue em aberto é só **baixar o conteúdo** (passo 6) e saber em que formato ele vem.

> ## 🔁 "Preciso fazer isso toda semana?" Não — a captura é **uma vez só**
>
> A URL parece um bloco único, mas tem quatro pedaços com destinos diferentes:
>
> ```
> https://<tenant>-my.sharepoint.com/personal/<upn>/_api/v2.1/drives/b!xxxxxx...
> └──────────────────────── FIXO — nunca muda ────────────────────────────────┘
>    /items/<itemId>/media/transcripts/<transcriptId>/streamContent
>           └─ MUDA ─┘                    └───── MUDA ─────┘
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

> ## 🔴 Não adivinhe nome de campo. Nem eu acertei.
>
> Os conectores nomeiam os campos de formas diferentes — o do **SharePoint** usa chaves (`{Name}`, `{Path}`, `{Link}`), o do **OneDrive** não. Fora isso, **este guia não afirma quais campos o gatilho do OneDrive entrega**: duas tentativas de fixar o nome do campo de caminho (`{Path}` e depois `Path`) falharam em campo, em 21/08.
>
> O que está confirmado por execução real:
>
> | Campo | Status |
> |---|---|
> | `body/Name` | 🟢 **existe e vem populado** — provado pela Condição do passo 1 ter avaliado `true` |
> | campo de caminho | 🔴 não confirmado com nenhum nome testado |
>
> ### E aqui está a parte que engana
>
> **Campo inexistente no Power Automate não dá erro. Dá `Null`.**
>
> A ação que leu o campo fica **verde**, com nada dentro. O erro só estoura na ação seguinte, quando alguém tenta usar o valor — uma casa depois de onde está a causa, que é justamente onde você não vai olhar primeiro:
>
> ```
> gatilho ──► Caminho: replace(body/{Path}, …)   ← a causa está aqui, e fica verde
>                          │
>                          ▼  Null
>                    Do until: length(…)          ← o erro aparece aqui
> ```
>
> ### O Compose de diagnóstico
>
> Em vez de tentar nomes, gaste uma execução e leia o que o gatilho entrega. Adicione um **Compor** logo no começo, nome `Diagnostico`, com a entrada:
>
> ```
> triggerOutputs()
> ```
>
> Sem função nenhuma em volta — **não tem como falhar**, porque não há o que avaliar. Ele fica verde, e a *saída* dele traz o JSON inteiro do gatilho: todos os nomes de campo e todos os valores, copiáveis. Leia, ajuste as expressões, apague o `Diagnostico`.
>
> É melhor que abrir o painel do gatilho no histórico porque fica exatamente onde você já está olhando quando o fluxo falha.
>
> 🎯 **E prefira o seletor de conteúdo dinâmico a digitar.** Ele insere o nome que existe, seja qual for. Digitar de memória é o que gerou as duas rodadas perdidas.

> ## 🟡 Compose verde ≠ Compose com conteúdo
>
> Vale para **todo** Compose deste fluxo, não só o de diagnóstico, e é a armadilha que mais atrasou a montagem.
>
> Um **Compor** com `null` dentro fica **verde**. Ele não tem o que falhar — só guarda o que a expressão devolveu, e "nada" é um resultado válido. A cor da ação não diz nada sobre o conteúdo dela.
>
> O estrago aparece longe: a ação seguinte monta uma URL com um buraco no meio, ou uma expressão recebe `Null`, e você vai investigar **lá**, não aqui.
>
> **Regra:** ao depurar, abra a **saída** de cada Compose da cadeia, na ordem. O primeiro que estiver vazio é a causa. Já mordeu três vezes neste fluxo — duas no `Caminho` e uma no id da transcrição.

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
concat('/Recordings/', replace(triggerOutputs()?['body/Name'], ' ', '%20'))
```

> 🟢 **Repare no que este passo NÃO faz: ler o campo de caminho do gatilho.** Ele não precisa. O gatilho monitora uma pasta fixa — a mesma que você configurou — então o caminho é sempre `/Recordings/` + o nome do arquivo. E o nome é o campo comprovadamente populado.
>
> Isso troca um campo incerto por dois fatos que você controla. Foi a lição de duas rodadas perdidas tentando adivinhar o nome do campo de caminho.

| Trecho | Papel |
|---|---|
| `'/Recordings/'` | a pasta do gatilho, fixa. Nada a descobrir |
| `body/Name` | 🟢 o campo confirmado em execução real |
| `replace(…, ' ', '%20')` | 🔴 **nome de gravação sempre tem espaço** — `LT CDIO LATAM-20260819_190000-Gravação de Reunião.mp4` — e espaço cru na URI dá `400` no passo 3. Codifica só o espaço e preserva as barras, que é o que o endereçamento `root:/caminho:` precisa |

> ⚠️ **O limite desta solução:** se a LT virar reunião de canal, ou as gravações passarem a cair em subpastas, o `/Recordings/` fixo deixa de valer — aí o campo de caminho volta a ser necessário, e o Compose de diagnóstico (seção do gatilho) diz qual é o nome dele.

> 💡 **Este passo pode deixar de existir.** Veja a nota sobre endereçamento por `Id` no passo 3 — se o gatilho entregar o identificador do arquivo, some o Compose e somem junto espaço, acento, prefixo e pasta fixa.

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

> ## 💡 Endereçar por `Id` em vez de por caminho
>
> A URL capturada no F12 não usava caminho nenhum:
>
> ```
> _api/v2.1/drives/<driveId>/items/<itemId>/media/transcripts/<id>/streamContent
>                             └─ items/, não root:/caminho:/
> ```
>
> Se o `Diagnostico` mostrar um campo de identificador no gatilho, a URI vira
>
> ```
> _api/v2.1/drives/<driveId>/items/@{triggerOutputs()?['body/Id']}/media/transcripts
> ```
>
> e **o passo 2 deixa de existir**. Somem com ele: espaço no nome, acento no nome, prefixo `/Documents`, pasta fixa, subpasta. Toda essa família de problema é do endereçamento por caminho.
>
> ⚠️ Confirme antes de adotar: o identificador do conector precisa estar no mesmo formato que a API `_api/v2.1/drives/…/items/` espera. Rode uma vez com o `Id` e veja se responde `200`.

### Passo 4 — conferir que a transcrição ficou pronta

**Controle → Condição**, logo após o `Do until`, em modo avançado:

```
@greater(length(body('Listar_transcricoes')?['value']), 0)
```

- **Se sim** → o resto do fluxo
- **Se não** → **Controle → Encerrar** com `Failed`, código `TranscricaoNaoFicouPronta`

> ⚠️ **Por que isso é necessário:** um `Do until` que estoura o limite de tentativas termina com status **Sucesso**, não falha. Sem esta conferência, o fluxo seguiria com a lista vazia, o passo seguinte devolveria `null`, e você receberia um `404` confuso lá na frente — em vez do motivo real, que é "a transcrição nunca ficou pronta".

> 💡 **Dá para endurecer de graça.** O item traz um campo `size`, então a condição pode exigir conteúdo de verdade em vez de só presença:
>
> ```
> @greater(coalesce(last(body('Listar_transcricoes')?['value'])?['size'], 0), 0)
> ```
>
> Barra transcrição vazia **antes** de baixar, em vez de descobrir depois que a limpeza não achou nada. A guarda do passo 9 continua valendo — mas para outra coisa: o formato não bater.

### Passo 5 — pegar a URL de download que a API já devolveu

**Operações de dados → Compor**, nome `UrlTranscricao`, **depois** do `Do until`:

```
concat('_api/', last(split(last(body('Listar_transcricoes')?['value'])?['temporaryDownloadUrl'], '/_api/')))
```

Pego a **última** transcrição de propósito: se ela foi reiniciada no meio da reunião, a última é a completa.

> ## 🎯 O item de transcrição traz o endereço pronto
>
> Capturado em execução real, 21/08. Um item de `value` tem esta cara:
>
> | Campo | Exemplo | Para que serve |
> |---|---|---|
> | `id` | GUID | o identificador da transcrição |
> | `displayName` | `<nome>.json` | 🔴 **revela o formato nativo pela extensão** |
> | `size` | `8101` | guarda de transcrição vazia, **antes** de baixar |
> | `languageTag` | `pt-BR` | escolher a faixa certa se houver mais de um idioma |
> | `transcriptType` | `subtitle` | |
> | `isDefault` | `true` | qual usar quando há várias |
> | `temporaryDownloadUrl` | URL absoluta com `?tempauth=…` | 🎯 **a URL de download, já autenticada** |
>
> ### Por que usar essa URL em vez de montar a sua
>
> Compare o que a API devolve com o que dava vontade de escrever à mão:
>
> | | URL da API | URL montada à mão |
> |---|---|---|
> | item | `items/<itemId>` | `root:<caminho>:` |
> | **versão** | **`/versions/current`** | 🔴 **ausente** — a listagem dispensa esse segmento, o download **não** |
> | query | `?tempauth=<token>` | nada, ou um `format` inventado |
>
> Foi essa diferença que produziu o `400` de 21/08. E o consertar-diferença-por-diferença é o caminho errado: **quando a resposta traz um endereço, use o endereço.** Montar URL à mão é assumir a manutenção de um contrato que não é seu — a cada mudança da API, você descobre pelo erro.

**O que o `concat` faz:** a `temporaryDownloadUrl` é absoluta (`https://…/personal/<upn>/_api/v2.1/…`), e o campo URI do conector quer o caminho **relativo ao site**, porque o "Endereço do site" já cobre a primeira metade. O `split` corta no `/_api/`, o `last` fica com a metade da direita, e o `concat` devolve o prefixo.

> 💡 **Por que cortar no `/_api/` e não recortar por texto fixo:** assim a expressão não repete o tenant nem o UPN. Se a conta que conecta o OneDrive mudar, isto continua funcionando sem edição.

> 🔒 **O `tempauth` é credencial de verdade**, com escopos amplos e validade de algumas horas. Ele vai aparecer na URI dentro do histórico de execução — **não compartilhe print dessa tela**, e nunca cole essa URL num lugar público.

> 🔴 **Este passo é fácil de esquecer.** O passo 6 usa `@{outputs('UrlTranscricao')}` — se o Compose não existir com **exatamente** esse nome, o fluxo falha com referência não resolvida.

### Passo 6 — baixar a transcrição

**SharePoint → Enviar uma solicitação HTTP para o SharePoint**, nomeada `Baixar transcricao`:

| Campo | Valor |
|---|---|
| Endereço do site | o mesmo do passo 3 — **o OneDrive** |
| Método | `GET` |
| URI | `@{outputs('UrlTranscricao')}` |

E só. Nenhum pedaço de URL escrito à mão — `driveId`, caminho do item, `versions/current` e autenticação vêm todos prontos do passo 5.

> ✅ **Este é o portão.** Rode uma vez e **abra a saída desta ação**, não confie no verde. O `displayName` do item diz qual formato esperar:
>
> | O que voltar | O que fazer |
> |---|---|
> | **JSON** (é o que o `displayName` `.json` indica) | os passos 7–9 mudam: `Analisar JSON` no lugar do split por linha |
> | `WEBVTT` com `<v Nome>` | os passos 7–9 servem como estão |
>
> 💡 Vale um teste barato: acrescentar **`&format=text%2Fvtt`** no fim da URI — com `&`, porque o `tempauth` já ocupou o `?`, e com a barra codificada como `%2F`, porque barra crua em query string faz o conector montar a URL errada. Se a API souber converter, você ganha o VTT e a limpeza que já está pronta. Se ignorar, não custou nada.

> ## 🔴 O ponto onde o desenho trava: o conector não consegue baixar o stream
>
> **Estado em 21/08: este passo ainda devolve `400 / Unexpected response from the service`, mesmo com a URL correta.**
>
> Não é mais suspeita de endereço. O `UrlTranscricao` foi conferido e é **byte a byte** o caminho relativo da `temporaryDownloadUrl` que a própria API emitiu — `items/<itemId>`, `/versions/current`, `tempauth` e tudo. A URL está certa.
>
> ### A comparação que fecha o diagnóstico
>
> | | Passo 3 (listar) | Passo 6 (baixar) |
> |---|---|---|
> | Conector | o mesmo | o mesmo |
> | Host, site, autenticação | os mesmos | os mesmos |
> | Forma da URL | `_api/v2.1/drives/…` | `_api/v2.1/drives/…` |
> | **O que o endpoint devolve** | **JSON** | **um stream de mídia** |
> | Resultado | ✅ 200 | 🔴 400 |
>
> Só uma variável difere, e é a resposta. `Send an HTTP request to SharePoint` lida bem com JSON; com o que o `streamContent` devolve — provavelmente um **302** para um endereço pré-autenticado, que o conector não segue — ele não lida.
>
> Por isso mexer na query (`tempauth`, `format`, `is=1`) não muda nada: nenhuma dessas alterações muda o **tipo** da resposta.
>
> ### ⚖️ O bloqueio é o cliente HTTP, não a API
>
> Vale registrar porque desfaz uma confusão fácil: **isto não é um limite da rota SharePoint, e trocar para o Graph não resolveria.** O endpoint equivalente no Graph devolve o mesmo tipo de resposta, e o conector teria o mesmo problema. A pergunta certa não é "qual API chamar", é **"qual ação sabe seguir um redirecionamento"**.
>
> ### Teste decisivo, 30 segundos, no navegador
>
> Antes de mudar qualquer coisa no fluxo: abra o **DevTools → Network**, cole a `temporaryDownloadUrl` numa aba nova e olhe a **primeira** linha da lista.
>
> | O que aparecer | O que significa | Para onde ir |
> |---|---|---|
> | **302 / 307** | o conector não segue redirecionamento | ação **HTTP** (abaixo) |
> | **200** com `Content-Type` não-JSON | é negociação de conteúdo | tente o cabeçalho `Accept` (abaixo) |
> | **200** com `application/json` | a resposta é digerível e o problema é outro | reabra a URI do passo 6 caractere a caractere |
>
> É a mesma disciplina que resolveu as rodadas anteriores: ler o que o produto devolve em vez de tentar variações às cegas.
>
> ### Conserto A — cabeçalho `Accept` (grátis, 2 minutos)
>
> A ação tem um campo **Cabeçalhos** opcional. Acrescente:
>
> | Chave | Valor |
> |---|---|
> | `Accept` | `application/octet-stream` |
>
> Só resolve se o problema for negociação de conteúdo. Se for redirecionamento, não muda nada — mas custa dois minutos e descarta uma hipótese.
>
> ### Conserto B — a ação **HTTP** (é premium)
>
> **Adicionar ação → HTTP → HTTP**, e:
>
> | Campo | Valor |
> |---|---|
> | Método | `GET` |
> | URI | `@{last(body('Listar_transcricoes')?['value'])?['temporaryDownloadUrl']}` — a URL **absoluta**, sem cortar |
> | Autenticação | **nenhuma** |
>
> 🎯 **Repare que não precisa de credencial.** A `temporaryDownloadUrl` carrega o próprio `tempauth`, então a ação não precisa de conexão, de conta de serviço, nem de consentimento de administrador. É o motivo de esta ser a saída mais limpa, se a licença permitir.
>
> Se a ação HTTP também não seguir o redirecionamento, o `302` aparece na **saída** dela com o cabeçalho `Location` — e aí basta um segundo `HTTP` GET nesse endereço.
>
> ⚠️ **`HTTP` é conector premium.** Para saber se você tem: procure "HTTP" em Adicionar ação; se aparecer com a etiqueta *Premium* e deixar adicionar, teste. Se a execução falhar por licença, a mensagem diz isso explicitamente.
>
> ### Se não houver premium
>
> A Rota A2 deste guia (arrastar a transcrição manualmente para a pasta do SharePoint) continua valendo como plano de contenção — a automação para no download, não antes. Todo o resto do fluxo, do gatilho até a listagem, já está montado e funcionando.

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
> 2. Use os nomes deste guia: `Caminho`, `Listar transcricoes`, `UrlTranscricao`, `Baixar transcricao`, `Linhas`, `Falas`, `TextoLimpo`
> 3. **Antes de rodar, faça a conferência cruzada:** para cada `body('X')` / `outputs('X')` do fluxo, existe uma ação chamada exatamente `X`? É um minuto e evita a maioria das execuções vermelhas

> ## ✅ O formato: VTT, e **sem marcação de locutor**
>
> Confirmado em execução real, 21/08. O `streamContent` devolve **VTT**, com esta cara:
>
> ```
> WEBVTT
>
> <guid-do-bloco>/5-0                ← identificador do bloco
> 00:00:03.380 --> 00:00:04.020      ← timestamp
> Vou ver o que acontece,            ← a fala, sem marcação nenhuma
> fazer o teste                      ← um bloco pode ter mais de uma linha
> ```
>
> ⚠️ **O `displayName` do item termina em `.json` e isso é pista falsa.** Este guia previu JSON por causa dele e errou. A extensão no `displayName` não diz o que o `streamContent` entrega.
>
> ### 🔴 Não vem `<v Nome>`
>
> Um VTT do Teams *pode* trazer o locutor marcado como `<v Nome Sobrenome>fala</v>`. **O que vem por este endpoint não traz.** Nenhuma linha do arquivo tem essa marcação.
>
> Consequência direta: **perde-se quem disse o quê**, e sobra o texto corrido da reunião. Para a busca semântica do agente isso serve; para cobrar alguém pelo que disse na LT, não. Ver *Atribuição de locutor*, no fim desta rota.
>
> É por isso que os passos 8 a 11 abaixo **não** procuram marcação — eles descartam o que não é fala.

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
@and(not(empty(item())), not(equals(item(), 'WEBVTT')), not(contains(item(), '-->')), or(contains(item(), ' '), not(contains(item(), '/'))))
```

**A lógica é invertida de propósito.** Sem marcação de locutor não há como dizer o que *é* fala — então o filtro descarta o que comprovadamente **não é**:

| Regra | Descarta | Exemplo |
|---|---|---|
| `not(empty(…))` | as linhas em branco entre blocos | `""` |
| `not(equals(…, 'WEBVTT'))` | o cabeçalho | `WEBVTT` |
| `not(contains(…, '-->'))` | os timestamps | `00:00:03.380 --> 00:00:04.020` |
| `or(contains(' '), not(contains('/')))` | os identificadores de bloco | `<guid>/5-0` |

A última precisa de explicação: identificador tem `/` e **nenhum espaço**; fala quase sempre tem espaço. A regra guarda a linha se ela tem espaço **ou** se não tem `/` — o que preserva falas curtas como `Eita.`

> ⚠️ **Limite conhecido:** uma linha que seja *só* uma data — `08/05` sozinha — cai fora. Uma data no meio de uma frase (`vamos rever em 08/05 o Go-Live`) fica, porque tem espaço. Raro o bastante para não valer regra mais complicada.

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
| Mensagem | `Filtro nao achou linhas de fala — conferir a saida do download` |

> 🔴 **Não pule este passo, e não deixe o ramo "Se não" vazio.**
>
> Sem a condição, se o passo 6 não devolver VTT o filtro não acha nada e o fluxo **grava um arquivo vazio no SharePoint sem dar erro**.
>
> Com a condição mas **sem o Encerrar**, o arquivo vazio deixa de ser gravado ✅ — mas o fluxo termina com status **Sucesso**, verde no histórico. Você não fica sabendo.
>
> **A guarda tem duas metades:** impedir o arquivo ruim, e te avisar. Ramo falso vazio entrega só a primeira.

### Passo 10 — *(não existe mais)*

> 🗑️ **Aqui havia um `Selecionar` chamado `Limpar`**, que tirava `<v `, `</v>` e trocava `>` por `: ` para produzir `Nome: fala`.
>
> Como o VTT deste endpoint não traz marcação nenhuma, ele não tem o que limpar. **Se você já criou essa ação, apague** — e ajuste o passo 11, que a referenciava.
>
> Ele volta a fazer sentido no dia em que aparecer um endpoint com locutor. Ver *Atribuição de locutor*, no fim da rota.

### Passo 11 — juntar de volta

**Operações de dados → Compor**, nome `TextoLimpo`:

```
join(body('Falas'), decodeUriComponent('%0A'))
```

> ⚠️ `Falas` é **o nome da sua ação Filtrar matriz**. Se você a chamou de outra coisa, use o nome real — referência que não casa derruba o fluxo na execução.

> 📌 Um bloco do VTT pode ter mais de uma linha de fala, e o `join` mantém isso quebrado. O arquivo sai com algumas frases partidas em duas linhas. Não atrapalha a busca semântica — mas é bom saber antes de estranhar.

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

> ## 🎙️ Atribuição de locutor — o que ficou de fora, e como buscar
>
> **Estado:** o arquivo gravado tem o texto da reunião, **sem identificar quem falou**. O VTT que o `streamContent` devolve não traz `<v Nome>`, e a informação não está em lugar nenhum do arquivo — não é questão de expressão, é ausência de dado.
>
> **O que se perde:** o agente consegue responder *"o que foi dito sobre o Horizon 2"*, mas não *"quem se comprometeu com a data"*. Para a cobrança do §7 das instruções, o segundo é o que vale.
>
> **Por que ainda dá para buscar:** o player do Stream **mostra os nomes** na aba de transcrição. Se ele mostra, existe um endpoint que os entrega.
>
> **Método** — o mesmo que resolveu o `driveId` e a URL de download, e funcionou nas duas vezes:
>
> 1. Abra a gravação no Stream e mostre o painel de transcrição
> 2. **DevTools → Network**, e filtre por `transcript`
> 3. Ache a chamada cujo corpo traz os nomes, e compare com o `streamContent` que o fluxo usa hoje — provavelmente é o mesmo endereço com outro parâmetro de formato, ou um endpoint irmão
> 4. Se o corpo for JSON com campos de locutor, o passo 8 vira `Analisar JSON` e o passo 10 (`Limpar`) volta a existir, montando `Nome: fala`
>
> **Prioridade: depois do fluxo rodar.** Isto é melhoria, não bloqueio — o texto corrido já alimenta a busca semântica, e é melhor ter a LT sendo capturada toda semana do que esperar a versão perfeita.

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

## Como ler o erro: ele quase nunca está onde aparece

Numa execução vermelha o Power Automate costuma marcar **várias** ações. Isso raramente são vários problemas — normalmente é um só, com ecos. Duas regras que economizam rodadas:

**1. `ActionFailed` numa Condição não é a Condição.**

```
ActionFailed. An action failed. No dependent actions succeeded.
```

É mensagem de **contêiner**: a expressão da própria Condição avaliou bem, e o que falhou foi alguma ação **dentro** dela. Se o problema fosse a expressão, a mensagem seria `InvalidTemplate`. Essa linha te manda olhar para os filhos — e, de quebra, **confirma que os campos usados na condição estão certos**.

**2. `InvalidTemplate … type 'Null'` acusa quem *usou* o valor, não quem o produziu.**

Quem leu o campo inexistente ficou verde, com `Null` dentro. Suba uma casa na cadeia antes de mexer em qualquer coisa.

**3. `first parameter` quer dizer o primeiro argumento — conte-os.**

A mensagem nomeia **qual** argumento está errado, e é fácil corrigir o argumento vizinho sem perceber:

```
replace(  A ,  B ,  C  )
          │    │    └─ pelo quê trocar
          │    └────── o que procurar
          └─────────── onde procurar     ← 'first parameter'
```

Se o erro diz `'replace' expects its first parameter 'string' to be a string`, o problema é **`A`**. Mexer em `B` — trocar `/Documents` por `/Recordings`, por `/` — devolve exatamente o mesmo erro, quantas vezes você tentar, porque `A` continua nulo. Vale para qualquer função: leia qual parâmetro a mensagem cita antes de editar.

Foi assim que este fluxo apresentou três ações vermelhas de uma vez, em 21/08:

| Ação | Mensagem | O que era |
|---|---|---|
| `Caminho` | `'replace' expects … 'string' … type 'Null'` | 🔴 **a causa** — leitura de um campo de caminho que não existe no gatilho |
| `Do until` | `'length' expects … an array or a string … type 'Null'` | eco: sem caminho, a chamada não devolve corpo |
| `Condition` | `ActionFailed. An action failed.` | agregado dos dois de cima |

Uma correção só apagou as três — e a correção certa acabou sendo **parar de ler aquele campo**, montando o caminho a partir do `Name` (passo 2).

## Erros que você provavelmente vai encontrar

| Erro | Onde | O que é |
|---|---|---|
| `403 Forbidden` na listagem | Passo 4 | Application Access Policy não aplicada, ainda propagando, ou "Transcript API access" bloqueado no Teams |
| `value` vazio | Passo 3 | O `JoinWebUrl` não bateu exatamente — compare caractere a caractere |
| `404` na transcrição | Passo 5 | A reunião não teve transcrição ligada. **Ligue a transcrição automática na política de reunião** |
| `Filtrar matriz` volta **vazio** | Passo 8 | O VTT deste endpoint **não tem `<v Nome>`**. Use o filtro por exclusão do passo 8, não a busca por marcação |
| Arquivo com timestamps | Passo 8 | O Filtrar matriz não pegou — confira se está em **modo avançado**, e se a regra do `-->` está lá |
| `endsWith … expects … string … provided value is of type 'Null'` | Condição | **Gatilho errado.** `OnNewFileV2` devolve o conteúdo do arquivo, não as propriedades — troque por "(somente propriedades)" |
| `'replace' expects … 'string' … type 'Null'` | Passo 2 | **O campo de caminho não existe com o nome usado.** Não tente outro nome: monte o caminho com `concat('/Recordings/', body/Name)`, ou endereço por `Id`. E confira se você não está editando o argumento errado — ver "Como ler o erro" |
| `'length' expects … an array or a string … type 'Null'` | Passo 3 | Ou o `Caminho` saiu vazio (linha acima), ou falta o `coalesce` na condição do `Do until` |
| `ActionFailed. An action failed.` numa Condição | qualquer | **Não é a Condição.** É mensagem agregada — falhou uma ação dentro dela. Se fosse a expressão, seria `InvalidTemplate` |
| `400` na chamada do passo 3 | Passo 2 | Espaço no nome do arquivo entrou cru na URI. Falta o `replace(…, ' ', '%20')` |
| `400` + `Unexpected response from the service` | Passo 6 | `source` é o **conector**, não o SharePoint. Com a URL já correta, a causa é **o tipo da resposta**: o conector do SharePoint não segue o redirecionamento do `streamContent`. Ver o bloco do passo 6 — teste no DevTools, cabeçalho `Accept`, ou a ação `HTTP` |
| `Compose` verde mas o passo seguinte quebra | qualquer | Compose com `null` fica verde. Abra a **saída** de cada Compose da cadeia; o primeiro vazio é a causa |
| Campo do gatilho sempre vazio | qualquer | O nome não existe nesse conector. Rode uma vez, abra a saída do gatilho e use o nome real |
| **Só aparece `.mp4` na pasta** | Rota A | **É o comportamento normal.** A transcrição é anexo do vídeo, não arquivo solto. É dela que os passos 3 e 5 vão buscar |
| `The template language expression ... cannot be evaluated` | qualquer passo | Uma referência `body('X')`/`outputs('X')` aponta para ação que **não existe com esse nome**. Confira os nomes das ações contra as referências |
| O `Do until` termina em segundos | Passo 3 | **Falta o `Delay` dentro do loop.** "Tempo limite" é teto de duração, não ritmo — sem Delay, as 60 iterações queimam de uma vez |
| Arquivo gravado **vazio** no SharePoint | Passo 9 | A guarda não foi criada, e o passo 6 não devolveu VTT. Abra a saída do passo 6 e veja o que realmente voltou |
| `Do until` aborta na 1ª volta | Passo 3 | A chamada falhou (404 de "ainda não pronto") e derrubou o loop. Marque **com falha** em Configurar execução após |
| **Fluxo verde, mas nada foi gravado** | Passo 9 | O ramo "Se não" da guarda está **vazio**. Sem o `Encerrar`, o fluxo termina em sucesso e o problema fica invisível |
| **Fluxo verde, e a transcrição nunca chegou** | Passo 4 | Um `Do until` que estoura o limite termina em **sucesso**, não falha. Falta a condição pós-loop |
| `404` no passo 6, com o passo 3 tendo funcionado | Passo 5 | A URL saiu vazia — quase sempre é o nome da ação não batendo com `outputs('UrlTranscricao')` |
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
- [ ] **Compose de diagnóstico rodado uma vez** — `triggerOutputs()` puro, para ler os nomes de campo reais em vez de adivinhar
- [ ] **Saída de cada Compose conferida** — verde não basta; o `UrlTranscricao` precisa ter uma URL de verdade dentro
- [ ] **Status da `temporaryDownloadUrl` verificado no DevTools** — 302 ou 200? decide entre cabeçalho `Accept` e a ação `HTTP`
- [ ] Arquivo chegou como `LT-AAAA-MM-DD.txt`, sem timestamps, no formato `Locutor: fala`
- [ ] Fonte de conhecimento apontando para a biblioteca, **com a descrição colada**
- [ ] Teste no agente: `o que foi decidido na LT sobre <projeto>?` — tem que responder da transcrição, sem rodar query

O último item é o que prova o circuito inteiro.
