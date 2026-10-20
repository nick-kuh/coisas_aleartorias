# Race to 2030 — Hook (2027 Big Bets · LATAM)

Video de abertura (~94 s, 1920×1080, 30 fps) para o resumo executivo aos VPs.
Visual baseado no **GDT Template.pptx**: paleta *Unilever Desire 2025*, fundos "aurora",
lockup **Unilever | Global Digital & Technology** e os layouts *Stat*, *Big Statement* e *Key Points*.

- **Vídeo final:** `out/race-to-2030-hook.mp4`, com narração em inglês (voz feminina de IA) e trilha
  sonora original. A música abaixa sozinha quando a voz fala. Volume no padrão de vídeo online (−16 LUFS).
- **Narração:** `audio/narration.py`. Usa o modelo de voz Kokoro-82M (licença Apache 2.0) com a voz
  `af_heart`, gerada localmente a partir do modelo oficial no Hugging Face. É uma voz sintética, não de
  uma pessoa real.
- **Trilha:** `audio/soundtrack.py`. Foi sintetizada do zero, então não há música de terceiros nem
  direitos a liberar.
- **Animação:** `index.html`. Dá para abrir no navegador para pré-visualizar, com barra de rolagem e
  Espaço para pausar.

## Roteiro com tempos

As animações seguem a voz: cada coluna, card e destaque aparece no momento em que a palavra é dita.
As frases **em negrito** são as frases-chave que aparecem destacadas na tela.

| Tempo | Cena (na tela) | Narração |
|---|---|---|
| 0:00–0:06 | **Hook**: contador 2026 → 2030 correndo na linha do tempo | "**The race to 2030** *(impacto)* **is already underway.**" |
| 0:06–0:11 | Statement | "The decisions we make **now** will determine whether we **lead tomorrow**." |
| 0:11–0:26 | **Proven strengths**: 4 colunas com check | "We have proven strengths: **best-in-class execution in stores**, **strong operational performance across Logistics and S&OP**, and critical progress in strategic priorities, such as **Tax Reform Compliance** and **Factory Transformation**." |
| 0:26–0:35 | Virada (fundo azul) | "But future leadership requires more than **operational excellence**. It requires accelerating where the market is evolving fastest." |
| 0:35–0:54 | **Where we must accelerate**: 3 cards | "**Our Data Agenda gap** remains one of our most important opportunities to create competitive advantage. **Our TPM Journey needs stronger momentum.** And as **Social Commerce reshapes** how consumers discover, engage, and buy, **we must move faster to unlock its full potential.**" |
| 0:54–1:04 | **AI-First** by 2030 | "These priorities become even more critical as we advance toward Unilever's ambition of becoming an **AI-First company by 2030**." |
| 1:04–1:20 | **Our strategy**: Reinforce · Accelerate · Concentrate | "**Our strategy is therefore clear**: reinforce what already makes us strong, accelerate the capabilities that will define future competitiveness, and concentrate investment on the few bets that can create disproportionate impact for LATAM." |
| 1:20–1:29 | **2027 Big Bets**: Today → Tomorrow | "**Our 2027 Big Bets turn that strategy into action, strengthening today's core while building tomorrow's competitive advantage.**" |
| 1:29–1:34 | Encerramento (capa do template) | *(só música, como transição para as estratégias)* |

### Ajustes feitos no texto original
- strenghths → **strengths** · perfomance → **performance** · ans → **and**
- he market → **the market** · strenthening → **strengthening**
- "Such as Social Commerce reshapes…" → "**And as** Social Commerce reshapes…" (concordância)

### Pronúncia
Conferida transcrevendo a narração com Whisper: o texto reconhecido bate com o roteiro.
Duas pronúncias foram fixadas à mão no `audio/narration.py`: *Unilever's* ("YOO-ni-lee-vers") e
*LATAM* ("LAH-tam"). *S&OP* é lido como "S and O P".

## Trilha sonora

Corporativa/tech em Ré maior, 100 BPM, cortada no tempo de cada cena:

| Momento | O que a música faz |
|---|---|
| 0:00–0:03 | Tensão: drone grave, "ticks" subindo a cada virada do contador, riser |
| 0:03 | **Impacto** quando o contador crava 2030 |
| 0:06–0:26 | Pads e arpejo suaves; batida leve e um "ping" em cada check das forças |
| 0:26–0:35 | A virada: a música esvazia e vai crescendo até… |
| 0:35 | **Drop** em "Where we must accelerate": batida completa |
| 0:54 | Respiro etéreo, brilhos acompanhando a onda de pontos, impacto no "AI-First" |
| 1:04–1:20 | Batida volta, construindo |
| 1:20 | Pico em "2027 Big Bets", impacto quando o contador crava 2027 |
| 1:29 | Acorde final resolvendo, com fade |

## Como gerar de novo

```bash
# 1. narração -> out/narration.wav e timeline.js (tempos das cenas e de cada animação)
pip install -r audio/requirements-voice.txt     # veja as notas no arquivo (modelo do spaCy)
python audio/narration.py                       # baixa o Kokoro do Hugging Face na 1ª vez

# 2. imagem -> out/video.mp4
npm install && node render.mjs

# 3. música -> out/soundtrack.wav (só numpy + ffmpeg), segue o timeline.js
python3 audio/soundtrack.py

# 4. tudo junto -> out/race-to-2030-hook.mp4
python3 audio/mux.py --voice out/narration.wav
```

- Para mudar o texto ou a voz, edite `CUES` / `VOICE` / `SPEED` em `audio/narration.py` e rode os 4 passos.
- Para gravar a voz de vocês, troque `out/narration.wav` pela gravação (mesmos tempos do roteiro) e rode só o passo 4.
- `node render.mjs --stills 3,20,55` gera quadros soltos para conferir. `CHROMIUM=/caminho/do/chrome` define outro navegador.

**Fonte:** a fonte da marca, *Unilever Desire*, não vem dentro do template. Se ela estiver instalada
na máquina que renderiza, o vídeo usa ela automaticamente. Sem ela, entra a *Plus Jakarta Sans*
(licença OFL), que é a mais parecida.
