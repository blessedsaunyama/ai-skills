#!/usr/bin/env python3
"""Multi-format planning + FAST-mode crops.

  python3 formats.py table                                  platform table (show it at intake)
  python3 formats.py plan 9x16,16x9 --seconds 45 [--spf 4]  FAST vs BEST: master size, safe box, render-time estimate
  python3 formats.py crop out/Title.mp4 9x16,16x9           FAST: centre-crop the master into each format (ffmpeg)
  python3 formats.py safe 16x9                              print the platform UI safe zone (px) for a format

--spf = measured seconds per frame at 1080x1920 (render.mjs prints it). Default 5 (CPU SwiftShader is ~3-10).
Render cost is assumed to scale with pixel count.
Standard library only.
"""
import json, os, subprocess, sys

FORMATS = {  # key: (w, h, label)
    "9x16": (1080, 1920, "Vertical 9:16"),
    "16x9": (1920, 1080, "Landscape 16:9"),
    "1x1": (1080, 1080, "Square 1:1"),
    "4x5": (1080, 1350, "Portrait 4:5"),
}
PLATFORMS = {
    "9x16": "WhatsApp Status, TikTok, Instagram Reels/Stories, YouTube Shorts, Facebook Reels",
    "16x9": "YouTube (main), church projector/TV screen, Facebook/WhatsApp video (landscape)",
    "1x1": "Facebook/Instagram feed posts, WhatsApp chats (fits both phone orientations)",
    "4x5": "Instagram/Facebook feed (takes the most feed space without being full-screen)",
}
# Platform UI overlays to keep text/faces out of: (top, bottom, left, right) in px at the format's native size.
SAFE = {
    "9x16": (220, 420, 60, 140),   # top bar / caption + buttons at the bottom / like-share column on the right
    "16x9": (54, 54, 96, 96),      # 90 % title-safe (projectors and TVs crop edges)
    "1x1": (60, 140, 60, 60),      # feed caption bar
    "4x5": (70, 160, 60, 60),
}


def parse(keys):
    ks = [k.strip() for k in keys.split(",") if k.strip()]
    bad = [k for k in ks if k not in FORMATS]
    if bad:
        sys.exit(f"unknown format(s) {bad}; use {list(FORMATS)}")
    return ks


def master_for(ks):
    """FAST master = max width x max height of the chosen formats, so every crop is native resolution, centred."""
    W = max(FORMATS[k][0] for k in ks); H = max(FORMATS[k][1] for k in ks)
    sw = min(FORMATS[k][0] for k in ks); sh = min(FORMATS[k][1] for k in ks)
    return W, H, sw, sh


def table():
    print("| Format | Size | Best for |\n|---|---|---|")
    for k, (w, h, label) in FORMATS.items():
        print(f"| {label} (`{k}`) | {w}x{h} | {PLATFORMS[k]} |")


def fmt_t(s):
    return f"{s/60:.0f} min" if s < 3600 else f"{s/3600:.1f} h"


def plan(ks, seconds, spf):
    frames = round(seconds * 30); ref = 1080 * 1920
    W, H, sw, sh = master_for(ks)
    best = sum(frames * spf * FORMATS[k][0] * FORMATS[k][1] / ref for k in ks)
    fast = frames * spf * W * H / ref
    out = {"formats": ks, "frames": frames, "fast": {"master": f"{W}x{H}", "centre_safe_box": f"{sw}x{sh}", "est_render": fmt_t(fast)},
           "best": {"renders": [f"{k} {FORMATS[k][0]}x{FORMATS[k][1]}" for k in ks], "est_render": fmt_t(best)}}
    print(json.dumps(out, indent=1))
    print(f"\nFAST: one {W}x{H} master (fit=focal); keep faces/action inside the centre {sw}x{sh} box; ~{fmt_t(fast)} + seconds of ffmpeg cropping.")
    print(f"BEST: {len(ks)} render(s), each framed for its own shape; ~{fmt_t(best)}.")
    if len(ks) == 1:
        print("Only one format chosen: FAST and BEST are the same (just render it).")


def crop(src, ks):
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                            "-of", "default=nw=1:nk=1", src], capture_output=True, text=True).stdout
    nums = [int(x) for x in probe.split() if x.strip().isdigit()]   # robust across ffprobe versions
    if len(nums) < 2:
        sys.exit(f"could not read the size of {src} (is ffprobe on PATH?)")
    w0, h0 = nums[:2]
    base, ext = os.path.splitext(src)
    for k in ks:
        w, h, _ = FORMATS[k]
        if w > w0 or h > h0:
            print(f"skip {k}: master {w0}x{h0} is smaller than {w}x{h}"); continue
        out = f"{base}_{k}{ext}"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", f"crop={w}:{h}:(iw-{w})/2:(ih-{h})/2",
                        "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", out], check=True)
        print(out)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(1)
    if a[0] == "table":
        table()
    elif a[0] == "plan":
        secs = float(a[a.index("--seconds") + 1]) if "--seconds" in a else 45
        spf = float(a[a.index("--spf") + 1]) if "--spf" in a else 5
        plan(parse(a[1]), secs, spf)
    elif a[0] == "crop":
        crop(a[1], parse(a[2]))
    elif a[0] == "safe":
        print(dict(zip(("top", "bottom", "left", "right"), SAFE[a[1]])))
    else:
        print(__doc__)
