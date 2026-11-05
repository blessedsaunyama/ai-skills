"""Find the user's uploads, describe them, and copy them into a work folder.

    python assets.py scan [PROJECT_DIR]                 -> lists logos/, photos/, reference/ (+ loose files)
    python assets.py copy PROJECT_DIR WORK_DIR          -> copies everything to WORK_DIR/assets (originals untouched)
    python assets.py palette IMAGE [IMAGE...]           -> main colours (for brand colours / reference mood)

Logos: PNG with transparency is best. Photos: real photos only (no AI people).
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageOps

IMG = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".gif"}
OTHER = {".psd", ".svg", ".pdf"}
FOLDERS = ("logos", "photos", "reference")


def describe(p):
    d = {"file": str(p), "name": p.name, "kind": p.suffix.lower().lstrip(".")}
    if p.suffix.lower() in IMG:
        try:
            im = ImageOps.exif_transpose(Image.open(p))
            d["size"] = f"{im.width}x{im.height}"
            has_a = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
            transparent = False
            if has_a:
                a = im.convert("RGBA").getchannel("A")
                transparent = a.getextrema()[0] < 250
            d["transparent"] = transparent
            mp = im.width * im.height / 1e6
            d["print_A4_ok"] = im.width >= 1200 or im.height >= 1200
            notes = []
            if not transparent and "logo" in str(p).lower():
                notes.append("logo has a solid background: will sit on a white chip unless cut out")
            is_logo = "logo" in str(p).lower()
            if (is_logo and max(im.size) < 400) or (not is_logo and mp < 0.8):
                notes.append("small image: fine for social, soft in print")
            d["notes"] = notes
        except Exception as e:
            d["error"] = str(e)
    return d


def guess_role(p):
    n = p.name.lower()
    if "logo" in n or "icon" in n or "emblem" in n:
        return "logos"
    if "ref" in n or "inspo" in n or "example" in n:
        return "reference"
    return "photos"


def scan(root):
    root = Path(root)
    out = {f: [] for f in FOLDERS}
    out["loose"] = []
    for f in FOLDERS:
        d = root / f
        if d.is_dir():
            for p in sorted(d.iterdir()):
                if p.suffix.lower() in IMG | OTHER:
                    out[f].append(describe(p))
    for p in sorted(root.iterdir()) if root.is_dir() else []:
        if p.is_file() and p.suffix.lower() in IMG | OTHER:
            d = describe(p)
            d["guess"] = guess_role(p)
            out["loose"].append(d)
    return out


def copy(root, work):
    root, work = Path(root), Path(work) / "assets"
    for f in FOLDERS:
        (work / f).mkdir(parents=True, exist_ok=True)
    res = scan(root)
    copied = []
    for f in FOLDERS:
        for d in res[f]:
            dst = work / f / d["name"]
            shutil.copy2(d["file"], dst)
            copied.append(str(dst))
    for d in res["loose"]:
        dst = work / d["guess"] / d["name"]
        shutil.copy2(d["file"], dst)
        copied.append(str(dst))
    return copied


def palette(paths, n=5):
    cols = {}
    for p in paths:
        im = Image.open(p).convert("RGBA")
        im.thumbnail((200, 200))
        raw = im.tobytes()
        px = [tuple(raw[i:i + 3]) for i in range(0, len(raw), 4) if raw[i + 3] > 128]
        if not px:
            continue
        q = Image.new("RGB", (len(px), 1))
        q.putdata(px)
        q = q.quantize(colors=n + 3, method=Image.Quantize.MEDIANCUT)
        pal = q.getpalette()
        for count, idx in sorted(q.getcolors(), reverse=True):
            r, g, b = pal[idx * 3: idx * 3 + 3]
            if max(r, g, b) > 245 and min(r, g, b) > 235:
                continue  # skip near-white backgrounds
            near = next((k for k in cols if sum(abs(a - b2) for a, b2 in zip(bytes.fromhex(k[1:]), (r, g, b))) < 60), None)
            key = near or "#%02X%02X%02X" % (r, g, b)
            cols[key] = cols.get(key, 0) + count
    return [c for c, _ in sorted(cols.items(), key=lambda kv: -kv[1])[:n]]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    cmd = sys.argv[1]
    if cmd == "scan":
        print(json.dumps(scan(sys.argv[2] if len(sys.argv) > 2 else "."), indent=2))
    elif cmd == "copy":
        print("\n".join(copy(sys.argv[2], sys.argv[3])))
    elif cmd == "palette":
        print(" ".join(palette(sys.argv[2:])))
    else:
        print(__doc__)
