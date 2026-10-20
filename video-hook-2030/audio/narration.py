#!/usr/bin/env python3
"""AI voice-over for the "Race to 2030" hook, and the timeline that follows it.

Each line of the script is synthesised with Kokoro-82M (Apache-2.0, official
ONNX export from Hugging Face, voice af_heart) and then laid out back to back.
Scene start times and every on-screen beat (columns, cards, highlights) are
derived from where the words actually fall, and written to ../timeline.js so
the animation (index.html) and the music (soundtrack.py) follow the voice.

    pip install -r audio/requirements-voice.txt     (see ROTEIRO.md)
    python audio/narration.py                       -> out/narration.wav + timeline.js
"""
import json
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
SPEED = 0.94          # a touch slower than default: executive pace
SR = 24000            # Kokoro output rate

# The script. Pronunciations Kokoro would get wrong are pinned as [word](/phonemes/).
CUES = [
    ('s1.a', 'The race to 2030,'),
    ('s1.b', 'is already underway.'),
    ('s2.a', 'The decisions we make now will determine whether we lead tomorrow.'),
    ('s3.title', 'We have proven strengths:'),
    ('s3.c1', 'best-in-class execution in stores,'),
    ('s3.c2', 'strong operational performance across Logistics and S and O P,'),
    ('s3.c3', 'and critical progress in strategic priorities, such as Tax Reform Compliance,'),
    ('s3.c4', 'and Factory Transformation.'),
    ('s4.a', 'But future leadership requires more than operational excellence.'),
    ('s4.b', 'It requires accelerating where the market is evolving fastest.'),
    ('s5.c1', 'Our Data Agenda gap remains one of our most important opportunities to create competitive advantage.'),
    ('s5.c2', 'Our TPM Journey needs stronger momentum.'),
    ('s5.c3', 'And as Social Commerce reshapes how consumers discover, engage, and buy,'),
    ('s5.c4', 'we must move faster to unlock its full potential.'),
    ('s6.a', "These priorities become even more critical as we advance toward [Unilever's](/jˈunɪlˌivəɹz/) "
             'ambition of becoming an AI-First company by 2030.'),
    ('s7.title', 'Our strategy is therefore clear:'),
    ('s7.c1', 'reinforce what already makes us strong,'),
    ('s7.c2', 'accelerate the capabilities that will define future competitiveness,'),
    ('s7.c3', 'and concentrate investment on the few bets that can create disproportionate impact for [LATAM](/lˈɑtˌæm/).'),
    ('s8.a', 'Our 2027 Big Bets turn that strategy into action,'),
    ('s8.b', "strengthening today's core,"),
    ('s8.c', "while building tomorrow's competitive advantage."),
]

# Words whose timing drives an on-screen beat: cue -> words to locate.
MARKS = {
    's2.a': ['now', 'lead'], 's3.title': ['proven'], 's3.c3': ['Tax'],
    's4.a': ['operational'], 's4.b': ['accelerating', 'fastest'], 's5.c2': ['stronger'],
    's5.c3': ['discover', 'engage', 'buy'], 's6.a': ['AI-First', 'company'], 's7.title': ['therefore'],
    's8.a': ['Big', 'turn'],
}

LAND = 2.98           # the hook's odometer lands on 2030 here (index.html)


def fetch(name):
    dst = MODELS / name
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        print('downloading', name)
        urllib.request.urlretrieve(HF + name, dst)
    return dst


def align(clips):
    """Swap the estimated word times for real ones when faster-whisper is installed."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print('(faster-whisper not installed: using estimated word times)')
        return
    model = WhisperModel('small.en', device='cpu', compute_type='int8')
    key = lambda w: ''.join(ch for ch in w.split('-')[0].lower() if ch.isalnum())
    for cid, c in clips.items():
        if not c['marks']:
            continue
        audio16 = np.interp(np.arange(0, len(c['wav']), SR / 16000), np.arange(len(c['wav'])), c['wav'])
        segs, _ = model.transcribe(audio16.astype(np.float32), word_timestamps=True, beam_size=5)
        words = [(key(w.word), w.start) for s in segs for w in s.words]
        for w in c['marks']:
            hit = next((t for k, t in words if k.startswith(key(w))), None)
            if hit is not None:
                c['marks'][w] = hit


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


def main():
    import onnxruntime as ort
    sess = ort.InferenceSession(str(fetch('onnx/model.onnx')), providers=['CPUExecutionProvider'])
    vocab = json.loads(fetch('tokenizer.json').read_text())['model']['vocab']
    voice = np.fromfile(fetch(f'voices/{VOICE}.bin'), dtype=np.float32).reshape(-1, 1, 256)
    g2p = make_g2p()

    def phon(text):
        return g2p(text)[0]

    def speak(text):
        ps = phon(text)
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

    def word_time(text, ps, dur, word):
        """Where `word` starts, by its share of the phoneme string (good to ~0.15 s)."""
        head = text[:text.index(word)].rstrip()
        k = len(phon(head)) if head else 0
        return dur * min(k / max(len(ps), 1), 1)

    clips = {}
    for cid, text in CUES:
        wav, ps = speak(text)
        dur = len(wav) / SR
        marks = {w: word_time(text, ps, dur, w) for w in MARKS.get(cid, [])}
        clips[cid] = dict(text=text, wav=wav, dur=dur, marks=marks)
        print(f'{cid:9s} {dur:5.2f}s  {text[:70]}')
    align(clips)

    # ---- lay the lines out scene by scene
    lead = {'s2': 0.55, 's3': 0.45, 's4': 0.45, 's5': 0.95, 's6': 0.5, 's7': 0.45, 's8': 0.35}
    hold = {'s1': 0.7, 's2': 0.7, 's3': 0.7, 's4': 0.6, 's5': 0.7, 's6': 1.1, 's7': 0.7, 's8': 1.0}
    min_len = {'s1': 6.0, 's2': 4.6}

    def gap(text):
        return {',': 0.14, ':': 0.28, '.': 0.5}.get(text.rstrip()[-1], 0.2)

    scenes, at = {'s1': 0.0}, {}
    # hook: "...2030," finishes just as the odometer lands, "is already underway." follows the impact
    at['s1.a'] = LAND - 0.05 - clips['s1.a']['dur']
    at['s1.b'] = LAND + 0.42
    for sc in ['s2', 's3', 's4', 's5', 's6', 's7', 's8']:
        prev = [c for c in at if c.startswith(f's{int(sc[1]) - 1}.')]
        prev_sc = f's{int(sc[1]) - 1}'
        end_prev = max(at[c] + clips[c]['dur'] for c in prev)
        scenes[sc] = max(end_prev + hold[prev_sc], scenes[prev_sc] + min_len.get(prev_sc, 0))
        t = scenes[sc] + lead[sc]
        for cid, text in CUES:
            if cid.startswith(sc + '.'):
                at[cid] = t
                t += clips[cid]['dur'] + gap(text)
    last = max(at[c] + clips[c]['dur'] for c in at if c.startswith('s8.'))
    scenes['end'] = last + hold['s8']
    scenes['out'] = scenes['end'] + 4.6

    def start(c):
        return at[c]

    def end(c):
        return at[c] + clips[c]['dur']

    def mark(c, w):
        return at[c] + clips[c]['marks'][w]

    beats = {
        's1.underway': start('s1.b') - 0.15, 's1.underwayMark': start('s1.b') + 0.5 * clips['s1.b']['dur'],
        's2.now': mark('s2.a', 'now'), 's2.lead': mark('s2.a', 'lead'),
        's3.titleMark': mark('s3.title', 'proven'),
        's3.col1': start('s3.c1') - 0.1, 's3.col2': start('s3.c2') - 0.1,
        's3.col3': mark('s3.c3', 'Tax') - 0.2, 's3.col4': start('s3.c4') - 0.1,
        's4.aMark': mark('s4.a', 'operational'), 's4.dim': start('s4.b') - 0.35, 's4.b': start('s4.b') - 0.15,
        's4.accel': mark('s4.b', 'accelerating'), 's4.fastest': mark('s4.b', 'fastest'),
        's5.card1': start('s5.c1') - 0.3, 's5.card2': start('s5.c2') - 0.3, 's5.chev': mark('s5.c2', 'stronger'),
        's5.card3': start('s5.c3') - 0.3, 's5.discover': mark('s5.c3', 'discover'),
        's5.engage': mark('s5.c3', 'engage'), 's5.buy': mark('s5.c3', 'buy'), 's5.must': start('s5.c4') - 0.1,
        's6.lift': mark('s6.a', 'AI-First') - 0.75, 's6.ai': mark('s6.a', 'AI-First') - 0.2,
        's6.by': mark('s6.a', 'company') - 0.1,
        's7.titleMark': mark('s7.title', 'therefore'),
        's7.col1': start('s7.c1') - 0.1, 's7.col2': start('s7.c2') - 0.1, 's7.col3': start('s7.c3') - 0.1,
        's8.our': start('s8.a') - 0.15, 's8.roll': mark('s8.a', 'Big') - 0.65, 's8.bets': mark('s8.a', 'Big') - 0.05,
        's8.action': mark('s8.a', 'turn') - 0.1, 's8.tile1': start('s8.b') - 0.15,
        's8.arrow': start('s8.c') - 0.45, 's8.tile2': start('s8.c') - 0.1, 's8.glow': end('s8.c') - 0.3,
    }
    r = lambda d: {k: round(v, 3) for k, v in d.items()}
    (ROOT / 'timeline.js').write_text(
        '// Generated by audio/narration.py from the voice-over: scene start times and the\n'
        '// moments each on-screen beat fires (seconds). index.html and audio/soundtrack.py read it.\n'
        f'window.TIMELINE = {json.dumps({"scenes": r(scenes), "beats": r(beats)}, indent=1)};\n')

    # ---- the narration track, on the video's clock (48 kHz for the mix)
    total = scenes['out'] + 0.8
    track = np.zeros(int(total * SR))
    for cid, c in clips.items():
        i0 = int(at[cid] * SR)
        track[i0:i0 + len(c['wav'])] += c['wav']
    out = ROOT / 'out' / 'narration.wav'
    out.parent.mkdir(exist_ok=True)
    pcm = (np.clip(track, -1, 1) * 32767).astype('<i2')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 's16le', '-ar', str(SR), '-ac', '1', '-i', '-',
                    '-af', 'highpass=f=70,aresample=48000:resampler=soxr', str(out)], input=pcm.tobytes(), check=True)
    print('\n'.join(f'  {k:4s} {v:6.2f}s' for k, v in scenes.items()))
    print(out, f'{total:.1f}s')


if __name__ == '__main__':
    main()
