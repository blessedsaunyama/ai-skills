#!/usr/bin/env python3
"""Predict render time and disk use BEFORE a render, by rendering 3 sample frames (first, middle, last).

  python shared/estimate.py --engine py2d SCENE.json --fmt 9x16[,16x9] [--quality preview|final] [--style NAME] [--seconds N]
  python shared/estimate.py --engine manim SCENE.py --name SceneName --fmt 9x16 [--quality final] [--timing work/phrases.json]
  python shared/estimate.py --engine toon3d PROJECT_DIR --fmt 9x16 [--quality preview]   (PROJECT_DIR has story.js + world.js)
  python shared/estimate.py --engine blender SCENE.json --fmt 16x9 [--quality preview]   (Eevee; tier limits apply)
    (Manim can't render single frames: it renders the whole scene once at preview size and scales the time up for 1080p)

Prints, per format: seconds/frame, "~X min, Y GB disk", and a DECISION line:
  DECISION: OK      within the tier's limit -> render
  DECISION: ASK     longer than the tier's limit (10 min STANDARD/LITE, 30 min POWER) -> ask the user first, offer a 5 s preview
  DECISION: REFUSE  free disk < 2x the estimate -> free space first (or render a shorter preview)
Exit code: 0 OK, 2 ASK, 3 REFUSE. Sample frames go to a temporary folder that is deleted afterwards.
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import SKILL_DIR, gb, memory, utf8, venv_python  # noqa: E402
from formats import parse, size  # noqa: E402

ENGINES = {
    "py2d": lambda scene, fmt, q, style, out, frames: [venv_python(), str(SKILL_DIR / "engines" / "py2d" / "render.py"), scene,
                                                       "--fmt", fmt, "--quality", q, "--out", out, "--frames", frames,
                                                       "--workers", "1", "--force"] + (["--style", style] if style else []),
    "manim": lambda scene, fmt, q, style, out, frames, name=None, timing=None: [venv_python(), str(SKILL_DIR / "engines" / "manim" / "render.py"),
                                                                             scene, name, "--fmt", fmt, "--quality", "preview", "--out", out, "--force"]
                                                                            + (["--style", style] if style else []) + (["--timing", timing] if timing else []),
    "toon3d": lambda scene, fmt, q, style, out, frames: [sys.executable, str(SKILL_DIR / "engines" / "toon3d" / "render.py"), scene,
                                                          "--fmt", fmt, "--quality", q, "--out", out, "--frames", frames, "--force"],
    "blender": lambda scene, fmt, q, style, out, frames: [sys.executable, str(SKILL_DIR / "engines" / "blender" / "render.py"), scene,
                                                           "--fmt", fmt, "--quality", q, "--out", out, "--frames", frames, "--force"],
}
BITRATE = {"preview": 4e6, "final": 10e6}      # MP4 bits/s (generous)


def tier_info():
    total, _ = memory()
    th = os.cpu_count() or 1
    lite = (total and total < 11.5 * 1024 ** 3) or th < 4
    if lite:
        return "LITE", max(1, th // 2), 10
    if total >= 31 * 1024 ** 3:
        return "POWER?", max(1, th - 1), 30      # POWER also needs a dedicated GPU; hwcheck decides, py2d is CPU-only
    return "STANDARD", max(1, th - 2), 10


def main():
    utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default="py2d"); ap.add_argument("scene"); ap.add_argument("--fmt", default="9x16")
    ap.add_argument("--quality", default="preview"); ap.add_argument("--style"); ap.add_argument("--seconds", type=float)
    ap.add_argument("--name"); ap.add_argument("--timing")
    a = ap.parse_args()
    if a.engine not in ENGINES:
        sys.exit(f"estimate.py does not know engine '{a.engine}' yet (known: {', '.join(ENGINES)})")
    if a.engine == "manim":
        if not a.name:
            sys.exit("--name SceneName is needed for manim")
        secs = a.seconds or (json.loads(Path(a.timing).read_text(encoding="utf-8"))["duration"] if a.timing else 10)
        fps = 30
    elif a.engine == "toon3d":                       # PROJECT folder: TOTAL frames come from story.js
        import re as _re
        m_ = _re.search(r"TOTAL\s*=\s*(\d+)", (Path(a.scene) / "story.js").read_text(encoding="utf-8"))
        fps = 30
        secs = a.seconds or (int(m_.group(1)) / 30 if m_ else 5)
    else:
        scene = json.loads(Path(a.scene).read_text(encoding="utf-8"))
        secs = a.seconds or scene.get("duration", 5)
        fps = scene.get("fps", 30)
    n = int(round(secs * fps))
    tier, workers, limit_min = tier_info()
    eff = 1 + (workers - 1) * 0.7                # parallel efficiency on laptops is well below 100 %
    free_disk = shutil.disk_usage(os.getcwd()).free
    worst = 0
    print(f"tier {tier}: {workers} worker(s), ask above {limit_min} min. Free disk {gb(free_disk)}.")
    print("| Format | Size | s/frame | Frames | Time | Disk (frames + mp4) | Decision |\n|---|---|---|---|---|---|---|")
    for fmt in parse(a.fmt):
        W, H = size(fmt, a.quality)
        tmp = tempfile.mkdtemp(prefix="as-est-")
        try:
            sample = f"0,{n // 2},{n - 1}"
            t0 = time.perf_counter()
            args = (a.scene, fmt, a.quality, a.style, tmp, sample) + ((a.name, a.timing) if a.engine == "manim" else ())
            r = subprocess.run(ENGINES[a.engine](*args), capture_output=True, text=True)
            wall = time.perf_counter() - t0
            m = re.search(r"spf=([\d.]+)", r.stdout)
            if r.returncode or not m:
                print(r.stdout[-800:], r.stderr[-800:]); sys.exit(f"sample render failed for {fmt}")
            spf = float(m.group(1)) * 1.1           # +10 %: busy scenes and thermal slow-down
            if a.engine == "manim":                 # measured at preview size; scale to the target size (cost grows slower than pixels)
                pw, ph = size(fmt, "preview")
                spf *= ((W * H) / (pw * ph)) ** 0.8
            jpgs = [p for p in Path(tmp).glob("f*.jpg")]
            avg = sum(p.stat().st_size for p in jpgs) / max(1, len(jpgs))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        total_s = n * spf / (1 if a.engine in ('manim', 'toon3d', 'blender') else eff) + {'toon3d': 40, 'blender': 90}.get(a.engine, 10)   # + start-up / scene build
        disk = n * avg + secs * BITRATE[a.quality] / 8
        if free_disk < 2 * disk:
            dec, code = "REFUSE (free disk < 2x estimate)", 3
        elif total_s / 60 > limit_min:
            dec, code = f"ASK (over {limit_min} min)", 2
        else:
            dec, code = "OK", 0
        worst = max(worst, code)
        t = f"~{total_s / 60:.1f} min" if total_s >= 60 else f"~{total_s:.0f} s"
        print(f"| {fmt} | {W}x{H} | {spf:.2f} | {n} | {t} | {disk / 1e9:.2f} GB | {dec} |")
    print("DECISION:", {0: "OK", 2: "ASK", 3: "REFUSE"}[worst])
    sys.exit(worst)


if __name__ == "__main__":
    main()
