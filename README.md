# Aura Agent — migração para a nova experiência do Copilot Studio

Reconstrução do agente de análise de portfólio **CDIO LATAM** (Unilever) do Copilot Studio clássico para a nova experiência.

O agente clássico funcionava. A Microsoft removeu tópicos e child agents em junho/2026 e **não existe conversão entre as duas experiências** — o que migrou automaticamente foi uma fração do original, com defeitos de configuração. Este repositório contém o diagnóstico, o manual da ferramenta nova e os arquivos prontos para reconstruir o agente melhor do que ele era.

---

## Comece por aqui

| Se você quer… | Leia |
|---|---|
| Entender **o que são** os dois arquivos exportados | [`docs/01-os-dois-arquivos.md`](docs/01-os-dois-arquivos.md) |
| Saber **exatamente o que quebrou** e por quê | [`docs/02-diagnostico-completo.md`](docs/02-diagnostico-completo.md) |
| Aprender **como funciona** a nova experiência (skills, tools, memory, workflows) | [`docs/03-manual-nova-experiencia.md`](docs/03-manual-nova-experiencia.md) |
| **Executar** a reconstrução, clique a clique | [`docs/04-passo-a-passo.md`](docs/04-passo-a-passo.md) |
| Configurar **cada tool**, campo a campo | [`docs/05-tools-spec.md`](docs/05-tools-spec.md) |

---

## O diagnóstico em 6 linhas

1. **Azure DevOps: 5 ferramentas → 0.** Não sobrou nenhuma referência ao conector.
2. **`Power BI Master DB Search` ficou sem os bindings de input** — `groupid` e `datasetid` caíram em "preencher com IA" e o modelo não adivinha GUID. Daí o HTTP 400.
3. **A `Power BI Portfolio Database` não foi recriada** — era o motor DAX livre, a ferramenta mais usada do agente.
4. **A skill migrada chama tools que não existem** por aquele nome.
5. **As instruções mandam ler `Global.tabela_pbi`**, variável que morreu junto com os tópicos.
6. **O idioma caiu para en-US** e a moderação subiu para Máxima.

---

## O que tem aqui

```
docs/       diagnóstico, manual da nova experiência, passo a passo, spec das tools
agent/      instruções reescritas (6.3k chars), greeting/prompts, checklist de settings
skills/     as 6 skills — SKILL.md + references/
dist/       os .zip prontos para upload no Copilot Studio
scripts/    validador e empacotador
```

### As 6 skills

| Skill | Substitui | Novo? |
|---|---|---|
| `inicio-de-conversa` | tópico `Início da conversa` | corrigida |
| `portfolio-overview` | tópicos `BU's Query` / `Area's Query` | ✅ |
| `project-deep-dive` | tópico `Project Deep Dive` | ✅ |
| `meeting-preparation` | tópico `Meeting Preparation_` | ✅ |
| `update-devops` | tool `Update Project` + protocolo de confirmação | ✅ |
| `notificar-gestor` | — cobrança do gestor pelo Teams | 🆕 |

### As 8 tools

| # | Tool | Ação |
|---|---|---|
| 1 | `Power BI Portfolio Database` | 🆕 criar |
| 2 | `Power BI Master DB Search` | 🔧 corrigir inputs |
| 3 | `Power BI KPI Agente` | ✏️ renomear |
| 4 | `DevOps Portfolio Master Query` | 🆕 criar |
| 5 | `DevOps Query by Area or BU` | 🆕 criar |
| 6 | `DevOps Work Item Details` | 🆕 criar |
| 7 | `DevOps Update Work Item` | 🆕 criar ⚠️ grava |
| 8 | `Teams — Postar mensagem` | ✅ manter |

---

## Como usar os pacotes de skill

Os `.zip` já estão em [`dist/`](dist/) — baixe e suba direto em **Copilot Studio → Skills → Adicionar skill → Carregar arquivo**.

Se editar alguma skill, regenere:

```bash
./scripts/build-skill-packages.sh    # valida e reempacota tudo em dist/
./scripts/validate-skills.sh         # só valida
```

O validador confere frontmatter, `name` em kebab-case, tamanho da `description`, e — o mais útil — **se toda tool citada numa skill realmente existe** na lista das 8. Foi exatamente esse tipo de erro que quebrou a skill migrada.

> Use sempre o `.zip`, nunca o `.md` solto: só o zip carrega a pasta `references/`, onde estão os GUIDs, o dicionário de campos e as receitas de DAX.

---

## Duas coisas que você precisa decidir

**1. O controle de acesso da pauta executiva.** No clássico era Power Fx que *executava*. Numa skill vira instrução — obedecida quase sempre, não sempre. Se for crítico, precisa sair da skill: grupo de segurança, agente separado, ou workflow. Detalhes em [`docs/03`](docs/03-manual-nova-experiencia.md), seção 3.8.

**2. A combinação `poster`/`location` do Teams.** Não dá para determinar pelo arquivo — varia por tenant. Teste a tool mandando mensagem para você mesmo antes de ligar a `notificar-gestor`, e trave os valores que funcionarem.

---

## Origem dos dados

Todo GUID, Query ID, `operationId`, nome de coluna DAX e reference name `Custom.*` deste repositório foi extraído do `botContent.yml` do agente clássico e conferido linha a linha. **Nada foi inventado.** As referências de linha estão em [`docs/05-tools-spec.md`](docs/05-tools-spec.md).
