#!/usr/bin/env python3
"""Thumbnail from a rendered still + a short title.

  python3 thumb.py stills/key/f0420.jpg "Daniel and the Lions" out/thumb_16x9.jpg [--size 1280x720] [--pos top|bottom]
Render the still in the target format first (e.g. FMT=16x9 node render.mjs stills/key "420").
YouTube wants 1280x720 (16:9); for 9:16 use 1080x1920. Keep the title to 2-5 words, no verse text,
no faces of God the Father (there are none), and keep text out of the platform safe zone (formats.py safe <fmt>).
Needs Pillow.
"""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps

FONTS = ["arialbd.ttf", "Arial Bold.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVuSans-Bold.ttf"]


def font(size):
    for f in FONTS:
        try:
            return ImageFont.truetype(f, size)
        except Exception:
            pass
    return ImageFont.load_default(size=size)


a = sys.argv[1:]
if len(a) < 3:
    print(__doc__); sys.exit(1)
src, title, out = a[0], a[1], a[2]
im = Image.open(src).convert("RGB")
if "--size" in a:
    W, H = map(int, a[a.index("--size") + 1].lower().split("x")); im = ImageOps.fit(im, (W, H))
W, H = im.size
pos = a[a.index("--pos") + 1] if "--pos" in a else ("top" if H > W else "bottom")
g = ImageDraw.Draw(im)
size = int(min(W, H) * 0.11); f = font(size)
lines, cur = [], ""
for w in title.split():                       # wrap to ~85 % width
    t = (cur + " " + w).strip()
    if g.textlength(t, font=f) > W * 0.85 and cur:
        lines.append(cur); cur = w
    else:
        cur = t
lines.append(cur)
lh = int(size * 1.15); y = int(H * (0.14 if H > W else 0.08)) if pos == "top" else H - lh * len(lines) - int(H * (0.25 if H > W else 0.08))
for ln in lines:
    x = (W - g.textlength(ln, font=f)) / 2
    g.text((x, y), ln, font=f, fill="#fff6d8", stroke_width=max(4, size // 9), stroke_fill="#241726"); y += lh
im.save(out, quality=92); print(out, f"{W}x{H}")
