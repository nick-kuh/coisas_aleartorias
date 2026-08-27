# Pacotes de importação do fluxo de transcrições

Este diretório guarda o **modelo** de configuração. Os pacotes gerados e as
configurações preenchidas **não são versionados** — eles carregam UPN, `driveId`
e GUID de biblioteca reais, que não entram neste repositório.

## Como gerar

```bash
cp flows/config-exemplo.json /tmp/config-pessoa.json   # fora do repo
# preencha os valores
python3 scripts/gerar-fluxo.py /tmp/config-pessoa.json /tmp/fluxo-pessoa.zip
```

O script imprime a expressão do `Area` que ele montou, para você conferir antes
de importar.

## O que o pacote já traz pronto

| | |
|---|---|
| Gatilho | OneDrive, **somente propriedades**, com `splitOn` |
| `Area` | classifica a reunião pelo nome do arquivo — **fonte única** das palavras-chave |
| `Condition` | `.mp4` **e** área reconhecida. Gravação de outra reunião cai no ramo vazio e o fluxo termina **verde sem fazer nada** |
| `Caminho` | pasta de gravações do config + `%20` no espaço |
| `Do until` | `Delay` de 30 s, `Passo_4`, e um `Tolera` que impede o `404` de "ainda processando" derrubar o loop |
| `Condition_2` | guarda pós-loop, com `Encerrar` no ramo falso |
| `Passo_5` | ação **HTTP** sobre a `temporaryDownloadUrl` — sem autenticação, a URL carrega a dela |
| `Linhas` / `Falas` | quebra em linhas e filtra por exclusão (VTT sem locutor) |
| `Condition_1` | guarda de transcrição vazia, com `Encerrar` |
| `Create_file` | `LT-<Área>-AAAA-MM-DD-HHmm.txt` na biblioteca de destino |

## Depois de importar — o que ainda é manual

1. **Escolher as conexões** no assistente de importação. A do OneDrive tem que
   ser a **do dono do drive** — conexão não se transfere
2. **Abrir o gatilho e reescolher a pasta.** O `folderId` é `driveId.itemId`, e o
   `itemId` da pasta só existe naquele drive
3. **Conferir o nome da pasta**: `Recordings`, `Gravações` ou `Grabaciones`,
   conforme o idioma da conta. Se diferir do config, ajuste o `Caminho`

O passo 2 é obrigatório mesmo que o `folderId` do config esteja certo — o
seletor é o que valida que a conexão enxerga aquela pasta.
