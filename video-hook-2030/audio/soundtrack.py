#!/usr/bin/env python3
"""Original soundtrack for the "Race to 2030" hook.

Everything is synthesized here from scratch (numpy only), so there is no
third-party music and no licensing to clear. The arrangement is cut to the
scene timeline in ../timeline.js: each scene starts on a downbeat, and the hits
line up with the on-screen beats in ../index.html (odometer landing on 2030,
the drop on "accelerate", AI-First, 2027).

    python3 audio/soundtrack.py            -> out/soundtrack.wav (48 kHz stereo)
"""
import json
import pathlib
import subprocess
import sys

import numpy as np

SR = 48000
BPM = 100
BEAT = 60 / BPM
BAR = 4 * BEAT
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
rng = np.random.default_rng(2030)


def load_timeline():
    txt = (ROOT / 'timeline.js').read_text()
    return json.loads(txt[txt.index('{'): txt.rindex('}') + 1])


T = load_timeline()
DUR = T['out'] + 0.8                     # matches the rendered video length
N = int(DUR * SR)


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


def transition(at, size='small'):
    fx.add(whoosh(1.1 if size == 'small' else 1.5), at - 0.55, 0.22 if size == 'small' else 0.32)
    if size != 'small':
        fx.add(reverse_swell([62, 66, 69, 74], 1.1, IR), at - 1.1, 0.5)


def hit(at, chord='D', level=1.0):
    fx.add(impact(), at, 0.9 * level)
    fx.add(hat(open_=True) * 1.4, at, 0.35 * level, pan=0.4)
    for m in CHORDS[chord]['pad']:
        pad.add(pad_note(m + 12, 1.2, 4200, attack=0.005, release=2.4, level=0.12 * level), at)


# --- S1 · hook: tension, odometer ticks, impact on "2030"
land = T['s1'] + 2.98
for m in (26, 33, 38, 45):
    pad.add(pad_note(m, land - 0.3, np.linspace(250, 1400, 64), attack=1.8, release=0.6, level=.16), 0.0)
bass.add(sub_note(38, land - 0.2) * (tvec(land - 0.12) / land) ** 1.5, 0.0, 0.35)
for i, s in enumerate([0.62, 1.30, 1.78, 2.18, 2.52]):
    bells.add(bell([69, 71, 73, 74, 76][i], dur=1.2, decay=0.5), T['s1'] + s, 0.16, pan=0.5 + 0.1 * (i - 2))
    drums.add(kick(punch=0.3), T['s1'] + s, 0.45 + 0.08 * i)
fx.add(riser(land - 0.9, 300, 8000), 0.9, 0.5)
fx.add(reverse_swell([62, 66, 69, 76], 1.2, IR), land - 1.2, 0.55)
hit(land, 'D', 1.1)
for m in CHORDS['D']['pad']:
    pad.add(pad_note(m, T['s2'] - land, 2600, attack=0.03, release=1.8, level=.5 / 5), land)
bass.add(sub_note(38, T['s2'] - land) * np.exp(-tvec(T['s2'] - land + .08) * 0.4), land, .45)
for i, m in enumerate([74, 78, 81, 88, 86, 81]):
    bells.add(bell(m, dur=2.0, decay=0.9), land + 0.35 + i * 0.22, 0.07, pan=0.3 + 0.08 * i)

# --- S2 · statement
transition(T['s2'])
section(T['s2'], T['s3'], ['G', 'A'], pad_lvl=.45, bright=1700, arp_mode='8', arp_lvl=.16, arp_bright=4200)

# --- S3 · proven strengths (+ a soft ping on each check mark)
transition(T['s3'])
section(T['s3'], T['s4'], ['D', 'Bm', 'G', 'A'], pad_lvl=.45, bright=2000, arp_mode='16', arp_lvl=.15,
        arp_bright=5000, drum_mode='soft', bass_mode='pulse', bass_lvl=.32)
for k, off in enumerate([2.1, 4.1, 9.4, 10.9]):
    bells.add(bell([86, 88, 90, 93][k], dur=1.5, decay=0.6), T['s3'] + off + 0.4, 0.09, pan=0.3 + 0.13 * k)

# --- S4 · the shift: strip back, then build into the drop
transition(T['s4'], 'big')
section(T['s4'], T['s5'], ['Bm', 'G', 'A'], pad_lvl=.5, bright=800, bright_to=3500, arp_mode='16', arp_lvl=.2,
        arp_bright=5000, arp_from=T['s4'] + 3.8, bass_mode='long', bass_lvl=.42)
fx.add(riser(T['s5'] - (T['s4'] + 3.6), 250, 9000), T['s4'] + 3.6, 0.55)
for i in range(6):   # speed-line swishes
    fx.add(whoosh(0.6), T['s4'] + 4.0 + i * 0.55, 0.08)

# --- S5 · where we must accelerate: the drop
hit(T['s5'], 'D', 1.0)
transition(T['s5'], 'big')
section(T['s5'], T['s6'], ['D', 'A', 'Bm', 'G'], pad_lvl=.42, bright=2800, arp_mode='16', arp_lvl=.22,
        arp_bright=6500, drum_mode='drive', bass_mode='pulse', bass_lvl=.42)
for k, off in enumerate([0.9, 6.6, 9.6]):
    fx.add(whoosh(0.7), T['s5'] + off - 0.2, 0.1)

# --- S6 · AI-First: airy breakdown, sparkle on the dot wave, hit on "AI-First"
transition(T['s6'], 'big')
section(T['s6'], T['s7'], ['G', 'Bm', 'A', 'A'], pad_lvl=.5, bright=2400, bass_mode='long', bass_lvl=.35)
penta = [74, 76, 78, 81, 83, 86, 88, 90, 93]
for i in range(18):
    bells.add(bell(penta[rng.integers(len(penta))], dur=1.8, decay=0.7), T['s6'] + 0.6 + i * 0.27, 0.05,
              pan=float(rng.uniform(0.2, 0.8)))
fx.add(riser(1.6, 600, 9000), T['s6'] + 5.8 - 1.6, 0.3)
hit(T['s6'] + 5.8, 'A', 0.8)

# --- S7 · strategy: groove returns, steady build
transition(T['s7'])
section(T['s7'], T['s8'], ['Bm', 'G', 'D', 'A'], pad_lvl=.42, bright=2500, arp_mode='16', arp_lvl=.2,
        arp_bright=5500, drum_mode='build', bass_mode='pulse', bass_lvl=.4)
fx.add(riser(2.4, 300, 9000), T['s8'] - 2.4, 0.4)

# --- S8 · 2027 Big Bets: peak, hit when the odometer lands on 2027
hit(T['s8'], 'D', 1.0)
transition(T['s8'], 'big')
section(T['s8'], T['end'], ['D', 'A', 'G', 'A'], pad_lvl=.46, bright=3400, arp_mode='16', arp_lvl=.24,
        arp_bright=7000, drum_mode='drive', bass_mode='pulse', bass_lvl=.44)
fx.add(impact(), T['s8'] + 1.4, 0.45)

# --- End card: resolve on D and let it ring
transition(T['end'], 'big')
hit(T['end'], 'D', 0.8)
for m in CHORDS['D']['pad'] + [69]:
    pad.add(pad_note(m, DUR - T['end'], 3000, attack=0.05, release=2.0, level=.55 / 5), T['end'])
bass.add(sub_note(38, 2.5) * np.exp(-tvec(2.58) * 1.2), T['end'], .5)
for i, m in enumerate([74, 78, 81, 86]):
    bells.add(bell(m, dur=4.0, decay=1.6), T['end'] + 0.25 + i * 0.18, 0.08, pan=0.35 + 0.1 * i)

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

# fade out at the very end, gentle glue, peak-normalise
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
