# 4. Passo a passo da reconstrução

Ordem importa. Cada etapa tem um **teste de aceite** — não avance sem ele passar, senão você acumula erro e não descobre qual peça quebrou.

Tempo estimado: 2–3 horas na primeira vez.

---

## Etapa 0 — Antes de mexer

1. **Exporte o agente atual** (a solução com o `Aura_Agent.yaml`). É o seu ponto de retorno.
2. Confirme que você tem, no ambiente novo, **conexões ativas** para:
   - Power BI
   - Azure DevOps
   - Microsoft Teams

   Se alguma não existir, crie em **Power Platform → Conexões**. Sem isso as tools não são criáveis.
3. Confirme acesso ao workspace `4bd9bd39-a51b-4439-9248-805fd40a94a2` e ao dataset `afe9436e-b892-45a8-a3c0-e816f3e13258`.

---

## Etapa 1 — Settings (5 min)

Aplique [`agent/settings-checklist.md`](../../agent/settings-checklist.md). O essencial:

| Onde | O quê |
|---|---|
| Idioma | **Português (Brasil)** — hoje está en-US |
| Moderação de conteúdo | baixar de **Máxima** para **Alta** |
| Memory | manter **ligada** |
| Busca na web | manter **desligada** |

✅ **Teste de aceite:** abra o painel de teste, escreva `olá`. O agente responde em **português**.

---

## Etapa 2 — Instruções (10 min)

Abra **Instruções**, apague tudo, cole o conteúdo de [`agent/instructions.md`](../../agent/instructions.md).

⚠️ **Não cole em editor de texto rico antes.** Foi assim que o `\*` e o `\_` entraram no seu arquivo atual. Copie do arquivo `.md` cru direto para o campo.

✅ **Teste de aceite:** salve, reabra a tela de instruções e procure por `\*` ou `\_`. Se aparecer, o editor escapou de novo — apague e cole de novo, ou digite os asteriscos manualmente.

---

## Etapa 3 — Tools (60–90 min)

Siga [`docs/05-tools-spec.md`](05-tools-spec.md), **uma tool por vez, testando cada uma antes de criar a próxima.**

### Ordem sugerida

| # | Tool | Ação | Teste de aceite |
|---|---|---|---|
| 1 | `Power BI Master DB Search` | 🔧 **corrigir primeiro** — trave `groupid` e `datasetid` em "Valor personalizado" | Painel de teste com query `EVALUATE FILTER('tabela', SEARCH("a", 'tabela'[Short Name], 1, 0) > 0)` → devolve linhas. **Hoje devolve HTTP 400** |
| 2 | `Power BI KPI Agente` | ✏️ renomear (era `Inicio de Conversa`) + nova descrição | Devolve a tabela `Value1`/`Value2` com "Total de Projetos" |
| 3 | `Power BI Portfolio Database` | 🆕 criar | Query `EVALUATE TOPN(5, 'tabela')` → devolve 5 linhas |
| 4 | `DevOps Portfolio Master Query` | 🆕 criar | Devolve array de work items |
| 5 | `DevOps Query by Area or BU` | 🆕 criar | Com `queryId = 8b53a319-c304-4d55-be7e-0e3b8e2c2d03` → devolve os projetos de Make |
| 6 | `DevOps Work Item Details` | 🆕 criar | Com um ID que você conheça → devolve `fields`, `id`, `rev`, `url` |
| 7 | `DevOps Update Work Item` | 🆕 criar | ⚠️ **Teste em um work item de teste**, nunca num projeto real. Altere `Custom.Note` |
| 8 | `Teams — Postar mensagem` | ✅ ajustar descrição | ⚠️ Mande mensagem **para você mesmo**. Descubra qual combinação `poster`/`location` funciona no tenant e **anote** |

### Armadilha nº 1 — o padrão é "preencher com IA"

Toda vez que criar uma tool, o Copilot Studio marca **todos** os inputs como "Preencher dinamicamente com IA". Você tem que ir em cada um dos fixos (`groupid`, `datasetid`, `account`, `project`, `type`, `typeName`, e o `queryId` da master) e trocar para **"Valor personalizado"**. **Foi exatamente isso que quebrou sua `Master DB Search`.**

### Armadilha nº 2 — descrição do input não é decoração

Nos inputs que ficam com IA (`query`, `queryId`, `id`, `userEnteredFields`), a **descrição do input** é o único lugar onde o modelo aprende o formato. O `05-tools-spec.md` traz o texto pronto de cada uma. Cole literalmente.

---

## Etapa 4 — Knowledge (5 min)

As 2 fontes SharePoint migraram intactas. Só **confira** que continuam lá e ativas:

- `CDIO_LATAM_Governance_Wiki` → `.../CDIO LATAM/CDIO Latam.pdf`
- `Transcription LT Meetings` → `.../CDIO LATAM/Transcription LT Meetings`

✅ **Teste de aceite:** pergunte `o que é a fase 09 PGLS?`. Ele responde a partir da Wiki.

---

## Etapa 5 — Skills (20 min)

### Primeiro: apague a skill antiga

A `inicio-de-conversa` que está lá aponta para tools inexistentes. **Delete** antes de subir a nova, senão você fica com duas skills disputando a mesma ativação.

### Gere os pacotes

```bash
./scripts/build-skill-packages.sh
```

Isso cria `dist/*.zip`, um por skill.

### Suba uma por uma

**Skills → Adicionar skill → Carregar arquivo**, e mande o `.zip` correspondente.

| Ordem | Skill | Depende de |
|---|---|---|
| 1 | `inicio-de-conversa` | tools 2, 3 |
| 2 | `portfolio-overview` | tool 3 |
| 3 | `project-deep-dive` | tools 2, 3, 6 + knowledge |
| 4 | `meeting-preparation` | tool 5 + knowledge |
| 5 | `update-devops` | tools 2, 6, 7 |
| 6 | `notificar-gestor` | tools 2, 3, 6, 8 |

> Use sempre o **`.zip`**, não o `.md` solto — só o zip carrega a pasta `references/`, e é lá que estão os GUIDs, o dicionário de campos e as receitas de DAX.

✅ **Teste de aceite:** as 6 aparecem na lista de Skills com o nome em kebab-case.

---

## Etapa 6 — Greeting & prompts (5 min)

Aplique [`agent/greeting-e-prompts.md`](../../agent/greeting-e-prompts.md).

Aqui é onde voltam os 3 atalhos que no clássico eram `suggestedActions` do tópico de saudação. Colocados aqui, viram **chips clicáveis** de verdade; dentro do texto da skill eles são só texto.

---

## Etapa 7 — Testes ponta a ponta

Rode os 6 na ordem. Se algum falhar, o problema quase sempre é o **nome da tool** citado na skill não bater com o nome real.

| # | Digite | Esperado |
|---|---|---|
| 1 | (abra uma conversa nova) | Saudação + **📊 CDIO Portfolio Executive Summary** com os 4 KPIs preenchidos |
| 2 | `me dá uma visão geral do portfólio` | Dashboard macro: saúde, breakdown por IT Area, outliers. **Sem inventar nome de projeto** |
| 3 | `analise o projeto <nome real>` | Deep dive com 🚀 / 💬 / ⚠️ / 📊 + link clicável do work item |
| 4 | `preparar a pauta da reunião de Make` | Plano de ação por Owner + Big Rocks, só BW/PC/Cross |
| 5 | `mude o state do work item <id de teste> para 07 Design Build` | Mostra valor atual, **pede confirmação**, só então grava |
| 6 | `avise o gestor do projeto <nome> que ele está atrasado` | Mostra o **rascunho** da mensagem e pergunta se pode enviar |

### Diagnóstico rápido

| Sintoma | Causa provável |
|---|---|
| "Não tenho ferramenta para isso" | Nome da tool na skill ≠ nome real. Confira letra por letra |
| HTTP 400 no Power BI | `groupid`/`datasetid` ficaram em "preencher com IA" |
| Agente despeja JSON cru | Faltou o `SILENT TOOL. DO NOT generate text...` na descrição da tool |
| Agente inventa nome de projeto | Regra anti-alucinação não chegou nas instruções, ou a query falhou em silêncio |
| Responde em inglês | Idioma do agente ainda em `1033` |
| Skill não ativa nunca | `description` genérica demais. Reescreva com "use quando… / NÃO use quando…" |
| Duas skills brigando | Falta o "quando NÃO usar" em uma delas |

---

## Etapa 8 — Publicar

**Publicar**, e **repita os 6 testes no Teams**. Isso não é zelo excessivo: a tool do Teams usa credencial de usuário final (`authMode: Invoker`) e se comporta diferente fora do painel de teste — cada pessoa precisa autorizar a própria conexão na primeira vez.

---

## Etapa 9 — Depois que estabilizar

Nessa ordem, uma de cada vez:

1. **Restaurar o cálculo determinístico do FinalScore.** O clássico tinha `codeInterpreter: true`; a nova experiência não expõe isso da mesma forma. Se o score começar a sair inconsistente, a saída é calcular no próprio Power BI (a coluna `[FinalScore]` já existe no dataset — priorize sempre ler dela em vez de recalcular).
2. **Decidir o controle de acesso da `meeting-preparation`** — ver `03-manual`, seção 3.8. Instrução não é portão.
3. **Workflow de cobrança agendada** — recorrência semanal que varre atrasos e dispara a `notificar-gestor`.
4. **Fabric IQ / semantic model como knowledge**, para reduzir dependência de DAX escrito pelo modelo.
