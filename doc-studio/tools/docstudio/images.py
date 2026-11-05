"""Images: SVG -> PNG, image size limits and the user's images/captions.csv."""
import csv, hashlib
from pathlib import Path

MAX_PX = 2000  # big phone photos are shrunk so documents stay small


def _hide_broken_cairocffi():
    """rlPyCairo prefers cairocffi; if cairocffi is installed but its cairo DLL is missing it raises OSError
    (not ImportError) and never falls back to pycairo. Hide it so pycairo is used."""
    import sys
    try:
        import cairocffi  # noqa: F401
    except ImportError:
        pass
    except OSError:
        sys.modules["cairocffi"] = None


def svg_to_png(svg, out_dir, width_px=1600):
    _hide_broken_cairocffi()
    try:
        from reportlab.graphics import renderPM
        from svglib.svglib import svg2rlg
    except ImportError:
        raise SystemExit("SVG needs svglib + rlPyCairo (python tools/setup_check.py shows the install command)")
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    h = hashlib.md5(Path(svg).read_bytes()).hexdigest()[:8]
    out = out_dir / f"{Path(svg).stem}_{h}.png"
    if out.exists():
        return str(out)
    d = svg2rlg(str(svg))
    if d is None:
        raise SystemExit(f"could not read SVG: {svg}")
    dpi = max(72, min(600, 72 * width_px / max(1, d.width)))
    renderPM.drawToFile(d, str(out), fmt="PNG", dpi=dpi, bg=0xFFFFFF)
    return str(out)


def shrink(path, out_dir):
    from PIL import Image, ImageOps
    im = Image.open(path)
    if max(im.size) <= MAX_PX and im.format in ("PNG", "JPEG"):
        return str(path)
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    im = ImageOps.exif_transpose(im)
    im.thumbnail((MAX_PX, MAX_PX))
    keep_alpha = im.mode in ("RGBA", "LA", "P")
    out = out_dir / (Path(path).stem + (".png" if keep_alpha else ".jpg"))
    if keep_alpha:
        im.save(out)
    else:
        im.convert("RGB").save(out, quality=88)
    return str(out)


def read_captions(folder):
    """images/captions.csv columns: file,caption,credit,licence,source,own (own = yes for the user's own photo or AI-drawn art)."""
    p = Path(folder) / "captions.csv"
    if not p.exists():
        return {}
    with open(p, newline="", encoding="utf-8-sig") as f:
        return {r["file"].strip(): {k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f) if r.get("file")}
