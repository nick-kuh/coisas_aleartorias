# 7. `Create Project` e `Remove Project` — o que ajustar

Duas tools novas no `botContent_77`. Uma precisa de três entradas para funcionar. A outra **não faz o que o nome diz** — e essa é a parte importante.

---

## 🔴 Primeiro: `Remove Project` não remove projeto

O nome que você deu é `Remove Project`. A operação por trás é outra:

```yaml
modelDisplayName: Remove Project
modelDescription: Exclui um link de um item de trabalho.
operationId: DeleteWorkItemLinkAsync        # ← apaga um LINK, não o item
```

`DeleteWorkItemLinkAsync` apaga uma **relação entre dois work items** — aquele vínculo de "Related", "Parent", "Child". O work item continua lá, intacto.

E tem um segundo problema: no export a tool **não tem `dynamicInputSchema` nenhum**. Ou seja, ela não tem por onde receber qual link apagar. Do jeito que está, ou falha, ou não faz nada.

**O risco concreto:** o modelo lê "Remove Project" na descrição, o usuário pede "apaga esse projeto", e ele chama a tool achando que vai apagar. O resultado é imprevisível — e não é o que ninguém queria.

### O que fazer no lugar: `00 Cancelled`

O seu próprio processo já tem a resposta. `00 Cancelled` é a **primeira das 13 fases oficiais**, e existe exatamente para retirar um projeto do portfólio.

| | Apagar o work item | Mover para `00 Cancelled` |
|---|---|---|
| Histórico | perdido | preservado |
| Power BI | a linha some, os totais históricos mudam | continua, filtrada por `[N State] = 0` |
| Auditoria | não dá para saber que existiu | fica registrado quem cancelou e quando |
| Reverter | lixeira, com prazo | trocar o State de volta |
| Ferramenta nova | precisa | **nenhuma — o `Update Project` já faz** |

**Recomendação: apague a tool `Remove Project` e trate cancelamento como troca de State.** Não é só mais seguro — é menos trabalho, porque a tool que faz isso já existe e já está configurada.

### Se você realmente quiser deleção de verdade

O conector do Azure DevOps **não tem** ação de apagar work item. O único caminho é a ação genérica **"Enviar uma solicitação HTTP para o Azure DevOps"**:

```
Método: DELETE
URI:    /CDIO Portfolio/_apis/wit/workitems/{id}?api-version=7.1
```

Antes de fazer isso, dois pontos que eu preciso colocar na mesa:

1. **O portão de confirmação é uma instrução, não um `ConditionGroup`.** Desde que os tópicos saíram, "confirme antes de gravar" é seguido quase sempre — não sempre. Para atualizar um campo, "quase sempre" é um risco aceitável. Para apagar um item do portfólio, a conta é outra.
2. **Vai para a lixeira do Azure DevOps**, com prazo de retenção. Passado o prazo, acabou.

Se ainda assim for o caminho, o mínimo é: tool separada, com `type` fixo, descrição de input deixando explícito que só pode ser chamada com ID confirmado pelo usuário na mesma mensagem, e um work item de teste para validar.

---

## ✅ `Create Project` — falta declarar três entradas

A tool está apontando certo (`operationId: CreateWorkItem`), com os fixos no lugar:

| Entrada | `kind` | Valor | Status |
|---|---|---|---|
| `account` | `ManualTaskInput` | `CDIO-IT-LATAM` | ✅ |
| `project` | `ManualTaskInput` | `CDIO Portfolio` | ✅ |
| `type` | `ManualTaskInput` | `IT Project` | ✅ |
| **`title`** | `AutomaticTaskInput` | — | 🔴 **obrigatório no schema, não declarado** |
| **`description`** | `AutomaticTaskInput` | — | 🟠 adicionar |
| **`userEnteredFields`** | `AutomaticTaskInput` | — | 🟠 adicionar |

**Sem o `title` a tool não cria nada** — é obrigatório no `dynamicInputSchema` do conector. É o mesmo defeito que a `Update Project` tinha com o `userEnteredFields`.

> ⚠️ O `userEnteredFields` aparece na lista como **"Other Fields"**, com visibilidade **Advanced**. Se não estiver visível, expanda **"Mostrar todas as entradas"**.

### Descrição da entrada `title`  `219/1024`

```
The project title, exactly as the user dictated it. Do not invent it, do not
translate it, do not reformat it. If the user has not given a title, ask for one.
NEVER create a work item with a placeholder or guessed name.
```

### Descrição da entrada `description`  `223/1024`

```
A short business description: what the project delivers and for whom, in the
user's own words. Never invent scope, numbers, benefits or dates. If the user
gave no description, send an empty string rather than making one up.
```

### Descrição da entrada `userEnteredFields`  `1005/1024`

```
A JSON object whose keys are FULL Azure DevOps reference names, setting governance fields at creation. Valid keys include: "System.State", "System.AssignedTo", "Custom.ProjectType", "Custom.ITArea", "Custom.BGorBUEngagement", "Custom.SpecifyCross", "Custom.BusinessBenefit", "Custom.BusinessProductsDomain", "Custom.ProjectITManager", "Custom.CountryDeployed", "Custom.PortfolioYear", "Custom.ImplementionTimeinMonths".
Include ONLY fields the user actually provided. Never guess a value to fill a gap.
New projects start at "01 Idea" unless the user names another phase. "System.State" accepts ONLY these 13 strings: "00 Cancelled", "01 Idea", "02 Scoping", "03 Scope Approv", "04 Costing", "05 Cost Approv", "06 Plan Analyze", "07 Design Build", "08 UAT", "09 PGLS", "10 Deployed", "11 Closed", "12 On Holding".
FORMATS: dates as YYYY-MM-DD. Money and months as plain numbers, no symbol, no separator.
NEVER call this tool before showing the user the complete draft and getting an explicit confirmation.
```

### Descrição da tool  `303/1024`

Troque a atual (`Crie um item de trabalho com os atributos fornecidos.`) por:

```
Creates a new IT Project work item in the CDIO Portfolio. Use ONLY when the user
explicitly asks to create or register a new project, and ONLY after showing them
the complete draft and receiving an explicit confirmation. NEVER use it to answer
a question, to test, or to fix data on an existing project.
```

A última frase importa: sem ela, a descrição genérica de hoje deixa o orquestrador chamar a tool sem querer.

---

## ✅ Teste

Num ambiente onde criar lixo não incomoda:

| # | Peça | Esperado |
|---|---|---|
| 1 | `crie um projeto chamado Teste AURA na IT Area Make` | Monta o rascunho e **pergunta antes de criar** |
| 2 | Confirmar | Cria e devolve `Teste AURA (novo id)` com o link `_workitems/edit/` |
| 3 | `crie um projeto` (sem nome) | **Pede o título** em vez de inventar um |
| 4 | `apaga o projeto <id>` | Propõe mover para `00 Cancelled`, não tenta apagar |

O teste 3 é o que prova que a descrição do `title` pegou. O teste 4 vale depois de remover a `Remove Project`.
