# Race to 2030 — Promo (CDIO LATAM · 2027 Big Bets)

Vídeo de abertura para os VPs, em formato promo: **~78 s**, 1920×1080, 30 fps.
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
  - 3 estratégias, 5 pilares e 26 iniciativas;
  - €57.1M + €51.06M + €53.784M = **€161.9M** de benefício quantificado.
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
| 0:08 | Proven strengths: Stores · Logistics & S&OP · Tax Reform \| Factory | "We have proven strengths: best-in-class execution in stores, strong Logistics and S&OP, and critical progress on Tax Reform Compliance and Factory Transformation." |
| 0:20 | **A virada**: a música para | "But leadership requires more than operational excellence. It requires acceleration." |
| 0:26 | **DROP**: "Accelerate" | *(música)* |
| 0:27 | Data Agenda gap · TPM Journey · Social Commerce (Discover → Engage → Buy) · "faster." | "Our Data Agenda gap is a big opportunity. Our TPM Journey needs stronger momentum. And Social Commerce is reshaping how consumers discover, engage, and buy. We must move faster to unlock its full potential," |
| 0:42 | **AI-First** (núcleo AI @ Scale) | "…on the way to an AI-First Unilever by 2030." |
| 0:45 | Our strategy is clear → Reinforce / Accelerate / Concentrate | "Our strategy is clear: reinforce what already makes us strong, accelerate the capabilities that define our future, and concentrate on the few bets with disproportionate impact for LATAM." |
| 0:57 | **2027 Big Bets** → 3 · 5 · 26 → €161.9M | "Our 2027 Big Bets turn that strategy into action: three strategies, five pillars, 26 initiatives, and more than 160 million euros in benefit," |
| 1:08 | Today's core → Tomorrow's advantage | "…strengthening today's core while building tomorrow's advantage." |
| 1:12 | **The race is on.** → logo Unilever · GDT | "The race is on." |

O que entrou além do texto original:
- Os números do HTML do CDIO (3 · 5 · 26 · €161.9M).
- O fechamento "The race is on.", que retoma o "The race to 2030" do começo.

Os dois estão em `CUES`, no `audio/narration.py`, e dá para tirar.

Pronúncias fixadas à mão: *Unilever* ("YOO-ni-lee-ver"), *LATAM* ("LAH-tam"), *AI* ("A-I") e o "and" de
"Logistics and S&OP".

## Trilha sonora

Original e sintetizada do zero (`audio/soundtrack.py`), 110 BPM, no mesmo grid da voz:
- **Hook:** relógio acelerando, "ticks" a cada virada do contador, riser e **impacto** quando crava 2030.
- **Forças:** batida four-on-the-floor e um "ping" em cada check.
- **Virada:** a música some em "more than operational excellence". Depois vêm rufar de caixa e riser, um
  respiro de silêncio e o **drop** em "Accelerate".
- **Impactos:** em AI-First, em cada verbo (Reinforce / Accelerate / Concentrate), no 2027 e no €161.9M.
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
