"""Soft flute, tanpura and tabla bed, synthesised (no samples, nothing to license). One seed per episode.

  python3 music.py <seconds> <out.wav> [--seed N] [--mood calm|tense|grief|joy]

Raga Bhupali (Sa Re Ga Pa Dha) for calm/joy, Bhairavi-like (komal Re Ga Dha Ni) for grief/tense.
Tanpura: additive Pa-Sa-Sa-Sa plucks with jawari shimmer. Flute: bansuri-like tone (breathy,
vibrato, meend glides). Tabla: keherwa theka, bayan with pitch bend, tuned dayan.
"""
import argparse
import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt
import soundfile as sf

SR = 44100
SA = 146.83                                        # D3; flute plays two octaves up
SCALES = {"calm": [0, 2, 4, 7, 9], "joy": [0, 2, 4, 7, 9], "grief": [0, 1, 3, 7, 8, 10], "tense": [0, 1, 3, 6, 7, 8]}


def env(n, a, r):
    e = np.ones(n); a, r = int(a * SR), int(r * SR)
    if a: e[:a] = np.linspace(0, 1, a) ** 1.5
    if r: e[-r:] *= np.linspace(1, 0, r) ** 1.2
    return e


def tanpura(T, rng):
    out = np.zeros(int(T * SR)); period = 1.25
    seq = [7 - 12, 12, 12, 0]                     # Pa (low), Sa', Sa', Sa
    t, k = 0.0, 0
    while t < T:
        f = SA * 2 ** (seq[k % 4] / 12); n = int(min(5.0, T - t) * SR)
        tt = np.arange(n) / SR; s = np.zeros(n)
        for h in range(1, 16):
            shimmer = 1 + 0.6 * np.sin(2 * np.pi * (0.3 + 0.05 * h) * tt + rng.uniform(0, 6))   # jawari
            s += (1 / h ** 0.9) * shimmer * np.sin(2 * np.pi * f * h * (1 + rng.normal(0, 3e-4)) * tt) * np.exp(-tt * (0.6 + 0.12 * h))
        i0 = int(t * SR); out[i0:i0 + n] += s * env(n, 0.01, 0.3)
        t += period * rng.uniform(0.97, 1.03); k += 1
    return out / (np.abs(out).max() + 1e-9)


def flute_note(f0, f1, dur, rng, glide=0.12):
    n = int(dur * SR); tt = np.arange(n) / SR
    g = np.clip(tt / glide, 0, 1)
    f = np.exp(np.log(f0) * (1 - g) + np.log(f1) * g)                     # meend from the previous note
    vib = 1 + 0.006 * np.clip((tt - 0.35) / 0.4, 0, 1) * np.sin(2 * np.pi * 5.3 * tt)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    tone = np.sin(ph) + 0.28 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph) + 0.03 * np.sin(4 * ph)
    noise = rng.normal(0, 1, n)
    sos = butter(2, [min(f1 * 1.6, 9000), min(f1 * 3.2, 15000)], btype="band", fs=SR, output="sos")
    breath = sosfilt(sos, noise) * 0.9
    amp = env(n, 0.14, min(0.35, dur * 0.4)) * (0.85 + 0.15 * np.sin(2 * np.pi * 0.7 * tt))
    return (tone + breath) * amp


def flute(T, rng, scale):
    out = np.zeros(int(T * SR)); notes = [s + 24 for s in scale] + [s + 36 for s in scale[:3]]
    t = rng.uniform(2.0, 4.0); last = SA * 2 ** (notes[0] / 12) * 4
    idx = rng.integers(0, len(notes))
    while t < T - 3:
        for _ in range(rng.integers(3, 7)):                                 # one phrase
            idx = int(np.clip(idx + rng.choice([-2, -1, -1, 1, 1, 2, 0]), 0, len(notes) - 1))
            f = SA * 2 ** (notes[idx] / 12) * 2
            d = float(rng.choice([0.6, 0.9, 1.2, 1.8, 2.4], p=[.2, .3, .25, .15, .1]))
            if t + d > T - 1: break
            s = flute_note(last, f, d, rng); i0 = int(t * SR)
            out[i0:i0 + len(s)] += s[:len(out) - i0]; last = f; t += d * 0.93
        t += rng.uniform(1.5, 3.5)                                          # breathe between phrases
    return out / (np.abs(out).max() + 1e-9)


def tabla(T, rng, bpm=72):
    out = np.zeros(int(T * SR)); beat = 60 / bpm
    theka = ["Dha", "Ge", "Na", "Ti", "Na", "Ka", "Dhi", "Na"]             # keherwa
    def bayan(n, a):
        tt = np.arange(n) / SR; f = 70 + 45 * np.exp(-tt * 9)
        return a * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 6)
    def dayan(n, a, decay):
        tt = np.arange(n) / SR; f = SA * 2
        s = sum(w * np.sin(2 * np.pi * f * h * tt) for h, w in zip((1, 2, 3, 4, 5), (1, .5, .35, .2, .1)))
        click = rng.normal(0, 1, n) * np.exp(-tt * 300) * 0.4
        return a * (s * np.exp(-tt * decay) + click)
    t, k = 0.0, 0
    while t < T:
        n = int(0.9 * SR); s = np.zeros(n); b = theka[k % 8]
        if b in ("Dha", "Ge", "Dhi"): s += bayan(n, 0.9)
        if b in ("Dha", "Na", "Dhi"): s += dayan(n, 0.6, 9 if b == "Na" else 6)
        if b == "Ti": s += dayan(n, 0.4, 40)
        if b == "Ka": s += rng.normal(0, 1, n) * np.exp(-np.arange(n) / SR * 80) * 0.25
        i0 = int((t + rng.normal(0, 0.006)) * SR)
        if 0 <= i0 < len(out): out[i0:i0 + n] += s[:len(out) - i0] * rng.uniform(0.85, 1.0)
        t += beat / 2; k += 1
    return out / (np.abs(out).max() + 1e-9)


def reverb(x, rng, secs=2.2, mix=0.25):
    n = int(secs * SR); ir = rng.normal(0, 1, n) * np.exp(-np.arange(n) / SR * 3.2)
    wet = fftconvolve(x, ir)[:len(x)]; wet /= np.abs(wet).max() + 1e-9
    return (1 - mix) * x + mix * wet


def make(T, seed=1, mood="calm"):
    rng = np.random.default_rng(seed)
    scale = SCALES.get(mood, SCALES["calm"])
    tp, fl = tanpura(T, rng), flute(T, rng, scale)
    tb = tabla(T, rng, 66 if mood in ("calm", "grief") else 80)
    mix = 0.30 * tp + 0.55 * reverb(fl, rng, mix=0.35) + (0.0 if mood == "grief" else 0.28) * tb
    mix = reverb(mix, rng, 1.4, 0.12)
    mix *= env(len(mix), 1.5, 2.5)
    st = np.stack([mix * 0.98, np.roll(mix, int(0.012 * SR))], 1)           # a little width
    return st / (np.abs(st).max() + 1e-9) * 0.8


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("seconds", type=float); ap.add_argument("out")
    ap.add_argument("--seed", type=int, default=1); ap.add_argument("--mood", default="calm")
    a = ap.parse_args()
    sf.write(a.out, make(a.seconds, a.seed, a.mood), SR)
    print(f"music: {a.out} ({a.seconds:.1f}s, {a.mood}, seed {a.seed})")
