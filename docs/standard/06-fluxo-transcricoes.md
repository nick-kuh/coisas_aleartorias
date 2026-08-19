# 6. Fluxo do Power Automate — transcrição da LT no SharePoint

Objetivo: a cada reunião de LT, a transcrição chega sozinha na biblioteca do SharePoint, limpa e nomeada de forma que o AURA consiga usá-la.

---

## Antes de escolher o caminho: onde o Teams já guarda

O Teams **já salva a transcrição sozinho**, sem nenhum fluxo. Onde depende do tipo de reunião:

| Tipo de reunião | Onde a transcrição cai |
|---|---|
| Reunião agendada / privada | **OneDrive do organizador** → pasta `Gravações` (`Recordings`) |
| Reunião de canal | **SharePoint do canal** → `Documentos/Gravações` |

Formato: **`.vtt`** (WebVTT — texto com marcação de tempo). Alguns tenants também geram `.docx`.

Isso muda tudo, porque significa que **existe um caminho sem precisar de admin nenhum**.

---

## As duas rotas

| | **Rota A — arquivo** | **Rota B — Graph API** |
|---|---|---|
| Como pega | observa a pasta onde o Teams já salvou | chama a API e baixa a transcrição |
| Precisa de admin? | **Não** | **Sim** — consentimento + policy + config do Teams |
| Pega ID de reunião/transcrição? | não precisa | sim |
| Funciona se o organizador variar? | só na pasta observada | sim |
| Tempo para montar | ~20 min | ~2h + espera do admin |

> 🎯 **Recomendação: comece pela Rota A.** Ela resolve o caso da LT quinzenal, que tem organizador fixo e cadência fixa. A Rota B só ganha se você precisar varrer reuniões de várias pessoas — e ela depende de aprovações que, pelo histórico do Bloco 0, demoram.

---

# Rota A — sem admin, observando a pasta

## A1. Preparar o destino no SharePoint

1. No site do CDIO LATAM → **Novo → Biblioteca de documentos**
2. Nome: **`Transcricoes LT`**
3. Dentro dela, **+ Adicionar coluna**:

| Coluna | Tipo | Para quê |
|---|---|---|
| `DataReuniao` | Data | permite o agente dizer "na LT de 12/08…" |
| `Origem` | Texto | `Teams` — distingue do que for subido à mão |

## A2. Criar o fluxo

**Power Automate → Criar → Fluxo de nuvem automatizado**

### Gatilho

**OneDrive for Business → Quando um arquivo é criado (somente propriedades)**

| Campo | Valor |
|---|---|
| Pasta | `/Gravações` (ou `/Recordings`, conforme o idioma da conta) |

> ⚠️ O gatilho roda na conta de **quem conectar o OneDrive** — precisa ser a do organizador da LT. Se o organizador mudar, o fluxo para de ver os arquivos.

### Passo 1 — filtrar só transcrição

**Controle → Condição**

```
endsWith(triggerOutputs()?['body/Name'], '.vtt')
```

é igual a `true`. Todo o resto do fluxo vai no ramo **Se sim**.

Isso descarta o `.mp4` da gravação, que cai na mesma pasta.

### Passo 2 — ler o conteúdo

**OneDrive for Business → Obter conteúdo do arquivo**

| Campo | Valor |
|---|---|
| Arquivo | `Identificador` do gatilho |

### Passo 3 — quebrar em linhas

**Operações de dados → Compor**, nome `Linhas`:

```
split(replace(string(body('Obter_conteúdo_do_arquivo')), decodeUriComponent('%0D'), ''), decodeUriComponent('%0A'))
```

O `decodeUriComponent('%0D')` é `\r` e o `%0A` é `\n`. O Power Automate não aceita `\n` literal numa expressão — é por isso desse jeito.

### Passo 4 — jogar fora tudo que não é fala

**Operações de dados → Filtrar matriz**

| Campo | Valor |
|---|---|
| De | `outputs('Linhas')` |

Condição, em **modo avançado**:

```
@contains(item(), '<v ')
```

**Por que só isso basta:** num `.vtt`, só as linhas de fala têm a marcação de locutor `<v Nome>`. O cabeçalho `WEBVTT`, os identificadores de bloco, os timestamps `00:00:05.123 --> 00:00:08.456` e as linhas em branco **não têm** — e caem todos de uma vez.

### Passo 5 — limpar a marcação

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

### Passo 6 — juntar de volta

**Operações de dados → Compor**, nome `TextoLimpo`:

```
join(body('Selecionar'), decodeUriComponent('%0A'))
```

### Passo 7 — gravar no SharePoint

**SharePoint → Criar arquivo**

| Campo | Valor |
|---|---|
| Endereço do site | o site do CDIO LATAM |
| Caminho da pasta | `/Transcricoes LT` |
| Nome do arquivo | expressão abaixo |
| Conteúdo do arquivo | `outputs('TextoLimpo')` |

```
concat('LT-', formatDateTime(triggerOutputs()?['body/LastModified'], 'yyyy-MM-dd'), '.txt')
```

Resultado: `LT-2026-08-19.txt`.

> 🎯 **A data no nome não é enfeite.** É como o agente responde "o que foi decidido na LT de agosto" — a busca semântica lê o nome do arquivo junto com o conteúdo. Nome genérico como `transcricao.txt` derruba a precisão.

### Passo 8 — preencher as colunas

**SharePoint → Atualizar propriedades do arquivo**

| Campo | Valor |
|---|---|
| Id | `ItemId` do passo anterior |
| DataReuniao | `formatDateTime(triggerOutputs()?['body/LastModified'], 'yyyy-MM-dd')` |
| Origem | `Teams` |

## A3. Ligar no agente

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

Reaproveite os **passos 3 a 8 da Rota A** (quebrar em linhas, filtrar `<v `, limpar, juntar, gravar no SharePoint), trocando só a origem do texto: em vez de `body('Obter_conteúdo_do_arquivo')`, use `body('Passo_5')`.

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
| Arquivo com timestamps | Passo 7 | O Filtrar matriz não pegou — confira se está em **modo avançado** com `@contains(item(), '<v ')` |
| Gatilho não dispara | Rota A | A pasta pode chamar `Recordings` em vez de `Gravações`, conforme o idioma da conta |
| Fluxo roda 2x | Rota A | O `.vtt` e o `.docx` caem os dois. A condição do Passo 1 já resolve |

## Checklist

- [ ] Biblioteca `Transcricoes LT` criada, com as colunas `DataReuniao` e `Origem`
- [ ] Fluxo criado e testado numa reunião de teste, com transcrição ligada
- [ ] Arquivo chegou como `LT-AAAA-MM-DD.txt`, sem timestamps, no formato `Locutor: fala`
- [ ] Fonte de conhecimento apontando para a biblioteca, **com a descrição colada**
- [ ] Teste no agente: `o que foi decidido na LT sobre <projeto>?` — tem que responder da transcrição, sem rodar query

O último item é o que prova o circuito inteiro.
