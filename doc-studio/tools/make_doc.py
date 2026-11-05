#!/usr/bin/env python3
"""doc-studio: build documents from one JSON spec.

  python tools/make_doc.py SPEC.json --formats docx,pdf,pptx,xlsx,csv --out OUT_DIR [--name FILE_STEM]
         [--sources scripture.md egw.md ...]    check every verse/EGW quote word for word against fetched text
         [--check]                              checks only, write nothing
The spec format is in references/spec-format.md. Exit 1 = errors (nothing written), 2 = a quote failed verification.
"""
import copy, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from docstudio.common import lint, load_spec, plain, resolve, utf8, verify_quotes  # noqa: E402
from docstudio.images import read_captions, shrink, svg_to_png  # noqa: E402

FORMATS = ("docx", "pdf", "pptx", "xlsx", "csv")


def arg(a, name, default=None, many=False):
    if name not in a:
        return default
    i = a.index(name) + 1
    if not many:
        return a[i]
    vals = []
    while i < len(a) and not a[i].startswith("--"):
        vals.append(a[i]); i += 1
    return vals


def prepare_images(spec, cache):
    """SVG -> PNG, shrink huge photos, and fill caption/credit from images/captions.csv."""
    caps = {}
    for b in spec["blocks"] + (spec.get("slides") or []):
        key = "path" if b.get("type") == "image" else "image"
        p = b.get(key)
        if not p:
            continue
        full = resolve(spec, p)
        folder = str(Path(full).parent)
        if folder not in caps:
            caps[folder] = read_captions(folder)
        c = caps[folder].get(Path(full).name)
        if c and b.get("type") == "image":
            b.setdefault("caption", c.get("caption"))
            if c.get("own", "").lower() in ("yes", "y", "true", "1"):
                b.setdefault("own", True)
            elif c.get("credit"):
                b.setdefault("credit", c["credit"])
                if not any(x.get("image") == Path(full).name for x in spec["credits"]):
                    spec["credits"].append({"image": Path(full).name, "author": c.get("credit"), "licence": c.get("licence"), "source": c.get("source")})
        if not Path(full).exists():
            continue
        if full.lower().endswith(".svg"):
            full = svg_to_png(full, cache)
        else:
            full = shrink(full, cache)
        b[key] = full  # absolute path now


def main():
    utf8()
    a = sys.argv[1:]
    if not a or a[0].startswith("-"):
        print(__doc__); sys.exit(1)
    spec = load_spec(a[0])
    fmts = [f.strip().lower() for f in (arg(a, "--formats") or spec.get("formats") and ",".join(spec["formats"]) or "docx").split(",")]
    bad = [f for f in fmts if f not in FORMATS]
    if bad:
        sys.exit(f"unknown format(s) {bad}; use {FORMATS}")
    out = Path(arg(a, "--out", "."))
    stem = arg(a, "--name") or re.sub(r"[^A-Za-z0-9]+", "-", re.sub(r"['’]", "", plain(spec.get("title", "document")))).strip("-").lower()[:60] or "document"

    err, warn = lint(spec)
    for e in err:
        print("ERROR  " + e)
    for w in warn:
        print("WARN   " + w)
    if err:
        print("Nothing written: fix the errors above."); sys.exit(1)

    rc = 0
    srcs = arg(a, "--sources", many=True)
    if srcs:
        res = verify_quotes(spec, srcs)
        for ref, ok in res:
            print(f"{'QUOTE OK ' if ok else 'QUOTE NOT FOUND'}  {ref}")
        if not all(ok for _, ok in res):
            print("Fix the quote from the fetched text, or mark it UNVERIFIED."); rc = 2
    elif any(b.get("type") in ("verse", "egw") for b in spec["blocks"]):
        print("WARN   verses/EGW quotes present but no --sources given: quotes were not checked against fetched text")

    if "--check" in a:
        print("check only: nothing written"); sys.exit(rc)
    if rc:
        sys.exit(rc)

    prepare_images(spec, out.resolve() / ".cache")
    written = []
    for f in fmts:
        s = copy.deepcopy(spec)
        target = out / f"{stem}.{f}"
        if f == "docx":
            from docstudio import docx_r
            written.append(docx_r.render(s, target))
        elif f == "pdf":
            from docstudio import pdf_r
            written.append(pdf_r.render(s, target))
        elif f == "pptx":
            from docstudio import pptx_r
            written.append(pptx_r.render(s, target))
        elif f == "xlsx":
            from docstudio import xlsx_r
            written.append(xlsx_r.render_xlsx(s, target))
        elif f == "csv":
            from docstudio import xlsx_r
            written += xlsx_r.render_csv(s, target)
    print("\nWritten:")
    for w in written:
        print(f"  {w}  ({Path(w).stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
