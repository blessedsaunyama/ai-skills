#!/usr/bin/env python3
"""Engine C (Toon 3D): 2D character cards in an inked, painted three.js world, rendered in headless Chromium.

  python engines/toon3d/render.py PROJECT --fmt 9x16 [--quality preview|final] [--out frames_9x16] [--frames 0-149 | 0,75,149]
         [--master 1920x1920] [--confirm-long] [--force]
    PROJECT  a folder with story.js (shots, cameras, lights, actors, fx) and world.js (buildWorld) -- see README.md

- Builds PROJECT's web folder in OUT/_web (engine + three.js r160 + toon library + the project's files); the project stays clean.
- Tier limits (shared/hwcheck.py): LITE -> stills only (max 6 frames); STANDARD -> at most 5 s (150 frames) unless
  --confirm-long (ask the user first: CPU WebGL is slow, ~2-5 s per frame); POWER -> no limit.
- Existing frames are skipped (re-run = resume; frames are written atomically). --force re-renders them.
- Low CPU priority, one render at a time, pauses (exit code 4) if free RAM drops below 15 %.
- --master WxH renders one FAST master (fit=focal) to crop into several formats (shared/formats.py crop).
Needs node 22.6+, Playwright + Chromium (python shared/setup_check.py --engine toon3d). Prints "spf=" at the end.
"""
import argparse, os, re, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
from common import acquire_lock, free_ram_fraction, low_priority, memory, need_tool, on_battery, release_lock, utf8  # noqa: E402

SCALE = {"preview": 2 / 3, "final": 1.0}


def build_web(project: Path, web: Path, node):
    (web / "lib").mkdir(parents=True, exist_ok=True)
    for f in (HERE / "engine").iterdir():
        shutil.copy2(f, web / f.name)
    shutil.copy2(HERE / "vendor" / "three.module.js", web / "lib" / "three.module.js")
    base = web / "toonbase.js"
    src = HERE / "vendor" / "toon.ts"
    if not base.exists() or base.stat().st_mtime < src.stat().st_mtime:
        js = ("const m=require('node:module'),fs=require('fs');"
              "fs.writeFileSync(process.argv[2],m.stripTypeScriptTypes(fs.readFileSync(process.argv[1],'utf8'),{mode:'transform'}))")
        subprocess.run([node, "-e", js, str(src), str(base)], check=True)
    (web / "toon.js").write_text(base.read_text(encoding="utf-8") + "\n" + (web / "roman.js").read_text(encoding="utf-8") + "\n"
                                 + (web / "biblical.js").read_text(encoding="utf-8"), encoding="utf-8")
    for f in project.glob("*.js"):                        # story.js, world.js and any helpers of the project
        shutil.copy2(f, web / f.name)
    for need in ("story.js", "world.js"):
        if not (web / need).exists():
            sys.exit(f"{project} has no {need} (see engines/toon3d/README.md)")


def tier():
    total, _ = memory()
    th = os.cpu_count() or 1
    if (total and total < 11.5 * 1024 ** 3) or th < 4:
        return "LITE"
    return "STANDARD" if total < 31 * 1024 ** 3 else "POWER?"   # POWER also needs a dedicated GPU: hwcheck.py decides


def main():
    utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("project"); ap.add_argument("--fmt", default="9x16"); ap.add_argument("--quality", default="preview")
    ap.add_argument("--out"); ap.add_argument("--frames"); ap.add_argument("--master"); ap.add_argument("--confirm-long", action="store_true")
    ap.add_argument("--force", action="store_true"); ap.add_argument("--workers"); ap.add_argument("--style")   # accepted for estimate.py
    ap.add_argument("--power", action="store_true", help="hwcheck.py said POWER (dedicated GPU): lift the 5 s limit")
    a = ap.parse_args()
    node = need_tool("node")
    v = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip().lstrip("v").split(".")
    if tuple(int(x) for x in v[:2]) < (22, 6):
        sys.exit("node 22.6+ is needed (it strips the TypeScript types of the toon library)")
    project = Path(a.project).resolve()
    story = (project / "story.js").read_text(encoding="utf-8")
    m = re.search(r"TOTAL\s*=\s*(\d+)", story)
    total = int(m.group(1)) if m else 150
    spec = a.frames or f"0-{total - 1}"
    frames = []
    for part in spec.split(","):
        if "-" in part:
            x, y = part.split("-"); frames += range(int(x), int(y) + 1)
        elif part.strip():
            frames.append(int(part))
    t = "POWER" if a.power else tier()
    if t == "LITE" and len(frames) > 6:
        sys.exit("LITE computer: Toon 3D is limited to stills (up to 6 frames, e.g. --frames 0,60,120). "
                 "Offer the same story in an engine-A style (Flat 2D, Storybook) for the video.")
    if t.startswith("STANDARD") and len(frames) > 150 and not a.confirm_long:
        sys.exit(f"STANDARD computer: Toon 3D renders up to 5 s (150 frames) by default; this is {len(frames)} frames "
                 f"(~{len(frames) * 3 / 60:.0f}-{len(frames) * 5 / 60:.0f} min). Run shared/estimate.py, ask the user, then add --confirm-long. "
                 "The render resumes if interrupted.")
    out = Path(a.out or f"frames_{a.master or a.fmt}"); out.mkdir(parents=True, exist_ok=True)
    web = out / "_web"
    build_web(project, web, node)
    env = dict(os.environ, WEB=str(web.resolve()))
    if a.master:
        env["SIZE"] = a.master
    else:
        env["FMT"] = a.fmt
        if SCALE.get(a.quality, 1) != 1:
            env["SCALE"] = f"{SCALE[a.quality]:.4f}"
    if not a.force:
        env["RESUME"] = "1"
    if on_battery():
        print("⚠️ This laptop is ON BATTERY. Plug in: CPU WebGL rendering is heavy.")
    acquire_lock(f"toon3d {project.name} {a.master or a.fmt}")
    low_priority()
    print(f"toon3d: {project.name} {a.master or a.fmt} ({a.quality}), {len(frames)} frames, tier {t}, low priority")
    t0 = time.perf_counter()
    log = []
    try:
        p = subprocess.Popen([node, str(HERE / "tools" / "render.mjs"), str(out.resolve()), spec], env=env, cwd=str(web),
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        import threading
        def pump():
            for line in p.stdout:
                log.append(line); print(line.rstrip(), flush=True)
        th = threading.Thread(target=pump, daemon=True); th.start()
        while p.poll() is None:
            time.sleep(1.0)
            if free_ram_fraction() < 0.15:
                p.terminate()
                print("⏸ PAUSED: free RAM fell below 15 %. Close other apps, then run the SAME command again to resume."); sys.exit(4)
        th.join(timeout=5)
        if p.returncode:
            sys.exit(f"render.mjs failed (exit {p.returncode})")
    finally:
        release_lock()
    m = re.search(r"done (\d+) frames, ([\d.]+) s/frame", "".join(log))
    n, spf = (int(m.group(1)), float(m.group(2))) if m else (0, 0.0)
    print(f"done: {n} new frames in {time.perf_counter() - t0:.1f}s -> {out}")
    st = re.search(r"steady ([\d.]+) s/frame", "".join(log))
    print(f"spf={float(st.group(1)) if st else spf:.3f} wall_spf={spf:.3f} workers=1")


if __name__ == "__main__":
    main()
