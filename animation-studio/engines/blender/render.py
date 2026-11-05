#!/usr/bin/env python3
"""Engine D (Blender, background mode): cinematic 3D frames from a scene.json, safely.

  python engines/blender/render.py SCENE.json --fmt 16x9 [--quality preview|final] [--engine eevee|cycles] [--samples N]
         [--out frames_16x9] [--frames 0-89 | 0,45,89] [--tier STANDARD|POWER|LITE] [--override-limits] [--force] [--save-blend f.blend]

Tier limits (from shared/hwcheck.py; pass --tier, or it is detected):
  LITE      stills only (<= 6 frames), 720p, Eevee 16 samples
  STANDARD  Eevee only, <= 5 s (150 frames), <= 720p, 16 samples (preview) / 32 (final)
  POWER     Eevee or Cycles on the GPU, any length, 1080p+, Cycles 128 samples
--override-limits lifts them only after the user accepted a clear warning (it can make the computer hot and slow).
Missing frames only are rendered (re-run = resume; frames are written atomically). Low priority, one job at a time,
pauses (exit code 4) below 15 % free RAM. Blender is GPL and is called, never bundled. Prints "spf=" at the end.
"""
import argparse, json, os, re, subprocess, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
from common import (SKILL_DIR, acquire_lock, find_tool, free_ram_fraction, low_priority, on_battery, release_lock,  # noqa: E402
                    utf8)
from formats import size as fmt_size  # noqa: E402

LIMITS = {
    "LITE": {"max_frames": 6, "max_h": 720, "engines": ["EEVEE"], "samples": {"preview": 16, "final": 16}},
    "STANDARD": {"max_frames": 150, "max_h": 720, "engines": ["EEVEE"], "samples": {"preview": 12, "final": 32}},
    "POWER": {"max_frames": None, "max_h": 2160, "engines": ["EEVEE", "CYCLES"], "samples": {"preview": 32, "final": 128}},
}


def detect_tier():
    sys.path.insert(0, str(HERE.parents[1] / "shared"))
    import hwcheck
    hw = hwcheck.detect()
    return hwcheck.tier_of(hw)


def style_json(name):
    p = SKILL_DIR / "styles" / f"{name}.md"
    m = re.search(r"```json\s*\n(.*?)\n```", p.read_text(encoding="utf-8"), re.S)
    return json.loads(m.group(1))


def main():
    utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("scene"); ap.add_argument("--fmt", default="16x9"); ap.add_argument("--quality", default="preview")
    ap.add_argument("--engine", default="eevee"); ap.add_argument("--samples", type=int); ap.add_argument("--out"); ap.add_argument("--frames")
    ap.add_argument("--tier"); ap.add_argument("--override-limits", action="store_true"); ap.add_argument("--force", action="store_true")
    ap.add_argument("--save-blend"); ap.add_argument("--workers"); ap.add_argument("--style")
    a = ap.parse_args()
    blender = find_tool("blender")
    if not blender:
        sys.exit("Blender not found. Install (ask the user first): winget install BlenderFoundation.Blender | brew install --cask blender | sudo snap install blender --classic")
    scene = json.loads(Path(a.scene).read_text(encoding="utf-8"))
    total = int(round(scene["duration"] * scene.get("fps", 30)))
    frames = []
    for part in (a.frames or f"0-{total - 1}").split(","):
        if "-" in part:
            x, y = part.split("-"); frames += range(int(x), int(y) + 1)
        elif part.strip():
            frames.append(int(part))
    tier = (a.tier or detect_tier()).upper()
    lim = LIMITS.get(tier, LIMITS["STANDARD"])
    engine = a.engine.upper()
    W, H = fmt_size(a.fmt, a.quality)
    warn = []
    if engine not in lim["engines"]:
        warn.append(f"{tier}: {engine} is not allowed (Eevee only)")
    if lim["max_frames"] and len(frames) > lim["max_frames"]:
        warn.append(f"{tier}: {len(frames)} frames is over the limit of {lim['max_frames']}" + (" (stills only)" if tier == "LITE" else " (5 s)"))
    if min(W, H) > lim["max_h"]:
        warn.append(f"{tier}: {min(W, H)}p is over the {lim['max_h']}p limit")
    if warn and not a.override_limits:
        sys.exit("Refused to keep the computer safe:\n  - " + "\n  - ".join(warn) +
                 "\nOptions: shorten the shot, use --quality preview, use Eevee, or (only after the user accepts the risk) --override-limits.")
    if warn:
        print("⚠️ LIMITS OVERRIDDEN by request: " + "; ".join(warn) + ". Save your work; the computer may get hot and slow.")
    samples = a.samples or lim["samples"].get(a.quality, 16)
    if not a.override_limits and tier != "POWER":
        samples = min(samples, lim["samples"]["final"])
    out = Path(a.out or f"frames_{a.fmt}").resolve(); out.mkdir(parents=True, exist_ok=True)
    todo = [f for f in frames if a.force or not (out / f"f{f:04d}.jpg").exists()]
    print(f"blender: {Path(a.scene).name} {a.fmt} {W}x{H} {engine} {samples} samples, tier {tier}, "
          f"{len(frames) - len(todo)} done, {len(todo)} to render, low priority")
    if not todo:
        print("spf=0 (nothing to do)"); return
    if on_battery():
        print("⚠️ This laptop is ON BATTERY. Plug in before rendering 3D.")
    args = {"scene": str(Path(a.scene).resolve()), "style": style_json(a.style or scene.get("style", "cinematic-3d")), "out": str(out),
            "width": W, "height": H, "fmt": a.fmt, "engine": engine, "samples": samples, "frames": todo,
            "gpu": engine == "CYCLES", "save_blend": a.save_blend}
    af = Path(tempfile.gettempdir()) / f"as-blender-{os.getpid()}.json"
    af.write_text(json.dumps(args), encoding="utf-8")
    acquire_lock(f"blender {Path(a.scene).name} {a.fmt}")
    low_priority()
    t0 = time.perf_counter(); times = []
    try:
        p = subprocess.Popen([blender, "-b", "--factory-startup", "--python-exit-code", "1", "-P", str(HERE / "build_scene.py"), "--", str(af)],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        import threading
        log = []
        def pump():
            for line in p.stdout:
                log.append(line)
                m = re.match(r"FRAME (\d+) ([\d.]+)s", line)
                if m:
                    times.append(float(m.group(2)))
                    if len(times) % 10 == 0 or len(times) == len(todo):
                        el = time.perf_counter() - t0
                        print(f"  {len(times)}/{len(todo)} frames  {el:.0f}s elapsed  ~{el / len(times) * (len(todo) - len(times)):.0f}s left", flush=True)
                elif re.search(r"Error|error:|Traceback|skipped|fallback", line):
                    print("  blender:", line.rstrip(), flush=True)
        th = threading.Thread(target=pump, daemon=True); th.start()
        while p.poll() is None:
            time.sleep(1.0)
            if free_ram_fraction() < 0.15:
                p.terminate()
                print("⏸ PAUSED: free RAM fell below 15 %. Close other apps, then run the SAME command again to resume."); sys.exit(4)
        th.join(timeout=5)
        if p.returncode:
            print("".join(log[-30:])); sys.exit(f"Blender failed (exit {p.returncode})")
    finally:
        release_lock(); af.unlink(missing_ok=True)
    steady = sorted(times[1:])[len(times[1:]) // 2] if len(times) > 1 else (times[0] if times else 0)
    print(f"done: {len(times)} frames in {time.perf_counter() - t0:.1f}s -> {out}")
    print(f"spf={steady:.3f} wall_spf={(time.perf_counter() - t0) / max(1, len(times)):.3f} workers=1")


if __name__ == "__main__":
    main()
