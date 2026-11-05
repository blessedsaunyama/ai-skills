#!/usr/bin/env python3
"""Output formats, preview sizes and platform safe zones (shared by every engine).

  python shared/formats.py table          platform table (show it at intake)
  python shared/formats.py size 9x16 preview
  python shared/formats.py safe 16x9
  python shared/formats.py crop out/Title_master.mp4 9x16,16x9     FAST mode: centre-crop a master
Standard library only.
"""
import os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import need_tool  # noqa: E402

FORMATS = {  # key: (w, h, label)
    "9x16": (1080, 1920, "Vertical 9:16"),
    "16x9": (1920, 1080, "Landscape 16:9"),
    "1x1": (1080, 1080, "Square 1:1"),
    "4x5": (1080, 1350, "Portrait 4:5"),
}
PLATFORMS = {
    "9x16": "TikTok, Instagram Reels/Stories, YouTube Shorts, Facebook Reels, WhatsApp Status",
    "16x9": "YouTube, projector/TV screen, Facebook/WhatsApp landscape video",
    "1x1": "Facebook/Instagram feed, WhatsApp chats",
    "4x5": "Instagram/Facebook feed (largest non-full-screen post)",
}
# Platform UI overlays to keep text and faces out of: (top, bottom, left, right) px at native size.
SAFE = {"9x16": (220, 420, 60, 140), "16x9": (54, 54, 96, 96), "1x1": (60, 140, 60, 60), "4x5": (70, 160, 60, 60)}
QUALITY = {"preview": 720, "final": 1080}   # short side in px


def size(fmt, quality="final"):
    if fmt not in FORMATS:
        sys.exit(f"unknown format '{fmt}'; use one of {', '.join(FORMATS)}")
    w, h, _ = FORMATS[fmt]
    k = QUALITY.get(quality, 1080) / min(w, h)
    even = lambda v: int(round(v * k / 2)) * 2
    return even(w), even(h)


def safe(fmt, quality="final"):
    w, _ = size(fmt, quality)
    k = w / FORMATS[fmt][0]
    return tuple(int(v * k) for v in SAFE[fmt])


def parse(keys):
    ks = [k.strip() for k in keys.split(",") if k.strip()]
    bad = [k for k in ks if k not in FORMATS]
    if bad:
        sys.exit(f"unknown format(s) {bad}; use {list(FORMATS)}")
    return ks


def crop(src, ks):
    ffprobe, ffmpeg = need_tool("ffprobe"), need_tool("ffmpeg")
    out = subprocess.run([ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                          "-of", "default=nw=1:nk=1", src], capture_output=True, text=True).stdout
    w0, h0 = [int(x) for x in out.split() if x.isdigit()][:2]
    base, ext = os.path.splitext(src)
    for k in ks:
        w, h, _ = FORMATS[k]
        if w > w0 or h > h0:
            print(f"skip {k}: master {w0}x{h0} is smaller than {w}x{h}"); continue
        o = f"{base}_{k}{ext}"
        subprocess.run([ffmpeg, "-v", "error", "-y", "-i", src, "-vf", f"crop={w}:{h}:(iw-{w})/2:(ih-{h})/2", "-c:v", "libx264",
                        "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", o], check=True)
        print(o)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(1)
    if a[0] == "table":
        print("| Format | Size | Best for |\n|---|---|---|")
        for k, (w, h, label) in FORMATS.items():
            print(f"| {label} (`{k}`) | {w}x{h} | {PLATFORMS[k]} |")
    elif a[0] == "size":
        print("%dx%d" % size(a[1], a[2] if len(a) > 2 else "final"))
    elif a[0] == "safe":
        print(dict(zip(("top", "bottom", "left", "right"), safe(a[1], a[2] if len(a) > 2 else "final"))))
    elif a[0] == "crop":
        crop(a[1], parse(a[2]))
    else:
        print(__doc__)
