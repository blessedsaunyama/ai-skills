#!/usr/bin/env python3
"""Contact sheet of stills, for any aspect ratio, with optional safe-zone overlays.

  python3 sheet.py stills/a stills/sheet_a.jpg [cols] [--safe 9x16] [--centre 1080x1080]
    --safe KEY      draw that platform's UI safe zone (red) on every tile (KEY = 9x16, 16x9, 1x1, 4x5)
    --centre WxH    FAST master check: draw the centre-safe box (green) every crop keeps, plus each crop outline (yellow)
                    e.g. master 1920x1920 for 9x16+16x9 -> --centre 1080x1080 --crops 9x16,16x9
    --crops LIST    outline these crops (needs --centre)
Tiles are 480 px on their long side. Needs Pillow.
"""
import glob, os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from formats import FORMATS, SAFE
except Exception:
    FORMATS, SAFE = {}, {}


def opt(name):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else None


pos = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith("--") and not sys.argv[i - 1].startswith("--")]
d, out = pos[0], pos[1]
cols = int(pos[2]) if len(pos) > 2 else None
fs = sorted(glob.glob(os.path.join(d, "f*.jpg")))
if not fs:
    sys.exit(f"no f*.jpg in {d}")
W0, H0 = Image.open(fs[0]).size
k = 480 / max(W0, H0); tw, th = round(W0 * k), round(H0 * k)
cols = cols or max(1, min(len(fs), 1890 // tw))
safe, centre, crops = opt("--safe"), opt("--centre"), opt("--crops")
sh = Image.new("RGB", (tw * min(cols, len(fs)), th * ((len(fs) + cols - 1) // cols)), "black")
for i, f in enumerate(fs):
    im = Image.open(f).convert("RGB").resize((tw, th)); g = ImageDraw.Draw(im)
    if safe and safe in SAFE:
        t, b, l, r = (v * k for v in SAFE[safe])
        g.rectangle([l, t, tw - r, th - b], outline=(255, 60, 60), width=2)
    if centre:
        cw, ch = (int(v) * k for v in centre.lower().split("x"))
        g.rectangle([(tw - cw) / 2, (th - ch) / 2, (tw + cw) / 2, (th + ch) / 2], outline=(60, 255, 90), width=2)
        for c in (crops or "").split(","):
            if c in FORMATS:
                cw2, ch2 = FORMATS[c][0] * k, FORMATS[c][1] * k
                g.rectangle([(tw - cw2) / 2, (th - ch2) / 2, (tw + cw2) / 2, (th + ch2) / 2], outline=(255, 220, 40), width=1)
    g.text((6, 4), os.path.basename(f)[1:-4], fill=(255, 255, 255))
    sh.paste(im, ((i % cols) * tw, (i // cols) * th))
sh.save(out, quality=88)
print(out, len(fs), f"tiles {tw}x{th}")
