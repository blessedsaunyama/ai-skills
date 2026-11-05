"""Optional power tools: the ArtCraft apps (VectorCraft, PhotoCraft, DesignCraft), used ONLY when installed.
They open AND save back .ai / .eps / .psd / .idml, convert to CMYK, and are fast. Without them the skill
uses edit_file.py (Inkscape) and its own engine. Every command works on a copy; originals are never changed.

    python artcraft.py check                                 -> which ArtCraft apps are installed
    python artcraft.py install-fonts                         -> one time: add the bundled OFL fonts to VectorCraft (ask first)
    python artcraft.py info FILE                             -> texts / layers / stories, colours, fonts, warnings (JSON-ish)
    python artcraft.py edit FILE --out OUT.ext [ops] [--also OUT2.png ...]
          --replace "old" "new"        find/replace text (VectorCraft, DesignCraft)
          --text ID "new text"         set one text object / PSD type layer / IDML story
          --color "#old" "#new"        recolour (VectorCraft: all artwork incl. gradients and images)
          --font "Missing=Bundled"     replace a font family (e.g. "Helvetica=Montserrat")
          --hide ID / --show ID        hide or show an object / layer
          --cmyk                       convert colours to CMYK (VectorCraft / PhotoCraft)
    python artcraft.py cmyk IN.pdf --out OUT.pdf            -> CMYK copy of a print PDF (for print shops)

App per file type: .ai .eps .pdf .svg .afdesign .cdr-like vectors -> VectorCraft; .psd .psb .tif photos -> PhotoCraft;
.idml .designcraft layouts -> DesignCraft. Output format = the --out extension.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONT_DIR = HERE.parent / "fonts"
APPS = {"vector": "VectorCraft/vectorcraft-cli", "photo": "PhotoCraft/photocraft-cli", "design": "DesignCraft/designcraft-cli"}
KIND = {**{e: "vector" for e in (".ai", ".ait", ".eps", ".pdf", ".svg", ".svgz", ".afdesign", ".af", ".afpub", ".dxf", ".emf", ".wmf", ".vectorcraft")},
        **{e: "photo" for e in (".psd", ".psb", ".pcraft", ".tif", ".tiff", ".exr")},
        **{e: "design" for e in (".idml", ".designcraft")}}


def find(app):
    name = APPS[app].split("/")[1]
    p = shutil.which(name)
    if p:
        return p
    for base in (os.environ.get("ProgramFiles", r"C:\Program Files"), os.environ.get("LOCALAPPDATA", "") + r"\Programs",
                 "/Applications", "/usr/bin", "/usr/local/bin", "/opt"):
        for cand in (Path(base) / (APPS[app] + ".exe"), Path(base) / APPS[app],
                     Path(base) / f"{APPS[app].split('/')[0]}.app/Contents/MacOS/{name}"):
            if cand.exists():
                return str(cand)
    return None


def run(app, args, check=True):
    exe = find(app)
    if not exe:
        sys.exit(f"{APPS[app].split('/')[0]} is not installed (ArtCraft: getartcraft.com). Use edit_file.py instead.")
    p = subprocess.run([exe] + args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    steps = []
    for line in p.stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                steps.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    if check and p.returncode:
        sys.exit(f"{Path(exe).name} failed:\n{(p.stderr or p.stdout)[-1500:]}")
    return steps, p


def kind_of(path):
    k = KIND.get(Path(path).suffix.lower())
    if not k:
        sys.exit(f"ArtCraft has no app for {Path(path).suffix} here: try edit_file.py")
    return k


def work_copy(src, out):
    """Copy the original next to the output (fonts folders travel with it). Never edit the original."""
    src, out = Path(src).resolve(), Path(out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    cp = out.parent / ("_src_" + src.name)
    if cp.resolve() == src:
        sys.exit("Output folder must differ from the original's folder")
    shutil.copy2(src, cp)
    return cp


def pj(o):
    return json.dumps(o, ensure_ascii=False)


# ------------------------------------------------------------------ commands
def cmd_check(_a):
    for app in APPS:
        print(f"  [{'OK' if find(app) else '--'}] {APPS[app].split('/')[0]:12} {find(app) or ''}")


def vc_font_dir():
    """VectorCraft's own Fonts folder (next to its preferences); the app and vectorcraft-cli both read it."""
    if os.name == "nt":
        return Path(os.environ["APPDATA"]) / "VectorCraft" / "Fonts"
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/VectorCraft/Fonts"
    return Path.home() / ".config/VectorCraft/Fonts"


def cmd_install_fonts(_a):
    """Copy the bundled OFL fonts into VectorCraft's Fonts folder (never replaces a file), then rescan.
    (text.addFontFiles does the same, but its background search doesn't finish inside a batch run.)"""
    d = vc_font_dir()
    d.mkdir(parents=True, exist_ok=True)
    copied = kept = 0
    for f in FONT_DIR.glob("*.ttf"):
        t = d / f.name
        if t.exists():
            kept += 1
        else:
            shutil.copy2(f, t)
            copied += 1
    steps, _ = run("vector", ["run", "--cmd", "text.rescanFonts"] +
                   sum((["--cmd", "text.fontList", "--params", pj({"family": fam})] for fam in
                        ("Bebas Neue", "Lato", "Montserrat", "Open Sans", "Playfair Display", "Poppins")), []))
    ok = [s["result"]["family"] for s in steps if s.get("command") == "text.fontList" and s["result"].get("styles")]
    print(f"VectorCraft fonts folder: {d}")
    print(f"  copied {copied}, already there {kept}; VectorCraft sees: {', '.join(ok)}")
    print("(PhotoCraft/DesignCraft: put fonts in a 'Document Fonts' folder beside the file; DesignCraft loads it automatically.)")


def cmd_info(a):
    k = kind_of(a.file)
    if k == "vector":
        steps, _ = run("vector", ["run", "--in", str(a.file), "--cmd", "document.find", "--params", pj({"kind": "Type", "limit": 500}),
                                  "--cmd", "select.all", "--cmd", "recolor.colors", "--cmd", "select.none", "--cmd", "text.missingFonts", "--cmd", "document.inspect", "--params", pj({"depth": 2, "childLimit": 40})])
        for s in steps:
            st, r = s.get("step"), s.get("result", {})
            if st == "open" and r.get("warnings"):
                print("WARNINGS: " + "; ".join(r["warnings"]))
            elif s.get("command") == "document.find":
                objs = r.get("objects") or r.get("matches") or r.get("results") or r
                print("TEXTS:")
                for o in (objs if isinstance(objs, list) else []):
                    print(f"  {o.get('id')}  \"{(o.get('text') or o.get('contents') or o.get('name') or '')[:70]}\"")
            elif s.get("command") == "recolor.colors":
                print("COLOURS: " + " ".join(c.get("hex") or c.get("key", "") for c in r.get("colors", [])[:20]))
            elif s.get("command") == "text.missingFonts" and r.get("count"):
                print("MISSING FONTS: " + ", ".join(f"{f['family']} {f.get('style', '')} -> shown as {f['resolved']['family']}" for f in r["fonts"]))
            elif s.get("command") == "document.inspect":
                print("LAYERS: " + ", ".join(f"{l.get('name')} ({l.get('id')})" + (" hidden" if l.get("hidden") or l.get("visible") is False else "")
                                           for l in (r.get("layers") or [])[:30]))
    elif k == "photo":
        _, p = run("photo", ["info", str(a.file), "--compact"])
        doc = json.loads(p.stdout[p.stdout.index("{"):])
        print(f"PSD {doc.get('width')}x{doc.get('height')} {doc.get('mode', '')}")

        def walk(ls, d=0):
            for l in ls or []:
                t = l.get("text") if isinstance(l.get("text"), dict) else {}
                extra = f'  "{t.get("text", "")[:60]}"  [{t.get("font", "")} {t.get("sizePt", "")}pt]' if t else ""
                print(f"{'  ' * (d + 1)}{l.get('id')}  [{l.get('kind')}] {l.get('name')}"
                      + ("" if l.get("visible", True) else "  (hidden)") + extra)
                walk(l.get("children") or l.get("layers"), d + 1)
        walk(doc.get("layers"))
    else:
        steps, _ = run("design", ["run", "--in", str(a.file), "--cmd", "document.inspect", "--cmd", "font.list", "--cmd", "links.list"])
        for r in steps:
            if "stories" in r:
                print(f"LAYOUT: {r.get('pageCount')} page(s), {len(r['stories'])} stories (text flows)")
                for st in r["stories"]:
                    print(f"  story {st['id']:>3}  \"{(st.get('preview') or '')[:70]}\"" + ("  OVERSET (text doesn't fit)" if st.get("overset") else ""))
                print("SWATCHES: " + ", ".join(str(sw.get("name", sw)) if isinstance(sw, dict) else str(sw) for sw in r.get("swatches", [])[:20]))
        # font.list / links.list come back as JSON lists
        _, p = run("design", ["run", "--in", str(a.file), "--cmd", "font.list"])
        for line in p.stdout.splitlines():
            if line.startswith("["):
                fonts = json.loads(line)
                print("FONTS: " + ", ".join(f"{f['family']} {f.get('style', '')}" + (" (MISSING)" if f.get("missing") else "") for f in fonts))


def cmd_edit(a):
    k = kind_of(a.file)
    src = work_copy(a.file, a.out)
    exports = [a.out] + (a.also or [])
    args = ["run", "--in", str(src)]

    def c(cid, params=None):
        args.extend(["--cmd", cid] + (["--params", pj(params)] if params is not None and k != "design" else []))
        if k == "design" and params is not None:
            args[-1] = f"{cid}={pj(params)}"
    if k == "vector":
        for old, new in a.replace or []:
            c("edit.findReplace", {"find": old, "replace": new})
        for i, new in a.text or []:
            c("text.setText", {"id": i, "text": new})
        for spec in a.font or []:
            frm, to = spec.split("=", 1)
            c("text.replaceFont", {"from": {"family": frm}, "to": {"family": to}})
        if a.color:
            c("select.all")
            c("recolor.apply", {"map": {o: n for o, n in a.color}})
            c("select.none")
        for i in a.hide or []:
            c("select.set", {"ids": [int(i)]})
            c("object.hide", {})
            c("select.none")
        if a.cmyk:
            c("select.all")
            c("edit.colors.toCMYK", {"includeImages": True})
        args += sum((["--export", str(Path(e).resolve())] for e in exports), [])
        app = "vector"
    elif k == "photo":
        for i, new in a.text or []:
            c("type.edit", {"layer": int(i) if str(i).isdigit() else i, "text": new})
        for spec in a.font or []:
            frm, to = spec.split("=", 1)
            c("type.resolveMissingFonts", {"map": {frm: to}})
        for i in a.hide or []:
            c("layer.hideLayers", {"layer": int(i) if str(i).isdigit() else i})
        for i in a.show or []:
            c("layer.showLayers", {"layer": int(i) if str(i).isdigit() else i})
        if a.cmyk:
            c("image.mode.cmyk", {})
        args = ["run", str(src)] + args[3:] + ["--out", str(Path(a.out).resolve())]
        app = "photo"
    else:
        for i, new in a.text or []:
            c("story.setText", {"story": int(i) if str(i).isdigit() else i, "text": new})
        for old, new in a.replace or []:
            c("find.change", {"find": old, "change": new})
        for spec in a.font or []:
            frm, to = spec.split("=", 1)
            c("font.replace", {"family": frm, "toFamily": to})
            bundled = [f for f in FONT_DIR.glob("*.ttf") if f.stem.replace("-", "").lower().startswith(to.replace(" ", "").lower())]
            if bundled:  # DesignCraft loads a 'Document Fonts' folder beside the file: no install needed
                df = src.parent / "Document Fonts"
                df.mkdir(exist_ok=True)
                for f in bundled:
                    shutil.copy2(f, df / f.name)
        args += sum((["--export", str(Path(e).resolve())] for e in exports), [])
        app = "design"
    steps, _ = run(app, args)
    src.unlink(missing_ok=True)
    if app == "design":
        for r in steps:
            if "path" in r and "bytes" in r:
                print(f"OK {r['path']}  ({r['bytes'] // 1024} KB)")
            else:
                print("  " + json.dumps({k: v for k, v in r.items() if k in ("count", "changed", "runs", "story", "replaced")}, ensure_ascii=False))
            for w in r.get("warnings", []):
                print("WARNING " + str(w))
        for e in exports:
            if Path(e).exists():
                print(f"OK {Path(e).resolve()}  ({Path(e).stat().st_size // 1024} KB)")
        return
    warn = []
    for s in steps:
        r = s.get("result", {})
        if s.get("command"):
            short = {kk: (len(v) if isinstance(v, list) else v) for kk, v in r.items()
                     if kk in ("count", "changed", "runs", "replaced")} if isinstance(r, dict) else r
            print(f"  {s['command']}: {short}")
        if isinstance(r, dict):
            warn += r.get("warnings", [])
        if s.get("step") == "export" and isinstance(r, dict):
            print(f"OK {r.get('path')}  ({r.get('bytes', 0) // 1024} KB)")
    if app == "photo" and Path(a.out).exists():
        print(f"OK {Path(a.out).resolve()}  ({Path(a.out).stat().st_size // 1024} KB)")
        for extra in a.also or []:  # previews: convert the saved file
            run("photo", ["convert", str(Path(a.out).resolve()), str(Path(extra).resolve())])
            print(f"OK {Path(extra).resolve()}")
    for w in sorted(set(warn)):
        print("WARNING " + w)
    if any("fallback font" in w for w in warn):
        print("-> run: artcraft.py install-fonts (bundled fonts), ask the user for the missing font files, or use --font \"Missing=Bundled\"")


def cmd_cmyk(a):
    """Print-shop PDF: whole document to CMYK, exported as PDF/X (x1a: CMYK only, transparency flattened -
    the safest for printers; x4: keeps transparency, colours ICC-tagged)."""
    src = work_copy(a.pdf, a.out)
    std = {"x1a": "pdfX1a", "x4": "pdfX4", "x3": "pdfX3"}[a.standard]
    steps, _ = run("vector", ["run", "--in", str(src), "--cmd", "file.documentColorMode", "--params", pj({"mode": "cmyk"}),
                              "--cmd", "document.exportPdf", "--params", pj({"path": str(Path(a.out).resolve()), "standard": std})])
    src.unlink(missing_ok=True)
    for s in steps:
        r = s.get("result") or {}
        if s.get("command"):
            print(f"  {s['command']}: " + ", ".join(f"{k}={v}" for k, v in r.items() if k in ("changed", "path", "bytes", "standard")))
        for w in r.get("warnings", []) if isinstance(r, dict) else []:
            print("WARNING " + w)
    print(f"OK {Path(a.out).resolve()}  (PDF/X-{a.standard[1:]}, CMYK)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    sub.add_parser("install-fonts")
    i = sub.add_parser("info")
    i.add_argument("file")
    e = sub.add_parser("edit")
    e.add_argument("file")
    e.add_argument("--out", required=True)
    e.add_argument("--also", action="append", help="extra export (e.g. a PNG preview)")
    e.add_argument("--replace", nargs=2, action="append")
    e.add_argument("--text", nargs=2, action="append")
    e.add_argument("--color", nargs=2, action="append")
    e.add_argument("--font", action="append")
    e.add_argument("--hide", action="append")
    e.add_argument("--show", action="append")
    e.add_argument("--cmyk", action="store_true")
    cm = sub.add_parser("cmyk")
    cm.add_argument("pdf")
    cm.add_argument("--out", required=True)
    cm.add_argument("--standard", default="x1a", choices=["x1a", "x4", "x3"])
    a = ap.parse_args()
    {"check": cmd_check, "install-fonts": cmd_install_fonts, "info": cmd_info, "edit": cmd_edit, "cmyk": cmd_cmyk}[a.cmd](a)


if __name__ == "__main__":
    main()
