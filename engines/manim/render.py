#!/usr/bin/env python3
"""Engine B (Manim Community): render a Manim scene file to our standard f0000.jpg frames, safely.

  python engines/manim/render.py SCENE.py SceneName --fmt 9x16 [--quality preview|final] [--style manim]
         [--timing work/phrases.json] [--out frames_9x16] [--frames 0,60,120] [--force]

- The scene file must start with `from studio import *` (engines/manim/studio.py): format, safe zone, style colours,
  voice timeline, LaTeX-free maths fallback.
- Manim renders an MP4 into OUT/_manim (it caches every finished animation, so re-running RESUMES), then ffmpeg
  writes OUT/f0000.jpg ... so captions.py, sheet.py and finish.py work exactly as for the other engines.
- --frames 0,60,120: Manim can't render single frames of an animation, so it renders the whole scene at preview size
  and keeps only those frames (a quick look check; scenes are usually short and fast).
- Low CPU priority, one render at a time, pauses (exit code 4) if free RAM drops below 15 %.
Prints "spf=" (seconds per frame) at the end for shared/estimate.py.
"""
import argparse, os, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
from common import acquire_lock, find_tool, free_ram_fraction, low_priority, need_tool, on_battery, release_lock, utf8, venv_python  # noqa: E402
from formats import size as fmt_size  # noqa: E402


def main():
    utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("scene"); ap.add_argument("name"); ap.add_argument("--fmt", default="16x9"); ap.add_argument("--quality", default="preview")
    ap.add_argument("--style", default="manim"); ap.add_argument("--timing"); ap.add_argument("--out"); ap.add_argument("--frames")
    ap.add_argument("--force", action="store_true"); ap.add_argument("--workers")   # --workers accepted for estimate.py; Manim is single-process
    a = ap.parse_args()
    ffmpeg = need_tool("ffmpeg")
    py = venv_python()
    if subprocess.run([py, "-c", "import manim"], capture_output=True).returncode:
        sys.exit("Manim is not installed. With the user's OK: python shared/setup_check.py --engine manim --install")
    W, H = fmt_size(a.fmt, "preview" if a.frames else a.quality)
    out = Path(a.out or f"frames_{a.fmt}"); out.mkdir(parents=True, exist_ok=True)
    media = out / "_manim"
    if a.force and media.exists():
        shutil.rmtree(media)
    env = dict(os.environ, AS_FMT=a.fmt, AS_STYLE=a.style, PYTHONPATH=str(HERE) + os.pathsep + os.environ.get("PYTHONPATH", ""))
    latex = find_tool("latex")                        # LaTeX may be installed but not on PATH yet (fresh install, old shell)
    if latex:
        env["PATH"] = os.path.dirname(latex) + os.pathsep + env.get("PATH", "")
        env["AS_LATEX"] = "1"
    if a.timing:
        env["AS_TIMING"] = str(Path(a.timing).resolve())
    if on_battery():
        print("⚠️ This laptop is ON BATTERY. Plug in for long renders.")
    acquire_lock(f"manim {a.scene} {a.fmt}")
    low_priority()
    cmd = [py, "-m", "manim", "render", str(Path(a.scene).resolve()), a.name, "-r", f"{W},{H}", "--fps", "30",
           "--format", "mp4", "--media_dir", str(media.resolve()), "-o", f"{a.name}_{a.fmt}", "--progress_bar", "none", "-v", "WARNING"]
    print(f"manim: {a.name} {a.fmt} {W}x{H} ({'look check' if a.frames else a.quality}), style {a.style}, low priority")
    t0 = time.perf_counter()
    try:
        p = subprocess.Popen(cmd, env=env, cwd=str(Path(a.scene).resolve().parent))
        while p.poll() is None:
            time.sleep(1.0)
            if free_ram_fraction() < 0.15:
                p.terminate()
                print("⏸ PAUSED: free RAM fell below 15 %. Close other apps and run the SAME command again "
                      "(finished animations are cached and will not re-render)."); sys.exit(4)
        if p.returncode:
            sys.exit(f"manim failed (exit {p.returncode}); read the error above")
    finally:
        release_lock()
    mp4 = next(iter(sorted(media.rglob(f"{a.name}_{a.fmt}.mp4"))), None)
    if not mp4:
        sys.exit("manim finished but no video was found in " + str(media))
    wall = time.perf_counter() - t0
    for old in out.glob("f*.jpg"):
        old.unlink()
    subprocess.run([ffmpeg, "-v", "error", "-y", "-i", str(mp4), "-q:v", "2", "-start_number", "0", str(out / "f%04d.jpg")], check=True)
    if a.frames:                                      # look check: keep only the requested frames
        keep = {int(x) for x in a.frames.split(",")}
        for f in out.glob("f*.jpg"):
            if int(f.stem[1:]) not in keep:
                f.unlink()
    n = len(list(out.glob("f*.jpg")))
    total = int(float(subprocess.run([need_tool("ffprobe"), "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                                      "stream=nb_read_packets", "-of", "csv=p=0", str(mp4)], capture_output=True, text=True).stdout.strip() or n))
    print(f"done: {n} frame(s) -> {out}  (video {mp4.name}, {total} frames, {wall:.1f}s)")
    print(f"spf={wall / max(1, total):.3f} wall_spf={wall / max(1, total):.3f} workers=1")


if __name__ == "__main__":
    main()
