#!/usr/bin/env python3
"""Synthesized music beds and sound effects: generated in code, so there is no copyright risk.

  python shared/sound.py music OUT.wav --seconds 30 [--mood warm|tech|playful|calm|tense] [--bpm N] [--seed N]
  python shared/sound.py sfx OUT.wav --seconds 30 --cues cues.json
      cues.json: [{"t": 1.2, "kind": "pop"}, {"t": 3.0, "kind": "whoosh"}, {"t": 4.0, "kind": "rain", "dur": 5}]
      kinds: pop, whoosh, click, type (typing burst, use "dur"), chime, swell, rain ("dur"), thunder (soft, distant), success
  python shared/sound.py list

Moods: warm = soft pad + harp-like plucks, major (Bible, storybook) · calm = slow pad only (solemn, prayer)
       tense = low minor drone + slow pulse (danger, implied) · tech = light plucky arpeggio + soft kick (explainers)
       playful = bouncy marimba-like line + light percussion (kids, general stories)
Then mix: python shared/mix.py voice.wav music.wav sfx.wav  (music sits 6 dB or more under the voice).
Needs numpy. 48 kHz mono WAV output.
"""
import json, math, sys, wave

import numpy as np

SR = 48000
MOODS = {
    "warm": dict(bpm=76, scale=[0, 2, 4, 7, 9], root=50, chords=[[0, 4, 7], [-3, 0, 4], [5, 9, 12], [7, 11, 14]], pad=0.5, pluck=0.35, kick=0, hat=0),
    "calm": dict(bpm=60, scale=[0, 2, 4, 7, 9], root=48, chords=[[0, 7, 16], [5, 12, 16], [-3, 4, 12], [7, 14, 19]], pad=0.6, pluck=0.0, kick=0, hat=0),
    "tense": dict(bpm=70, scale=[0, 2, 3, 7, 8], root=45, chords=[[0, 7, 15], [0, 8, 15], [-2, 5, 14], [0, 7, 15]], pad=0.45, pluck=0.12, kick=0.25, hat=0),
    "tech": dict(bpm=104, scale=[0, 2, 4, 7, 9, 11], root=52, chords=[[0, 4, 11], [-3, 4, 7], [5, 9, 16], [7, 11, 14]], pad=0.25, pluck=0.45, kick=0.35, hat=0.12),
    "playful": dict(bpm=112, scale=[0, 2, 4, 5, 7, 9], root=55, chords=[[0, 4, 7], [5, 9, 12], [7, 11, 14], [0, 4, 7]], pad=0.15, pluck=0.5, kick=0.25, hat=0.1),
}


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def env(n, a=0.01, r=0.3):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / max(r, 1e-4))
    return e.astype(np.float32)


def pluck(f, dur, bright=0.5):
    n = int(dur * SR); t = np.arange(n) / SR
    x = sum((bright ** k) * np.sin(2 * np.pi * f * (k + 1) * t) / (k + 1) for k in range(5))
    return (x * env(n, 0.004, dur * 0.35)).astype(np.float32)


def pad(freqs, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for f in freqs:
        for det in (-0.12, 0.0, 0.12):                       # gentle chorus
            x += np.sin(2 * np.pi * f * (1 + det / 100) * t + det).astype(np.float32)
    att = np.minimum(1, t / 0.8) * np.minimum(1, (dur - t) / 0.8)
    return (x / (3 * len(freqs)) * att).astype(np.float32)


def kick(dur=0.35):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 50 + 70 * np.exp(-t * 30)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.12)).astype(np.float32)


def noise(n, rng, lp=0.0):
    x = rng.standard_normal(n).astype(np.float32)
    if lp > 0:                                            # one-pole low-pass: softer, darker noise
        y = np.empty_like(x); acc = 0.0; a = lp
        for i in range(n):
            acc = a * acc + (1 - a) * x[i]; y[i] = acc
        x = y
    return x


def add(buf, x, t):
    i = int(t * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(x))
    buf[i:j] += x[: j - i]


def music(seconds, mood="warm", bpm=None, seed=1):
    m = MOODS[mood]
    bpm = bpm or m["bpm"]
    beat = 60 / bpm
    rng = np.random.default_rng(seed)
    buf = np.zeros(int((seconds + 2) * SR), np.float32)
    bar = 4 * beat
    nbars = int(math.ceil(seconds / bar)) + 1
    for b in range(nbars):
        ch = m["chords"][b % len(m["chords"])]
        t0 = b * bar
        if m["pad"]:
            add(buf, m["pad"] * pad([hz(m["root"] + c) for c in ch], bar + 0.6), t0)
        if m["pluck"]:
            for s in range(8):                             # eighth notes, mostly chord tones
                if rng.random() < (0.85 if mood in ("tech", "playful") else 0.55):
                    deg = ch[rng.integers(len(ch))] + 12 * (1 if rng.random() < 0.5 else 2)
                    add(buf, m["pluck"] * pluck(hz(m["root"] + deg), 0.9 if mood != "playful" else 0.35, 0.45), t0 + s * beat / 2)
        for k in range(4):
            if m["kick"] and (k % 2 == 0 or mood == "tense"):
                add(buf, m["kick"] * kick(), t0 + k * beat)
            if m["hat"]:
                h = noise(int(0.05 * SR), rng) * env(int(0.05 * SR), 0.001, 0.015)
                add(buf, m["hat"] * np.diff(h, prepend=0), t0 + k * beat + beat / 2)
    buf = buf[: int(seconds * SR)]
    fade = int(min(1.5, seconds / 4) * SR)
    buf[:int(0.3 * SR)] *= np.linspace(0, 1, int(0.3 * SR))
    buf[-fade:] *= np.linspace(1, 0, fade)
    return buf / (np.abs(buf).max() + 1e-9) * 0.8


def sfx(seconds, cues, seed=2):
    rng = np.random.default_rng(seed)
    buf = np.zeros(int((seconds + 3) * SR), np.float32)
    for c in cues:
        k, t, dur = c["kind"], float(c["t"]), float(c.get("dur", 1.0))
        g = float(c.get("gain", 1.0))
        if k == "pop":
            n = int(0.12 * SR); tt = np.arange(n) / SR
            x = np.sin(2 * np.pi * (500 + 900 * np.exp(-tt * 40)) * tt) * env(n, 0.001, 0.04)
        elif k == "click":
            n = int(0.03 * SR); x = noise(n, rng) * env(n, 0.0005, 0.006)
        elif k == "type":
            x = np.zeros(int(dur * SR), np.float32)
            for i in range(int(dur * 11)):
                n = int(0.025 * SR); add(x, 0.6 * noise(n, rng) * env(n, 0.0005, 0.005), i / 11 + rng.uniform(0, 0.03))
        elif k == "whoosh":
            n = int(0.6 * SR); tt = np.linspace(0, 1, n)
            x = noise(n, rng, 0.9) * np.sin(np.pi * tt) ** 2 * 3
        elif k == "chime":
            x = sum(pluck(hz(m), 1.6, 0.3) * w for m, w in ((84, 0.6), (88, 0.4), (91, 0.3)))
        elif k == "success":
            x = np.zeros(int(0.8 * SR), np.float32)
            for i, m in enumerate((72, 76, 79)):
                add(x, 0.6 * pluck(hz(m), 0.6, 0.4), i * 0.09)
        elif k == "swell":
            n = int(dur * SR); tt = np.linspace(0, 1, n)
            x = pad([hz(60), hz(64), hz(67), hz(72)], dur) * (tt ** 1.5) * 2
        elif k == "rain":
            n = int(dur * SR)
            x = noise(n, rng, 0.6) * 0.5
            att = np.minimum(1, np.arange(n) / (1.0 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.8 * SR))
            x = x * att
        elif k == "thunder":                                 # soft and distant: no scary cracks
            n = int(2.5 * SR); tt = np.arange(n) / SR
            x = noise(n, rng, 0.985) * 12 * np.exp(-tt * 1.6) * np.minimum(1, tt / 0.15)
        else:
            print(f"unknown sfx kind '{k}' (skipped)"); continue
        add(buf, g * np.asarray(x, np.float32), t)
    buf = buf[: int(seconds * SR)]
    pk = np.abs(buf).max()
    return buf / pk * 0.8 if pk > 0 else buf


def write(path, x):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def main():
    a = sys.argv[1:]
    if not a or a[0] not in ("music", "sfx", "list"):
        print(__doc__); sys.exit(1)
    if a[0] == "list":
        print("moods:", ", ".join(MOODS)); print("sfx: pop, whoosh, click, type, chime, success, swell, rain, thunder"); return
    opt = lambda n, d=None: a[a.index(n) + 1] if n in a else d
    secs = float(opt("--seconds", 30))
    if a[0] == "music":
        x = music(secs, opt("--mood", "warm"), float(opt("--bpm")) if opt("--bpm") else None, int(opt("--seed", 1)))
    else:
        x = sfx(secs, json.load(open(opt("--cues"), encoding="utf-8")))
    write(a[1], x)
    print(f"{a[1]}: {secs:.1f} s ({a[0]})")


if __name__ == "__main__":
    main()
