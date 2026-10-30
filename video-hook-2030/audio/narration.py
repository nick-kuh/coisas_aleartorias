#!/usr/bin/env python3
"""AI voice-over for the "Race to 2030" promo, and the timeline the cuts follow.

The script is synthesised with Kokoro-82M (Apache-2.0, official ONNX export from
Hugging Face, voice af_heart) in whole passages, so the voice flows from one
sentence to the next like a narrator instead of reading slide by slide. The
picture follows the voice: every shot cut and word slam is placed where its words
actually fall inside the passage (faster-whisper word timestamps when installed,
otherwise an estimate). The result is written to ../timeline.js, which index.html
(picture) and soundtrack.py (music) both read.

    pip install -r audio/requirements-voice.txt     (see ROTEIRO.md)
    python audio/narration.py                       -> out/narration.wav + timeline.js
"""
import difflib
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
SPEED = 1.0           # natural narration pace
SR = 24000            # Kokoro output rate
BPM = 110
BEAT = 60 / BPM
LAND = 6 * BEAT       # the hook's odometer lands on 2030 on beat 3 of bar 2

# The script, line by line (each line drives a shot or an on-screen beat).
# Pronunciations Kokoro would get wrong are pinned as [word](/phonemes/).
CUES = {
    'hook.a': 'The race to 2030,',
    'hook.b': 'is already underway.',
    'now.a': 'The decisions we make now',
    'now.b': 'determine whether we lead tomorrow.',
    'str.t': 'We have proven strengths:',
    'str.1': 'improvements in execution, aiming for best-in-class execution in stores,',
    'str.2': 'strong evolution in Logistics capabilities [and](/ˈænd/) S and O P,',
    'ppl.a': '[AI](/ˌAˈI/) included in the day-to-day of our people,',
    'str.3': 'and critical progress on Tax Reform Compliance',
    'str.4': 'and Factory Transformation.',
    'piv.a': 'But leadership requires more than operational excellence.',
    'piv.b': 'It requires growth acceleration.',
    'acc.1': 'Our Data Agenda gap is a big opportunity.',
    'acc.2': 'Our TPM Journey needs stronger momentum.',
    'acc.3': 'And Social Commerce is reshaping how consumers discover, engage, and buy.',
    'acc.4': 'We must move faster to unlock its full potential,',
    'ai.a': 'on the way to an [AI](/ˌAˈI/)-First [Unilever](/jˈunɪlˌivəɹ/) by 2030.',
    'stg.t': 'Our strategy is clear:',
    'stg.1': 'reinforce what already makes us strong,',
    'stg.2': 'accelerate the capabilities that define our future,',
    'stg.3': 'and concentrate on the few bets with disproportionate impact for [LATAM](/lˈɑtˌæm/).',
    'bet.a': 'Our 2027 Big Bets turn that strategy into action:',
    'bet.b': 'three strategies, five pillars, and 28 initiatives,',
    'bet.d': "strengthening today's core while building tomorrow's advantage.",
    'end.a': 'The race is on.',
}
# Lines spoken in one breath. The hook keeps its beat for the impact on 2030,
# and the music takes over between "acceleration." and the drop.
PASSAGES = [
    ['hook.a'], ['hook.b'],
    ['now.a', 'now.b', 'str.t', 'str.1', 'str.2', 'ppl.a', 'str.3', 'str.4'],
    ['piv.a', 'piv.b'],
    ['acc.1', 'acc.2', 'acc.3', 'acc.4', 'ai.a'],
    ['stg.t', 'stg.1', 'stg.2', 'stg.3'],
    ['bet.a', 'bet.b', 'bet.d'],
    ['end.a'],
]


def key(w):
    """Normalised word key: 'AI-First,' -> 'ai', "[LATAM](/…/)." -> 'latam'."""
    w = w.split('](')[0].strip('[')
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


def whisper_words(wav):
    """[(key, start, end)] from faster-whisper, or None when it is not installed."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    if not hasattr(whisper_words, 'model'):
        whisper_words.model = WhisperModel('small.en', device='cpu', compute_type='int8')
    audio16 = np.interp(np.arange(0, len(wav), SR / 16000), np.arange(len(wav)), wav).astype(np.float32)
    segs, _ = whisper_words.model.transcribe(audio16, word_timestamps=True, beam_size=5)
    return [(key(w.word), w.start, w.end) for s in segs for w in s.words]


def onset(wav, t, prev, look=0.6):
    """Whisper can date a word that follows a pause late: snap it back to where its sound starts."""
    fr = int(0.01 * SR)
    a = int(max(t - look, prev + 0.15, 0) * SR)     # the previous word sounds for a while first
    if int(t * SR) - a < 10 * fr:
        return t
    rms = np.sqrt(np.convolve(wav[a:int(t * SR)] ** 2, np.ones(fr) / fr, mode='same'))[::fr]
    edge = np.flatnonzero(np.diff(np.r_[0, (rms < 10 ** (-45 / 20)).astype(int), 0]))
    pauses = [e for s, e in zip(edge[::2], edge[1::2]) if e - s >= 8]      # quiet for 80 ms or more
    if not pauses:
        return t
    t_on = a / SR + pauses[-1] * 0.01
    return t_on if t - t_on >= 0.04 else t


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
        wav *= 10 ** (-18 / 20) / np.sqrt(np.mean(wav ** 2))      # even level passage to passage
        return wav, ps

    # ---- synthesise each passage and find where every word of every line falls in it
    passages = []
    for ids in PASSAGES:
        text = ' '.join(CUES[c] for c in ids)
        wav, ps = speak(text)
        dur = len(wav) / SR
        words = [(c, key(tok)) for c in ids for tok in CUES[c].split()]
        # estimate first: each word by its share of the phoneme string
        est, toks = [], text.split()
        for i in range(len(toks)):
            k = len(g2p(' '.join(toks[:i]))[0]) if i else 0
            est.append(dur * min(k / max(len(ps), 1), 1))
        times = list(est)
        heard = whisper_words(wav)
        if heard:                                  # then snap to what is actually heard
            sm = difflib.SequenceMatcher(None, [w for _, w in words], [h[0] for h in heard], autojunk=False)
            for blk in sm.get_matching_blocks():
                for j in range(blk.size):
                    times[blk.a + j] = heard[blk.b + j][1]
            times = [onset(wav, t, times[i - 1] if i else 0.0) for i, t in enumerate(times)]
            for i in range(1, len(times)):         # keep the order sane where nothing matched
                times[i] = max(times[i], times[i - 1] + 0.05)
        passages.append(dict(ids=ids, wav=wav, dur=dur, words=words, times=times))
        print(f'{"+".join(ids):45s} {dur:5.2f}s  {text[:60]}…')

    # ---- lay the passages out: one continuous narration, pauses only where the music needs them
    def q(t):
        return math.ceil(t / BEAT - 1e-6) * BEAT

    start = {}
    p = {tuple(x['ids']): x for x in passages}
    hook_a, hook_b = p[('hook.a',)], p[('hook.b',)]
    start[0] = LAND - 0.06 - hook_a['dur']        # "...2030," finishes as the odometer lands
    start[1] = LAND + 0.35                         # "is already underway." follows the impact
    cur = start[1] + hook_b['dur']
    marks = {'land': LAND}
    for i, ps_ in enumerate(passages[2:], start=2):
        first = ps_['ids'][0]
        if first == 'acc.1':                       # music: build, drop on "Accelerate", voice back in
            marks['drop'] = q(cur + 0.45)
            start[i] = marks['drop'] + 3 * BEAT
        else:
            start[i] = cur + (0.6 if first in ('stg.t', 'bet.a', 'end.a') else 0.45)
        cur = start[i] + ps_['dur']

    cues = {}
    for i, ps_ in enumerate(passages):
        t0 = start[i]
        for c in ps_['ids']:
            idx = [j for j, (cc, _) in enumerate(ps_['words']) if cc == c]
            w = {}
            for j in idx:
                w.setdefault(ps_['words'][j][1], round(t0 + ps_['times'][j], 3))
            nxt = idx[-1] + 1
            e = t0 + (ps_['times'][nxt] - 0.05 if nxt < len(ps_['times']) else ps_['dur'])
            cues[c] = {'s': round(t0 + ps_['times'][idx[0]], 3), 'e': round(e, 3), 'w': w}

    def s(c):
        return cues[c]['s']

    def w(c, word):
        return cues[c]['w'][word]

    # the picture leads the voice slightly ("now" carries on into "lead tomorrow" inside one shot)
    shots = {'hook': 0.0, 'now': s('now.a') - 0.15}
    for name, c in [('strT', 'str.t'), ('str1', 'str.1'), ('str2', 'str.2'), ('ppl', 'ppl.a'), ('str3', 'str.3'),
                    ('piv1', 'piv.a'), ('piv2', 'piv.b')]:
        shots[name] = s(c) - 0.15
    shots['drop'] = marks['drop']
    for name, c in [('acc1', 'acc.1'), ('acc2', 'acc.2'), ('acc3', 'acc.3'), ('acc4', 'acc.4'), ('ai', 'ai.a'),
                    ('stgT', 'stg.t'), ('stg1', 'stg.1'), ('stg2', 'stg.2'), ('stg3', 'stg.3'),
                    ('bet1', 'bet.a'), ('bet2', 'bet.b'), ('bet4', 'bet.d'), ('end', 'end.a')]:
        shots[name] = s(c) - 0.15
    shots['logo'] = q(cues['end.a']['e'] + 0.8)
    out_t = shots['logo'] + 3.0

    r3 = lambda v: round(v, 3)
    timeline = {'bpm': BPM, 'out': r3(out_t), 'shots': {k: r3(v) for k, v in shots.items()},
                'marks': {k: r3(v) for k, v in marks.items()}, 'cues': cues}
    (ROOT / 'timeline.js').write_text(
        '// Generated by audio/narration.py from the voice-over: shot cuts, music marks and the\n'
        '// time every spoken word lands (seconds). index.html and audio/soundtrack.py read it.\n'
        f'window.TIMELINE = {json.dumps(timeline, indent=1)};\n')

    # ---- the narration track, on the video's clock (48 kHz for the mix)
    total = out_t + 0.6
    track = np.zeros(int(total * SR))
    for i, ps_ in enumerate(passages):
        i0 = int(start[i] * SR)
        track[i0:i0 + len(ps_['wav'])] += ps_['wav']
    out = ROOT / 'out' / 'narration.wav'
    out.parent.mkdir(exist_ok=True)
    pcm = (np.clip(track, -1, 1) * 32767).astype('<i2')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 's16le', '-ar', str(SR), '-ac', '1', '-i', '-',
                    '-af', 'highpass=f=70,aresample=48000:resampler=soxr', str(out)], input=pcm.tobytes(), check=True)
    keys = list(shots)
    print('\n'.join(f'  {k:5s} {v:6.2f}s  ({(shots[keys[n + 1]] if n + 1 < len(keys) else out_t) - v:4.2f}s)'
                    for n, (k, v) in enumerate(shots.items())))
    print(out, f'{total:.1f}s')


if __name__ == '__main__':
    main()
