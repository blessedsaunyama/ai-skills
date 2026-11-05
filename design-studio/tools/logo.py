"""Original, simple SVG logos: 3 concepts, each in colour / mono / reversed / icon-only.

    python logo.py --name "Arcetel Solutions" --initials AS --tagline "Software that works"
                   --colors "#0B5FFF,#FFB400" --out OUTDIR [--style modern|youthful|formal|elegant]

Concepts: 1 monogram (initials in a shape), 2 spark (abstract symbol), 3 wordmark + accent.
Built only from basic geometry + OFL fonts; review references/logos.md before showing.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render  # noqa: E402
import styles  # noqa: E402
import textpath as tp  # noqa: E402

FONTS = {"modern": ("Montserrat", 800, "Montserrat", 500), "youthful": ("Poppins", 700, "Poppins", 400),
         "formal": ("Playfair Display", 700, "Lato", 400), "elegant": ("Playfair Display", 400, "Lato", 400)}


def shape_path(kind, cx, cy, r):
    if kind == "circle":
        return f"M{cx - r} {cy}a{r} {r} 0 1 0 {2 * r} 0a{r} {r} 0 1 0 {-2 * r} 0z"
    if kind == "hex":
        pts = [(cx + r * math.cos(math.pi / 6 + i * math.pi / 3), cy + r * math.sin(math.pi / 6 + i * math.pi / 3)) for i in range(6)]
        return "M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in pts) + "z"
    q = r * 0.28  # rounded square
    s = r * 0.9
    return (f"M{cx - s + q} {cy - s}H{cx + s - q}Q{cx + s} {cy - s} {cx + s} {cy - s + q}V{cy + s - q}Q{cx + s} {cy + s} {cx + s - q} {cy + s}"
            f"H{cx - s + q}Q{cx - s} {cy + s} {cx - s} {cy + s - q}V{cy - s + q}Q{cx - s} {cy - s} {cx - s + q} {cy - s}z")


def icon_monogram(ini, c1, c2, fg, fonts, seed):
    kind = ["rsquare", "circle", "hex"][seed % 3]
    d = shape_path(kind, 50, 50, 46)
    fam, wt = fonts[0], fonts[1]
    size = 100
    w = tp.measure(ini, fam, wt, size)
    m = tp.metrics(fam, wt, size)
    size *= min(58 / w, 46 / m["cap"])
    m = tp.metrics(fam, wt, size)
    txt, _ = tp.outline(ini, fam, wt, size, 50, 50 + m["cap"] / 2, "middle")
    bar = f'<path d="M36 {50 + m["cap"] / 2 + 9:.1f} H64" stroke="{c2}" stroke-width="6" stroke-linecap="round"/>'
    return f'<path d="{d}" fill="{c1}"/><path d="{txt}" fill="{fg}"/>{bar}'


def icon_spark(ini, c1, c2, fg, fonts, seed):
    n = 6 + 2 * (seed % 2)
    parts = []
    for i in range(n):
        a = 360 / n * i
        col = c1 if i % 2 == 0 else c2
        parts.append(f'<rect x="44" y="6" width="12" height="40" rx="6" fill="{col}" transform="rotate({a:.1f} 50 50)"/>')
    parts.append(f'<circle cx="50" cy="50" r="9" fill="{c2}"/>')
    return "".join(parts)


def icon_rise(ini, c1, c2, fg, fonts, seed):
    # three stepped rounded bars + an arc: "growth / rising"
    return (f'<rect x="12" y="56" width="18" height="32" rx="5" fill="{c1}"/>'
            f'<rect x="41" y="40" width="18" height="48" rx="5" fill="{c1}"/>'
            f'<rect x="70" y="22" width="18" height="66" rx="5" fill="{c2}"/>'
            f'<path d="M10 40 Q40 6 84 10" stroke="{c2}" stroke-width="6" fill="none" stroke-linecap="round"/>')


CONCEPTS = [("monogram", icon_monogram), ("spark", icon_spark), ("rise", icon_rise)]


def lockup(icon_svg, name, tagline, fonts, name_col, tag_col):
    fam, wt, tfam, twt = fonts
    ns = 46
    nw = tp.measure(name, fam, wt, ns)
    tw = tp.measure(tagline.upper(), tfam, twt, 15, 0.18) if tagline else 0
    tx = 122
    W = tx + max(nw, tw) + 12
    H = 100
    nd, _ = tp.outline(name, fam, wt, ns, tx, 58 if tagline else 66)
    out = f'<g>{icon_svg}</g><path d="{nd}" fill="{name_col}"/>'
    if tagline:
        td, _ = tp.outline(tagline.upper(), tfam, twt, 15, tx + 2, 84, "start", 0.18)
        out += f'<path d="{td}" fill="{tag_col}"/>'
    return out, W, H


def svg_doc(inner, W, H, bg=None):
    b = f'<rect x="-10" y="-10" width="{W + 20}" height="{H + 20}" fill="{bg}"/>' if bg else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-10 -10 {W + 20} {H + 20}" width="{(W + 20) * 4:.0f}" height="{(H + 20) * 4:.0f}">{b}{inner}</svg>\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--initials")
    ap.add_argument("--tagline", default="")
    ap.add_argument("--colors", default="#0B1F3A,#18C3B0")
    ap.add_argument("--style", default="modern", choices=list(FONTS))
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", help="comma list of concepts to build (monogram,spark,rise)")
    a = ap.parse_args()
    cols = [c.strip() for c in a.colors.split(",")]
    c1, c2 = cols[0], (cols[1] if len(cols) > 1 else "#FFB400")
    fonts = FONTS[a.style]
    ini = (a.initials or "".join(w[0] for w in a.name.split()[:2])).upper()
    seed = int(hashlib.md5(a.name.encode()).hexdigest(), 16)
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    dark = c1 if styles.luminance(c1) < 0.25 else "#111827"
    jobs, made = [], []
    only = set(a.only.split(",")) if a.only else None
    for n, (cname, fn) in enumerate(CONCEPTS, 1):
        if only and cname not in only:
            continue
        variants = {
            "color": (fn(ini, c1, c2, "#FFFFFF", fonts, seed), c1, styles.mix(c1, "#888888", 0.4), None),
            "mono": (fn(ini, "#111111", "#111111", "#FFFFFF", fonts, seed), "#111111", "#111111", None),
            "reversed": (fn(ini, "#FFFFFF", c2 if styles.contrast(c2, dark) > 3 else "#FFFFFF", dark, fonts, seed), "#FFFFFF", "#DDDDDD", dark),
        }
        for vname, (ic, ncol, tcol, bg) in variants.items():
            inner, W, H = lockup(ic, a.name, a.tagline, fonts, ncol, tcol)
            p = out / f"logo{n}-{cname}-{vname}.svg"
            p.write_text(svg_doc(inner, W, H, bg), encoding="utf-8")
            jobs.append({"svg": str(p), "out": str(p.with_suffix(".png")), "type": "png", "w": (W + 20) * 4, "h": (H + 20) * 4, "transparent": bg is None})
            made.append(p)
        p = out / f"logo{n}-{cname}-icon.svg"
        p.write_text(svg_doc(variants["color"][0], 100, 100), encoding="utf-8")
        jobs.append({"svg": str(p), "out": str(p.with_suffix(".png")), "type": "png", "w": 480, "h": 480, "transparent": True})
        made.append(p)
    render.run(jobs)
    sheet = make_sheet([Path(j["out"]) for j in jobs], out / "logos-sheet.png")
    print(json.dumps({"files": [str(m) for m in made], "sheet": str(sheet)}, indent=2))


def make_sheet(pngs, out):
    from PIL import Image, ImageDraw
    cols = 4
    cell_w, cell_h = 560, 220
    rows = math.ceil(len(pngs) / cols)
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "#F2F2F5")
    d = ImageDraw.Draw(sheet)
    for i, p in enumerate(pngs):
        im = Image.open(p).convert("RGBA")
        im.thumbnail((cell_w - 40, cell_h - 50))
        x, y = (i % cols) * cell_w, (i // cols) * cell_h
        if "reversed" not in p.name:
            d.rectangle([x + 10, y + 10, x + cell_w - 10, y + cell_h - 10], fill="#FFFFFF")
        sheet.paste(im, (x + (cell_w - im.width) // 2, y + 15), im)
        d.text((x + 14, y + cell_h - 30), p.stem, fill="#333")
    sheet.save(out)
    return out


if __name__ == "__main__":
    main()
