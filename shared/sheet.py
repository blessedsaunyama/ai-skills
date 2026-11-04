#!/usr/bin/env python3
"""Contact sheet: one row per frames folder (e.g. one per style or format), labelled, with optional safe zones.

  python shared/sheet.py OUT.jpg DIR [DIR ...] [--pick 0,60,110,149] [--labels a,b,c] [--safe 9x16] [--tile 360]
    --pick    frame numbers to show (default: up to 8 evenly spaced frames that exist)
    --safe    draw the platform UI safe zone (red) for that format key
    --tile    long side of each tile in px (default 360)
Needs Pillow. (Based on the cartoon kit's sheet.py.)
"""
import glob, os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from formats import FORMATS, SAFE  # noqa: E402


def opt(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main():
    pos, skip = [], False
    for i, x in enumerate(sys.argv[1:], 1):
        if skip:
            skip = False; continue
        if x.startswith("--"):
            skip = True; continue
        pos.append(x)
    if len(pos) < 2:
        print(__doc__); sys.exit(1)
    out, dirs = pos[0], pos[1:]
    labels = (opt("--labels") or ",".join(os.path.basename(os.path.normpath(d)) for d in dirs)).split(",")
    tile = int(opt("--tile", 360))
    safe = opt("--safe")
    rows = []
    for d in dirs:
        fs = sorted(glob.glob(os.path.join(d, "f[0-9]*.jpg")))
        fs = [f for f in fs if not f.endswith(".tmp.jpg")]
        if opt("--pick"):
            want = {int(x) for x in opt("--pick").split(",")}
            fs = [f for f in fs if int(os.path.basename(f)[1:5]) in want]
        elif len(fs) > 8:
            fs = [fs[round(i * (len(fs) - 1) / 7)] for i in range(8)]
        if not fs:
            sys.exit(f"no frames in {d}")
        rows.append(fs)
    sizes = []
    for fs in rows:                                       # each row keeps its own aspect ratio (mixed formats)
        W0, H0 = Image.open(fs[0]).size
        k = tile / max(W0, H0); sizes.append((round(W0 * k), round(H0 * k)))
    lab_h = 26
    cols = max(len(r) for r in rows)
    sheet = Image.new("RGB", (max(tw * len(r) for (tw, _), r in zip(sizes, rows)), sum(th + lab_h for _, th in sizes)), (24, 24, 28))
    g = ImageDraw.Draw(sheet)
    y = 0
    for ri, fs in enumerate(rows):
        tw, th = sizes[ri]
        if ri:
            y += sizes[ri - 1][1] + lab_h
        g.text((8, y + 6), f"{labels[ri] if ri < len(labels) else ''}", fill=(255, 255, 255))
        for ci, f in enumerate(fs):
            im = Image.open(f).convert("RGB").resize((tw, th), Image.LANCZOS)
            d = ImageDraw.Draw(im)
            if safe in SAFE and abs(tw / th - FORMATS[safe][0] / FORMATS[safe][1]) < 0.02:   # only on rows of that format
                s = tw / FORMATS[safe][0]
                t_, b_, l_, r_ = (v * s for v in SAFE[safe])
                d.rectangle([l_, t_, tw - r_, th - b_], outline=(255, 60, 60), width=1)
            d.text((5, 4), os.path.basename(f)[1:5], fill=(255, 255, 255))
            sheet.paste(im, (ci * tw, y + lab_h))
    sheet.save(out, quality=90)
    print(out, f"{len(rows)} row(s) x {cols}")


if __name__ == "__main__":
    main()
