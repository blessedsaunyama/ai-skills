"""Spec -> Word .docx (python-docx)."""
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

from .common import CODE, LETTERS, page_mm, palette, plain, questions, resolve, rgb, runs

LABELS = {
    "en": {"summary": "Summary", "topic": "Topic", "points": "Key points", "takeaway": "Takeaway", "refs": "References",
           "credits": "Image credits", "answers": "Answer key", "page": "Page", "of": "of", "contents": "Contents",
           "note": "Note", "warning": "Important", "todo": "Your turn", "tip": "Tip", "egw": "Ellen G. White"},
    "sn": {"summary": "Pfupiso", "topic": "Musoro", "points": "Pfungwa huru", "takeaway": "Chidzidzo", "refs": "Mareferensi",
           "credits": "Vanobva mifananidzo", "answers": "Mhinduro", "page": "Peji", "of": "pa", "contents": "Zviri mukati",
           "note": "Cherechedza", "warning": "Zvakakosha", "todo": "Wava wako", "tip": "Zano", "egw": "Ellen G. White"},
}


def L(spec, k):
    return LABELS.get(spec.get("language", "en"), LABELS["en"]).get(k, LABELS["en"][k])


# ---------------- low-level helpers ----------------
def shade(cell, hexs):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), hexs)
    tcPr.append(sh)


def cell_borders(cell, left=None, others="nil", size=24):
    tcPr = cell._tc.get_or_add_tcPr()
    b = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right"):
        e = OxmlElement(f"w:{side}")
        if side == "left" and left:
            e.set(qn("w:val"), "single"); e.set(qn("w:sz"), str(size)); e.set(qn("w:color"), left)
        elif others != "nil":
            e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:color"), others)
        else:
            e.set(qn("w:val"), "nil")
        b.append(e)
    tcPr.append(b)


def hyperlink(par, text, url, color):
    rid = par.part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    h = OxmlElement("w:hyperlink"); h.set(qn("r:id"), rid)
    r = OxmlElement("w:r"); rPr = OxmlElement("w:rPr")
    c = OxmlElement("w:color"); c.set(qn("w:val"), color); rPr.append(c)
    u = OxmlElement("w:u"); u.set(qn("w:val"), "single"); rPr.append(u)
    r.append(rPr); t = OxmlElement("w:t"); t.text = text; t.set(qn("xml:space"), "preserve"); r.append(t)
    h.append(r); par._p.append(h)


def add_runs(par, text, pal, size=None, italic=False, bold=False, color=None, font=None):
    for t, b, i, url in runs(text):
        if url and url != CODE:
            hyperlink(par, t, url, pal["primary"])
            continue
        r = par.add_run(t)
        if url == CODE:
            r.font.name = "Consolas"
        r.bold = b or bold or None
        r.italic = i or italic or None
        if size:
            r.font.size = Pt(size)
        if color:
            r.font.color.rgb = RGBColor(*rgb(color))
        if font and url != CODE:
            r.font.name = font
    return par


def field(par, code):
    r = par.add_run()
    f1 = OxmlElement("w:fldChar"); f1.set(qn("w:fldCharType"), "begin")
    it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = code
    f2 = OxmlElement("w:fldChar"); f2.set(qn("w:fldCharType"), "separate")
    t = OxmlElement("w:t"); t.text = "1"
    f3 = OxmlElement("w:fldChar"); f3.set(qn("w:fldCharType"), "end")
    for e in (f1, it, f2, t, f3):
        r._r.append(e)


def spacing(par, before=0, after=6):
    par.paragraph_format.space_before = Pt(before)
    par.paragraph_format.space_after = Pt(after)


def row_flags(row, header=False):
    trPr = row._tr.get_or_add_trPr()
    e = OxmlElement("w:cantSplit"); trPr.append(e)
    if header:
        h = OxmlElement("w:tblHeader"); trPr.append(h)


def box(doc, fill, left):
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    row_flags(t.rows[0])
    c = t.cell(0, 0)
    shade(c, fill)
    cell_borders(c, left=left)
    c.paragraphs[0].text = ""
    return c


def after_box(doc):
    spacing(doc.add_paragraph(), 0, 2)


# ---------------- document setup ----------------
def setup(doc, spec, pal, fonts):
    w, h = page_mm(spec)
    for s in doc.sections:
        s.page_width, s.page_height = Mm(w), Mm(h)
        if spec.get("orientation") == "landscape":
            s.orientation = WD_ORIENT.LANDSCAPE
        m = 20 if spec.get("style") != "screen" else 18
        s.left_margin = s.right_margin = Mm(m)
        s.top_margin, s.bottom_margin = Mm(20), Mm(18)
    st = doc.styles
    n = st["Normal"]; n.font.name = fonts["body"]
    n.font.size = Pt(10 if spec.get("compact") else 11 if spec.get("style") != "screen" else 12)
    n.font.color.rgb = RGBColor(*rgb(pal["text"]))
    n.element.rPr.rFonts.set(qn("w:eastAsia"), fonts["body"])
    n.paragraph_format.space_after = Pt(3 if spec.get("compact") else 6)
    n.paragraph_format.line_spacing = 1.05 if spec.get("compact") else 1.15
    for lvl, size in ((1, 18), (2, 14), (3, 12)):
        hs = st[f"Heading {lvl}"]
        hs.font.name = fonts["heading"]; hs.font.size = Pt(size); hs.font.bold = True
        hs.font.color.rgb = RGBColor(*rgb(pal["primary"] if lvl < 3 else pal["accent"]))
        hs.paragraph_format.space_before = Pt(14 if lvl == 1 else 10); hs.paragraph_format.space_after = Pt(4)
        hs.paragraph_format.keep_with_next = True
    ti = st["Title"]; ti.font.name = fonts["heading"]; ti.font.size = Pt(26); ti.font.color.rgb = RGBColor(*rgb(pal["primary"]))
    lang = {"en": "en-GB", "sn": "sn-ZW"}.get(spec.get("language", "en"), "en-GB")
    doc.core_properties.language = lang
    doc.core_properties.title = plain(spec.get("title", ""))
    doc.core_properties.author = spec.get("author") or (spec.get("_brand") or {}).get("name") or ""
    doc.core_properties.subject = plain((spec.get("summary") or {}).get("topic", ""))


def header_footer(doc, spec, pal):
    b = spec.get("_brand")
    s = doc.sections[0]
    hp = s.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if b:
        if b.get("logo"):
            hp.add_run().add_picture(b["logo"], height=Mm(10))
            hp.add_run("  ")
        add_runs(hp, b.get("name", ""), pal, size=9, bold=True, color=pal["primary"])
        if b.get("tagline"):
            add_runs(hp, "  |  " + b["tagline"], pal, size=8, color=pal["muted"])
    else:
        add_runs(hp, plain(spec.get("title", "")), pal, size=8, color=pal["muted"])
    fp = s.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if b:
        bits = [x for x in [", ".join(b.get("phones") or []), ", ".join(b.get("emails") or []), b.get("website")] if x]
        if bits:
            add_runs(fp, "  ·  ".join(bits), pal, size=8, color=pal["muted"])
            fp = s.footer.add_paragraph(); fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fp.add_run(f"{L(spec, 'page')} "); r.font.size = Pt(8)
    field(fp, "PAGE")
    r = fp.add_run(f" {L(spec, 'of')} "); r.font.size = Pt(8)
    field(fp, "NUMPAGES")


def title_block(doc, spec, pal):
    p = doc.add_paragraph(style="Title")
    add_runs(p, spec.get("title", "Untitled"), pal)
    if spec.get("subtitle"):
        p = doc.add_paragraph(); add_runs(p, spec["subtitle"], pal, size=13, color=pal["accent"]); spacing(p, 0, 2)
    meta = "  ·  ".join(x for x in [spec.get("author"), spec.get("date"), spec.get("audience")] if x)
    if meta:
        p = doc.add_paragraph(); add_runs(p, meta, pal, size=9, color=pal["muted"]); spacing(p, 0, 10)


def summary(doc, spec, pal):
    s = spec.get("summary") or {}
    c = box(doc, pal["soft"], pal["primary"])
    p = c.paragraphs[0]; add_runs(p, L(spec, "summary").upper(), pal, size=9, bold=True, color=pal["primary"]); spacing(p, 4, 2)
    p = c.add_paragraph(); add_runs(p, f"**{L(spec, 'topic')}:** {s.get('topic', '')}", pal); spacing(p, 0, 2)
    p = c.add_paragraph(); add_runs(p, f"**{L(spec, 'points')}:**", pal); spacing(p, 0, 1)
    for kp in s.get("key_points", []):
        p = c.add_paragraph(); p.paragraph_format.left_indent = Mm(5); add_runs(p, "•  " + kp, pal); spacing(p, 0, 1)
    p = c.add_paragraph(); add_runs(p, f"**{L(spec, 'takeaway')}:** {s.get('takeaway', '')}", pal); spacing(p, 2, 4)
    after_box(doc)
    if spec.get("disclaimer"):
        p = doc.add_paragraph(); add_runs(p, spec["disclaimer"], pal, size=9, italic=True, color=pal["muted"])


# ---------------- blocks ----------------
def table(doc, spec, b, pal):
    cols = b.get("columns") or []
    rows = b.get("rows") or []
    t = doc.add_table(rows=1 + len(rows), cols=max(1, len(cols) or (len(rows[0]) if rows else 1)))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, c in enumerate(cols):
        cell = t.cell(0, j); shade(cell, pal["primary"]); cell.paragraphs[0].text = ""
        add_runs(cell.paragraphs[0], str(c), pal, bold=True, color="FFFFFF", size=10)
    for i, row in enumerate(rows, 1):
        for j, v in enumerate(row[:len(t.columns)]):
            cell = t.cell(i, j); cell.paragraphs[0].text = ""
            add_runs(cell.paragraphs[0], str(v), pal, size=10)
            if i % 2 == 0:
                shade(cell, pal["soft"])
    for k, row in enumerate(t.rows):
        row_flags(row, header=(k == 0 and bool(cols)))
    w = b.get("widths")
    if w and len(w) == len(t.columns):
        total = (page_mm(spec)[0] - 40)
        t.autofit = False
        for j, col in enumerate(t.columns):
            mm_w = Mm(total * w[j] / sum(w))
            for cell in col.cells:
                cell.width = mm_w
    if not cols:
        t._tbl.remove(t.rows[0]._tr)
    if b.get("caption"):
        p = doc.add_paragraph(); add_runs(p, b["caption"], pal, size=9, italic=True, color=pal["muted"])
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        after_box(doc)


def image(doc, spec, b, pal):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    w, _ = page_mm(spec)
    width = (w - 40) * min(100, b.get("width_pct", 80)) / 100
    p.add_run().add_picture(resolve(spec, b["path"]), width=Mm(width))
    spacing(p, 4, 2)
    cap = b.get("caption", "")
    if b.get("credit"):
        cap = (cap + "  " if cap else "") + f"({b['credit']})"
    if cap:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_runs(p, cap, pal, size=9, italic=True, color=pal["muted"])


def block(doc, spec, b, pal, fonts, qnum):
    t = b.get("type")
    if t == "heading":
        p = doc.add_heading(level=min(3, max(1, b.get("level", 1)))); add_runs(p, b.get("text", ""), pal)
    elif t == "paragraph":
        p = doc.add_paragraph(); add_runs(p, b.get("text", ""), pal)
        if b.get("align") == "center":
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif t == "bullets":
        for it in b.get("items", []):
            p = doc.add_paragraph(style="List Bullet"); add_runs(p, it, pal); spacing(p, 0, 2)
    elif t == "numbered":
        for k, it in enumerate(b.get("items", []), 1):
            p = doc.add_paragraph(); p.paragraph_format.left_indent = Mm(8); p.paragraph_format.first_line_indent = Mm(-6)
            add_runs(p, f"{k}.\t{it}", pal); spacing(p, 0, 2)
    elif t == "verse":
        c = box(doc, pal["soft"], pal["accent"])
        p = c.paragraphs[0]; add_runs(p, b.get("text", ""), pal, size=11.5, font=fonts["heading"]); spacing(p, 4, 2)
        p = c.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        add_runs(p, f"{b.get('ref', '')} ({b.get('version', 'KJV')})", pal, size=9.5, bold=True, color=pal["accent"]); spacing(p, 0, 4)
        after_box(doc)
    elif t == "egw":
        c = box(doc, "FFFFFF", pal["primary"])
        cell_borders(c, left=pal["primary"], others=pal["muted"], size=12)
        p = c.paragraphs[0]
        tag = L(spec, "egw") + ("" if b.get("verified") else "  (UNVERIFIED)")
        add_runs(p, tag.upper(), pal, size=8, bold=True, color=pal["primary"]); spacing(p, 4, 2)
        p = c.add_paragraph(); add_runs(p, f"“{b.get('text', '')}”", pal, italic=True, size=10.5); spacing(p, 0, 2)
        p = c.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        src = f"{b.get('book', '')}, {b.get('ref', '')}".strip(", ")
        if b.get("url"):
            p.add_run("— "); hyperlink(p, src, b["url"], pal["primary"])
        else:
            add_runs(p, "— " + src, pal, size=9)
        spacing(p, 0, 4)
        after_box(doc)
    elif t == "quote":
        p = doc.add_paragraph(); p.paragraph_format.left_indent = Mm(10); p.paragraph_format.right_indent = Mm(10)
        add_runs(p, b.get("text", ""), pal, italic=True)
        if b.get("source"):
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.RIGHT; add_runs(p, "— " + b["source"], pal, size=9, color=pal["muted"])
    elif t == "callout":
        kind = b.get("kind", "note")
        col = {"warning": "B54708", "todo": "1D7A3A", "tip": pal["accent"]}.get(kind, pal["primary"])
        c = box(doc, pal["soft"], col)
        p = c.paragraphs[0]; add_runs(p, (b.get("title") or L(spec, kind if kind in ("note", "warning", "todo", "tip") else "note")).upper(),
                                      pal, size=8.5, bold=True, color=col); spacing(p, 4, 2)
        p = c.add_paragraph(); add_runs(p, b.get("text", ""), pal); spacing(p, 0, 4)
        after_box(doc)
    elif t == "table":
        table(doc, spec, b, pal)
    elif t == "image":
        image(doc, spec, b, pal)
    elif t == "question":
        qnum[0] += 1
        p = doc.add_paragraph(); add_runs(p, f"**{qnum[0]}.** {b.get('q', '')}", pal); spacing(p, 6, 2)
        p.paragraph_format.keep_with_next = True
        for k, ch in enumerate(b.get("choices", [])):
            p = doc.add_paragraph(); p.paragraph_format.left_indent = Mm(8); add_runs(p, f"{LETTERS[k]})  {ch}", pal); spacing(p, 0, 1)
        if not b.get("choices"):
            for _ in range(b.get("lines", 3)):
                p = doc.add_paragraph("_" * 80); spacing(p, 0, 2)
    elif t == "pagebreak":
        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    elif t == "toc":
        p = doc.add_paragraph(); add_runs(p, L(spec, "contents"), pal, size=18, bold=True, color=pal["primary"], font=fonts["heading"])
        spacing(p, 14, 4)
        p = doc.add_paragraph(); field(p, 'TOC \\o "1-3" \\h \\z \\u')
        p = doc.add_paragraph(); add_runs(p, "(Right-click → Update field to refresh the contents.)", pal, size=8, italic=True, color=pal["muted"])


def endmatter(doc, spec, pal):
    qs = questions(spec)
    if qs and spec.get("answer_key", True):
        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        doc.add_heading(L(spec, "answers"), level=1)
        for k, q in enumerate(qs, 1):
            a = q.get("answer", "")
            p = doc.add_paragraph(); add_runs(p, f"**{k}.** {a}" + (f" — {q['explain']}" if q.get("explain") else ""), pal); spacing(p, 0, 2)
    if spec.get("references"):
        doc.add_heading(L(spec, "refs"), level=2)
        for k, r in enumerate(spec["references"], 1):
            p = doc.add_paragraph(); p.paragraph_format.left_indent = Mm(8); p.paragraph_format.first_line_indent = Mm(-6)
            add_runs(p, f"{k}.\t{r.get('text', '')}", pal, size=9.5)
            if r.get("url"):
                p.add_run(" "); hyperlink(p, r["url"], r["url"], pal["primary"])
            spacing(p, 0, 2)
    if spec.get("credits"):
        doc.add_heading(L(spec, "credits"), level=2)
        for c in spec["credits"]:
            bits = [c.get("image"), c.get("author"), c.get("licence"), c.get("source")]
            p = doc.add_paragraph(); add_runs(p, "•  " + " — ".join(x for x in bits if x), pal, size=9); spacing(p, 0, 1)


def render(spec, out):
    pal, fonts = palette(spec)
    doc = Document()
    setup(doc, spec, pal, fonts)
    header_footer(doc, spec, pal)
    title_block(doc, spec, pal)
    summary(doc, spec, pal)
    qnum = [0]
    for b in spec["blocks"]:
        block(doc, spec, b, pal, fonts, qnum)
    endmatter(doc, spec, pal)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    doc.save(out)
    return out
