# `flows/` — soluções do Power Automate versionadas

Fonte da verdade dos fluxos que o AURA chama como tool. O que você importa no Power Automate é o zip; o que se revisa em diff é o JSON.

| Pasta | Fluxo | Doc |
|---|---|---|
| [`CDIORelatorioArea/`](CDIORelatorioArea/) | `GerarRelatorioArea` — relatório executivo por IT Area, publicado no SharePoint | [`docs/standard/08-relatorio-automatizado.md`](../docs/standard/08-relatorio-automatizado.md) |

## Empacotar

```bash
flows/build.sh          # lê a <Version> de solution.xml → dist/CDIORelatorioArea_<versão>.zip
```

O zip precisa ter `[Content_Types].xml`, `solution.xml` e `customizations.xml` **na raiz** — por isso o script zipa de dentro da pasta, e não a pasta.

## Ao mexer no JSON

1. **Suba a `<Version>` em `solution.xml` — sempre.** Nunca reempacote conteúdo diferente sob um número já publicado: quem baixou não tem como distinguir os dois zips, e o Power Automate também não. Já aconteceu aqui.
2. Rode `flows/build.sh` e importe.
3. As referências de conexão (`unilever_adocdioreport`, `unilever_spocdioreport`) são remapeadas na importação — não edite os GUIDs à mão.

## Duas armadilhas de expressão que já custaram caro aqui

- **`and()` e `or()` não fazem curto-circuito.** Todos os argumentos são avaliados, então uma guarda à esquerda não protege um `formatDateTime` à direita. Calcule o campo seguro no `Select` e filtre por string.
- **`if()` avalia os dois ramos em vários runtimes.** Nunca deixe uma função que possa lançar no ramo não escolhido: use uma sentinela (`'1900-01-01T00:00:00Z'`) ou embrulhe em `coalesce`.
