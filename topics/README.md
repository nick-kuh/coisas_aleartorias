# Tópicos prontos para colar

> ⚠️ **São dois tópicos separados.** Um arquivo = um tópico. **Não cole os dois no mesmo.** Eles são as duas metades do mesmo ciclo: um é a ida, o outro é a volta.

Dois tópicos que fecham o ciclo completo de governança: **detectar qualquer falha → cobrar o gestor → receber a informação → gravar no DevOps**.

Cobrem **qualquer** campo de governança — data de Go-Live, data de PGLS, fase (State), budget, benefit, payback, tempo de implementação, país, business benefit, IT Manager, note, ou qualquer outro reference name via modo avançado.

| Arquivo | O que faz |
|---|---|
| [`cobranca-gestor.yaml`](cobranca-gestor.yaml) | Você pede para cobrar. Lê o work item, **audita a governança** (lista atrasos, campos faltando, watermelons…), deixa você escolher o que cobrar, monta o rascunho, **espera sua aprovação**, envia pelo Teams |
| [`resposta-do-gestor.yaml`](resposta-do-gestor.yaml) | O gestor responde com uma informação — data, valor, fase, texto. Menu escolhe **qual campo**, valida o tipo, mostra o de-para, **espera confirmação**, grava no reference name correto |

### O que a resposta cobre

Menu fechado no `resposta-do-gestor`, agrupado por tipo de dado — cinco branches em vez de um por campo:

| Tipo | Campos |
|---|---|
| Data | Go-Live Date, PGLS End Date |
| Número | Project Total Budget, Project Benefit Value, Payback in Months, Implementation Time in Months |
| Fase (lista fechada de 13) | State |
| Lista fechada Business Benefit | Compliance / Value Added |
| Texto | Country Deployed, Project IT Manager, Assigned To, Note / observação |
| Avançado | Qualquer outro — pergunta reference name e valor livre |

O `System.State` é sempre gravado a partir da lista oficial das 13 fases — o produto **impede** que um valor fora da lista seja gravado, porque a `Question` usa `ClosedListEntity`.

Ambos foram validados: **dialeto do Copilot Studio**, YAML parseável, root `kind: AdaptiveDialog`, ids de nó únicos, e **todas as tools referenciadas existem no `crdc4_AURAAgent`** com o schemaName exato. Rode você mesmo:

```bash
python3 scripts/validate-topics.py
```

---

## Como colar

1. Copilot Studio → AURA Agent → **Tópicos** → **+ Adicionar um tópico** → **Do zero**
2. No canto superior direito, menu **⋯** → **Abrir editor de código**
3. Apague tudo e cole o conteúdo do `.yaml`
4. **Salvar**

Repita para o segundo arquivo.

---

## Pré-requisitos

Estes tópicos **não funcionam** enquanto as correções de tool não forem aplicadas:

| Tópico | Depende de |
|---|---|
| `cobranca-gestor` | Correção 3 (`id` na tool de detalhes) e Correção 5 (Teams completo — inclusive publicar o agente no Teams) |
| `resposta-do-gestor` | Correção 3 e **Correção 1** (`type` e `userEnteredFields` na `Update Project`) |

Veja [`docs/standard/02-correcao-das-tools.md`](../docs/standard/02-correcao-das-tools.md).

> Os tópicos passam os argumentos por binding, o que funciona mesmo com o input não declarado — é o que já acontece hoje no `Início da conversa`. Mas **aplique as correções assim que possível**: sem elas o agente continua incapaz de fazer essas mesmas coisas fora dos tópicos, na conversa normal.

---

## O dialeto YAML do Copilot Studio

Isto custou um erro de parse na primeira versão, então vale registrar.

**O Copilot Studio não implementa YAML completo.** Ele implementa um subconjunto, e o editor de código recusa construções que qualquer validador YAML aprovaria. A mensagem de erro entrega o vocabulário aceito:

```
expected: UnquotedValue or QuotedStringValue or MultilineStringValue
```

Três tipos de valor. Só isso.

| Construção | Vale? | Observação |
|---|---|---|
| `campo: valor` | ✅ | *UnquotedValue* |
| `campo: "valor"` | ✅ | *QuotedStringValue* |
| `campo: \|-` + bloco indentado | ✅ | *MultilineStringValue* — **é este que você usa para texto de várias linhas** |
| `campo: >-` + bloco indentado | ❌ | *folded scalar*. YAML padrão, **não existe aqui** |
| `&ancora` / `*alias` | ❌ | não aparece em nenhum export |
| `!!tipo` | ❌ | idem |
| `---` separando documentos | ❌ | um arquivo = um documento |

**A armadilha do `>-`:** o parser não reconhece o token, sai consumindo o resto do arquivo procurando um valor válido, e só reclama no fim. **O erro aponta a última linha do arquivo, mas o problema está na primeira ocorrência.** Se você ver um erro apontando o fim do arquivo, procure um `>-`.

Diferença prática entre os dois:

- `>-` junta as linhas em uma só (é por isso que é tentador para texto corrido)
- `|-` **preserva as quebras de linha**

Como só `|-` existe, escreva cada parágrafo como uma linha só e use linha em branco onde quiser separar parágrafos.

**Variável de `ClosedListEntity` é `EmbeddedOptionSet`, não `String`.** Segunda armadilha, que só o *type checker* do produto pega — depois do parse. Uma `Question` com

```yaml
      entity:
        kind: EmbeddedEntity
        definition:
          kind: ClosedListEntity
          items: [...]
```

produz uma variável tipada. Comparar direto com string literal (`=Topic.X = "Enviar"`) gera:

> Comparação de tipos incompatível. Tipo: String, esperado: EmbeddedOptionSet

Envolva em `Text()`, como o próprio agente antigo faz (`Meeting Preparation`, linha 1703):

```yaml
condition: =Text(Topic.Aprovacao) = "Enviar"
```

O validador rastreia isso — reprova toda `condition` que compara uma variável choice com string sem `Text()`.

**Texto vs. Power Fx.** Nos campos de texto (`activity`, `prompt`), use interpolação — é o que os exports do seu agente fazem:

```yaml
activity: |-
  ✅ Cobrança enviada para **{Topic.EmailGestor}**.
```

Guarde Power Fx (`="..." & Var & "..."`) para os campos que **são** Power Fx: `value`, `condition`, `userInput` e `input`. Concatenar string em campo de texto funciona, mas multiplica as chances de errar uma aspa.

**O validador cobre isso.** `scripts/validate-topics.py` roda a checagem de dialeto antes do parse e reprova `>-`, âncoras, aliases, tags e multi-documento. Rode antes de colar:

```bash
python3 scripts/validate-topics.py
```

---

## ⚠️ Três pontos que eu não consigo verificar daqui

Não tenho acesso ao seu tenant. Estes trechos seguem a convenção do próprio arquivo exportado, mas precisam de um teste real. Se o editor reclamar ou a execução falhar, é aqui.

### 1. As entidades `NumberPrebuiltEntity` e `DateTimePrebuiltEntity`

Os seus exports comprovam apenas `StringPrebuiltEntity` e `BooleanPrebuiltEntity`. As outras duas são entidades padrão do produto e o nome quase certamente está certo — mas não tenho como confirmar pelos seus arquivos, e o validador avisa sobre elas de propósito.

**Se o editor reclamar dessas linhas**, troque por `StringPrebuiltEntity`. Onde aparece `NumberPrebuiltEntity` (todos os `perguntarId` e o `perguntarNumero` do branch de tipo número), a leitura por `=Value(Topic.X)` continua convertendo texto para número, então normalmente basta trocar a linha da `entity` e nada mais.

### 2. O binding dos campos do Teams

Em `cobranca-gestor.yaml`:

```yaml
      input:
        body.recipient: =Topic.EmailGestor
        body.messageBody: =Topic.Rascunho
```

A notação com ponto vem do próprio export do seu agente, que declara `propertyName: body.bot`. Deve funcionar.

**Se o editor recusar:** abra o nó `enviarTeams` no **editor visual**, e mapeie os dois campos pela interface — `Recipient` ← `Topic.EmailGestor` e `Message` ← `Topic.Rascunho`. O resto do tópico continua igual. O YAML é o esqueleto; esse mapeamento fino é mais seguro pela UI.

### 3. O formato da data enviada ao DevOps

Em `resposta-do-gestor.yaml`:

```yaml
    - kind: SetVariable
      id: formatarDataApi
      variable: Topic.DataApi
      value: =Text(Topic.NovaData, "yyyy-mm-dd")
```

Campos de data do Azure DevOps costumam aceitar ISO (`yyyy-mm-dd`), e é por isso que está assim. Mas o `Custom.GoLiveDate` do CDIO pode estar configurado como texto no formato LATAM.

**Se o PATCH falhar ou gravar a data errada:** troque para `"dd/mm/yyyy"`. A variável `Topic.DataFormatada` (que é o que o usuário vê) já está em `dd/mm/yyyy` e não muda.

Um jeito rápido de descobrir sem tentativa e erro: rode `me traz os detalhes do work item 376` depois da Correção 3 e olhe em que formato o `GoLive Date` volta. Grave no mesmo formato.

---

## O que estes tópicos garantem

O ponto mais importante, e o motivo de valer a pena fazer no standard em vez da experiência nova:

**Aqui o `Question` e o `ConditionGroup` executam de verdade.** A aprovação antes de enviar a mensagem, e a confirmação antes de gravar no DevOps, são **portões reais** — não instruções que o modelo pode contornar. Na experiência nova, com skills, isso viraria texto e o modelo poderia pular.

- `cobranca-gestor` **não chama o Teams** enquanto você não escolher **Enviar**.
- `resposta-do-gestor` **não chama o Update** enquanto você não escolher **Confirmar**.
- Nenhum dos dois inventa dado: o rascunho e a data atual saem de `Topic.DevOpsFields`, com `mode: Restricted` e instrução explícita de não inventar.

---

## Roteiro de teste

Faça nesta ordem, e **com você mesmo como destinatário** nas duas primeiras rodadas.

| # | Onde | Ação | Esperado |
|---|---|---|---|
| 1 | Painel de teste | `cobrar o gestor` | Pergunta o Work Item ID |
| 2 | | responda `376` | Lê o DevOps, sugere um e-mail, pede confirmação |
| 3 | | informe **seu próprio** e-mail | Mostra o rascunho e pergunta se pode enviar |
| 4 | | escolha **Cancelar** | Não envia nada ✅ (teste o portão antes de testar o envio) |
| 5 | | repita e escolha **Enviar** | Chega mensagem no seu Teams, no chat com o AURA Agent |
| 6 | Teams, no chat com o agente | responda `a nova data é 30/11/2026` | Dispara `resposta-do-gestor`, pede o ID |
| 7 | | responda `376` | Mostra o de-para e pede confirmação |
| 8 | | **Confirmar** | Grava e devolve o link. Confira no DevOps |
| 9 | Painel de teste | repita o passo 1 com o e-mail de um gestor real | Só depois de tudo acima passar |

---

## Ajustes que você provavelmente vai querer

**Campo diferente de GoLive Date.** O `resposta-do-gestor` grava `Custom.GoLiveDate`. Para cobrar budget, benefício ou state, troque a linha do `userEnteredFields` — os reference names estão em [`skills/update-devops/references/campos-devops.md`](../skills/update-devops/references/campos-devops.md). Exemplo para budget:

```yaml
                userEnteredFields: "={'Custom.ProjectTotalBudget': Topic.Valor}"
```

**Cobrança em lote.** Estes tópicos tratam um projeto por vez, de propósito — cinco mensagens erradas são cinco erros, não um. Para varredura semanal automática, o caminho é um fluxo do Power Automate; o desenho está em [`docs/standard/03-teams-conversa-com-gestor.md`](../docs/standard/03-teams-conversa-com-gestor.md), §3.6.

**Frases de gatilho.** As de `resposta-do-gestor` (`a nova data é`, `vai para`, `remarcamos para`) são propositalmente genéricas, porque o gestor não vai usar o vocabulário que você usaria. Se estiver disparando na hora errada, especialize; se não estiver disparando, acrescente as frases que os gestores realmente escreveram.
