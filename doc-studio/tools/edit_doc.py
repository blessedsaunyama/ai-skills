#!/usr/bin/env python3
"""Edit an existing DOCX / PPTX / XLSX in its own format, always on a COPY.

  python tools/edit_doc.py inspect FILE                 outline: headings/paragraphs, slides, or sheets (read only)
  python tools/edit_doc.py text FILE                    all text, for reading the document's content
  python tools/edit_doc.py apply FILE OPS.json [--out NEW_FILE] [--force]
        default NEW_FILE = <name>_edited.<ext> next to the original (refuses to overwrite an existing file without --force)
        --overwrite-original   only after the user explicitly said yes to replacing the original

OPS.json is a list of operations (references/editing.md):
  DOCX  {"op":"add_section", "after_section":"Heading text" | "before_heading":"Heading text" | "at":"end",
         "heading":"New heading", "level":2, "blocks":[...spec blocks: paragraph, bullets, numbered, table, image, callout, verse, quote]}
        {"op":"replace_text", "find":"old", "replace":"new"}
  PPTX  {"op":"add_slide", "title":"...", "bullets":["..."], "after":3, "notes":"..."}      (after = slide number; default end)
        {"op":"replace_text", "find":"old", "replace":"new"}
  XLSX  {"op":"add_sheet", "name":"...", "columns":[...], "rows":[[...]]}
        {"op":"append_rows", "sheet":"...", "rows":[[...]]}
        {"op":"set_cells", "sheet":"...", "cells":{"B2": 10, "C2": "=B2*2"}}
        {"op":"replace_text", "find":"old", "replace":"new"}
New content uses the document's OWN styles (its Heading/Normal/List styles, its slide master), so the format is kept.
"""
import copy, json, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from docstudio.common import runs, utf8  # noqa: E402


# ---------------- DOCX ----------------
def docx_outline(path, full=False):
    from docx import Document
    d = Document(path)
    print(f"DOCX {path}: {len(d.paragraphs)} paragraphs, {len(d.tables)} tables, {len(d.inline_shapes)} pictures")
    print("styles in use: " + ", ".join(sorted({p.style.name for p in d.paragraphs if p.text.strip()})))
    for i, p in enumerate(d.paragraphs):
        if not p.text.strip():
            continue
        if full:
            print(p.text)
        elif p.style.name.startswith(("Heading", "Title")):
            print(f"  [{i:>4}] {p.style.name:10} {p.text[:90]}")
    if not full:
        print("(headings shown; use 'text' for everything)")


def docx_add_runs(par, text):
    for t, b, i, url in runs(text):
        r = par.add_run(t)
        if b:
            r.bold = True
        if i:
            r.italic = True
        if url:
            r.underline = True
            par.add_run(f" ({url})")


def has_style(doc, name):
    try:
        doc.styles[name]
        return True
    except KeyError:
        return False


def heading_level(p):
    n = p.style.name
    if n == "Title":
        return 0
    if n.startswith("Heading "):
        try:
            return int(n.split()[1])
        except ValueError:
            return None
    return None


def docx_anchor(doc, op):
    """Return the element after which new content goes (None = end of document)."""
    paras = doc.paragraphs
    key = op.get("after_section") or op.get("before_heading")
    if not key or op.get("at") == "end":
        return None
    idx = next((i for i, p in enumerate(paras) if heading_level(p) is not None and key.lower() in p.text.lower()), None)
    if idx is None:
        sys.exit(f"heading containing '{key}' not found (run: edit_doc.py inspect FILE)")
    if op.get("before_heading"):
        prev = paras[idx]._p.getprevious()
        return prev if prev is not None else "START"
    lvl = heading_level(paras[idx])
    body = paras[idx]._p.getparent()
    el = paras[idx]._p
    nxt = el.getnext()
    while nxt is not None:  # walk to the end of this section (next heading of same or higher level)
        if nxt.tag.endswith("}p"):
            from docx.text.paragraph import Paragraph
            hp = heading_level(Paragraph(nxt, paras[idx]._parent))
            if hp is not None and hp <= lvl:
                break
        if nxt.tag.endswith("}sectPr"):
            break
        el, nxt = nxt, nxt.getnext()
    return el


def docx_apply(doc, op, base):
    from docx.shared import Mm
    t = op["op"]
    if t == "replace_text":
        n = 0
        def fix(pars):
            nonlocal n
            for p in pars:
                if op["find"] in p.text:
                    done = False
                    for r in p.runs:
                        if op["find"] in r.text:
                            r.text = r.text.replace(op["find"], op["replace"]); done = True; n += 1
                    if not done:  # text split across runs: rebuild in the first run's format
                        full = p.text.replace(op["find"], op["replace"])
                        for r in p.runs[1:]:
                            r._r.getparent().remove(r._r)
                        p.runs[0].text = full; n += 1
        fix(doc.paragraphs)
        for tb in doc.tables:
            for row in tb.rows:
                for c in row.cells:
                    fix(c.paragraphs)
        print(f"replace_text: {n} change(s)")
        return
    if t != "add_section":
        sys.exit(f"unknown DOCX op {t}")
    anchor = docx_anchor(doc, op)
    new = []
    if op.get("heading"):
        new.append(doc.add_heading(op["heading"], level=op.get("level", 2))._p)
    for b in op.get("blocks", []):
        bt = b.get("type")
        if bt == "heading":
            new.append(doc.add_heading(b.get("text", ""), level=b.get("level", 3))._p)
        elif bt in ("paragraph", "quote"):
            p = doc.add_paragraph(); docx_add_runs(p, b.get("text", ""))
            if bt == "quote":
                p.paragraph_format.left_indent = Mm(10)
                for r in p.runs:
                    r.italic = True
            new.append(p._p)
        elif bt in ("bullets", "numbered"):
            style = "List Bullet" if bt == "bullets" else "List Number"
            for k, it in enumerate(b.get("items", []), 1):
                if has_style(doc, style) and bt == "bullets":
                    p = doc.add_paragraph(style=style); docx_add_runs(p, it)
                else:
                    p = doc.add_paragraph(); docx_add_runs(p, (f"{k}. " if bt == "numbered" else "• ") + it)
                    p.paragraph_format.left_indent = Mm(6)
                new.append(p._p)
        elif bt in ("callout", "verse"):
            p = doc.add_paragraph(); p.paragraph_format.left_indent = Mm(8)
            label = b.get("title") or (b.get("ref") if bt == "verse" else "Note")
            r = p.add_run(f"{label}: "); r.bold = True
            docx_add_runs(p, b.get("text", ""))
            new.append(p._p)
        elif bt == "table":
            cols, rows = b.get("columns") or [], b.get("rows") or []
            n = max(len(cols), max((len(r) for r in rows), default=1))
            tb = doc.add_table(rows=(1 if cols else 0) + len(rows), cols=n)
            if has_style(doc, "Table Grid"):
                tb.style = "Table Grid"
            r0 = 0
            if cols:
                for j, c in enumerate(cols):
                    tb.cell(0, j).text = str(c)
                    for r in tb.cell(0, j).paragraphs[0].runs:
                        r.bold = True
                r0 = 1
            for i, row in enumerate(rows):
                for j, v in enumerate(row):
                    tb.cell(r0 + i, j).text = str(v)
            new.append(tb._tbl)
        elif bt == "image":
            pth = Path(b["path"]) if Path(b["path"]).is_absolute() else Path(base) / b["path"]
            p = doc.add_paragraph(); p.add_run().add_picture(str(pth), width=Mm(b.get("width_mm", 120)))
            new.append(p._p)
            if b.get("caption"):
                c = doc.add_paragraph(); r = c.add_run(b["caption"]); r.italic = True
                new.append(c._p)
        else:
            print(f"  (skipped block type {bt})")
    # move the new elements (created at the end) to the anchor
    if anchor is None:
        print(f"add_section: {len(new)} element(s) added at the end")
        return
    if anchor == "START":
        body = doc.element.body
        for k, el in enumerate(new):
            body.insert(k, el)
    else:
        cur = anchor
        for el in new:
            cur.addnext(el); cur = el
    print(f"add_section: {len(new)} element(s) inserted")


# ---------------- PPTX ----------------
def pptx_outline(path, full=False):
    from pptx import Presentation
    prs = Presentation(path)
    print(f"PPTX {path}: {len(prs.slides)} slides, layouts: " + ", ".join(l.name for l in prs.slide_layouts))
    for i, s in enumerate(prs.slides, 1):
        boxes = [sh for sh in s.shapes if sh.has_text_frame and sh.text_frame.text.strip()]
        texts = [sh.text_frame.text.strip() for sh in boxes]
        if s.shapes.title is not None and s.shapes.title.has_text_frame and s.shapes.title.text.strip():
            title = s.shapes.title.text
        else:  # no title placeholder: take the topmost text that isn't in the footer area
            body = [sh for sh in boxes if (sh.top or 0) < prs.slide_height * 0.8]
            body.sort(key=lambda sh: ((sh.top or 0), -(sh.width or 0)))
            title = body[0].text_frame.text.strip().splitlines()[0] if body else ""
        print(f"  slide {i:>2}: {title[:80]}")
        if full:
            for t in texts:
                print("      " + t.replace("\n", "\n      "))


def pptx_apply(prs, op):
    t = op["op"]
    if t == "replace_text":
        n = 0
        for s in prs.slides:
            for sh in s.shapes:
                if sh.has_text_frame:
                    for p in sh.text_frame.paragraphs:
                        for r in p.runs:
                            if op["find"] in r.text:
                                r.text = r.text.replace(op["find"], op["replace"]); n += 1
        print(f"replace_text: {n} change(s)")
        return
    if t != "add_slide":
        sys.exit(f"unknown PPTX op {t}")
    lay = next((l for l in prs.slide_layouts if l.name.lower() in ("title and content", "title, content")), prs.slide_layouts[1 if len(prs.slide_layouts) > 1 else 0])
    s = prs.slides.add_slide(lay)
    if s.shapes.title is not None:
        s.shapes.title.text = op.get("title", "")
    body = next((ph for ph in s.placeholders if ph.placeholder_format.idx == 1), None)
    if body is not None:
        tf = body.text_frame
        for k, b in enumerate(op.get("bullets", [])):
            p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
            p.text = b
    if op.get("notes"):
        s.notes_slide.notes_text_frame.text = op["notes"]
    after = op.get("after")
    if after is not None:
        lst = prs.slides._sldIdLst
        el = lst[-1]
        lst.remove(el)
        lst.insert(int(after), el)
    print(f"add_slide: '{op.get('title', '')}' at position {int(after) + 1 if after is not None else len(prs.slides)}")


# ---------------- XLSX ----------------
def xlsx_outline(path, full=False):
    from openpyxl import load_workbook
    wb = load_workbook(path)
    print(f"XLSX {path}: sheets " + ", ".join(wb.sheetnames))
    for ws in wb.worksheets:
        print(f"  {ws.title}: {ws.max_row} rows x {ws.max_column} cols")
        for row in ws.iter_rows(min_row=1, max_row=ws.max_row if full else min(3, ws.max_row), values_only=True):
            print("      " + " | ".join("" if v is None else str(v) for v in row))


def xlsx_apply(wb, op):
    from openpyxl.styles import Font
    t = op["op"]
    if t == "add_sheet":
        ws = wb.create_sheet(op["name"][:31])
        if op.get("columns"):
            ws.append(op["columns"])
            for c in ws[1]:
                c.font = Font(bold=True)
        for r in op.get("rows", []):
            ws.append(r)
        print(f"add_sheet: {ws.title}")
    elif t == "append_rows":
        ws = wb[op["sheet"]]
        for r in op["rows"]:
            ws.append(r)
        print(f"append_rows: {len(op['rows'])} row(s) to {ws.title}")
    elif t == "set_cells":
        ws = wb[op["sheet"]]
        for k, v in op["cells"].items():
            ws[k] = v
        print(f"set_cells: {len(op['cells'])} cell(s) in {ws.title}")
    elif t == "replace_text":
        n = 0
        for ws in wb.worksheets:
            for row in ws.iter_rows():
                for c in row:
                    if isinstance(c.value, str) and op["find"] in c.value:
                        c.value = c.value.replace(op["find"], op["replace"]); n += 1
        print(f"replace_text: {n} change(s)")
    else:
        sys.exit(f"unknown XLSX op {t}")


def main():
    utf8()
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__); sys.exit(1)
    cmd, src = a[0], Path(a[1])
    if not src.exists():
        sys.exit(f"not found: {src}")
    ext = src.suffix.lower()
    if ext not in (".docx", ".pptx", ".xlsx"):
        sys.exit("edit_doc handles .docx, .pptx and .xlsx (PDF/CSV: read them, then rebuild with make_doc.py)")
    if cmd in ("inspect", "text"):
        {".docx": docx_outline, ".pptx": pptx_outline, ".xlsx": xlsx_outline}[ext](str(src), full=cmd == "text")
        return
    if cmd != "apply" or len(a) < 3:
        print(__doc__); sys.exit(1)
    ops = json.loads(Path(a[2]).read_text(encoding="utf-8"))
    ops = ops if isinstance(ops, list) else [ops]
    out = Path(a[a.index("--out") + 1]) if "--out" in a else src.with_name(f"{src.stem}_edited{src.suffix}")
    if out.resolve() == src.resolve() and "--overwrite-original" not in a:
        sys.exit("refusing to overwrite the original: ask the user first, then add --overwrite-original")
    if out.exists() and out.resolve() != src.resolve() and "--force" not in a:
        sys.exit(f"{out} already exists: choose another --out, or ask the user and add --force")
    if out.resolve() == src.resolve():
        backup = src.with_name(f"{src.stem}_backup{src.suffix}")
        shutil.copy2(src, backup)
        print(f"backup of the original: {backup}")
    else:
        shutil.copy2(src, out)
    base = str(Path(a[2]).resolve().parent)
    if ext == ".docx":
        from docx import Document
        d = Document(str(out))
        for op in ops:
            docx_apply(d, op, base)
        d.save(str(out))
    elif ext == ".pptx":
        from pptx import Presentation
        p = Presentation(str(out))
        for op in ops:
            pptx_apply(p, op)
        p.save(str(out))
    else:
        from openpyxl import load_workbook
        wb = load_workbook(str(out))
        for op in ops:
            xlsx_apply(wb, op)
        wb.save(str(out))
    print(f"\nSaved: {out}  (original untouched: {src})" if out.resolve() != src.resolve() else f"\nSaved over the original: {out}")


if __name__ == "__main__":
    main()
