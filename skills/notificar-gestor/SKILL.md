---
name: notificar-gestor
description: >
  Envia uma mensagem de cobrança pelo Microsoft Teams ao IT Manager responsável
  por um projeto do portfólio CDIO LATAM — tipicamente quando o projeto está
  atrasado, parado além do limite da fase, ou com campo obrigatório de
  governança em branco. Identifica o gestor a partir dos dados do projeto,
  redige o rascunho com os fatos concretos (ID, fase, dias parado, o que falta,
  o que se espera) e SEMPRE mostra o rascunho para aprovação antes de enviar.
  Use quando pedirem "avise o gestor", "cobre o responsável", "manda mensagem
  para o dono do projeto X", "notifique quem está atrasado".
  NÃO use para responder perguntas ao próprio usuário, nem para alterar dados
  no DevOps (use update-devops).
---

# Notificar gestor via Teams

⚠️ Esta skill **envia mensagem para outra pessoa**. Uma mensagem enviada não volta atrás. O passo de aprovação não é opcional.

## Passo 1 — Identifique o projeto e o gestor

Se o usuário deu o nome, chame **`Power BI Master DB Search`**:

```dax
EVALUATE FILTER('tabela', SEARCH("<nome>", 'tabela'[Short Name], 1, 0) > 0 || SEARCH("<nome>", 'tabela'[Title], 1, 0) > 0)
```

Colete `[Work Item Id]`, `[Short Name]`, `[Project IT Manager]`, `[StatusProjeto]`, `[GoLive Date]`, `[N State]`.

Depois chame **`DevOps Work Item Details`** com o ID para pegar o `Assigned To` oficial e o histórico recente.

| Situação | O que fazer |
|---|---|
| Gestor identificado em ambas as fontes e batem | Siga |
| Fontes divergem | Mostre as duas opções e **pergunte para quem enviar** |
| Nenhuma fonte traz o gestor | **Pare.** Diga que não foi possível identificar o responsável e peça o nome |
| Múltiplos projetos com o nome | **Pare.** Peça o ID exato |

⛔ **Nunca deduza o e-mail de um gestor a partir do nome.** Se você não tem o endereço vindo do sistema, peça.

## Passo 2 — Monte o caso concreto

Uma cobrança sem fato é ruído. Levante, do que já veio das ferramentas:

- **O que está errado** — atrasado, parado há X dias em uma fase, campo obrigatório em branco, Go-Live estourado, PGLS infinito. Limiares em `references/riscos-e-fases.md`
- **Desde quando** — data ou nº de dias
- **O que se espera** — a ação concreta e o prazo

Se houver contexto relevante em **`Transcription LT Meetings`** (algo que esse gestor prometeu na última reunião), inclua. É o que transforma cobrança genérica em cobrança que não tem resposta.

## Passo 3 — Rascunho + aprovação (obrigatório)

Mostre exatamente isto e **pare**:

```
✉️ **Rascunho da mensagem**

**Para:** [Nome do gestor] ([e-mail])
**Projeto:** [Short Name] — #[ID]
**Motivo:** [o problema, em uma linha]

---
[texto da mensagem]
---

Posso enviar? Responda **sim** para disparar no Teams, ou me diga o que ajustar.
```

**Não chame a tool do Teams antes de um "sim" explícito.** Se o usuário pedir ajuste, refaça o rascunho e pergunte de novo.

### Tom da mensagem

Direto, factual, profissional. Cobra o dado, não a pessoa. Sempre com o link do work item.

```
Oi [Nome], tudo bem?

Passando sobre o **[Short Name]** (#[ID]), que está em **[fase]** desde [data].

[O fato: o que está faltando ou atrasado.]

Você consegue [ação esperada] até [prazo]? Se houver algum bloqueio, me avisa que eu levo para a LT.

🔗 https://dev.azure.com/CDIO-IT-LATAM/CDIO%20Portfolio/_workitems/edit/[ID]
```

## Passo 4 — Envie

Só depois do "sim", chame **`Teams — Postar mensagem`** com o destinatário e o texto aprovados.

> A tool usa credencial do usuário final (`authMode: Invoker`) — a mensagem sai **como o usuário**, não como um bot. É o comportamento certo para cobrança, e significa que na primeira vez a pessoa precisa autorizar a própria conexão do Teams.

## Passo 5 — Confirme

```
✅ Mensagem enviada para **[Nome]** sobre o **[Short Name]** (#[ID]).
```

Se falhar, mostre o erro real e ofereça o texto pronto para o usuário copiar e colar. **Nunca diga que enviou se não enviou.**

## Cobrança em lote

Se pedirem para avisar **todos** os gestores de projetos atrasados:

1. Levante a lista com a **`Power BI Portfolio Database`** (receitas em `../portfolio-overview/references/dax-cookbook.md`)
2. Apresente a lista consolidada **primeiro**: quem, qual projeto, qual problema
3. Peça aprovação **da lista inteira**, e ofereça a opção de tirar alguém
4. Envie um a um, confirmando o total no fim

⛔ **Nunca dispare lote sem essa revisão.** Cinco mensagens erradas são cinco erros, não um.

## Guardrails

- **Nunca invente** fato, número, data ou prazo. Cada afirmação da mensagem tem que vir de uma chamada bem-sucedida nesta conversa.
- **Nunca** notifique projeto em `10 Deployed` ou `11 Closed` — foi entregue, não se cobra.
- Datas em DD/MM/YYYY.
- Se o usuário pedir para enviar algo agressivo ou pessoal, reescreva em tom profissional e mostre a versão reescrita para aprovação.
- Se o usuário mandar "envia" antes de você ter mostrado o rascunho, mostre o rascunho mesmo assim.
