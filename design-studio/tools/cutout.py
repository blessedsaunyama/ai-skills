"""Remove a photo's background (offline, free) with rembg. Always writes a NEW file.

    python cutout.py photos/speaker.jpg --out work/speaker-cutout.png [--kind person|object] [--crop x0,y0,x1,y1]

--kind person (default) uses the u2net_human_seg model (best for people).
--crop (fractions 0-1) crops first, e.g. 0.25,0,0.75,1 to keep just the middle person.
First use downloads the model (~170 MB) into the user home folder (~/.rembg or ~/.u2net).
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

MODELS = {"person": "u2net_human_seg", "object": "isnet-general-use"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--out", required=True)
    ap.add_argument("--kind", default="person", choices=list(MODELS))
    ap.add_argument("--crop")
    ap.add_argument("--max", type=int, default=2600, help="longest side to process (speed / memory)")
    a = ap.parse_args()
    try:
        from rembg import new_session, remove
    except ImportError:
        sys.exit("rembg is not installed. Ask the user, then: python3 -m pip install \"rembg[cpu]\"")
    src, out = Path(a.image), Path(a.out)
    if src.resolve() == out.resolve():
        sys.exit("Refusing to overwrite the original photo: choose another --out")
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    if a.crop:
        x0, y0, x1, y1 = (float(v) for v in a.crop.split(","))
        im = im.crop((int(x0 * im.width), int(y0 * im.height), int(x1 * im.width), int(y1 * im.height)))
    im.thumbnail((a.max, a.max))
    res = remove(im, session=new_session(MODELS[a.kind]), post_process_mask=True)
    alpha = res.getchannel("A").filter(ImageFilter.GaussianBlur(0.8))
    res.putalpha(alpha)
    bb = alpha.point(lambda v: 255 if v > 12 else 0).getbbox()
    if bb:
        res = res.crop(bb)
    out.parent.mkdir(parents=True, exist_ok=True)
    res.save(out)
    cover = sum(alpha.histogram()[128:]) / (alpha.width * alpha.height)
    print(f"OK {out}  {res.width}x{res.height}  subject covers {cover:.0%} of the frame")
    if cover < 0.05:
        print("WARNING: very little was kept - check the result or try --kind object")


if __name__ == "__main__":
    main()
