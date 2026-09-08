# AURA Agent — Copilot Studio · CDIO LATAM

Diagnóstico e correção do agente de análise de portfólio do **CDIO LATAM** (Unilever) no Microsoft Copilot Studio.

O repositório cobre duas trilhas, porque o agente passou por duas tentativas de reconstrução:

| Trilha | Situação | Onde |
|---|---|---|
| 🟢 **Standard / clássico** | **ATIVA** — é por aqui que a reconstrução está indo | [`docs/standard/`](docs/standard/) |
| ⚪ Nova experiência (skills) | Referência. Descartada porque o motor do GitHub Copilot consome crédito até para testar | [`docs/nova-experiencia/`](docs/nova-experiencia/) |

---

## 🟢 Trilha standard — comece aqui

O agente `crdc4_AURAAgent` (13/08/2026) é uma boa reconstrução e **já funciona parcialmente**: o dashboard de abertura roda ponta a ponta, com 422 iniciativas, €412,637 Mi de benefício, €311,092 Mi de budget e 61% on schedule. Voltaram as 5 tools do DevOps, as 3 do Power BI, a do Teams, as 2 fontes de conhecimento e o idioma pt-BR.

O que falta é um defeito único, repetido em 5 tools.

### 👉 [**Comece por aqui: `00-comece-aqui.md`**](docs/standard/00-comece-aqui.md)

O checklist linear — o que fazer, em que ordem, o que depende de terceiros e o teste que prova que cada bloco acabou. É o único documento que você precisa abrir para trabalhar; os outros são referência.

| Bloco | O quê | Tempo | Depende de |
|---|---|---|---|
| **0** | Pedir liberação de app personalizado no Teams Admin Center | 2 min | — (mas destrava o B) |
| **A** | 4 correções de tool — é onde o agente destrava | ~40 min | ninguém ✅ |
| **B** | Publicar no Teams + completar a tool | ~20 min | Bloco 0 aprovado |
| **C** | Migrar para a arquitetura de 3 camadas | ~20 min | Bloco A |
| **D** | Polimento | ~15 min | ninguém |

### Referência

| Documento | Para quê |
|---|---|
| [`01-diagnostico-aura-agent.md`](docs/standard/01-diagnostico-aura-agent.md) | Auditoria tool a tool, com a evidência tirada do seu próprio log de conversa |
| [`02-correcao-das-tools.md`](docs/standard/02-correcao-das-tools.md) | O que abrir e o que colar, com teste de aceite por tool |
| [`03-teams-conversa-com-gestor.md`](docs/standard/03-teams-conversa-com-gestor.md) | Por que o dropdown **Agent** está vazio, e como o agente conversa com o gestor |
| [`09-erro-400-label-as-notification.md`](docs/standard/09-erro-400-label-as-notification.md) | **O 400 do Teams** — causa-raiz provada no log, a correção de 1 campo e a auditoria da tool |
| [`04-work-iq.md`](docs/standard/04-work-iq.md) | O que é, quanto custa, e por que ele **não** resolve a cobrança do gestor |
| [`05-arquitetura-3-camadas.md`](docs/standard/05-arquitetura-3-camadas.md) | Por que os tópicos saíram, as três camadas e o checklist de cobertura |
| [`06-fluxo-transcricoes.md`](docs/standard/06-fluxo-transcricoes.md) | Fluxo do Power Automate para levar a transcrição da LT ao SharePoint — duas rotas |
| [`07-criar-e-remover-projeto.md`](docs/standard/07-criar-e-remover-projeto.md) | As tools `Create` e `Remove Project` — e por que `Remove` não remove |
| [`agent/instructions-standard.md`](agent/instructions-standard.md) | As instruções para colar — 6.367 caracteres, contra 8.096 das antigas |
| **Dois tetos do produto** | Instruções ~8.000 no total · **descrição de entrada 1.024 por entrada**. `validate-topics.py` mede os dois |
| [`playbook/`](playbook/) | O playbook analítico (`.md` versionado + `.docx` para o SharePoint) |
| [`topics/`](topics/) | ⛔ Os dois tópicos, **descontinuados** — mantidos como histórico e caminho de volta |

### O defeito, em uma frase

No classic, a lista `inputs:` de uma tool é **o que o orquestrador consegue preencher**. Um tópico passa argumento por binding mesmo sem o input declarado — por isso sua abertura funciona. Mas o modelo só enxerga o que está declarado como entrada dinâmica.

| Tool | Falta | Chamada por tópico? | Efeito |
|---|---|---|---|
| `Power BI Portfolio Database` | `query` | Sim | Abertura ✅, mas o modelo **não escreve DAX** — morre a análise sob demanda |
| `Obter os detalhes do work item` | `id` | Sim | Deep Dive ✅, mas o modelo não puxa work item sozinho |
| `Query Devops BU` | `queryId` | Não | Inútil |
| `Update Project` | `type`, `userEnteredFields` | Não | **Não atualiza nada** |
| `Teams — Postar mensagem` | `body.bot` vazio, `recipient`, `messageBody` | Não | Não envia |

Sumiram também três descrições que faziam o trabalho pesado: o dicionário DAX do input `query`, o formato JSON do `userEnteredFields`, e o `SILENT TOOL. DO NOT generate text` da tool de detalhes.

### As respostas rápidas

**Teams — o dropdown vazio.** `body.bot` é um campo `dynamicValuesConfig: capability: List`, preenchido por uma chamada que lista **agentes publicados no Teams**. Seu agente nunca foi publicado. Publique (admin center → canal Teams → publicar → instalar) e ele aparece. E o cenário de mão dupla funciona: a mensagem cai no chat 1:1 do gestor **com o agente**, então a resposta dele volta como turno normal de conversa.

**Work IQ.** Existe no standard, via **Ferramentas → Model Context Protocol → Work IQ (preview)**. Duas ressalvas: é cobrado por **consumo em Copilot Credits** (reintroduz o custo de que você fugiu ao sair do motor do GitHub Copilot), e roda no contexto do **usuário logado** — lê a caixa de quem fala com o agente, **não a do gestor**. Não substitui a mensagem proativa.

---

## Material compartilhado pelas duas trilhas

Vale igual no standard e na experiência nova. No standard vira **descrição de entrada de tool**; na nova, `references/` de skill.

| Arquivo | Conteúdo |
|---|---|
| [`dax-cookbook.md`](skills/portfolio-overview/references/dax-cookbook.md) | Colunas válidas e 9 receitas de DAX (watermelons, big rocks, governança, filtro Cross-BU) |
| [`campos-devops.md`](skills/update-devops/references/campos-devops.md) | Todos os reference names `Custom.*`, os read-only proibidos e os domínios fechados |
| [`query-ids.md`](skills/portfolio-overview/references/query-ids.md) | Query IDs do DevOps por IT Area e por BU |
| [`riscos-e-fases.md`](skills/portfolio-overview/references/riscos-e-fases.md) | As 13 fases, limiares de risco, campos obrigatórios e condicionais |
| [`agent/instructions.md`](agent/instructions.md) | Instruções reescritas e enxutas |

---

## Scripts

```bash
python3 scripts/validate-topics.py      # valida topics/*.yaml e confere as tools referenciadas
./scripts/validate-skills.sh            # valida os SKILL.md (trilha da experiência nova)
./scripts/build-skill-packages.sh       # empacota as skills em dist/*.zip
```

O `validate-topics.py` confere que YAML é parseável, que o root é `AdaptiveDialog`, que os ids de nó são únicos e que **toda tool referenciada existe de fato no agente exportado** — é o tipo de erro que só aparece em runtime.

---

## ⚪ Trilha da experiência nova

Material da tentativa anterior, mantido como referência: [`docs/nova-experiencia/`](docs/nova-experiencia/), [`skills/`](skills/), [`dist/`](dist/). Continua válido se um dia essa trilha voltar a fazer sentido — e o diagnóstico daquele export explica por que ela não funcionou.

---

## Origem dos dados

Todo GUID, Query ID, `operationId`, coluna DAX e reference name `Custom.*` deste repositório foi extraído dos exports do próprio agente e conferido linha a linha. **Nada foi inventado.**

Onde não consegui verificar sem acesso ao tenant — o binding dos campos do Teams e o formato de data aceito pelo `Custom.GoLiveDate` — está marcado explicitamente em [`topics/README.md`](topics/README.md), com o teste para descobrir e o que trocar.
