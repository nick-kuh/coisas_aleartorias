# Race to 2030 — Hook (2027 Big Bets · LATAM)

Video de abertura (~87 s, 1920×1080, 30 fps) para o resumo executivo aos VPs.
Visual baseado no **GDT Template.pptx**: paleta *Unilever Desire 2025*, fundos "aurora",
lockup **Unilever | Global Digital & Technology** e os layouts *Stat*, *Big Statement* e *Key Points*.

- Vídeo final: `out/race-to-2030-hook.mp4`, com trilha sonora original sincronizada às cenas (-16 LUFS)
- Fonte da animação: `index.html` (abra no navegador para pré-visualizar, com barra de rolagem e Espaço para pausar)
- Trilha: `audio/soundtrack.py` (sintetizada do zero, sem música de terceiros e sem direitos a liberar)

## Roteiro de narração com tempos

Ritmo pensado para ~145 palavras/min, tom executivo e pausado.
As frases **em negrito** são as frases-chave que aparecem destacadas na tela.

| Tempo | Cena (na tela) | Narração |
|---|---|---|
| 0:00–0:06 | **Hook**: contador 2026 → 2030 correndo na linha do tempo | *(comece em ~0:01)* "**The race to 2030 is already underway.**" |
| 0:06–0:11 | Statement | "The decisions we make **now** will determine whether we **lead tomorrow**." |
| 0:11–0:25 | **Proven strengths**: 4 colunas com check | "We have proven strengths: **best-in-class execution in stores**, **strong operational performance across Logistics and S&OP**, and critical progress in strategic priorities such as **Tax Reform Compliance** and **Factory Transformation**." |
| 0:25–0:32 | Virada (fundo azul) | "But future leadership requires more than **operational excellence**. It requires accelerating where the market is evolving fastest." |
| 0:32–0:50 | **Where we must accelerate**: 3 cards | "**Our Data Agenda gap** remains one of our most important opportunities to create competitive advantage. **Our TPM Journey needs stronger momentum.** And as **Social Commerce reshapes** how consumers discover, engage, and buy, **we must move faster to unlock its full potential.**" |
| 0:50–0:59 | **AI-First** by 2030 | "These priorities become even more critical as we advance toward Unilever's ambition of becoming an **AI-First company by 2030**." |
| 0:59–1:13 | **Our strategy**: Reinforce · Accelerate · Concentrate | "**Our strategy is therefore clear**: reinforce what already makes us strong, accelerate the capabilities that will define future competitiveness, and concentrate investment on the few bets that can create disproportionate impact for LATAM." |
| 1:13–1:21 | **2027 Big Bets**: Today → Tomorrow | "**Our 2027 Big Bets turn that strategy into action, strengthening today's core while building tomorrow's competitive advantage.**" |
| 1:21–1:27 | Encerramento (capa do template) | *(silêncio / transição para as estratégias)* |

### Ajustes feitos no texto original
- strenghths → **strengths** · perfomance → **performance** · ans → **and**
- he market → **the market** · strenthening → **strengthening**
- "Such as Social Commerce reshapes…" → "**And as** Social Commerce reshapes…" (concordância)

## Trilha sonora

Corporativa/tech em Ré maior, 100 BPM, cortada no tempo de cada cena:

| Momento | O que a música faz |
|---|---|
| 0:00–0:03 | Tensão: drone grave, "ticks" subindo a cada virada do contador, riser |
| 0:03 | **Impacto** quando o contador crava 2030 |
| 0:06–0:25 | Pads e arpejo suaves; batida leve e um "ping" em cada check das forças |
| 0:25–0:32 | A virada: a música esvazia e vai crescendo até… |
| 0:32 | **Drop** em "Where we must accelerate": batida completa |
| 0:50 | Respiro etéreo, brilhos acompanhando a onda de pontos, impacto no "AI-First" |
| 0:59–1:13 | Batida volta, construindo |
| 1:13 | Pico em "2027 Big Bets", impacto quando o contador crava 2027 |
| 1:21 | Acorde final resolvendo, com fade |

Com narração, `audio/mux.py --voice` abaixa a música automaticamente sempre que a voz fala (ducking).

## Como ajustar e renderizar de novo

Os tempos de cada cena ficam em `timeline.js`, usado pelo vídeo e pela trilha:

```js
window.TIMELINE = {"s1": 0, "s2": 6.2, "s3": 11.4, "s4": 24.6, "s5": 32.2, "s6": 50.0, "s7": 58.6, "s8": 72.8, "end": 81.4, "out": 86.0};
```

Se a narração ficar mais rápida ou mais lenta, mude esses números. Animações e música acompanham.
Para gerar tudo de novo:

```bash
npm install                      # playwright-core (usa o Chromium já instalado)
node render.mjs                  # -> out/video.mp4 (imagem, sem som)
python3 audio/soundtrack.py      # -> out/soundtrack.wav (só precisa de numpy + ffmpeg)
python3 audio/mux.py             # -> out/race-to-2030-hook.mp4 (imagem + trilha)
python3 audio/mux.py --voice narracao.wav   # com narração, música abaixa sob a voz
node render.mjs --stills 3,20,55 # quadros soltos para conferir
```

`CHROMIUM=/caminho/do/chrome` define outro navegador.

**Fonte:** a fonte da marca, *Unilever Desire*, não vem dentro do template. Se ela estiver instalada
na máquina que renderiza, o vídeo usa ela automaticamente. Sem ela, entra a *Plus Jakarta Sans*
(licença OFL), que é a mais parecida.
