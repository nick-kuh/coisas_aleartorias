# 5. Arquitetura de 3 camadas — tirar os tópicos, libertar o agente

> **O que mudou:** o agente deixa de depender de tópicos (fluxos determinísticos) para cobrar gestor e gravar no DevOps. Passa a decidir sozinho, guiado por instruções enxutas, descrições de input e um playbook no SharePoint.

---

## Por que mudar

### 1. As instruções antigas estavam truncadas

**8.096 caracteres**, acima do limite de ~8.000 do Copilot Studio. O corte come o **fim** do texto — e o fim era justamente onde moravam os formatos de relatório, o bypass de onboarding e a lista de campos obrigatórios.

O agente não estava "burro". Estava lendo instruções incompletas.

### 2. Tópico é prisão, não capacidade

Tópico é um **dialog determinístico**. Uma vez disparado por uma frase-gatilho, ele executa o script do começo ao fim e o agente perde a capacidade de raciocinar dentro dele. Para cobrança de gestor isso é o oposto do desejado: quem decide **se**, **quando** e **o que** cobrar deveria ser a análise, não um gatilho de frase.

### 3. A prova de que instrução funciona já existia

No log do `botContent_73`, **sem nenhum tópico envolvido**, o agente terminou uma análise de Make/BPC oferecendo espontaneamente cobrar a governança com a gestora via Teams. Ele já fazia o que o tópico prometia — o tópico estava tirando capacidade, não dando.

---

## As três camadas

| Camada | Carrega quando | O que vai nela | Garantia |
|---|---|---|---|
| **Instruções** (6.440 chars) | sempre, toda mensagem | persona, roteamento, inegociáveis, as 4 lentes, protocolo Teams | ✅ **total** |
| **Descrição de tool/input** | quando o modelo considera aquela tool | DAX, reference names, fases válidas, formatos, read-only | ✅ **alta** |
| **SharePoint (playbook)** | busca semântica, sob demanda | frameworks analíticos, definições, exemplos, matriz completa | ⚠️ **probabilística** |

### A camada do meio é a descoberta

A descrição de input **já funcionava no seu agente e passou despercebida**. Foi ela que fez o DAX começar a sair correto — o dicionário de colunas vive na descrição do input `query`, e o log prova a autoria do modelo:

```json
{"arguments": {"query": "EVALUATE FILTER('tabela', 'tabela'[IT Area] = \"Make (Business Operation)\" && ..."},
 "autoFilledArguments": ["query"]}
```

`autoFilledArguments` é o campo que separa "o tópico passou isso" de "o modelo escreveu isso". Aqui foi o modelo.

Por que essa camada é boa: carrega **só quando relevante**, é lida no momento exato da decisão, e **não consome o orçamento de 8.000 caracteres das instruções**. É onde ficam as restrições que antes só o `ConditionGroup` do tópico garantia.

### ⚠️ Correção de expectativa sobre o SharePoint

O playbook **não é lido toda conversa**. Ele é recuperado por **busca semântica**: o agente consulta quando julga relevante, e recebe trechos, não o arquivo inteiro.

Não existe "leia obrigatoriamente este arquivo sempre". Por isso a regra é firme:

> **Regra inegociável nunca vai para o SharePoint.** Vai para as instruções, que carregam sempre.

O SharePoint carrega o que é **profundo mas dispensável numa resposta qualquer**: a matriz completa por fase, o raciocínio por trás de cada limiar, exemplos de análise fraca vs forte.

---

## Checklist de cobertura

Toda regra que saiu das instruções tem que reaparecer em outra camada. Item a item:

| Regra removida das instruções | Reaparece em | Camada |
|---|---|---|
| Dicionário de colunas do Power BI | descrição do input `query` | 🟢 alta |
| Regras de escrita DAX (EVALUATE, `'tabela'`, sem markdown) | descrição do input `query` | 🟢 alta |
| Filtro Cross-BU com `SEARCH` em `[Specify Cross]` | instruções §3 **+** descrição do `query` (regra 5) | ✅ dupla |
| Tradução de acrônimos (BPC, HPC, HPF) | instruções §3 **+** descrição do `query` (regra 6) | ✅ dupla |
| Lista literal das 13 fases | descrição do `userEnteredFields` **+** playbook §2 | ✅ dupla |
| Matriz de campos obrigatórios por fase | instruções §6 (resumo) **+** playbook §5 (completa) | ✅ dupla |
| `10 Deployed` / `11 Closed` nunca sinalizar | instruções §5 **+** descrição do `userEnteredFields` **+** playbook §2 | ✅ tripla |
| Reference names `Custom.*` | descrição do `userEnteredFields` **+** playbook §3 | ✅ dupla |
| Campos read-only que quebram o PATCH | descrição do `userEnteredFields` | 🟢 alta |
| Formato de data e de número na escrita | descrição do `userEnteredFields` | 🟢 alta |
| Limiares de risco (60d, 30d, PGLS 3m, 5 Big Rocks) | instruções §5 **+** playbook §4 | ✅ dupla |
| Definição de watermelon | instruções §5 **+** playbook §4 | ✅ dupla |
| Ecossistemas (`Horizon 1`/`Horizon 2`, tag `Related`) | instruções §3 **+** playbook §7 | ✅ dupla |
| Formatos de relatório (dashboard vs deep dive) | instruções §9 **+** playbook §6 | ✅ dupla |
| Bypass de pergunta conceitual (sem query) | instruções §9 | ✅ total |
| Nunca inventar dado | instruções §9 **+** aviso no topo do playbook | ✅ dupla |
| Nunca expor query, GUID, JSON | instruções §9 | ✅ total |
| **Mecânica do FinalScore** | **eliminada por decisão** — playbook §1 define o novo uso | ⚪ intencional |

### As duas garantias que os tópicos davam

Estas merecem atenção separada, porque são o custo real da troca:

| Garantia | Onde estava | Onde está agora |
|---|---|---|
| Confirmar antes de **enviar Teams** | `ConditionGroup` do `cobrancagestor` | instruções §7, passos 3–4 |
| Confirmar antes de **gravar no DevOps** | `ConditionGroup` do `respostadogestor` | instruções §8 **+** última linha da descrição do `userEnteredFields` |

**Sendo direto sobre o custo:** um `ConditionGroup` de tópico *executa* — não tem como o modelo contornar. Uma instrução é seguida quase sempre. Para envio de mensagem e escrita em DevOps, "quase sempre" é um risco real, e você está optando por ele em troca de flexibilidade.

A mitigação é colocar as duas restrições **na camada de descrição de input** — a que já provou aderência neste agente. Se a escrita indevida acontecer, o caminho de volta é recriar só o `respostadogestor`, que segue versionado em [`topics/`](../../topics/).

---

## A descrição da fonte de conhecimento

É **esta descrição** que dispara a busca semântica. Se ela for genérica, o playbook nunca é consultado.

Ao cadastrar o `.docx` no SharePoint como fonte de conhecimento, cole:

```
AURA Analytical Playbook — the CDIO LATAM portfolio analysis manual.
Consult this source when you need to know: how to evaluate or judge a project or
a portfolio; what the four decision lenses are (valor em risco, momento,
concentração, assimetria); what a project phase means and what is demanded in it
(01 Idea, 02 Scoping, 03 Scope Approv, 04 Costing, 05 Cost Approv, 06 Plan
Analyze, 07 Design Build, 08 UAT, 09 PGLS, 10 Deployed, 11 Closed, 12 On
Holding); which fields are mandatory in each phase; what a specific field means
for the business; what a watermelon, a Big Rock, PGLS, hypercare or Value
Realization is; the risk thresholds and the reasoning behind them; how to
structure a portfolio overview or a project deep dive; the difference between a
weak and a strong analysis; CDIO vocabulary, BU acronyms and the Cross-BU rule.
Contains no live data: every number in it is a frozen illustrative example.
```

A última linha é deliberada. Sem ela o agente pode citar os exemplos do playbook como se fossem a situação de hoje.

---

## O que fazer, na prática

1. **Instruções** — copiar [`agent/instructions-standard.md`](../../agent/instructions-standard.md) inteiro e colar em Copilot Studio → AURA Agent → **Instruções**, substituindo tudo. São 6.440 caracteres, cabem sem truncar.
2. **Descrições de input** — aplicar as duas expandidas em [`02-correcao-das-tools.md`](02-correcao-das-tools.md): `userEnteredFields` (Correção 1) e `query` (Correção 2).
3. **SharePoint** — subir [`playbook/AURA_Playbook_Analitico.docx`](../../playbook/AURA_Playbook_Analitico.docx) na biblioteca do CDIO LATAM, cadastrar como fonte de conhecimento e colar a descrição acima.
4. **Tópicos** — os dois seguem no repositório como histórico, mas saem do caminho crítico. Se já estiverem colados no agente, podem ser removidos.

---

## Como saber se funcionou

| # | Teste | O que prova |
|---|---|---|
| 1 | Colar as instruções | Cabe sem truncar |
| 2 | `analise o projeto <nome>` | Relatório com **decisão recomendada**, sem seção de matemática de score |
| 3 | `quais projetos estão em risco?` | Usa as 4 lentes, cita valor em risco e momento — não "score 86 = verde" |
| 4 | Depois de uma análise que exponha gap | Agente **oferece** cobrar o gestor, sem você pedir |
| 5 | Aceitar a oferta | Mostra rascunho, espera aprovação, só então envia |
| 6 | `mude o State do work item <teste> para 07 Design Build` | Confirma antes e grava com o reference name certo |
| 7 | `como o FinalScore é calculado?` | Aí sim explica a matemática — sob demanda |
| 8 | `o que é um watermelon?` | Responde do playbook, **sem rodar query** — prova que o SharePoint está sendo recuperado |

O teste 8 é o que valida a terceira camada. Se ele falhar, a descrição da fonte de conhecimento é o lugar para mexer — não o playbook.
