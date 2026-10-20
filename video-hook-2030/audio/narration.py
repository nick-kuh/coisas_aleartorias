#!/usr/bin/env python3
"""AI voice-over for the "Race to 2030" promo, and the timeline the cuts follow.

Each line is synthesised with Kokoro-82M (Apache-2.0, official ONNX export from
Hugging Face, voice af_heart). Lines are laid out on a 120 BPM grid (sections
start on a beat) and every shot cut and word slam is taken from where the words
actually fall (faster-whisper word timestamps when installed). The result is
written to ../timeline.js, which index.html (picture) and soundtrack.py (music)
both read.

    pip install -r audio/requirements-voice.txt     (see ROTEIRO.md)
    python audio/narration.py                       -> out/narration.wav + timeline.js
"""
import json
import math
import os
import pathlib
import subprocess
import tempfile
import urllib.request

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
MODELS = HERE / '.models'
HF = 'https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main/'
VOICE = 'af_heart'
SPEED = 1.06          # promo pace, still easy to follow
SR = 24000            # Kokoro output rate
BPM = 110
BEAT = 60 / BPM
LAND = 6 * BEAT       # the hook's odometer lands on 2030 on beat 3 of bar 2

# The script, grouped in sections; each section starts on a beat.
# Pronunciations Kokoro would get wrong are pinned as [word](/phonemes/).
SECTIONS = [
    ('now', [('now.a', 'The decisions we make now'),
             ('now.b', 'determine whether we lead tomorrow.')]),
    ('str', [('str.t', 'We have proven strengths:'),
             ('str.1', 'best-in-class execution in stores,'),
             ('str.2', 'strong Logistics and S and O P,'),
             ('str.3', 'progress on Tax Reform Compliance'),
             ('str.4', 'and Factory Transformation.')]),
    ('piv', [('piv.a', 'But leadership requires more than operational excellence.'),
             ('piv.b', 'It requires acceleration.')]),
    ('acc', [('acc.1', 'Our Data Agenda gap is a big opportunity.'),
             ('acc.2', 'Our TPM Journey needs stronger momentum.'),
             ('acc.3', 'Social Commerce is reshaping how consumers discover, engage, and buy.'),
             ('acc.4', 'We must move faster.')]),
    ('ai',  [('ai.a', 'On the way to an AI-First [Unilever](/jˈunɪlˌivəɹ/) by 2030.')]),
    ('stg', [('stg.t', 'Our strategy is clear:'),
             ('stg.1', 'Reinforce.'), ('stg.2', 'Accelerate.'), ('stg.3', 'Concentrate.')]),
    ('bet', [('bet.a', 'Our 2027 Big Bets:'),
             ('bet.b', 'three strategies, five pillars, twenty-six initiatives,'),
             ('bet.c', 'more than 160 million euros in benefit.'),
             ('bet.d', "Strengthening today's core, building tomorrow's advantage.")]),
    ('end', [('end.a', 'The race is on.')]),
]
HOOK = [('hook.a', 'The race to 2030,'), ('hook.b', 'is already underway.')]


def key(w):
    """Normalised word key: 'AI-First,' -> 'ai', "today's" -> 'todays'."""
    return ''.join(ch for ch in w.split('-')[0].lower() if ch.isalnum())


def fetch(name):
    dst = MODELS / name
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        print('downloading', name)
        urllib.request.urlretrieve(HF + name, dst)
    return dst


def make_g2p():
    import espeakng_loader
    # espeak-ng silently ignores data paths longer than 160 chars: point it at a short symlink
    short = pathlib.Path(tempfile.mkdtemp()) / 'esd'
    short.symlink_to(espeakng_loader.get_data_path())
    os.environ['ESPEAK_DATA_PATH'] = str(short)
    from phonemizer.backend.espeak.wrapper import EspeakWrapper
    EspeakWrapper.set_library(espeakng_loader.get_library_path())
    from misaki import en, espeak
    return en.G2P(trf=False, british=False, fallback=espeak.EspeakFallback(british=False))


def align(clips):
    """Real word start times per line, when faster-whisper is installed."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print('(faster-whisper not installed: using estimated word times)')
        return
    model = WhisperModel('small.en', device='cpu', compute_type='int8')
    for c in clips.values():
        audio16 = np.interp(np.arange(0, len(c['wav']), SR / 16000), np.arange(len(c['wav'])), c['wav'])
        segs, _ = model.transcribe(audio16.astype(np.float32), word_timestamps=True, beam_size=5)
        words = {}
        for s in segs:
            for w in s.words:
                words.setdefault(key(w.word), round(w.start, 3))
        c['words'].update(words)


def main():
    import onnxruntime as ort
    sess = ort.InferenceSession(str(fetch('onnx/model.onnx')), providers=['CPUExecutionProvider'])
    vocab = json.loads(fetch('tokenizer.json').read_text())['model']['vocab']
    voice = np.fromfile(fetch(f'voices/{VOICE}.bin'), dtype=np.float32).reshape(-1, 1, 256)
    g2p = make_g2p()

    def speak(text):
        ps = g2p(text)[0]
        ids = [vocab[c] for c in ps if c in vocab][:510]
        wav = sess.run(None, {'input_ids': np.array([[0, *ids, 0]], dtype=np.int64),
                              'style': voice[len(ids)], 'speed': np.array([SPEED], dtype=np.float32)})[0][0]
        # trim to the speech itself (-45 dBFS gate on 10 ms frames), keep 30 ms of air
        fr = int(0.01 * SR)
        rms = np.sqrt(np.convolve(wav ** 2, np.ones(fr) / fr, mode='same'))
        on = np.flatnonzero(rms > 10 ** (-45 / 20))
        a, b = max(on[0] - 3 * fr, 0), min(on[-1] + 3 * fr, len(wav))
        wav = wav[a:b].astype(np.float64)
        ramp = np.linspace(0, 1, fr)
        wav[:fr] *= ramp
        wav[-fr:] *= ramp[::-1]
        wav *= 10 ** (-18 / 20) / np.sqrt(np.mean(wav ** 2))      # even level line to line
        return wav, ps

    def estimate_words(text, ps, dur):
        """Word starts by their share of the phoneme string (fallback, good to ~0.2 s)."""
        out, toks = {}, text.split()
        for i, tok in enumerate(toks):
            head = ' '.join(toks[:i])
            k = len(g2p(head)[0]) if head else 0
            out.setdefault(key(tok.split('](')[0].strip('[')), round(dur * min(k / max(len(ps), 1), 1), 3))
        return out

    lines = HOOK + [c for _, cues in SECTIONS for c in cues]
    clips = {}
    for cid, text in lines:
        wav, ps = speak(text)
        dur = len(wav) / SR
        clips[cid] = dict(text=text, wav=wav, dur=dur, words=estimate_words(text, ps, dur))
        print(f'{cid:6s} {dur:5.2f}s  {text[:72]}')
    align(clips)

    # ---- lay the lines out: sections start on a beat, lines inside follow the punctuation
    def q(t):
        return math.ceil(t / BEAT - 1e-6) * BEAT

    MIN_SHOT = 2.2                 # no shot is shorter than this
    SAME_SHOT = {'str.4'}          # lines that carry on in the shot before (no cut)

    def hold(text):
        """Pause after a line before the next one: time to read the shot before the cut."""
        return {'.': 0.65, ':': 0.45, ',': 0.35}.get(text.rstrip()[-1], 0.3)

    at = {'hook.a': LAND - 0.06 - clips['hook.a']['dur'], 'hook.b': LAND + 0.35}
    cur, shot = at['hook.b'] + clips['hook.b']['dur'], 0.0
    marks = {'land': LAND}
    for name, cues in SECTIONS:
        t = q(max(cur + 0.8, shot + MIN_SHOT))
        if name == 'acc':                       # the drop: one bar of "Accelerate" before the first line
            marks['drop'] = t
            t += 4 * BEAT
        marks[name] = t
        for i, (cid, text) in enumerate(cues):
            if i:
                prev_text = cues[i - 1][1]
                t = cur + (0.15 if cid in SAME_SHOT else hold(prev_text))
                if cid not in SAME_SHOT:
                    t = max(t, shot + MIN_SHOT)
            if cid not in SAME_SHOT:
                shot = t
            at[cid] = t
            cur = t + clips[cid]['dur']

    def s(c):
        return at[c]

    def w(c, word):
        return at[c] + clips[c]['words'][word]

    shots = {
        'hook': 0.0, 'now': s('now.a') - 0.05, 'now2': s('now.b') - 0.05,
        'strT': s('str.t') - 0.05, 'str1': s('str.1') - 0.05, 'str2': s('str.2') - 0.05, 'str3': s('str.3') - 0.05,
        'piv1': s('piv.a') - 0.05, 'piv2': s('piv.b') - 0.05, 'drop': marks['drop'],
        'acc1': s('acc.1') - 0.05, 'acc2': s('acc.2') - 0.05, 'acc3': s('acc.3') - 0.05, 'acc4': s('acc.4') - 0.05,
        'ai': s('ai.a') - 0.05, 'stgT': s('stg.t') - 0.05,
        'stg1': s('stg.1') - 0.05, 'stg2': s('stg.2') - 0.05, 'stg3': s('stg.3') - 0.05,
        'bet1': s('bet.a') - 0.05, 'bet2': s('bet.b') - 0.05, 'bet3': s('bet.c') - 0.05, 'bet4': s('bet.d') - 0.05,
        'end': s('end.a') - 0.05,
    }
    shots['logo'] = q(at['end.a'] + clips['end.a']['dur'] + 0.9)
    out_t = shots['logo'] + 3.1

    r3 = lambda v: round(v, 3)
    timeline = {
        'bpm': BPM, 'out': r3(out_t),
        'shots': {k: r3(v) for k, v in shots.items()},
        'marks': {k: r3(v) for k, v in marks.items()},
        'cues': {c: {'s': r3(at[c]), 'e': r3(at[c] + clips[c]['dur']),
                     'w': {k: r3(at[c] + v) for k, v in clips[c]['words'].items()}} for c in at},
    }
    (ROOT / 'timeline.js').write_text(
        '// Generated by audio/narration.py from the voice-over: shot cuts, music marks and the\n'
        '// time every spoken word lands (seconds). index.html and audio/soundtrack.py read it.\n'
        f'window.TIMELINE = {json.dumps(timeline, indent=1)};\n')

    # ---- the narration track, on the video's clock (48 kHz for the mix)
    total = out_t + 0.6
    track = np.zeros(int(total * SR))
    for cid, c in clips.items():
        i0 = int(at[cid] * SR)
        track[i0:i0 + len(c['wav'])] += c['wav']
    out = ROOT / 'out' / 'narration.wav'
    out.parent.mkdir(exist_ok=True)
    pcm = (np.clip(track, -1, 1) * 32767).astype('<i2')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 's16le', '-ar', str(SR), '-ac', '1', '-i', '-',
                    '-af', 'highpass=f=70,aresample=48000:resampler=soxr', str(out)], input=pcm.tobytes(), check=True)
    print('\n'.join(f'  {k:5s} {v:6.2f}s' for k, v in shots.items()))
    print(out, f'{total:.1f}s')


if __name__ == '__main__':
    main()
