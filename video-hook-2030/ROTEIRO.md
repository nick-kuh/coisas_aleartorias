# Race to 2030 — Promo (CDIO LATAM · 2027 Big Bets)

Vídeo de abertura para os VPs, em formato promo: **~82 s**, 1920×1080, 30 fps.
São 24 cenas sincronizadas com a voz e com a batida da música. A narração é contínua, as cenas ficam
de 2 a 5 s na tela e as transições são suaves (~0,9 s).

- **Vídeo final:** `out/race-to-2030-hook.mp4`. Tem narração em inglês (voz feminina de IA), trilha original
  e volume no padrão de vídeo online (−16 LUFS). A música abaixa sozinha quando a voz fala.
- **Versão anterior:** `out/versao-apresentacao-94s.mp4`, a de 94 s no estilo apresentação, mantida para comparação.
- **Visual:** segue o `CDIO_LATAM_2027_Strategy_E3_v11 1.html`:
  - fundo "papel" `#F7F6F3` e tinta `#121A2E`;
  - fonte Inter (light + bold) e eyebrows com traço;
  - as 8 cores de estratégia e a linha em degradê que "cresce";
  - os badges, os chips BR · MX · AR e o núcleo "AI @ Scale".

  A jornada 2026 → 2030 vem do slide "Journey Data & Technology" que está dentro desse HTML.
- **Números:** também saem do HTML do CDIO:
  - 3 estratégias e 5 pilares (as **28 iniciativas** vêm da correção do time: a planilha do HTML lista 26);
  - os valores de benefício (€) **não** aparecem no vídeo, nem na tela nem na voz.
- **Transições:** wipe com a faixa degradê, push lateral, rise, zoom suave e crossfade (o texto antigo sai
  antes do novo entrar). Flash e "camera shake" leves só nos 3 grandes momentos: 2030, o drop e Big Bets.

## Roteiro (o que a voz fala)

A narração é **contínua**, como um locutor contando uma história, e não lendo slide por slide. Ela é
gerada em 6 blocos corridos, e a imagem troca **durante** a fala: cada corte entra no momento em que a palavra
é dita, com a transição começando um pouco antes. As únicas pausas maiores são as intencionais: o impacto do
2030 no começo e a subida da música antes do drop em "Accelerate".

| Tempo | Cena | Narração |
|---|---|---|
| 0:00 | **Hook**: contador 2026 → 2030 na linha da jornada, impacto em 2030 | "The race to 2030… is already underway." |
| 0:05 | "now." → (no mesmo quadro) "lead tomorrow." | "The decisions we make now determine whether we lead tomorrow." |
| 0:08 | Proven strengths: Stores · Logistics capabilities & S&OP · **AI no dia a dia das nossas pessoas** (pessoas conectadas ao núcleo de IA) · Tax Reform (BR) \| Factory (BR · MX · AR) | "We have proven strengths: improvements in execution, aiming for best-in-class execution in stores, strong evolution in Logistics capabilities and S&OP, AI included in the day-to-day of our people, and critical progress on Tax Reform Compliance and Factory Transformation." |
| 0:27 | **A virada**: a música para | "But leadership requires more than operational excellence. It requires growth acceleration." |
| 0:33 | **DROP**: "Accelerate" | *(música)* |
| 0:35 | Data Agenda gap · TPM Journey · Social Commerce (Discover → Engage → Buy) · "faster." | "Our Data Agenda gap is a big opportunity. Our TPM Journey needs stronger momentum. And Social Commerce is reshaping how consumers discover, engage, and buy. We must move faster to unlock its full potential," |
| 0:49 | **AI-First** (núcleo AI @ Scale) | "…on the way to an AI-First Unilever by 2030." |
| 0:53 | Our strategy is clear → Reinforce / Accelerate / Concentrate | "Our strategy is clear: reinforce what already makes us strong, accelerate the capabilities that define our future, and concentrate on the few bets with disproportionate impact for LATAM." |
| 1:05 | **2027 Big Bets** → 3 · 5 · 28 | "Our 2027 Big Bets turn that strategy into action: three strategies, five pillars, and 28 initiatives," |
| 1:13 | Today's core → Tomorrow's advantage | "…strengthening today's core while building tomorrow's advantage." |
| 1:16 | **The race is on.** → logo Unilever · GDT | "The race is on." |

O que entrou além do texto original:
- Os números do HTML do CDIO (3 estratégias · 5 pilares) e as 28 iniciativas.
- O fechamento "The race is on.", que retoma o "The race to 2030" do começo.

Os dois estão em `CUES`, no `audio/narration.py`, e dá para tirar.

Na lista de forças, "we include AI in the day-to-day of our people" é falado como "AI included in the
day-to-day of our people", para a frase continuar corrida junto com os outros itens (linha `ppl.a` em `CUES`).

Pronúncias fixadas à mão: *Unilever* ("YOO-ni-lee-ver"), *LATAM* ("LAH-tam"), *AI* ("A-I") e o "and" de
"Logistics and S&OP".

## Trilha sonora

Original e sintetizada do zero (`audio/soundtrack.py`), 110 BPM, no mesmo grid da voz:
- **Hook:** relógio acelerando, "ticks" a cada virada do contador, riser e **impacto** quando crava 2030.
- **Forças:** batida four-on-the-floor e um "ping" em cada check, com um brilho de sinos quando "our people" acendem
  em volta do núcleo de IA.
- **Virada:** a música some em "more than operational excellence". Depois vêm rufar de caixa e riser, um
  respiro de silêncio e o **drop** em "Accelerate".
- **Impactos:** em AI-First, em cada verbo (Reinforce / Accelerate / Concentrate), no 2027 e nos números (3 · 5 · 28).
- **Fim:** hit final em "The race is **on**", com o acorde soando sobre o logo.

## Como gerar de novo

```bash
pip install -r audio/requirements-voice.txt     # veja as notas no arquivo (modelo do spaCy)
python audio/narration.py        # voz -> out/narration.wav + timeline.js (cortes e tempo de cada palavra)
npm install && node render.mjs   # imagem -> out/video.mp4
python3 audio/soundtrack.py      # música -> out/soundtrack.wav (segue o timeline.js)
python3 audio/mux.py --voice out/narration.wav   # tudo junto -> out/race-to-2030-hook.mp4
```

- Para mudar o texto, a voz ou a velocidade, edite `CUES` / `VOICE` / `SPEED` em `audio/narration.py` e
  rode os 4 passos. Os cortes e a música se ajustam sozinhos à nova fala.
- `PASSAGES` define quais frases saem num fôlego só, e `shots` (no fim do script) define em que palavra
  entra cada cena.
- `node render.mjs --stills 3,20,55` gera quadros soltos para conferir.
- `index.html` abre no navegador como prévia, com barra de rolagem e Espaço para pausar.
- **Fonte:** Inter (licença OFL), a mesma do HTML do CDIO.

## Vídeo dentro da página do CDIO (HTML)

`out/CDIO_LATAM_2027_Strategy_E3_v18.html` é a página da estratégia (v14) com o vídeo **dentro do próprio
arquivo** (~12 MB, um único HTML). Toda vez que alguém abre a página, a intro aparece primeiro:

- Se o navegador deixa o vídeo tocar com som sozinho, ele já começa. Se não deixa (o padrão do Edge e do
  Chrome), aparece o botão **▶ Play intro** sobre a capa, e um clique toca com som.
- A barra acompanha o vídeo de verdade. Quando ele termina, a estratégia aparece sozinha.
- "Go to 2027 Strategy", Esc ou Enter pulam a intro. Espaço pausa. O botão **Watch intro**, no canto, revê.
- Funciona offline, de qualquer pasta, sem login. Não depende mais do link do SharePoint/Stream, que exigia
  login e era bloqueado com o arquivo aberto localmente.

Para gerar de novo depois de mudar o vídeo:

```bash
python3 embed_intro.py CDIO_LATAM_2027_Strategy_E3_v14.html   # -> out/CDIO_LATAM_2027_Strategy_E3_v18.html
```

### Compartilhar pelo Teams

A prévia do Teams/SharePoint **não roda JavaScript**. Por isso, ao clicar no HTML dentro do Teams, o vídeo
fica "carregando" e para na capa, e a parte interativa da estratégia também não funciona. Não tem como o
arquivo contornar isso: quem recebe precisa **baixar o arquivo e abrir no Edge ou no Chrome**.

Para ninguém ficar travado, a página agora mostra um aviso com esses dois passos:
- quando a prévia não roda scripts (caso do Teams);
- quando o visualizador bloqueia o player ou não tem o codec do vídeo;
- quando o vídeo fica 8 s sem sair do lugar depois de pedir para tocar.

Em qualquer caso, "Go to 2027 Strategy" (ou Esc) continua levando direto para a página.

Se a ideia for só mostrar o vídeo no chat, mande também o `out/race-to-2030-hook.mp4`. O Teams toca MP4
direto na conversa, sem baixar.
