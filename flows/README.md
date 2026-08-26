# `flows/` — soluções do Power Automate versionadas

Fonte da verdade dos fluxos que o AURA chama como tool. O que você importa no Power Automate é o zip; o que se revisa em diff é o JSON.

| Pasta | Fluxo | Doc |
|---|---|---|
| [`CDIORelatorioArea/`](CDIORelatorioArea/) | `PortfolioDataArea` (portfólio em JSON) + `PublishAreaReport` (relatório HTML no SharePoint) | [`docs/standard/08-relatorio-automatizado.md`](../docs/standard/08-relatorio-automatizado.md) |

## Empacotar

```bash
flows/build.sh          # lê a <Version> de solution.xml → dist/CDIORelatorioArea_<versão>.zip
```

O zip precisa ter `[Content_Types].xml`, `solution.xml` e `customizations.xml` **na raiz** — por isso o script zipa de dentro da pasta, e não a pasta.

## Validar antes de empacotar

```bash
python3 scripts/validate-flows.py
```

O Power Automate aceita **salvar e importar** um fluxo que ele depois recusa **ativar** — a validação de verdade só roda no `Ativar`, e a mensagem vem crua, sem apontar o arquivo. O script pega essa classe de erro em segundos — as três que já apareceram aqui estão cobertas.

## Ao mexer no JSON

1. **Suba a `<Version>` em `solution.xml` — sempre.** Nunca reempacote conteúdo diferente sob um número já publicado: quem baixou não tem como distinguir os dois zips, e o Power Automate também não. Já aconteceu aqui.
2. Rode `flows/build.sh` e importe.
3. As referências de conexão (`unilever_adocdioreport`, `unilever_spocdioreport`) são remapeadas na importação — não edite os GUIDs à mão.

## Nove armadilhas que já custaram caro aqui

- **`and()` e `or()` não fazem curto-circuito.** Todos os argumentos são avaliados, então uma guarda à esquerda não protege um `formatDateTime` à direita. Calcule o campo seguro no `Select` e filtre por string.
- **`if()` avalia os dois ramos em vários runtimes.** Nunca deixe uma função que possa lançar no ramo não escolhido: use uma sentinela (`'1900-01-01T00:00:00Z'`) ou embrulhe em `coalesce`.
- **`InitializeVariable` só existe na raiz do fluxo.** Dentro de Scope, Condition ou Foreach o fluxo importa e salva, e depois recusa ativar com `InvalidVariableInitialization`. `Response` dentro de Foreach/Until é a mesma história.
- **Somar array com `xpath` exige o array embrulhado.** `xml(json('{"v":[1,2]}'))` recusa com *"This document already has a 'DocumentElement' node"* — o array vira vários elementos na raiz. A forma que funciona é `concat('{"root":{"v":', string(array), '}}')` com xpath `sum(/root/v)`.
- **`round()` não existe.** Arredondar para inteiro é `formatNumber(x, 'F0')`. Mesma família de `select()` e `filter()`: importa, salva, ativa, e só quebra ao rodar.
- **`select()` e `filter()` não existem como funções.** São as ações `Select` e `Filter array`. Dentro de um `@{}` elas importam, salvam e ativam, e só quebram ao rodar com `InvalidTemplate: The template function 'select' is not defined`. Para transformar uma lista, use a ação; para somar, um `Select` mais o truque do `xpath`.
- **Campo de identidade do DevOps volta como objeto OU como string `"Nome <email>"`.** Depende da API e da projeção. `?['displayName']` sobre a string lança, e o fluxo importa, salva e ativa sem reclamar — só quebra rodando com dado real. Normalize com `split()`, nunca com seleção de propriedade.
- **Gatilho `kind: Skills` declara `$connections` E `$authentication`.** O runtime injeta os dois; declarar só um derruba a ativação com `InvalidTemplate`. Nunca reescreva o bloco `parameters` — copie-o do fluxo de origem.
- **Toda entrada do gatilho vira uma pergunta ao usuário quando o agente não consegue preenchê-la.** O Copilot Studio resolve todas as entradas antes de executar, e emite `shouldPromptUser: true` nelas. Entrada opcional que fica vazia numa chamada legítima trava o fluxo. Se duas chamadas precisam de conjuntos de entradas diferentes, são dois fluxos.
