---
name: update-devops
description: >
  Atualiza campos de um work item do Azure DevOps (CDIO Portfolio) com
  segurança, seguindo o protocolo ler → propor → confirmar → gravar → confirmar.
  Resolve o projeto pelo nome ou pelo ID, lê o estado atual, valida o novo State
  contra a taxonomia oficial das 13 fases, altera apenas os campos pedidos e
  exige aprovação explícita do usuário antes de qualquer escrita. Use quando
  pedirem "atualizar projeto", "mudar o status no DevOps", "alterar o campo X",
  "atualizar item de trabalho", "preencher o budget do projeto Y".
  NÃO use para consulta ou análise (use project-deep-dive ou portfolio-overview)
  nem para enviar mensagem a alguém (use notificar-gestor).
---

# Update DevOps — protocolo de escrita segura

⚠️ Esta é a única capacidade do agente que **grava** em sistema de produção. As cinco etapas abaixo são obrigatórias e não podem ser encadeadas sem parada.

## Passo 1 — Identifique o work item

Se o usuário deu o **ID numérico**, use-o.

Se deu o **nome**, chame **`Power BI Master DB Search`**:

```dax
EVALUATE FILTER('tabela', SEARCH("<nome>", 'tabela'[Short Name], 1, 0) > 0 || SEARCH("<nome>", 'tabela'[Title], 1, 0) > 0)
```

Se voltar mais de uma correspondência, **pare** e peça o ID exato. Nunca escolha por conta própria qual atualizar.

## Passo 2 — LEIA o estado atual (obrigatório)

Chame **`DevOps Work Item Details`** com o ID. Você precisa do valor atual de cada campo que vai mudar — sem isso não há como mostrar o "de → para".

## Passo 3 — Valide o que vai mudar

### Se estiver mudando `System.State`

Compare com a lista oficial das 13 fases:

`00 Cancelled` · `01 Idea` · `02 Scoping` · `03 Scope Approv` · `04 Costing` · `05 Cost Approv` · `06 Plan Analyze` · `07 Design Build` · `08 UAT` · `09 PGLS` · `10 Deployed` · `11 Closed` · `12 On Holding`

Se o usuário escreveu com pequena variação ("06 Design & Build", "Design Build", "uat"), **corrija autonomamente** para a string oficial exata por proximidade e informe a correção na proposta. Se não houver correspondência plausível, pare e mostre a lista.

### Para qualquer campo

- Use o **reference name completo** como chave: `Custom.Note`, não `Note`. Lista completa em `references/campos-devops.md`.
- ⛔ **Nunca** envie campos read-only: `System.CreatedBy`, `System.CreatedDate`, `System.ChangedBy`, `System.ChangedDate`, `Microsoft.VSTS.Common.StateChangeDate`, `System.TeamProject`, `System.WorkItemType`.
- ⛔ **Nunca** inclua campo que não foi pedido. Um campo não mencionado deve permanecer intocado.

## Passo 4 — PROPONHA e espere aprovação

Mostre exatamente isto e **pare**:

```
📝 **Alteração proposta no Work Item #[ID] — [Short Name]**

| Campo | De | Para |
|---|---|---|
| [nome amigável] | [valor atual] | [valor novo] |

Confirma? Responda **sim** para eu gravar no Azure DevOps.
```

**Não chame a ferramenta de escrita antes de uma aprovação explícita.** "Talvez", "acho que sim" ou silêncio não são aprovação. Se o usuário pedir ajuste, volte ao passo 3.

## Passo 5 — Grave

Só depois do "sim", chame **`DevOps Update Work Item`** com:

- `id` — o ID numérico
- `userEnteredFields` — objeto JSON só com os campos aprovados

```json
{ "System.State": "07 Design Build" }
```

## Passo 6 — Confirme

```
🚀 **DevOps atualizado!** O Work Item **#[ID]** foi modificado:
- **[Campo]:** [valor novo]

🔗 [Revisar o work item](https://dev.azure.com/CDIO-IT-LATAM/CDIO%20Portfolio/_workitems/edit/[ID])
```

Se a gravação falhar, mostre o erro real e **não** finja que deu certo.

## Casos de borda

| Situação | O que fazer |
|---|---|
| Projeto em `10 Deployed` ou `11 Closed` | Avise que já foi entregue/encerrado e pergunte se realmente quer alterar antes de propor |
| Usuário pede para atualizar vários work items | Trate um por vez, com confirmação individual. Nunca faça lote sem aprovação item a item |
| Usuário pede para "corrigir tudo que está faltando" | Não invente valores. Liste os campos obrigatórios faltantes e peça os valores |
| Campo com domínio fechado (`Project Type`, `Business Benefit`, `BG or BU Engagement`) | Valide contra os valores permitidos em `references/campos-devops.md` antes de propor |
| Valor financeiro | Confirme a moeda (€) e o formato antes de gravar |
| Data | Entrada e saída em DD/MM/YYYY |
