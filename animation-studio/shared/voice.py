#!/usr/bin/env python3
"""Free local narration with Piper TTS (runs offline, no account).

  python shared/voice.py script.txt voice.wav [--timing work] [--voice en_US-ljspeech-medium] [--speed 1.0] [--pause 0.35] [--download]
  python shared/voice.py --list

- Needs piper-tts in the skill's .venv:  python shared/setup_check.py --tts --install   (ask the user first)
- Voices live in the user's cache folder (not in the skill): Windows %LOCALAPPDATA%\\animation-studio\\voices,
  macOS ~/Library/Caches/animation-studio/voices, Linux ~/.cache/animation-studio/voices.
- --download fetches a missing voice (~60 MB). Ask the user first.
- --timing DIR writes exact words.json + phrases.json (same format as timing.py), so timing.py is not needed.
- --speed: 1.0 = normal; 0.9 = a little faster, 1.1 = slower (Piper's length scale).
LICENCES: a Piper voice inherits the licence of its training data. Published videos need a voice whose data allows it.
VOICES below were checked; any other voice is refused unless you pass --i-checked-the-licence.
"""
import os, subprocess, sys, wave
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import OS, utf8, venv_python  # noqa: E402

VOICES = {  # name: (language, description, dataset licence)
    "en_US-ljspeech-medium": ("en_US", "clear US female narrator (default)", "public domain (LJ Speech)"),
    "en_US-ljspeech-high": ("en_US", "same voice, higher quality, slower", "public domain (LJ Speech)"),
}
NOT_OK = {"en_US-lessac": "research-only licence", "en_US-ryan": "CC BY-NC-SA (non-commercial)"}
DEFAULT = "en_US-ljspeech-medium"


def voices_dir():
    if OS == "win":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif OS == "mac":
        base = Path.home() / "Library" / "Caches"
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / "animation-studio" / "voices"


def narration(text):
    """script.txt is narration only, but drop stray stage directions in [brackets] and blank lines."""
    import re
    lines = [re.sub(r"\[[^\]]*\]", "", l).strip() for l in text.splitlines()]
    return "\n".join(l for l in lines if l)


def main():
    utf8()
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); sys.exit(0)
    if a[0] == "--list":
        print("| Voice | Language | Sound | Data licence |\n|---|---|---|---|")
        for k, (lang, d, lic) in VOICES.items():
            print(f"| {k} | {lang} | {d} | {lic} |")
        print("\nAvoid for published videos: " + "; ".join(f"{k}* ({v})" for k, v in NOT_OK.items()))
        return
    opt = lambda n, d=None: a[a.index(n) + 1] if n in a else d
    script, out = a[0], a[1]
    voice = opt("--voice", DEFAULT)
    if voice not in VOICES and "--i-checked-the-licence" not in a:
        bad = next((v for k, v in NOT_OK.items() if voice.startswith(k)), None)
        sys.exit(f"Voice '{voice}' is not on the checked list" + (f" ({bad})" if bad else "") +
                 ". Read its MODEL_CARD licence on huggingface.co/rhasspy/piper-voices; if it allows your use, add --i-checked-the-licence.")
    py = venv_python()
    try:
        import piper  # noqa: F401
    except ImportError:
        if os.path.abspath(py) != os.path.abspath(sys.executable) and os.path.exists(py):
            sys.exit(subprocess.run([py, os.path.abspath(__file__), *sys.argv[1:]]).returncode)   # re-run inside the skill's .venv
        sys.exit("piper-tts is not installed. With the user's OK: python shared/setup_check.py --tts --install")
    vd = voices_dir(); model = vd / f"{voice}.onnx"
    if not model.exists():
        if "--download" not in a:
            sys.exit(f"Voice not downloaded yet ({model}). Ask the user, then re-run with --download (~60 MB).")
        vd.mkdir(parents=True, exist_ok=True)
        subprocess.run([sys.executable, "-m", "piper.download_voices", voice, "--download-dir", str(vd)], check=True)
    synth(model, narration(Path(script).read_text(encoding="utf-8")), out, float(opt("--speed", 1.0)),
          float(opt("--pause", 0.35)), opt("--timing"), voice)


def synth(model, text, out, speed, pause, timing_dir, voice):
    """Clause by clause, so every phrase has an EXACT start/end time (no guessing from silences)."""
    import json, re
    import numpy as np
    from piper import PiperVoice, SynthesisConfig
    from timing import syll
    pv = PiperVoice.load(str(model))
    cfg = SynthesisConfig(length_scale=speed)
    clauses = [c.strip() for c in re.findall(r"[^,.;:!?]+[,.;:!?\"”']*", text.replace("\n", " ")) if c.strip()]
    sr = None; parts = []; t = 0.0; phrases = []; words = []
    lead = 0.15
    for i, c in enumerate(clauses):
        audio = np.concatenate([ch.audio_float_array for ch in pv.synthesize(c, syn_config=cfg)])
        sr = sr or pv.config.sample_rate
        if i == 0:
            parts.append(np.zeros(int(lead * sr), np.float32)); t = lead
        # trim the model's own leading/trailing silence so times are tight
        nz = np.flatnonzero(np.abs(audio) > 0.01)
        if len(nz):
            audio = audio[max(0, nz[0] - int(0.02 * sr)): nz[-1] + int(0.05 * sr)]
        d = len(audio) / sr
        phrases.append({"text": c, "s": round(t, 3), "e": round(t + d, 3)})
        ws = c.split(); sy = [syll(w) for w in ws]; T = sum(sy); tw = t
        for w, k in zip(ws, sy):
            dd = d * k / T; words.append({"w": w, "s": round(tw, 3), "e": round(tw + dd, 3)}); tw += dd
        parts.append(audio.astype(np.float32)); t += d
        gap = pause if re.search(r"[.!?][\"”']*$", c) else pause * 0.45
        if i < len(clauses) - 1:
            parts.append(np.zeros(int(gap * sr), np.float32)); t += gap
    parts.append(np.zeros(int(0.4 * sr), np.float32)); t += 0.4
    x = np.concatenate(parts)
    x = x * (0.89 / max(1e-6, float(np.abs(x).max())))         # peak at -1 dBFS: headroom so resampling never clips
    pcm = (x * 32767).astype(np.int16)
    with wave.open(out, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())
    nw = len(text.split())
    print(f"{out}: {t:.1f} s, {nw} words ({nw / max(t, 0.1):.1f} words/s), voice {voice} [{VOICES.get(voice, ('', '', 'user-checked'))[2]}]")
    if timing_dir:
        os.makedirs(timing_dir, exist_ok=True)
        json.dump(words, open(os.path.join(timing_dir, "words.json"), "w", encoding="utf-8"), indent=1)
        json.dump({"duration": round(t, 3), "frames30": int(round(t * 30)), "source": "piper-exact", "segments": [[p["s"], p["e"]] for p in phrases],
                   "phrases": phrases}, open(os.path.join(timing_dir, "phrases.json"), "w", encoding="utf-8"), indent=1)
        for p in phrases:
            print(f"{p['s']:6.2f}-{p['e']:6.2f}  f{int(p['s'] * 30):4d}-{int(p['e'] * 30):4d}  {p['text']}")

if __name__ == "__main__":
    main()
