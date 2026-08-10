# Greeting & prompts

**Onde:** Copilot Studio → seu agente → **Settings → Greeting & prompts**

No clássico, a saudação e os 3 atalhos viviam dentro do tópico `Início da conversa`, como `SendActivity` + `suggestedActions` (`botContent.yml` L560–L648). Na nova experiência isso saiu do fluxo e virou configuração.

---

## Mensagem de saudação

```
**{System.Bot.Name} | _See Beyond_**

Olá {System.User.FirstName}. Um instante enquanto eu cruzo os dados do portfólio para montar o dashboard executivo de hoje...
```

> As variáveis `{System.Bot.Name}` e `{System.User.FirstName}` continuam válidas na nova experiência — a sua própria skill migrada já as usa.

---

## Suggested prompts (os chips clicáveis)

Estes são os 3 atalhos que existiam como `suggestedActions` no tópico antigo (L640–L647). **É importante configurá-los aqui e não dentro da skill:** listados no texto da skill eles saem como texto comum; configurados aqui, viram botões que o usuário clica.

| # | Título (curto) | Prompt (o que é enviado) |
|---|---|---|
| 1 | Analisar BPC e Make | `Analise o portfólio de BPC e da IT Area Make` |
| 2 | Projetos Watermelon | `Mostre os projetos watermelon — status verde mas com benefício zerado ou atrasados por dentro` |
| 3 | Top 3 Big Rocks | `Quais são os Top 3 Big Rocks do portfólio hoje?` |

### Bônus — o conversation starter que existia no GptComponent

O clássico tinha ainda um quarto atalho (L2448–L2450), que vale recuperar:

| Título | Prompt |
|---|---|
| Projetos de alto risco | `Identifique todos os projetos antigos parados na fase de Scope sem GoLive Date definida. Analise bloqueios estruturais e indique quais exigem decisão imediata da liderança` |

---

## ⚠️ Um aviso sobre o "carregar o portfólio na abertura"

O tópico antigo era **determinístico**: a conversa começava, o `OnConversationStart` disparava, as duas queries rodavam, ponto.

Na nova experiência, a skill `inicio-de-conversa` é **escolhida** pelo orquestrador. Na prática ela ativa quase sempre — a `description` foi escrita para isso e as instruções reforçam — mas não é uma garantia mecânica.

Se você notar que às vezes o dashboard não aparece na abertura:

1. Reforce na `description` da skill (ela já diz "Use this at the beginning of every conversation").
2. Aceite que o primeiro prompt do usuário dispare o carregamento — funciona igual na prática.
3. Se for inegociável, o único caminho realmente determinístico é um **Workflow** que roda antes e entrega os dados ao agente.

Custo/benefício: a opção 2 resolve 95% dos casos com zero trabalho. Recomendo começar por ela.
