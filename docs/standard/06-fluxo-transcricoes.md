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
| Risco | a URL varia por tenant; precisa confirmar no DevTools | nenhum | aprovações demoram |
| Tempo para montar | ~40 min | ~15 min | ~2h + espera |

> 🎯 **Ordem recomendada: monte a A2 primeiro, a A depois.**
>
> A A2 leva 15 minutos e funciona garantido — a LT da próxima semana já entra no SharePoint. Com isso resolvido, você valida a Rota A sem pressa e sem risco de ficar sem nada no meio do caminho.
>
> A Rota B só entra se você precisar varrer reuniões de muita gente diferente.

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
>         │  passos 1–5: gatilho no .mp4 · esperar · identificar · listar · baixar o VTT
>         ▼
>    limpeza (passos 6–9) — só texto, não toca em arquivo
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

> ### 🔑 Por que a ação "…para o SharePoint" funciona num arquivo do OneDrive
>
> Porque **OneDrive for Business é um site SharePoint por baixo**. O endereço dele é:
>
> ```
> https://<tenant>-my.sharepoint.com/personal/<upn com _ no lugar de . e @>
> ```
>
> Exemplo: `nicolas.kuhnast@unilever.com` → `.../personal/nicolas_kuhnast_unilever_com`
>
> Então nos passos 4 e 5, o campo **"Endereço do site"** recebe **esse endereço do OneDrive**, não o do site de equipe. Não é gambiarra — é o mesmo produto.
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

> ### 🎯 Antes de tudo: pegue a URL real do seu tenant
>
> Eu confirmei a **forma** do endpoint, mas não consigo testar no seu ambiente. Em vez de você depender de eu ter acertado, leia a URL do seu próprio navegador — leva 30 segundos e é verdade de campo:
>
> 1. Abra a gravação no Stream, com o painel **Transcrição** aberto
> 2. **F12** → aba **Rede** (Network) → filtre por `transcripts`
> 3. Recarregue a página
> 4. A chamada que aparecer é **a URL exata**, com `driveId` e `itemId` reais do seu tenant
>
> Guarde essa URL. Ela é o molde dos passos 4 e 5, e é mais confiável do que qualquer coisa que eu escreva aqui.

**Power Automate → Criar → Fluxo de nuvem automatizado**

### Gatilho

**OneDrive for Business → Quando um arquivo é criado (somente propriedades)**

| Campo | Valor |
|---|---|
| Pasta | `/Gravações` (ou `/Recordings`, conforme o idioma da conta) |

É **OneDrive**, não SharePoint — a gravação de reunião agendada cai no OneDrive do organizador.

> ⚠️ O gatilho roda na conta de **quem conectar o OneDrive** — precisa ser a do organizador da LT. Se o organizador mudar, o fluxo para de enxergar os arquivos. Ver a nota sobre reunião de canal no fim desta rota.

### Passo 1 — só o `.mp4`

**Controle → Condição**:

```
endsWith(triggerOutputs()?['body/Name'], '.mp4')
```

é igual a `true`. Todo o resto vai no ramo **Se sim**.

> 📌 Repare que é o **oposto** do que faria sentido à primeira vista. Não existe `.vtt` na pasta para filtrar — o `.mp4` é o item que **carrega** a transcrição, e é dele que vamos pedi-la.

### Passo 2 — esperar a transcrição ficar pronta

**Controle → Atraso** — 10 minutos.

O `.mp4` aparece na pasta **antes** de a transcrição terminar de processar. Sem essa espera, o passo 4 volta lista vazia e o fluxo "funciona" sem trazer nada.

> Se 10 minutos não bastarem no seu caso, o certo não é aumentar o número no chute: use **Controle → Do until**, repetindo o passo 4 até `length(body('Passo_4')?['value'])` ser maior que zero, com limite de tentativas.

### Passo 3 — identificar o vídeo

**OneDrive for Business → Obter metadados do arquivo**

| Campo | Valor |
|---|---|
| Arquivo | `Identificador` do gatilho |

Também **OneDrive**, pela mesma razão do gatilho: é lá que o arquivo está.

É daqui que saem os identificadores para montar a URL dos passos 4 e 5. Compare com a URL do DevTools — se o formato não bater, o molde do DevTools manda.

### Passo 4 — listar as transcrições do vídeo

**SharePoint → Enviar uma solicitação HTTP para o SharePoint**

| Campo | Valor |
|---|---|
| Endereço do site | 🔑 **o OneDrive**: `https://<tenant>-my.sharepoint.com/personal/<upn>` |
| Método | `GET` |
| URI | `_api/v2.1/drives/{driveId}/items/{itemId}/media/transcripts` |

> 📌 Aqui está a parte que confunde: a ação chama "…para o **SharePoint**", mas o endereço é o do **OneDrive**. Está certo — OneDrive é um site SharePoint. Use o host que aparecer no DevTools.

Devolve um JSON com a lista. **Compor** `TranscriptId`:

```
last(body('Passo_4')?['value'])?['id']
```

Pego a **última** de propósito: se a transcrição foi reiniciada no meio da reunião, a última é a completa.

### Passo 5 — baixar o VTT

**SharePoint → Enviar uma solicitação HTTP para o SharePoint**

| Campo | Valor |
|---|---|
| Endereço do site | o mesmo do passo 4 — **o OneDrive** |
| Método | `GET` |
| URI | `_api/v2.1/drives/{driveId}/items/{itemId}/media/transcripts/@{outputs('TranscriptId')}/streamContent?format=text/vtt` |

O corpo da resposta é o `.vtt` cru — o mesmo texto que você vê no painel lateral.

> ✅ **Este é o passo que decide tudo.** Se ele devolver o VTT, o resto é encanamento: os passos seguintes são os mesmos de qualquer transcrição em texto. Se devolver erro, teste a URL do DevTools direto antes de mexer em qualquer outra coisa.

### Passo 6 — quebrar em linhas

**Operações de dados → Compor**, nome `Linhas`:

```
split(replace(string(body('Passo_5')), decodeUriComponent('%0D'), ''), decodeUriComponent('%0A'))
```

O `decodeUriComponent('%0D')` é `\r` e o `%0A` é `\n`. O Power Automate não aceita `\n` literal numa expressão — é por isso desse jeito.

### Passo 7 — jogar fora tudo que não é fala

**Operações de dados → Filtrar matriz**

| Campo | Valor |
|---|---|
| De | `outputs('Linhas')` |

Condição, em **modo avançado**:

```
@contains(item(), '<v ')
```

**Por que só isso basta:** num `.vtt`, só as linhas de fala têm a marcação de locutor `<v Nome>`. O cabeçalho `WEBVTT`, os identificadores de bloco, os timestamps `00:00:05.123 --> 00:00:08.456` e as linhas em branco **não têm** — e caem todos de uma vez.

### Passo 8 — limpar a marcação

**Operações de dados → Selecionar**

| Campo | Valor |
|---|---|
| De | `body('Filtrar_matriz')` |
| Mapear | modo texto (ícone à direita), com a expressão abaixo |

```
replace(replace(replace(item(), '<v ', ''), '</v>', ''), '>', ': ')
```

O que acontece com uma linha:

```
<v Nicolas Kuhnast>Precisamos rever o Go-Live do Horizon 2</v>
   ↓  tira '<v '
Nicolas Kuhnast>Precisamos rever o Go-Live do Horizon 2</v>
   ↓  tira '</v>'
Nicolas Kuhnast>Precisamos rever o Go-Live do Horizon 2
   ↓  troca '>' por ': '
Nicolas Kuhnast: Precisamos rever o Go-Live do Horizon 2
```

> ⚠️ **Limitação honesta:** o `replace` troca **todas** as ocorrências. Se alguém falar algo com `>` no meio, aquela linha sai torta. Na prática é raro em transcrição de voz, e o custo de tratar isso direito não compensa — mas é bom você saber que existe.

### Passo 9 — juntar de volta

**Operações de dados → Compor**, nome `TextoLimpo`:

```
join(body('Selecionar'), decodeUriComponent('%0A'))
```

### Passo 10 — gravar no SharePoint 🎯 **aqui muda de lugar**

Até agora tudo aconteceu na **origem** (OneDrive). Deste passo em diante é o **destino**: o site de equipe do CDIO LATAM, que é o que o agente enxerga.

**SharePoint → Criar arquivo**

| Campo | Valor |
|---|---|
| Endereço do site | 🎯 **o site do CDIO LATAM** — `https://<tenant>.sharepoint.com/sites/<CDIO-LATAM>`, **não** o OneDrive dos passos 4 e 5 |
| Caminho da pasta | `/Transcricoes LT` |
| Nome do arquivo | expressão abaixo |
| Conteúdo do arquivo | `outputs('TextoLimpo')` |

```
concat('LT-', formatDateTime(triggerOutputs()?['body/LastModified'], 'yyyy-MM-dd'), '.txt')
```

Resultado: `LT-2026-08-19.txt`.

> 🎯 **A data no nome não é enfeite.** É como o agente responde "o que foi decidido na LT de agosto" — a busca semântica lê o nome do arquivo junto com o conteúdo. Nome genérico como `transcricao.txt` derruba a precisão.

### Passo 11 — preencher as colunas

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
| **Só aparece `.mp4` na pasta** | Rota A | **É o comportamento normal.** A transcrição é anexo do vídeo, não arquivo solto. É dela que os passos 4 e 5 vão buscar |
| Lista de transcrições vazia | Passo 4 | Ou a transcrição ainda está processando (aumente o atraso do passo 2), ou a reunião não teve transcrição ligada |
| `403` ou `404` na chamada HTTP | Passos 4–5 | A URL não bate com a do seu tenant. Compare com a que você pegou no DevTools |
| Gatilho não dispara | Rota A | A pasta pode chamar `Recordings` em vez de `Gravações`, conforme o idioma da conta |
| Fluxo roda 2x | Rota A | O `.vtt` e o `.docx` caem os dois. A condição do Passo 1 já resolve |

## Checklist

- [ ] URL real capturada no DevTools (F12 → Rede → `transcripts`)
- [ ] Chamada do passo 5 devolvendo o VTT cru — **é o portão, teste isolado antes do resto**
- [ ] Biblioteca `Transcricoes LT` criada, com as colunas `DataReuniao` e `Origem`
- [ ] Fluxo criado e testado numa reunião de teste, com transcrição ligada
- [ ] Arquivo chegou como `LT-AAAA-MM-DD.txt`, sem timestamps, no formato `Locutor: fala`
- [ ] Fonte de conhecimento apontando para a biblioteca, **com a descrição colada**
- [ ] Teste no agente: `o que foi decidido na LT sobre <projeto>?` — tem que responder da transcrição, sem rodar query

O último item é o que prova o circuito inteiro.
