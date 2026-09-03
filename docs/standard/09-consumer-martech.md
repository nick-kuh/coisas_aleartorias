# 9. Consumer BPC (B&W MarTech) — conectar ao agente e gerar o HTML

O time de **Consumer** roda fora do DevOps: o portfólio dele vive no tracker Excel
`BW_MarTech_2026_Controle_Projetos.xlsx`. Este guia conecta esse mundo ao agente
(Copilot Studio) e explica como o HTML da agenda sai — pelo agente ou automático.

São **três peças**, na mesma lógica do resto do agente:

| Peça | O quê | De onde |
|---|---|---|
| **Knowledge** | O Excel vira a fonte `Consumer MarTech Tracker` | `data/BW_MarTech_2026_Controle_Projetos.xlsx` |
| **Instruções** | O roteamento que manda toda pergunta de Consumer para o mundo certo | `agent/instructions-standard.md` (§2) |
| **Skill** | O esquema que ensina a analisar Consumer e montar o HTML | `dist/consumer-martech.zip` |

---

## Etapa 1 — Knowledge: subir o tracker (5 min)

O agente precisa **ler o Excel**. Coloque-o onde ele lê as outras fontes.

1. Suba `data/BW_MarTech_2026_Controle_Projetos.xlsx` para o **SharePoint/OneDrive**
   do time (o mesmo lugar das outras fontes, ver §Etapa 4 do passo-a-passo).
2. Em Copilot Studio → **Conhecimento → Adicionar conhecimento → Arquivos**
   (ou SharePoint), aponte para o arquivo.
3. **Dê a ele exatamente o nome `Consumer MarTech Tracker`** — é esse nome que a
   skill e o validador esperam. Se usar outro nome, ajuste também em
   `scripts/validate-skills.sh` (lista `KNOWLEDGE_OFICIAL`) e na skill.

> Dica: mantenha a planilha com as abas **Tracker**, **Painel** e **Legenda** como
> estão. A skill conta o farol pela mesma regra do Painel.

**Descrição sugerida** (cole no campo "Descrição" do conhecimento — é o que ajuda o
agente a saber quando puxar dessa fonte):

> Tracker de projetos do time de Consumer BPC (B&W Marketing Technology) — o
> portfólio que roda fora do DevOps. Traz as iniciativas organizadas por frente
> (Insights, Media & Influencer, dCom and Social Commerce, CoPilot and Agentic,
> LLM Search / GEO, Beauty Tech), a fase de cada uma (Adoption, Deployment,
> Framework, Status) e o farol de status por mercado — BR (Brasil), MX (México),
> AR (Argentina): No prazo, Atenção, Crítico, Não iniciado, N/A. Abas: Tracker
> (linha a linha), Painel (saúde por frente) e Legenda. Fonte única para qualquer
> pergunta sobre Consumer/MarTech, as frentes, o farol por país, uma iniciativa do
> tracker ou o dashboard de Consumer. Não usar para o portfólio DevOps/Power BI.

Versão curta, se o campo for pequeno:

> Portfólio do time de Consumer BPC (B&W Marketing Technology), fora do DevOps:
> iniciativas por frente, fase (Adoption/Deployment/Framework/Status) e farol de
> status por mercado (BR/MX/AR). Fonte única para perguntas de Consumer/MarTech e
> o dashboard de Consumer.

✅ **Teste de aceite:** pergunte ao agente "quais frentes existem no Consumer?".
Ele deve listar as seis (Insights, Media & Influencer, dCom and Social Commerce,
CoPilot and Agentic, LLM Search / GEO, Beauty Tech) **a partir do tracker**.

---

## Etapa 2 — Instruções: o roteamento (2 min)

As instruções já trazem o roteamento (bloco "Consumer BPC / B&W Marketing
Technology" em §2 e o alerta dos "dois Consumers" em §3). Se você ainda não colou a
versão nova, reaplique `agent/instructions-standard.md` (cole do `.md` cru, sem
editor de texto rico — ver Etapa 2 do passo-a-passo).

✅ **Teste de aceite:** pergunte "como está o dCom no Consumer?". O agente responde
pelo tracker, **sem** chamar Power BI/DevOps e **sem** citar Work Item Id.

---

## Etapa 3 — Skill: subir o esquema (3 min)

1. Gere/atualize o pacote: `./scripts/build-skill-packages.sh` (cria
   `dist/consumer-martech.zip`, já com o SKILL.md, as referências, **o logo** e a
   **fonte** embutidos).
2. Em Copilot Studio → **Skills → Adicionar skill → Carregar arquivo** →
   `dist/consumer-martech.zip`.

✅ **Teste de aceite:** peça "faça uma análise do portfólio de Consumer". O agente
deve cruzar as quatro lentes (realização de valor Deployment×Adoption, críticos,
concentração por mercado, backlog) e nomear os 2 críticos (Insights / 5Vs Dashboard
e Insights / FIBRA, ambos na adoção do Brasil).

---

## Como o HTML é gerado

Há **dois caminhos**. Use o que fizer sentido para cada situação.

### Caminho A — o agente gera na conversa (on-demand)

Peça: **"monte o HTML da agenda de Consumer"**. A skill `consumer-martech`
(Passo 5 + `references/html-template.md`) faz o agente devolver a página inteira
num bloco de código. Você copia e salva como `.html`.

- Bom para: um recorte rápido, uma versão para colar num e-mail/Teams.
- Ressalva: o logo (`references/logo-bw.svg`, ~48 KB) e a fonte
  (`references/poppins-inline.css`, ~43 KB) são grandes. Um modelo de chat nem
  sempre reproduz esses blocos base64 **byte a byte**. Se o logo/fonte saírem
  quebrados, use o Caminho B — ele é à prova de erro.

### Caminho B — geração automática, fiel (recomendado para o board oficial)

```bash
python3 scripts/gerar-consumer-html.py
# ou apontando para outra planilha / saída:
python3 scripts/gerar-consumer-html.py caminho/tracker.xlsx saida.html
```

O script lê o Excel e escreve `consumer-martech.html` **perfeito** — logo oficial e
fonte Poppins embutidos, farol por mercado, tom claro. É o mesmo esquema da skill,
mas determinístico. Toda vez que o tracker mudar, rode de novo.

> **Automatizar de vez:** dá para agendar o Caminho B num **Power Automate** (ou
> num job): gatilho "quando o Excel no SharePoint mudar" → rodar o script (via um
> runner Python/Azure Function) → publicar o `consumer-martech.html` num site
> interno ou canal do Teams. Assim o board se atualiza sozinho a cada semana.

---

## Resumo do fluxo

```
Excel (tracker)  ──►  Knowledge "Consumer MarTech Tracker"  ──►  agente analisa
      │                                                             (skill consumer-martech)
      └──►  scripts/gerar-consumer-html.py  ──►  consumer-martech.html (board fiel)
```

O agente **analisa e responde** sobre Consumer a partir do tracker; o **HTML** sai
pela skill (rápido) ou pelo script (fiel). Os dois falam a mesma língua — frentes,
fases, farol por mercado — definida em `skills/consumer-martech/`.

---

## Fazer o Consumer NUNCA entrar no DevOps

No agente exportado, duas coisas ainda puxam Consumer para o DevOps. Ajuste as duas.

### 1. Regra dura nas instruções (colar no topo)

Um único bullet no meio do roteamento é fraco perto de tudo que é DevOps. Cole este
bloco **enxuto como `# 0.`, no topo das instruções** (antes de `# 1. PERSONA`). Ele
domina o resto e ainda **libera o agente a montar o HTML** (senão o `# 11` o proíbe).
É curto de propósito: o campo de Instruções tem teto de ~8000 caracteres, então
prefira este `# 0.` compacto e **apague o bullet de Consumer do `# 2`** (fica
redundante).

```
# 0. CONSUMER = EXCEL ONLY (overrides everything below)
Consumer BPC / B&W Marketing Technology / MarTech — the 6 frentes (Insights, Media &
Influencer, dCom and Social Commerce, CoPilot and Agentic, LLM Search / GEO, Beauty
Tech), the BR/MX/AR farol, its initiatives and its dashboard/HTML — is the Consumer
MarTech Tracker Excel (BW_MarTech_2026_Controle_Projetos.xlsx), nothing else. Answer
it 100% from that Excel via the consumer-martech skill; NEVER use Power BI, DevOps or
the report tool, and never invent a Work Item Id, DAX or budget. To build its board
you DO write the HTML yourself (consumer-martech template + logo-bw.svg +
poppins-inline.css inline) — the DevOps report rule is the only "never hand-write
HTML". The DevOps IT Area Consumer is separate: use DevOps for "Consumer" only if the
user writes "DevOps".
```

Marque também o `# 11` como do DevOps: `# 11. THE PORTFOLIO REPORT (DevOps only — §0)`.

### 2. Tirar "Marketing"/"Consumer" do gatilho do relatório DevOps

O tópico **`CreateReport`** (o relatório executivo que roda Power BI/DevOps) mapeia a
palavra digitada para uma IT Area. Hoje ele tem:

```
"CONSUMER" in Upper(System.Activity.Text) Or "MARKETING" in Upper(System.Activity.Text), "Consumer",
```

Isso faz "Marketing"/"Consumer" cair no relatório DevOps. Ajuste em **Tópicos →
CreateReport → nó "set_area" (e o "set_area2")**:

- **Mínimo (recomendado):** tire o `Or "MARKETING" ...` — Marketing é o mundo Excel.
  Fica só `"CONSUMER" in Upper(System.Activity.Text), "Consumer",`.
- **Total (se você quer que nem "Consumer" gere relatório DevOps):** remova a linha
  inteira do Consumer. Aí o relatório DevOps do Consumer só sai se você mudar o
  mapa de propósito. O `# 0.` já manda o agente tratar Consumer pelo Excel.

### 3. Confira o nome do conhecimento

No export a fonte está como **`BW_MarTech_2026_Controle_Projetos.xlsx`**. Funciona
(o roteamento usa a descrição), mas para casar com a skill e ficar óbvio, renomeie o
**display name** do conhecimento para **`Consumer MarTech Tracker`**.

✅ **Teste de aceite:** digite "relatório de Marketing". O agente deve responder pelo
**Excel de Consumer** (frentes/farol) — **não** disparar o relatório DevOps. E ao
pedir "monta o HTML da agenda de Consumer", ele escreve a página do board.
