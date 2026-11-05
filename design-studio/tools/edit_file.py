"""Edit an EXISTING design file (SVG, AI, PDF, EPS, CDR...) on a copy: change text, colours, images.

    python edit_file.py open  FILE --work DIR [--page 1]   -> copies/converts to DIR/<name>.svg and lists what is editable
    python edit_file.py list  DIR/<name>.svg                -> texts, colours, images, fonts (with ids)
    python edit_file.py edit  DIR/<name>.svg [ops...] --out DIR/<name>-v2.svg
          --text ID "new text"          replace one text (use \\n for line breaks over its lines)
          --replace "old" "new"         find/replace in every text
          --color "#old" "#new"         swap a colour everywhere (fill, stroke, gradients, CSS)
          --image ID path.png           put another picture in an image's box (cropped to fill)
          --hide ID / --show ID         hide or show any element
    python edit_file.py export DIR/<name>-v2.svg --formats png,pdf [--dpi 150] [--renderer inkscape]

AI/PDF/EPS/CDR are converted to SVG with Inkscape (needs Inkscape; EPS also needs Ghostscript).
Results are SVG/PDF/PNG: it cannot save back as .ai/.cdr/.psd/.indd.
Original files are never changed.
"""
import argparse
import base64
import io
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render  # noqa: E402

SVG = "http://www.w3.org/2000/svg"
XL = "http://www.w3.org/1999/xlink"
for p, u in (("", SVG), ("xlink", XL), ("inkscape", "http://www.inkscape.org/namespaces/inkscape"),
             ("sodipodi", "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd")):
    ET.register_namespace(p, u)
T = lambda tag: f"{{{SVG}}}{tag}"  # noqa: E731
HEX = re.compile(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b")
CONVERT = {".ai", ".pdf", ".eps", ".ps", ".cdr", ".wmf", ".emf", ".vsd", ".svgz"}
UNSUPPORTED = {".indd": "InDesign files can't be read by free tools: export IDML or PDF from InDesign.",
               ".psd": "Use tools/psd_import.py for PSD files.",
               ".afdesign": "Affinity files are closed: export SVG or PDF from Affinity.",
               ".fig": "Figma files: export SVG or PDF from Figma.",
               ".xcf": "GIMP files need GIMP: export PNG/PSD from GIMP."}


def norm_hex(h):
    h = h.upper()
    return "#" + "".join(c * 2 for c in h[1:]) if len(h) == 4 else h


# ---------------------------------------------------------------- open / convert
def cmd_open(a):
    src = Path(a.file).resolve()
    ext = src.suffix.lower()
    if ext in UNSUPPORTED:
        sys.exit(UNSUPPORTED[ext])
    work = Path(a.work).resolve()
    work.mkdir(parents=True, exist_ok=True)
    dst = work / (src.stem + ".svg")
    if dst.resolve() == src:
        sys.exit("Work folder must be different from the original's folder name")
    if ext == ".svg":
        shutil.copy2(src, dst)
    elif ext in CONVERT:
        ink = render.find_inkscape()
        if not ink:
            sys.exit("Opening " + ext + " needs Inkscape. Ask the user to install it (inkscape.org or: winget install Inkscape.Inkscape).")
        args = [ink, str(src), "--export-type=svg", "--export-plain-svg", f"--export-filename={dst}"]
        if ext in (".pdf", ".ai"):
            # keep = text stays editable with its real font names (even if the font isn't installed)
            args[2:2] = [f"--pages={a.page}", "--pdf-font-strategy=keep"]
        p = subprocess.run(args, capture_output=True, text=True)
        if p.returncode or not dst.exists():
            msg = p.stderr[-800:]
            if ext in (".eps", ".ps"):
                msg += "\nEPS/PS import needs Ghostscript (ask the user before installing)."
            if ext == ".ai":
                msg += "\nThis .ai may have been saved without 'PDF compatible' - ask for a PDF or SVG export."
            sys.exit("Inkscape could not convert the file:\n" + msg)
    else:
        sys.exit(f"Unknown file type {ext}")
    tree = ET.parse(dst)
    add_ids(tree)
    tree.write(dst, encoding="utf-8", xml_declaration=True)
    print(f"Working copy: {dst}  (original untouched: {src})")
    print_list(dst)


def add_ids(tree):
    n = {"t": 0, "i": 0}
    for el in tree.iter():
        if el.tag in (T("text"), T("image")) and not el.get("id"):
            k = "t" if el.tag == T("text") else "i"
            n[k] += 1
            el.set("id", f"ds-{k}{n[k]}")


# ---------------------------------------------------------------- list
def text_of(el):
    tspans = [t for t in el.iter(T("tspan")) if (t.text or "").strip()]
    if tspans:
        return " / ".join(t.text.strip() for t in tspans)
    return "".join(el.itertext()).strip()


def style_get(el, key):
    m = re.search(rf"(?:^|;)\s*{key}\s*:\s*([^;]+)", el.get("style", ""))
    return (m.group(1).strip() if m else None) or el.get(key)


def inventory(path):
    tree = ET.parse(path)
    root = tree.getroot()
    texts, images, colours, fonts = [], [], {}, {}
    paths = 0
    masked = {id(e) for m in root.iter() if m.tag in (T("mask"), T("pattern")) for e in m.iter()}
    for el in root.iter():
        if el.tag == T("text"):
            fam = style_get(el, "font-family") or next((style_get(t, "font-family") for t in el.iter(T("tspan")) if style_get(t, "font-family")), None)
            size = style_get(el, "font-size") or next((style_get(t, "font-size") for t in el.iter(T("tspan")) if style_get(t, "font-size")), None)
            texts.append({"id": el.get("id"), "text": text_of(el), "font": fam, "size": size, "fill": style_get(el, "fill")})
            if fam:
                fonts[fam.strip("'\" ")] = fonts.get(fam.strip("'\" "), 0) + 1
        elif el.tag == T("image") and id(el) not in masked:
            href = el.get(f"{{{XL}}}href") or el.get("href") or ""
            images.append({"id": el.get("id"), "box": [el.get(k) for k in ("x", "y", "width", "height")],
                           "source": "embedded" if href.startswith("data:") else href[:80]})
        elif el.tag == T("path"):
            paths += 1
        for attr in ("fill", "stroke", "stop-color", "style", "flood-color"):
            for h in HEX.findall(el.get(attr, "") or ""):
                colours[norm_hex(h)] = colours.get(norm_hex(h), 0) + 1
        if el.tag == T("style") and el.text:
            for h in HEX.findall(el.text):
                colours[norm_hex(h)] = colours.get(norm_hex(h), 0) + 1
    return {"texts": texts, "images": images, "colours": dict(sorted(colours.items(), key=lambda kv: -kv[1])),
            "fonts": fonts, "paths": paths, "size": [root.get("width"), root.get("height"), root.get("viewBox")]}


def print_list(path):
    inv = inventory(path)
    print(f"\nSize: width={inv['size'][0]} height={inv['size'][1]} viewBox={inv['size'][2]}")
    print(f"\nTEXTS ({len(inv['texts'])}):")
    for t in inv["texts"]:
        print(f"  {t['id']:>12}  \"{t['text'][:70]}\"   [{t['font'] or '?'} {t['size'] or ''} {t['fill'] or ''}]")
    if not inv["texts"]:
        print("  none as live text" + (f" - {inv['paths']} shapes: text may be outlined (can recolour, not retype)" if inv["paths"] else ""))
    print(f"\nIMAGES ({len(inv['images'])}):")
    for i in inv["images"]:
        print(f"  {i['id']:>12}  box={i['box']}  {i['source']}")
    print(f"\nCOLOURS (most used first): {' '.join(list(inv['colours'])[:16])}")
    if inv["fonts"]:
        print(f"\nFONTS used: {', '.join(inv['fonts'])}")
        missing = [f for f in inv["fonts"] if not font_available(f, path)]
        local = [f for f in inv["fonts"] if not system_font(f) and font_files(f, path)]
        if local:
            print(f"  Not installed but font files found (export will use them via Chromium): {', '.join(local)}")
        if missing:
            print(f"  NOT FOUND on this computer: {', '.join(missing)} - renders will use a substitute font."
                  " Ask the user for the font file (or pick a bundled OFL font).")


SYS_FONT_DIRS = [Path("C:/Windows/Fonts"), Path.home() / "AppData/Local/Microsoft/Windows/Fonts", Path("/usr/share/fonts"),
                 Path.home() / ".fonts", Path.home() / ".local/share/fonts", Path("/Library/Fonts"), Path.home() / "Library/Fonts"]
GENERIC = {"sans-serif", "serif", "monospace", "cursive", "fantasy", "sans"}


def _key(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def system_font(fam):
    """True if the font is installed on this computer (what Inkscape / cairosvg can use)."""
    k = _key(fam)
    if k in GENERIC:
        return True
    for d in SYS_FONT_DIRS:
        if d.exists():
            for f in d.rglob("*"):
                if f.suffix.lower() in (".ttf", ".otf", ".ttc") and _key(f.stem).startswith(k[:12]):
                    return True
    return False


WEIGHTS = [("extrabold", 800), ("semibold", 600), ("black", 900), ("bold", 700), ("medium", 500),
           ("light", 300), ("thin", 100), ("regular", 400)]


def _weight(stem):
    k = _key(stem)
    return next((w for name, w in WEIGHTS if k.endswith(name)), 400)


def font_files(fam, svg_path):
    """Font files we can point Chromium at: bundled OFL fonts, or font files next to the design.
    Understands family names ('Poppins') and PDF/PostScript names ('ABCDEF+Poppins-SemiBold')."""
    import textpath
    fam = fam.split("+", 1)[-1]
    key = _key(fam)
    files = list(textpath.FONT_DIR.glob("*.ttf"))
    for d in (Path(svg_path).parent / "fonts", Path(svg_path).parent):
        if d.is_dir():
            files += list(d.glob("*.[ot]tf"))
    exact = [f for f in files if _key(f.stem) == key]
    if exact:  # a specific style was named: one file, use it for every weight
        return [(None, exact[0])]
    return [(_weight(f.stem), f) for f in files if _key(f.stem).startswith(key)]


def font_available(fam, svg_path="."):
    return system_font(fam) or bool(font_files(fam, svg_path))


# ---------------------------------------------------------------- edit
def find_id(root, i):
    for el in root.iter():
        if el.get("id") == i:
            return el
    sys.exit(f"No element with id '{i}'. Run: edit_file.py list <svg>")


def set_text(el, new):
    lines = new.split("\\n") if "\\n" in new else new.split("\n")
    tspans = [t for t in el.iter(T("tspan")) if t.text is not None or len(t) == 0]
    tspans = [t for t in tspans if not any(c.tag == T("tspan") for c in t)]
    if not tspans:
        for c in list(el):
            el.remove(c)
        el.text = lines[0]
        for extra in lines[1:]:
            el.text += " " + extra
        return
    for i, t in enumerate(tspans):
        t.text = lines[i] if i < len(lines) else ""
    if len(lines) > len(tspans):
        tspans[-1].text = " ".join(lines[len(tspans) - 1:])


def swap_colour(root, old, new):
    full = norm_hex(old)
    forms = {full}
    if full[1] == full[2] and full[3] == full[4] and full[5] == full[6]:
        forms.add("#" + full[1] + full[3] + full[5])  # short form, e.g. #FFF
    pat = re.compile("(" + "|".join(re.escape(f) for f in forms) + r")(?![0-9a-fA-F])", re.I)
    n = 0
    for el in root.iter():
        for attr in ("fill", "stroke", "stop-color", "style", "flood-color", "color"):
            v = el.get(attr)
            if v and pat.search(v):
                el.set(attr, pat.sub(new, v))
                n += 1
        if el.tag == T("style") and el.text and pat.search(el.text):
            el.text = pat.sub(new, el.text)
            n += 1
    return n


def swap_image(el, pic):
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(pic))
    w, h = float(el.get("width", im.width)), float(el.get("height", im.height))
    old = el.get(f"{{{XL}}}href") or el.get("href") or ""
    if old.startswith("data:") and (w <= 2 or h <= 2):  # PDF imports: 1x1 box + transform -> keep old picture's shape
        try:
            o = Image.open(io.BytesIO(base64.b64decode(old.split(",", 1)[1])))
            w, h = o.width, o.height
        except Exception:
            pass
    r = max(w / im.width, h / im.height)
    cw, ch = w / r, h / r
    x0, y0 = (im.width - cw) / 2, (im.height - ch) * 0.3
    im = im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch)))
    if im.width > 2400:
        im = im.resize((2400, int(2400 * im.height / im.width)))
    buf = io.BytesIO()
    if im.mode in ("RGBA", "LA", "P"):
        im.convert("RGBA").save(buf, "PNG")
        mime = "png"
    else:
        im.convert("RGB").save(buf, "JPEG", quality=90)
        mime = "jpeg"
    uri = f"data:image/{mime};base64," + base64.b64encode(buf.getvalue()).decode()
    el.set(f"{{{XL}}}href", uri)
    if "href" in el.attrib:
        el.set("href", uri)
    el.set("preserveAspectRatio", "none")


def cmd_edit(a):
    src, out = Path(a.svg), Path(a.out)
    if out.resolve() == src.resolve():
        sys.exit("Use a new --out file (keep the previous version)")
    tree = ET.parse(src)
    root = tree.getroot()
    log = []
    for i, new in a.text or []:
        set_text(find_id(root, i), new)
        log.append(f"text {i} -> {new}")
    for old, new in a.replace or []:
        n = 0
        for el in root.iter():
            for part in ("text", "tail"):
                v = getattr(el, part)
                if v and old in v and el.tag in (T("text"), T("tspan"), T("textPath")):
                    setattr(el, part, v.replace(old, new))
                    n += 1
        log.append(f"replace '{old}' -> '{new}': {n} place(s)")
    for old, new in a.color or []:
        log.append(f"colour {old} -> {new}: {swap_colour(root, old, new)} place(s)")
    for i, pic in a.image or []:
        swap_image(find_id(root, i), pic)
        log.append(f"image {i} <- {pic}")
    for i in a.hide or []:
        find_id(root, i).set("display", "none")
        log.append(f"hide {i}")
    for i in a.show or []:
        el = find_id(root, i)
        el.attrib.pop("display", None)
        el.set("style", re.sub(r"display\s*:\s*none;?", "", el.get("style", "")))
        log.append(f"show {i}")
    out.parent.mkdir(parents=True, exist_ok=True)
    tree.write(out, encoding="utf-8", xml_declaration=True)
    print("\n".join(log) or "no changes given")
    print(f"Saved {out}")
    zero = [l for l in log if l.endswith(": 0 place(s)")]
    if zero:
        print("WARNING nothing matched for: " + "; ".join(zero))


# ---------------------------------------------------------------- export
UNIT = {"px": 1, "": 1, "pt": 96 / 72, "pc": 16, "mm": 96 / 25.4, "cm": 96 / 2.54, "in": 96}


def size_px(root):
    def val(s):
        m = re.match(r"([\d.]+)\s*([a-z%]*)", s or "")
        if not m or m.group(2) == "%":
            return None
        return float(m.group(1)) * UNIT.get(m.group(2), 1)
    w, h = val(root.get("width")), val(root.get("height"))
    if not (w and h) and root.get("viewBox"):
        vb = [float(x) for x in re.split(r"[ ,]+", root.get("viewBox").strip())]
        w, h = vb[2], vb[3]
    return w, h


def cmd_export(a):
    svg = Path(a.svg).resolve()
    txt = svg.read_text(encoding="utf-8")
    root = ET.fromstring(txt.encode("utf-8"))
    w, h = size_px(root)
    fams = inventory(svg)["fonts"]
    need = [f for f in fams if not system_font(f)]
    css = ""
    for f in need:
        for wt, fp in font_files(f, svg):
            w_css = f"font-weight:{wt};" if wt else "font-weight:100 900;"
            css += f"@font-face{{font-family:'{f}';{w_css}src:url('{fp.resolve().as_uri()}')}}"
    unresolved = [f for f in need if not font_files(f, svg)]
    if unresolved:
        print(f"WARNING fonts not found anywhere: {', '.join(unresolved)} - a substitute font will be used")
    # Fonts not installed -> only Chromium can load font files. Otherwise Inkscape renders live text best
    # (cairosvg ignores kerning and letter-spacing).
    renderer = a.renderer or ("chromium" if css else ("inkscape" if render.find_inkscape() else "chromium"))
    if css and renderer != "chromium":
        print(f"WARNING {renderer} can't use font files that aren't installed: {', '.join(need)} will be substituted")
    m = re.search(r"<svg\b[^>]*>", txt)
    if css:
        txt = txt[:m.end()] + f"<style>{css}</style>" + txt[m.end():]
    jobs, tmps = [], []
    fm = set(a.formats.split(","))
    if "png" in fm:
        sc = a.dpi / 96
        pw, ph = round(w * sc), round(h * sc)
        m = re.search(r"<svg\b[^>]*>", txt)
        tag = re.sub(r'\s(width|height)="[^"]*"', "", m.group(0))
        if "viewBox" not in tag:
            tag = tag.replace("<svg", f'<svg viewBox="0 0 {w} {h}"', 1)
        tag = tag.replace("<svg", f'<svg width="{pw}" height="{ph}"', 1)
        tmp = svg.with_name("_" + svg.stem + ".png.svg")
        tmp.write_text(txt[:m.start()] + tag + txt[m.end():], encoding="utf-8")
        tmps.append(tmp)
        jobs.append({"svg": str(tmp), "out": str(svg.with_suffix(".png")), "type": "png", "w": pw, "h": ph})
    if "pdf" in fm:
        tmp = svg.with_name("_" + svg.stem + ".pdf.svg")
        tmp.write_text(txt, encoding="utf-8")
        tmps.append(tmp)
        jobs.append({"svg": str(tmp), "out": str(svg.with_suffix(".pdf")), "type": "pdf", "w": round(w * 25.4 / 96, 3), "h": round(h * 25.4 / 96, 3)})
    try:
        used = render.run(jobs, renderer)
    finally:
        for t in tmps:
            t.unlink(missing_ok=True)
    for j in jobs:
        print(f"OK {j['out']}")
    print(f"renderer: {used}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("open")
    o.add_argument("file")
    o.add_argument("--work", required=True)
    o.add_argument("--page", type=int, default=1)
    li = sub.add_parser("list")
    li.add_argument("svg")
    e = sub.add_parser("edit")
    e.add_argument("svg")
    e.add_argument("--out", required=True)
    e.add_argument("--text", nargs=2, action="append", metavar=("ID", "TEXT"))
    e.add_argument("--replace", nargs=2, action="append", metavar=("OLD", "NEW"))
    e.add_argument("--color", nargs=2, action="append", metavar=("OLD", "NEW"))
    e.add_argument("--image", nargs=2, action="append", metavar=("ID", "FILE"))
    e.add_argument("--hide", action="append")
    e.add_argument("--show", action="append")
    x = sub.add_parser("export")
    x.add_argument("svg")
    x.add_argument("--formats", default="png,pdf")
    x.add_argument("--dpi", type=float, default=150)
    x.add_argument("--renderer")
    a = ap.parse_args()
    {"open": cmd_open, "list": lambda a: print_list(a.svg), "edit": cmd_edit, "export": cmd_export}[a.cmd](a)


if __name__ == "__main__":
    main()
