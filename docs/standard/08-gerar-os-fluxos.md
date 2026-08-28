# 8. Gerar os fluxos das quatro áreas

> Este guia parte do fluxo **já validado em campo**. Se você ainda está montando o primeiro, comece por [`06-fluxo-transcricoes.md`](06-fluxo-transcricoes.md) — aqui só se trata de **replicar** o que já funciona para outras contas.

## Por que um gerador, e não copiar e colar

São **quatro reuniões de área** em **duas contas de OneDrive**. Cada fluxo muda em cinco pontos, e três deles são strings longas onde um caractere errado vira um `400` que parece outra coisa:

| Muda por conta | |
|---|---|
| `dataset` | o OneDrive de quem organiza |
| `driveId` | dentro da URI do passo 3 |
| `folderId` | `driveId.itemId` da pasta de gravações |
| pasta em `Caminho` | `Recordings` / `Gravações` / `Grabaciones` |
| palavras-chave do `Area` | as duas áreas daquela pessoa, mais a âncora |

O `scripts/gerar-fluxo.py` recebe esses cinco valores num JSON e cospe um pacote de importação pronto. O que **não** muda — espera, listagem, download, limpeza, gravação — vem sempre igual, porque vem do mesmo código.

## Como gerar

```bash
cp flows/config-exemplo.json /tmp/config-pessoa.json   # fora do repositório
# preencha os cinco valores
python3 scripts/gerar-fluxo.py /tmp/config-pessoa.json /tmp/fluxo-pessoa.zip
```

O script imprime a expressão do `Area` que montou. **Leia antes de importar** — é a única parte que depende de convenção humana.

> ## 🔎 Antes de gerar: leia um nome de arquivo real
>
> Abra a pasta `Recordings` e olhe os nomes que já estão lá — inclusive os das reuniões que **não** são LT. Dez segundos, e confirma o que de outro modo é suposição: como o título entra no nome do arquivo, e o que mais mora naquela pasta.
>
> **É lá que você escolhe a âncora.** O `prefixoObrigatorio` tem que ser um trecho que **só as LT têm** — nas quatro do CDIO LATAM, `leadership meeting`.

## 🔴 Palavra-chave curta é armadilha

Um `contains` solto pega mais do que você quer:

| Nome do arquivo | Só a palavra da área | Com a âncora |
|---|---|---|
| `BPC Leadership Meeting - CD-…` | CD ✅ | CD ✅ |
| `CDIO Sync Semanal-…` | **CD** 🔴 | (nenhuma) ✅ |
| `Make roadmap review-…` | **Make** 🔴 | (nenhuma) ✅ |
| `1:1 com o CD lead-…` | **CD** 🔴 | (nenhuma) ✅ |

**`cd` cabe dentro de `cdio`.** E o estrago é do pior tipo: a reunião errada seria baixada, limpa e gravada como `LT-CD-AAAA-MM-DD-HHmm.txt` na pasta que o agente indexa — **indistinguível de uma LT real**, sem nenhum passo do fluxo ficar vermelho.

O `prefixoObrigatorio` fecha isso: cada área vira `and(contains(nome, <âncora>), <palavra da área>)`.

**Ancore no trecho estável, não na string exata.** `leadership meeting`, e não `leadership meeting - cd` — o separador no nome do arquivo pode não ser exatamente ` - `. A precisão vem da combinação de duas condições, não de acertar um formato que você não viu.

> 🔒 O config preenchido e o `.zip` gerado carregam UPN, `driveId` e GUID de biblioteca reais. O `.gitignore` já os exclui; não force o commit.

## Como importar

**Power Automate → Meus fluxos → Importar → Importar Pacote (herdado)** e suba o `.zip`.

Na tela de importação:

| Recurso | O que fazer |
|---|---|
| O fluxo | já vem como **Criar como novo** — não sobrescreve nada |
| Conexão do **OneDrive** | 🔴 tem que ser a **do dono do drive** |
| Conexão do **SharePoint** | a dele também, se ele escrever na pasta de destino; senão, a sua |

## Depois de importar — três coisas manuais

**1. Reescolher a pasta no gatilho.** O `folderId` é `driveId.itemId`, e o `itemId` da pasta só existe naquele drive — o pacote vem com um marcador. Abra o gatilho e selecione a pasta de gravações. É esse clique que também prova que a conexão enxerga a pasta.

**2. Conferir o nome da pasta.** O `Caminho` tem o nome **fixo no texto**. Se o seletor mostrar `Grabaciones` e o `Caminho` disser `/Recordings/`, o passo 3 volta `400`. Ajuste o `Caminho`, ou regenere com o `pastaGravacoes` certo.

**3. Ligar o fluxo.** Ele nasce desligado.

## Como testar sem envolver ninguém

O classificador olha o **nome do arquivo**, que o Teams tira do **título da reunião**. E a regra é `contains`, não igualdade:

> O título do teste **não precisa ser igual** ao da reunião real, mas precisa conter a **âncora** e a palavra da área. Com a âncora `leadership meeting`, um teste chamado `BPC Leadership Meeting - Make teste` vira `Make`; um chamado só `Make teste` **não entra** — e está certo assim, é a mesma regra que impede a reunião errada de virar transcrição de LT.

Isso libera testar numa reunião nova, sem tocar nas recorrentes e sem convidar ninguém — reunião sozinho, com transcrição ligada, gera transcrição.

**Mas a gravação cai no OneDrive de quem clica em gravar.** Então testar o fluxo do William exige que **ele** grave. Para validar a estrutura antes de envolver alguém, gere um pacote apontando para o **seu próprio** OneDrive, com as quatro áreas na lista, e teste sozinho. O que você valida ali — classificador, guardas, `Tolera`, nome do arquivo — é idêntico ao que vai rodar na conta deles.

> 🔴 **Apague o `.txt` de teste depois.** O nome de saída guarda só a **área**, não o título: um teste vira `LT-Make-AAAA-MM-DD-HHmm.txt`, indistinguível de uma LT de verdade. E a pasta de destino é justamente a que o agente indexa — uma transcrição de teste ali faz o agente responder bobagem sobre a LT de Make.
>
> Se preferir não correr esse risco, aponte o `pastaDestino` para uma pasta de teste enquanto valida, e devolva depois.

## O teste de aceite, em três gravações

| # | O que gravar | O que tem que acontecer |
|---|---|---|
| 1 | Reunião chamada `LT Make teste` | Sai `LT-Make-AAAA-MM-DD-HHmm.txt` na pasta de destino |
| 2 | Reunião com nome qualquer, sem área | 🎯 Fluxo **verde, sem fazer nada** — não vermelho |
| 3 | Reunião de área, **sem transcrição ligada** | Vermelho com `TranscricaoNaoFicouPronta` |

O teste 2 é o que mais importa e o menos óbvio. A pasta observada é a de gravações **pessoal** do organizador, onde cai toda reunião que ele grava. Se essas terminassem vermelhas, o histórico viraria uma parede de vermelho normal — e aí vermelho deixa de significar que algo quebrou.

## O que o pacote já resolve, e que o fluxo original não tinha

| | Por quê |
|---|---|
| `Area` como **fonte única** das palavras-chave | a condição de entrada só checa se ele resolveu; não há dois lugares para manter sincronizados |
| `Tolera` dentro do `Do until` | enquanto a transcrição processa, a API responde `404`. Sem essa ação, o filho falhado derruba o loop na primeira volta e a espera nunca acontece |
| `Encerrar` nos dois ramos falsos | guarda tem duas metades: impedir o arquivo ruim **e** avisar. Ramo vazio entrega só a primeira |
| Nome com `HHmm` | duas gravações no mesmo dia colidiriam |
| `Compose_3` e `Diagnostico` removidos | o `Passo_5` usa a URL absoluta direto; os dois eram resíduo da depuração |

## Quando isso tudo deixa de ser necessário

Se as quatro LT virarem **reuniões de canal de canais do mesmo time**, a gravação nasce no SharePoint do time. Um gatilho de SharePoint, **um fluxo só**, e a pasta já é a área: sem `driveId`, sem convenção de nome, sem conexão de terceiro, e o acervo não vai embora quando alguém sai da empresa.
