#!/usr/bin/env python3
"""Original soundtrack for the "Race to 2030" promo.

Everything is synthesized here from scratch (numpy only), so there is no
third-party music and no licensing to clear. It runs at 110 BPM on the same
grid as the voice-over and follows ../timeline.js: hits land on the cuts and
words that matter (2030 landing, the drop on "Accelerate", AI-First, the three
strategy verbs, 2027, the euros, "The race is on").

    python3 audio/soundtrack.py            -> out/soundtrack.wav (48 kHz stereo)
"""
import json
import pathlib
import subprocess
import sys

import numpy as np

SR = 48000
BPM = 110
BEAT = 60 / BPM
BAR = 4 * BEAT
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
rng = np.random.default_rng(2030)


def load_timeline():
    txt = (ROOT / 'timeline.js').read_text()
    return json.loads(txt[txt.index('{'): txt.rindex('}') + 1])


TL = load_timeline()
SH, MK, CU = TL['shots'], TL['marks'], TL['cues']
DUR = TL['out']                          # matches the rendered video length
N = int(DUR * SR)


def W(cue, word):
    """When `word` is spoken in line `cue` (keys as in narration.py)."""
    k = ''.join(ch for ch in word.split('-')[0].lower() if ch.isalnum())
    return CU[cue]['w'].get(k, CU[cue]['s'])


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# Key of D major. pad = voicing, arp = notes cycled by the arpeggiator.
CHORDS = {
    'D':  dict(bass=38, pad=[50, 54, 57, 62, 64], arp=[62, 66, 69, 74, 76, 78]),
    'Bm': dict(bass=35, pad=[47, 54, 59, 62, 66], arp=[59, 62, 66, 71, 74, 78]),
    'G':  dict(bass=31, pad=[43, 50, 57, 59, 62], arp=[55, 59, 62, 67, 69, 74]),
    'A':  dict(bass=33, pad=[45, 52, 57, 61, 64], arp=[57, 61, 64, 69, 73, 76]),
}


# ---------------------------------------------------------------- helpers
class Bus:
    def __init__(self):
        self.x = np.zeros((2, N))

    def add(self, sig, t0, gain=1.0, pan=0.5):
        """Place a mono (n,) or stereo (2, n) signal at time t0 (seconds)."""
        i0 = int(round(t0 * SR))
        if sig.ndim == 1:
            sig = np.stack([sig * np.cos(pan * np.pi / 2), sig * np.sin(pan * np.pi / 2)]) * np.sqrt(2)
        if i0 < 0:
            sig, i0 = sig[:, -i0:], 0
        n = min(sig.shape[1], N - i0)
        if n > 0:
            self.x[:, i0:i0 + n] += gain * sig[:, :n]


def tvec(dur):
    return np.arange(int(dur * SR)) / SR


def fft_filter(x, lo=None, hi=None):
    X = np.fft.rfft(x, axis=-1)
    f = np.fft.rfftfreq(x.shape[-1], 1 / SR)
    m = np.ones_like(f)
    if lo:
        m *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1e-3)) ** 4)
    if hi:
        m *= 1 / np.sqrt(1 + (f / hi) ** 4)
    return np.fft.irfft(X * m, x.shape[-1], axis=-1)


def sweep_bandpass(x, centers, width_oct=0.8, frame=2048, hop=512):
    """Band-pass whose centre frequency (Hz, one value per sample) moves over time."""
    win = np.hanning(frame)
    out = np.zeros(len(x) + frame)
    norm = np.zeros(len(x) + frame)
    xp = np.concatenate([x, np.zeros(frame)])
    f = np.maximum(np.fft.rfftfreq(frame, 1 / SR), 1.0)
    for i in range(0, len(x), hop):
        c = centers[min(i + frame // 2, len(centers) - 1)]
        m = np.exp(-0.5 * (np.log2(f / c) / width_oct) ** 2)
        out[i:i + frame] += np.fft.irfft(np.fft.rfft(xp[i:i + frame] * win) * m, frame) * win
        norm[i:i + frame] += win ** 2
    return (out / np.maximum(norm, 1e-3))[:len(x)]


def fft_convolve(x, ir):
    n = x.shape[-1] + ir.shape[-1] - 1
    size = 1 << (n - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)
    return y[..., :x.shape[-1]]


def make_ir(rt=2.6):
    """Stereo hall-ish impulse response: band-split noise, darker as it decays."""
    n = int(rt * 1.3 * SR)
    t = np.arange(n) / SR
    f = np.fft.rfftfreq(n, 1 / SR)
    ir = np.zeros((2, n))
    for ch in range(2):
        X = np.fft.rfft(rng.standard_normal(n))
        for lo, hi, r in [(0, 400, rt), (400, 2500, rt * 0.85), (2500, 7000, rt * 0.55), (7000, SR, rt * 0.3)]:
            ir[ch] += np.fft.irfft(X * ((f >= lo) & (f < hi)), n) * np.exp(-6.91 * t / r)
    pre = int(0.018 * SR)
    ir[:, :pre] *= np.linspace(0, 1, pre)
    return ir / np.sqrt((ir ** 2).sum(axis=1, keepdims=True))


# ---------------------------------------------------------------- instruments
TABLE = 2048


def saw_table(f, bright):
    """One period of a band-limited saw, low-passed at `bright` Hz (2-pole slope)."""
    ph = np.arange(TABLE) / TABLE
    w = np.zeros(TABLE)
    for h in range(1, min(TABLE // 2, int(12000 / f)) + 1):
        w += (1 / h) / np.sqrt(1 + (h * f / bright) ** 4) * np.sin(2 * np.pi * h * ph)
    return w


def lookup(table, ph):
    idx = ph * TABLE
    i0 = idx.astype(int) % TABLE
    fr = idx - np.floor(idx)
    return table[i0] * (1 - fr) + table[(i0 + 1) % TABLE] * fr


def pad_note(m, dur, bright, attack=0.7, release=1.6, level=1.0):
    """Three detuned saws through a low-pass at `bright` Hz (scalar, or a ramp for sweeps)."""
    t = tvec(dur + release)
    n = len(t)
    env = np.where(t < dur, np.minimum(1, t / attack),
                   min(1, dur / attack) * np.exp(-(t - dur) / (release / 4)))
    if np.ndim(bright):
        br = np.interp(np.linspace(0, 1, n), np.linspace(0, 1, len(bright)), bright)
        levels = np.geomspace(br.min(), br.max() * 1.0001, 6)
        pos = np.interp(np.log(br), np.log(levels), np.arange(len(levels)))
        i0 = np.minimum(pos.astype(int), len(levels) - 2)
        fr = pos - i0
    else:
        levels = [bright]
    out = np.zeros((2, n))
    f0 = hz(m)
    for k, cents in enumerate((-9, 0, 9)):
        f = f0 * 2 ** (cents / 1200)
        ph = (rng.uniform() + f * t) % 1.0
        sigs = np.stack([lookup(saw_table(f, b), ph) for b in levels])
        if len(levels) == 1:
            sig = sigs[0]
        else:
            cols = np.arange(n)
            sig = sigs[i0, cols] * (1 - fr) + sigs[i0 + 1, cols] * fr
        pan = (0.15, 0.5, 0.85)[k]
        out[0] += sig * np.cos(pan * np.pi / 2)
        out[1] += sig * np.sin(pan * np.pi / 2)
    return out * env * level


def pluck(m, bright=4000, decay=0.32, dur=1.4):
    t = tvec(dur)
    f = hz(m)
    sig = np.zeros(len(t))
    for h in range(1, 30):
        if h * f > 14000:
            break
        amp = (1 / h ** 1.15) / np.sqrt(1 + (h * f / bright) ** 2)
        sig += amp * np.sin(2 * np.pi * f * h * t) * np.exp(-t / (decay / (1 + 0.45 * (h - 1))))
    return sig * (1 - np.exp(-t * 900))


def bell(m, dur=2.5, decay=1.4):
    t = tvec(dur)
    f = hz(m)
    sig = np.zeros(len(t))
    for ratio, amp, d in [(1, 1, 1), (2.0, .45, .6), (3.0, .25, .45), (4.17, .22, .3), (5.43, .14, .22), (6.79, .1, .15)]:
        if f * ratio < 16000:
            sig += amp * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t / (decay * d))
    return sig * (1 - np.exp(-t * 2000))


def kick(punch=1.0):
    t = tvec(0.6)
    fr = 52 + 120 * np.exp(-t * 30)
    body = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 7)
    click = fft_filter(rng.standard_normal(len(t)), lo=1500, hi=7000) * np.exp(-t * 350) * 0.25
    return (body + click * punch) * 0.9


def hat(open_=False):
    t = tvec(0.5 if open_ else 0.12)
    n = fft_filter(rng.standard_normal(len(t)), lo=7000, hi=15000)
    return n * np.exp(-t * (14 if open_ else 60)) * 0.5


def clap():
    t = tvec(0.45)
    n = fft_filter(rng.standard_normal(len(t)), lo=900, hi=4500)
    env = np.exp(-t * 16)
    for d in (0.0, 0.011, 0.022):
        env = env + 0.6 * np.exp(-np.maximum(t - d, 0) * 180) * (t >= d)
    return n * env * 0.45


def shaker():
    t = tvec(0.09)
    return fft_filter(rng.standard_normal(len(t)), lo=5000, hi=12000) * np.minimum(1, t / 0.008) * np.exp(-t * 45) * 0.3


def sub_note(m, dur):
    t = tvec(dur + 0.08)
    f = hz(m)
    env = np.minimum(1, t / 0.006) * np.where(t < dur, 1.0, np.exp(-(t - dur) / 0.02))
    return np.tanh(1.4 * (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(4 * np.pi * f * t) + 0.18 * np.sin(6 * np.pi * f * t))) * env


def riser(dur, f_from=300, f_to=7000):
    t = tvec(dur)
    x = rng.standard_normal(len(t))
    centers = f_from * (f_to / f_from) ** ((t / dur) ** 1.6)
    sig = sweep_bandpass(x, centers, width_oct=0.9)
    tone = np.sin(2 * np.pi * np.cumsum(120 * 2 ** (3 * (t / dur) ** 2)) / SR) * 0.15
    return (sig + tone) * (t / dur) ** 2.2


def whoosh(dur=1.0):
    t = tvec(dur)
    x = rng.standard_normal(len(t))
    u = t / dur
    centers = 500 * 2 ** (3.2 * np.sin(np.pi * u))
    sig = sweep_bandpass(x, centers, width_oct=0.7)
    pan_l = np.cos(u * np.pi / 2)
    pan_r = np.sin(u * np.pi / 2)
    env = np.sin(np.pi * u) ** 2
    return np.stack([sig * env * pan_l, sig * env * pan_r]) * 1.3


def impact():
    t = tvec(3.0)
    fr = 32 + 38 * np.exp(-t * 6)
    boom = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 1.3)
    hit = fft_filter(rng.standard_normal(len(t)), hi=2500) * np.exp(-t * 9) * 0.35
    air = fft_filter(rng.standard_normal(len(t)), lo=4000) * np.exp(-t * 2.2) * 0.08
    return (boom + hit + air) * np.minimum(1, t / 0.003)


def reverse_swell(m_list, dur=1.2, ir=None):
    """A reversed, reverb-soaked chord: the classic suck-in before a hit."""
    x = sum(pluck(m, bright=3500, decay=0.5, dur=dur) for m in m_list)
    st = np.stack([x, x])
    if ir is not None:
        st = 0.35 * st + fft_convolve(st, ir[:, :int(dur * SR)])
    st = st[:, ::-1]
    return st * (np.linspace(0, 1, st.shape[1]) ** 1.5)


# ---------------------------------------------------------------- arrangement
pad, arp, bass, drums, fx, bells = (Bus() for _ in range(6))
kicks = []                                   # kick times drive the sidechain pump
IR = make_ir()


def section(start, end, chords, *, pad_lvl=.5, bright=1400, bright_to=None, arp_mode=None, arp_lvl=.25,
            arp_bright=3500, arp_from=None, drum_mode=None, bass_mode='long', bass_lvl=.4):
    t, k = start, 0
    while t < end - 0.05:
        ch = CHORDS[chords[k % len(chords)]]
        d = min(BAR, end - t)
        if bright_to is None:
            br = bright
        else:   # per-sample brightness ramp across the whole section
            tt = t + tvec(d + 1.6)
            br = bright + (bright_to - bright) * np.clip((tt - start) / (end - start), 0, 1)
        for m in ch['pad']:
            pad.add(pad_note(m, d, br, level=pad_lvl / 5), t)
        if bass_mode == 'long':
            bass.add(sub_note(ch['bass'], d) * np.exp(-tvec(d + .08) * 0.25), t, bass_lvl)
        elif bass_mode == 'pulse':
            for s in np.arange(0, d - 1e-6, BEAT / 2):
                bass.add(sub_note(ch['bass'] + (12 if (s / (BEAT / 2)) % 4 == 3 else 0), BEAT / 2 * 0.8), t + s, bass_lvl)
        if arp_mode:
            step = BEAT / 4 if arp_mode == '16' else BEAT / 2
            seq = ch['arp'] + ch['arp'][-2:0:-1]
            for i, s in enumerate(np.arange(0, d - 1e-6, step)):
                if arp_from is not None and t + s < arp_from:
                    continue
                ramp = 1.0 if arp_from is None else min(1, (t + s - arp_from) / 2.5)
                accent = 1.0 if i % 4 == 0 else 0.72
                arp.add(pluck(seq[i % len(seq)], bright=arp_bright, decay=0.28, dur=0.9), t + s, arp_lvl * accent * ramp,
                        pan=0.5 + 0.18 * np.sin(i * 0.9))
        if drum_mode:
            for b in range(4):
                bt = t + b * BEAT
                if bt >= end - 0.02:
                    break
                if drum_mode == 'drive' or b in (0, 2):
                    drums.add(kick(), bt, 0.85)
                    kicks.append(bt)
                if drum_mode in ('drive', 'build'):
                    if bt + BEAT / 2 < end:
                        drums.add(hat(), bt + BEAT / 2, 0.55, pan=0.62)
                if drum_mode == 'drive' and b in (1, 3):
                    drums.add(clap(), bt, 0.7, pan=0.48)
                if drum_mode == 'soft':
                    for q in range(4):
                        if bt + q * BEAT / 4 < end:
                            drums.add(shaker(), bt + q * BEAT / 4, 0.5 if q % 2 else 0.25, pan=0.65)
        t += BAR
        k += 1


def hit(at, chord='D', level=1.0):
    fx.add(impact(), at, 0.9 * level)
    fx.add(hat(open_=True) * 1.4, at, 0.35 * level, pan=0.4)
    for m in CHORDS[chord]['pad']:
        pad.add(pad_note(m + 12, 1.2, 4200, attack=0.005, release=2.4, level=0.12 * level), at)


LAND, DROP = MK['land'], MK['drop']

# --- hook: a clock ticking faster, odometer steps, impact as it lands on 2030
for m in (26, 33, 38, 45):
    pad.add(pad_note(m, LAND - 0.2, np.linspace(250, 1600, 64), attack=1.2, release=0.5, level=.16), 0.0)
bass.add(sub_note(38, LAND - 0.1) * (tvec(LAND - 0.02) / LAND) ** 1.5, 0.0, 0.35)
for q in np.arange(0.0, LAND - 0.05, BEAT / 4):
    drums.add(hat(), q, 0.12 + 0.4 * q / LAND, pan=0.58)
for i, s in enumerate([0.55 * LAND / 2, 0.95 * LAND / 2, 1.3 * LAND / 2, 1.62 * LAND / 2]):   # odometer steps
    bells.add(bell([69, 71, 73, 74][i], dur=1.0, decay=0.45), s, 0.16, pan=0.4 + 0.07 * i)
    drums.add(kick(punch=0.3), s, 0.5 + 0.1 * i)
fx.add(riser(LAND - 0.3, 300, 8000), 0.3, 0.5)
fx.add(reverse_swell([62, 66, 69, 76], 1.0, IR), LAND - 1.0, 0.55)
hit(LAND, 'D', 1.1)

# --- "underway" / "now": the groove starts
section(LAND, SH['strT'], ['D', 'Bm', 'G'], pad_lvl=.42, bright=2200, arp_mode='16', arp_lvl=.15,
        arp_bright=4500, drum_mode='soft', bass_mode='pulse', bass_lvl=.34)

# --- proven strengths: four on the floor, a ping on each check
section(SH['strT'], SH['piv1'], ['D', 'A', 'Bm', 'G'], pad_lvl=.42, bright=2600, arp_mode='16', arp_lvl=.2,
        arp_bright=6000, drum_mode='drive', bass_mode='pulse', bass_lvl=.4)
for k, at in enumerate([W('str.t', 'strengths'), SH['str1'], SH['str2'], SH['str3'], W('str.4', 'factory')]):
    bells.add(bell([84, 86, 88, 90, 93][k], dur=1.4, decay=0.5), at + 0.2, 0.08, pan=0.3 + 0.1 * k)

# --- the stop: the beat drops out under "more than operational excellence", then builds into the drop
section(SH['piv1'], DROP, ['Bm', 'G', 'A'], pad_lvl=.24, bright=600, bright_to=3200, bass_mode='long', bass_lvl=.2)
b0, t = SH['piv2'], SH['piv2']
while t < DROP - 0.2:                         # snare roll: 8ths, 16ths, 32nds
    left = DROP - t
    drums.add(clap(), t, 0.22 + 0.5 * (t - b0) / (DROP - b0), pan=0.5)
    t += BEAT / 2 if left > 1.2 else BEAT / 4 if left > 0.6 else BEAT / 8
fx.add(riser(DROP - b0, 250, 9500), b0, 0.6)

# --- DROP: "Accelerate"
hit(DROP, 'D', 1.2)
section(DROP, SH['ai'], ['D', 'A', 'Bm', 'G'], pad_lvl=.44, bright=3200, arp_mode='16', arp_lvl=.24,
        arp_bright=7000, drum_mode='drive', bass_mode='pulse', bass_lvl=.46)
for k, w in enumerate(['discover', 'engage', 'buy']):
    bells.add(bell([86, 90, 93][k], dur=1.2, decay=0.5), W('acc.3', w), 0.1, pan=0.35 + 0.15 * k)

# --- AI-First: open up, sparkle, hit on the word
AI = W('ai.a', 'ai')
section(SH['ai'], SH['stgT'], ['G', 'A'], pad_lvl=.5, bright=2600, bass_mode='long', bass_lvl=.36)
penta = [74, 76, 78, 81, 83, 86, 88, 90, 93]
for i in range(int((SH['stgT'] - SH['ai']) / 0.2)):
    bells.add(bell(penta[rng.integers(len(penta))], dur=1.6, decay=0.6), SH['ai'] + i * 0.2, 0.05,
              pan=float(rng.uniform(0.2, 0.8)))
fx.add(riser(AI - SH['ai'], 600, 9000), SH['ai'], 0.35)
hit(AI, 'A', 0.9)

# --- strategy: beat back in, a hit on each verb
section(SH['stgT'], SH['bet1'], ['Bm', 'G', 'D'], pad_lvl=.42, bright=2600, arp_mode='16', arp_lvl=.18,
        arp_bright=6000, drum_mode='build', bass_mode='pulse', bass_lvl=.42)
for k, ch in enumerate(['Bm', 'G', 'D']):
    hit(CU[f'stg.{k + 1}']['s'], ch, 0.55 + 0.15 * k)
fx.add(riser(SH['bet1'] - CU['stg.3']['e'] + 0.3, 400, 9000), CU['stg.3']['e'] - 0.3, 0.4)

# --- 2027 Big Bets: the peak; hits on 2027, the numbers and the euros
hit(SH['bet1'], 'D', 1.2)
section(SH['bet1'], SH['end'], ['D', 'A', 'G', 'A'], pad_lvl=.46, bright=3600, arp_mode='16', arp_lvl=.26,
        arp_bright=7500, drum_mode='drive', bass_mode='pulse', bass_lvl=.46)
fx.add(impact(), W('bet.a', 'big') - 0.05, 0.4)
for k, w in enumerate(['three', 'five', '26']):
    bells.add(bell([86, 90, 93][k], dur=1.2, decay=0.5), W('bet.b', w), 0.12, pan=0.3 + 0.2 * k)
fx.add(impact(), W('bet.c', '160') - 0.1, 0.5)

# --- "The race is on." final hit, then ring out over the logo
ON = W('end.a', 'on')
fx.add(riser(ON - SH['end'] + 0.2, 400, 9000), SH['end'] - 0.2, 0.4)
hit(ON, 'D', 1.3)
for m in CHORDS['D']['pad'] + [69]:
    pad.add(pad_note(m, DUR - ON, 3200, attack=0.02, release=1.5, level=.55 / 5), ON)
bass.add(sub_note(38, 2.0) * np.exp(-tvec(2.08) * 1.2), ON, .5)
for i, m in enumerate([74, 78, 81, 86]):
    bells.add(bell(m, dur=3.0, decay=1.4), SH['logo'] + 0.1 + i * 0.16, 0.08, pan=0.35 + 0.1 * i)

# whooshes on the cuts that have no hit of their own
for name, at in SH.items():
    if name not in ('hook', 'piv1', 'drop', 'ai', 'stg1', 'stg2', 'stg3', 'bet1', 'end'):
        fx.add(whoosh(0.7), at - 0.35, 0.13)

# ---------------------------------------------------------------- mix
# sidechain pump from the kicks on pad / bass / arp
pump = np.ones(N)
tt = np.arange(int(0.35 * SR)) / SR
shape = 1 - 0.5 * np.exp(-tt / 0.09)
for kt in kicks:
    i0 = int(kt * SR)
    n = min(len(shape), N - i0)
    pump[i0:i0 + n] = np.minimum(pump[i0:i0 + n], shape[:n])

pad.x = fft_filter(pad.x, lo=90)
arp.x = fft_filter(arp.x, lo=180)
dry = 1.0 * pad.x * pump + 0.9 * arp.x * pump + 0.55 * bass.x * (0.4 + 0.6 * pump) + 0.65 * drums.x + 1.0 * fx.x + 1.0 * bells.x

# ping-pong delay on the arp (dotted eighth)
dly = np.zeros_like(arp.x)
src = arp.x.mean(axis=0)
d = int(0.75 * BEAT * SR)
for k in range(1, 6):
    src = fft_filter(src, hi=5000)
    dly[k % 2, k * d:] += (0.42 ** k) * src[:N - k * d]
dry += 0.55 * dly * pump

send = 0.30 * pad.x + 0.35 * arp.x + 0.55 * bells.x + 0.30 * fx.x + 0.08 * drums.x + 0.25 * dly
wet = fft_convolve(send, IR)
mix = dry + 0.55 * wet

# master EQ: clean up the sub, open up the top
F = np.fft.rfftfreq(N, 1 / SR)
gain_db = (-4 / (1 + (F / 60) ** 2) + 5 * (F / 5000) ** 2 / (1 + (F / 5000) ** 2))
eq = 10 ** (gain_db / 20) / np.sqrt(1 + (32 / np.maximum(F, 1e-3)) ** 4)
mix = np.fft.irfft(np.fft.rfft(mix, axis=-1) * eq, N, axis=-1)

# a breath of silence right before the drop, fade out at the very end, gentle glue, peak-normalise
gate = np.ones(N)
g0, g1, r = int((DROP - 0.2) * SR), int(DROP * SR), int(0.01 * SR)
gate[g0:g1] = 0
gate[g0 - r:g0] = np.linspace(1, 0, r)
mix *= gate
fade = np.ones(N)
fo = int(1.6 * SR)
fade[-fo:] = np.linspace(1, 0, fo) ** 1.5
mix *= fade
mix = np.tanh(1.2 * mix / np.max(np.abs(mix))) / np.tanh(1.2)
mix *= 10 ** (-1 / 20)

out = ROOT / 'out' / 'soundtrack.wav'
out.parent.mkdir(exist_ok=True)
pcm = (np.clip(mix.T, -1, 1) * 32767).astype('<i2')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 's16le', '-ar', str(SR), '-ac', '2', '-i', '-', str(out)],
               input=pcm.tobytes(), check=True)
print(out, f'{DUR:.1f}s')
