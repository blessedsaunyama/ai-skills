"""Build a design from a spec: variations -> SVG (outlined + editable) -> PNG / PDF / JPG.

    python make.py spec.json --out OUTDIR [--variations 3] [--only 2] [--formats png,pdf,svg,jpg]
                             [--renderer inkscape|cairosvg|chromium]

Paths inside the spec (logos, photos) are relative to the spec file.
Prints a JSON summary (files, warnings) at the end.
"""
import argparse
import copy
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compose  # noqa: E402
import render  # noqa: E402
import styles  # noqa: E402
import textpath as tp  # noqa: E402
import validate  # noqa: E402


def variants(spec, n):
    """v1 = the spec as written; the others change layout / side / palette."""
    t = spec.get("type", "event")
    flip = {"right": "left", "left": "right"}
    side = spec.get("photo_side", "right")
    out = [{}]
    if t in ("event", "flyer", "poster", "social", "banner"):
        cur = spec.get("layout", "split")
        others = [l for l in ("split", "hero", "bold") if l != cur]
        out += [{"layout": others[0], "photo_side": flip[side]}, {"layout": others[1]}]
    elif t == "thumbnail":
        alt = "warm" if spec.get("palette") != "warm" else "tech"
        out += [{"photo_side": flip[side]}, {"palette": alt, "highlight_line": 0}]
    elif t == "certificate":
        out += [{"palette": "royal"}, {"style": "elegant", "palette": "elegant"}]
    else:
        out += [{"palette": "warm"}, {"palette": "fresh"}]
    return out[:max(1, n)]


def font_css(fonts):
    rules = []
    for fam, wt in sorted(fonts):
        f = tp.FAMILIES[fam][wt]
        rules.append(f"@font-face{{font-family:'{fam}';font-weight:{wt};src:url('fonts/{f}')}}")
    return "".join(rules)


def build_one(spec, base, out, name, formats, prefer):
    c = compose.compose(spec, base)
    cv, size = c.cv, c.size
    files, jobs = [], []
    out.mkdir(parents=True, exist_ok=True)
    # screen-size PNG (print designs get a share copy at 150 dpi)
    if c.print:
        f = min(1.0, 150 / size["dpi"])
        pw, ph = round(c.W * f), round(c.H * f)
    else:
        pw, ph = c.W, c.H
    png_svg = out / f"_{name}.render.svg"
    png_svg.write_text(cv.svg("outlined", "trim", pw, ph), encoding="utf-8")
    png = out / f"{name}.png"
    jobs.append({"svg": str(png_svg), "out": str(png), "type": "png", "w": pw, "h": ph})
    if "svg" in formats:
        p = out / f"{name}.svg"
        p.write_text(cv.svg("outlined", "bleed" if c.print else "trim"), encoding="utf-8")
        files.append(p)
        e = out / f"{name}-editable.svg"
        e.write_text(cv.svg("live", "bleed" if c.print else "trim", font_css=font_css(cv.fonts)), encoding="utf-8")
        files.append(e)
        fd = out / "fonts"
        fd.mkdir(exist_ok=True)
        for fam, wt in cv.fonts:
            shutil.copy2(tp.FONT_DIR / tp.FAMILIES[fam][wt], fd)
    pdf_svg = None
    if "pdf" in formats:
        pr = spec.get("print", {})
        view = "marks" if (c.print and pr.get("crop_marks")) else ("bleed" if c.print and pr.get("bleed_mm", 3) else "trim")
        pdf_svg = out / f"_{name}.pdf.svg"
        pdf_svg.write_text(cv.svg("outlined", view), encoding="utf-8")
        off = {"trim": 0, "bleed": cv.bleed, "marks": cv.bleed + cv.mark}[view]
        if c.print:
            mw, mh = (c.W + 2 * off) / c.ppmm, (c.H + 2 * off) / c.ppmm
        else:
            mw, mh = c.W / 96 * 25.4, c.H / 96 * 25.4
        pdf = out / f"{name}.pdf"
        jobs.append({"svg": str(pdf_svg), "out": str(pdf), "type": "pdf", "w": round(mw, 3), "h": round(mh, 3)})
    used = render.run(jobs, prefer)
    png_svg.unlink()
    if pdf_svg:
        pdf_svg.unlink()
        files.append(out / f"{name}.pdf")
    files.insert(0, png)
    if "jpg" in formats or spec.get("type") == "thumbnail":
        jpg = out / f"{name}.jpg"
        q = render.to_jpg(png, jpg, max_bytes=2_000_000 if spec.get("type") == "thumbnail" else None)
        files.append(jpg)
    return files, sorted(set(cv.warn)), used, c


def contact_sheet(pngs, out):
    from PIL import Image, ImageDraw
    ims = [Image.open(p).convert("RGB") for p in pngs]
    th = 900
    ims = [im.resize((round(im.width * th / im.height), th)) for im in ims]
    gap = 30
    W = sum(i.width for i in ims) + gap * (len(ims) + 1)
    sheet = Image.new("RGB", (W, th + 2 * gap + 50), "#E9E9EE")
    d = ImageDraw.Draw(sheet)
    x = gap
    for n, im in enumerate(ims, 1):
        sheet.paste(im, (x, gap))
        d.text((x, th + gap + 12), f"Variation {n}", fill="#222")
        x += im.width + gap
    sheet.save(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out", required=True)
    ap.add_argument("--variations", type=int, default=1)
    ap.add_argument("--only", type=int, help="build just this variation number")
    ap.add_argument("--formats", default=None, help="png,pdf,svg,jpg (default: png+svg, plus pdf for print)")
    ap.add_argument("--renderer")
    a = ap.parse_args()
    sp = Path(a.spec).resolve()
    spec = json.loads(sp.read_text(encoding="utf-8"))
    if spec.get("brand"):  # saved brand fills only what the spec leaves out
        import brands
        b = brands.load(spec["brand"])
        for k in ("palette", "host_line", "style", "logos", "contacts", "fonts"):
            if k in b and k not in spec:
                spec[k] = b[k]
    probs = validate.check_spec(spec)
    bad = [p for p in probs if "WARNING" not in p]
    if bad:
        print("Fix these contact details first:\n  " + "\n  ".join(bad))
        sys.exit(1)
    import sizes
    sz = spec.get("size", "a4")
    kind = "screen" if isinstance(sz, dict) and sz.get("unit", "px") == "px" else (sizes.get(sz)["kind"] if not isinstance(sz, dict) else "print")
    formats = set((a.formats or ("png,svg,pdf" if kind == "print" else "png,svg")).split(","))
    out = Path(a.out).resolve()
    name = spec.get("name", sp.stem)
    vs = variants(spec, a.variations)
    summary = {"design": name, "size": None, "renderer": None, "variations": [], "warnings": probs}
    pngs, fonts_used = [], set()
    for i, v in enumerate(vs, 1):
        if a.only and i != a.only:
            continue
        s2 = copy.deepcopy(spec)
        s2.update(v)
        nm = f"{name}-v{i}" if len(vs) > 1 else name
        files, warns, used, c = build_one(s2, sp.parent, out, nm, formats, a.renderer)
        summary["size"] = f'{c.size["label"]} - {c.W} x {c.H} px' + (f' @ {c.size["dpi"]} dpi' if c.print else "")
        summary["renderer"] = used
        summary["variations"].append({"n": i, "changes": v, "files": [str(f) for f in files], "warnings": warns})
        pngs.append(files[0])
        fonts_used |= {f for f, _ in c.cv.fonts}
    if len(pngs) > 1:
        summary["sheet"] = str(contact_sheet(pngs, out / f"{name}-variations.png"))
    credits = spec.get("credits", [])
    lines = [f"Design: {name}", "", "Fonts (SIL Open Font License 1.1 - free to use, also commercially):"]
    lines += [f"  - {f}" for f in sorted(fonts_used)]
    lines += ["", "Images:"] + ([f"  - {c_}" for c_ in credits] or ["  - only the user's own uploads"])
    (out / "CREDITS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
