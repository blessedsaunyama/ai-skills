#!/usr/bin/env python3
"""Engine A (py2d): render a scene.json to numbered JPG frames, safely.

  python engines/py2d/render.py SCENE.json --fmt 9x16 [--quality preview|final] [--style NAME]
         [--out DIR] [--frames 0-149 | 0,75,149] [--seconds 5] [--workers N] [--force] [--override-limits]

- Frames go to DIR/f0000.jpg ... Existing frames are skipped, so re-running the same command RESUMES.
- Runs at low CPU priority with the worker count from the hardware tier (shared/hwcheck.py rules).
- Pauses safely (exit code 4) if free RAM drops below 15 %; warns when a laptop is on battery.
- Only one render at a time (a lock in the temp folder).
Prints "spf=<seconds per frame>" at the end (used by shared/estimate.py).
Needs numpy + Pillow (python shared/setup_check.py --engine py2d).
"""
import argparse, json, math, multiprocessing as mp, os, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "shared"))
from common import acquire_lock, free_ram_fraction, low_priority, memory, on_battery, release_lock, utf8  # noqa: E402
from formats import safe as fmt_safe, size as fmt_size  # noqa: E402

RAM_STOP = 0.15
_G = {}


def camera(scene, fmt, t, ease, W, H):
    keys = scene.get(f"camera_{fmt}") or scene["camera"]
    ks = [k for k in keys]
    if t <= ks[0]["t"]:
        a = b = ks[0]; u = 0
    elif t >= ks[-1]["t"]:
        a = b = ks[-1]; u = 0
    else:
        for a, b in zip(ks, ks[1:]):
            if a["t"] <= t <= b["t"]:
                break
        from canvas import EASE
        u = EASE.get(b.get("ease", ease), EASE["inOut"])((t - a["t"]) / max(1e-9, b["t"] - a["t"]))
    g = lambda k: a[k] + (b[k] - a[k]) * u
    w, h = g("w"), g("h")
    return {"x": g("x"), "y": g("y"), "k": min(W / w, H / h)}     # the must-see box always fits; extra room shows more world


def init_worker(scene, style, fmt, quality, out, ss):
    low_priority()
    from canvas import load_style
    st = load_style(style)
    W, H = fmt_size(fmt, quality)
    _G.update(scene=scene, style=st, fmt=fmt, out=out, W=W, H=H, ss=ss, safe=fmt_safe(fmt, quality))


def fx_state(el, t, st):
    """Entrance/exit effect for an element: None (plain), "hidden", or (kind, progress 0-1).
    "enter": 1.2 or {"t": 1.2, "kind": "pop|fade|slide|draw", "dur": 0.6}; "exit": same (fades out)."""
    en, ex = el.get("enter"), el.get("exit")
    if en is not None:
        e = en if isinstance(en, dict) else {"t": float(en)}
        kind = e.get("kind") or st.get("fx", {}).get("enter", "fade")
        dur = e.get("dur", st.get("fx", {}).get("dur", 0.6))
        u = (t - e["t"]) / max(1e-6, dur)
        if u <= 0:
            return "hidden"
        if u < 1:
            return (kind, u)
    if ex is not None:
        e = ex if isinstance(ex, dict) else {"t": float(ex)}
        u = (t - e["t"]) / max(1e-6, e.get("dur", 0.4))
        if u >= 1:
            return "hidden"
        if u > 0:
            return ("fade", 1 - u)
    return None


def render_frame(i):
    from actors import DRAW
    from canvas import Canvas, val
    sc, st = _G["scene"], _G["style"]
    fps = sc.get("fps", 30)
    hold = st["motion"].get("hold", 1)
    t = (i - i % hold) / fps
    t0 = time.perf_counter()
    cam = camera(sc, _G["fmt"], t, st["motion"].get("ease", "inOut"), _G["W"], _G["H"])
    cv = Canvas(_G["W"], _G["H"], _G["ss"], cam, st, i, t)
    cv.safe = _G["safe"]
    cv.fmt = _G["fmt"]
    cv.storm = float(val(sc.get("storm", 0), t, "inOut", 0))
    for n, el in enumerate(sc["elements"]):
        if "show" in el and el["type"] not in ("caption", "animal", "bird") and not (el["show"][0] <= t <= el["show"][1]):
            continue
        fx = fx_state(el, t, st)
        if fx == "hidden":
            continue
        if fx:
            cv.begin()
        DRAW[el["type"]](cv, el, t, el.get("seed", n + 1))
        if fx:
            cv.end(fx=fx)
    s = cv.storm
    img = cv.finish(grade=(1 - 0.22 * s, 1 - 0.18 * s, 1 - 0.08 * s) if s > 0 else None)
    dst = Path(_G["out"]) / f"f{i:04d}.jpg"
    tmp = dst.with_suffix(".tmp.jpg")
    img.save(tmp, quality=92)
    os.replace(tmp, dst)                      # a frame is either complete or absent: safe to resume
    return i, time.perf_counter() - t0


def parse_frames(spec, total):
    if not spec:
        return list(range(total))
    out = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-"); out += range(int(a), int(b) + 1)
        elif part.strip():
            out.append(int(part))
    return [f for f in out if 0 <= f < total]


def main():
    utf8()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scene"); ap.add_argument("--fmt", default="9x16"); ap.add_argument("--quality", default="preview")
    ap.add_argument("--style"); ap.add_argument("--out"); ap.add_argument("--frames"); ap.add_argument("--seconds", type=float)
    ap.add_argument("--workers", type=int); ap.add_argument("--ss", type=int, default=2); ap.add_argument("--force", action="store_true")
    ap.add_argument("--override-limits", action="store_true")
    a = ap.parse_args()
    scene = json.loads(Path(a.scene).read_text(encoding="utf-8"))
    style = a.style or scene.get("style", "flat-2d")
    fps = scene.get("fps", 30)
    dur = a.seconds or scene["duration"]
    total = int(round(dur * fps))
    W, H = fmt_size(a.fmt, a.quality)
    # --- tier limits (quick version of hwcheck: RAM + threads are all py2d needs) ---
    tot_ram, free_ram = memory()
    threads = os.cpu_count() or 1
    lite = tot_ram and tot_ram < 11.5 * 1024 ** 3 or threads < 4
    if lite and min(W, H) > 720 and not a.override_limits:
        print("LITE tier: limiting output to 720p (use --override-limits to force 1080p; it may be very slow)")
        a.quality = "preview"; W, H = fmt_size(a.fmt, "preview")
    tier_workers = max(1, threads // 2) if lite else (max(1, threads - 2) if tot_ram < 31 * 1024 ** 3 else max(1, threads - 1))
    per_worker = (W * a.ss) * (H * a.ss) * 4 * 6 + 150e6        # canvas + a few full-size layers + python
    ram_workers = max(1, int(free_ram * 0.5 // per_worker)) if free_ram else 1
    workers = a.workers or min(tier_workers, ram_workers)
    if a.workers and a.workers > tier_workers and not a.override_limits:
        print(f"⚠️ {a.workers} workers is above the safe limit ({tier_workers}) for this computer; using {tier_workers}.")
        workers = tier_workers
    out = Path(a.out or f"frames_{a.fmt}")
    out.mkdir(parents=True, exist_ok=True)
    frames = parse_frames(a.frames, total)
    todo = [f for f in frames if a.force or not (out / f"f{f:04d}.jpg").exists()]
    if on_battery():
        print("⚠️ This laptop is ON BATTERY. Plug in for long renders (it will be slower and drain the battery).")
    print(f"py2d: {style} {a.fmt} {W}x{H} ({a.quality}), {len(frames)} frames, {len(frames) - len(todo)} already done, "
          f"{len(todo)} to render with {workers} worker(s) at low priority")
    if not todo:
        print("spf=0 (nothing to do)"); return
    acquire_lock(f"py2d {a.scene} {a.fmt}")
    low_priority()
    t_start = time.perf_counter(); times = []; done = 0
    try:
        args = (scene, style, a.fmt, a.quality, str(out), a.ss)
        if workers == 1:
            init_worker(*args)
            it = map(render_frame, todo)
            pool = None
        else:
            pool = mp.Pool(workers, initializer=init_worker, initargs=args)
            it = pool.imap_unordered(render_frame, todo, chunksize=1)
        for i, dt in it:
            done += 1; times.append(dt)
            if done % 10 == 0 or done == len(todo):
                el = time.perf_counter() - t_start
                print(f"  {done}/{len(todo)} frames  {el:.0f}s elapsed  ~{el / done * (len(todo) - done):.0f}s left", flush=True)
            if done % 5 == 0 and free_ram_fraction() < RAM_STOP:
                if pool:
                    pool.terminate()
                print(f"⏸ PAUSED: free RAM fell below {int(RAM_STOP * 100)} %. Close other apps, then run the SAME command again to resume "
                      f"({done} new frames are saved).")
                sys.exit(4)
        if pool:
            pool.close(); pool.join()
    finally:
        release_lock()
    wall = time.perf_counter() - t_start
    print(f"done: {len(todo)} frames in {wall:.1f}s -> {out}")
    print(f"spf={sum(times) / len(times):.3f} wall_spf={wall / len(todo):.3f} workers={workers}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
