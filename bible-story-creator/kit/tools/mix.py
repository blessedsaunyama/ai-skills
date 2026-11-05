#!/usr/bin/env python3
"""Level-locked mix: voice untouched, music at exactly 50 % of the voice level (-6 dB gated RMS),
SFX at <= 50 % with peaks capped at 0.7x the voice peak. One linear gain + a peak limiter, no ducking.

Usage:  python3 mix.py voice.mp3 music.wav sfx.wav [--music-db -6] [--sfx-db -6]   -> mix_raw.wav
For reverent/solemn stories you may lower the bed (e.g. --music-db -9); never raise it above -6.
Needs numpy + ffmpeg.
"""
import subprocess, sys, wave
import numpy as np

SR = 48000


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def gated_rms(x, gate_db=-40.0, win=0.4):
    n = int(win * SR)
    if len(x) < n:
        return float(np.sqrt(np.mean(x ** 2)) + 1e-9)
    blocks = x[: len(x) // n * n].reshape(-1, n)
    r = np.sqrt(np.mean(blocks ** 2, axis=1)) + 1e-9
    top = r.max()
    keep = r[20 * np.log10(r / top) > gate_db]
    return float(np.sqrt(np.mean(keep ** 2)))


def db(x):
    return 20 * np.log10(max(x, 1e-9))


def main():
    a = [x for x in sys.argv[1:]]
    if len(a) < 3:
        print(__doc__); sys.exit(1)
    music_db = float(a[a.index("--music-db") + 1]) if "--music-db" in a else -6.0
    sfx_db = float(a[a.index("--sfx-db") + 1]) if "--sfx-db" in a else -6.0
    music_db, sfx_db = min(music_db, -6.0), min(sfx_db, -6.0)
    voice, music, sfx = load(a[0]), load(a[1]), load(a[2])
    N = len(voice)
    pad = lambda x: np.pad(x, (0, max(0, N - len(x))))[:N]
    music, sfx = pad(music), pad(sfx)
    v_rms, v_peak = gated_rms(voice), float(np.abs(voice).max())
    m = music * (v_rms * 10 ** (music_db / 20) / gated_rms(music)) if np.any(music) else music
    s = sfx * (v_rms * 10 ** (sfx_db / 20) / gated_rms(sfx)) if np.any(sfx) else sfx
    if np.any(s) and np.abs(s).max() > 0.7 * v_peak:
        s *= 0.7 * v_peak / np.abs(s).max()
    mix = voice + m + s
    peak = np.abs(mix).max()
    if peak > 0.98:                       # one linear gain so the limiter barely works
        mix *= 0.98 / peak
    mix = np.clip(mix, -0.99, 0.99)
    with wave.open("mix_raw.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
    print(f"voice  gated RMS {db(v_rms):6.1f} dBFS  peak {db(v_peak):6.1f}")
    print(f"music  {db(gated_rms(m)) - db(v_rms) if np.any(m) else float('-inf'):+6.1f} dB vs voice (target {music_db:+.1f})")
    print(f"sfx    {db(gated_rms(s)) - db(v_rms) if np.any(s) else float('-inf'):+6.1f} dB vs voice (<= {sfx_db:+.1f}), peak {db(np.abs(s).max()) if np.any(s) else float('-inf'):6.1f}")
    print("wrote mix_raw.wav  ->  bash finish.sh \"Title\"")


if __name__ == "__main__":
    main()
