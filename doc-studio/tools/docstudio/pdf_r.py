"""Spec -> PDF (reportlab platypus). Built-in PDF fonts only, so it works on every computer."""
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, ListFlowable, ListItem, PageBreak,
                                PageTemplate, Paragraph, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

from .common import CODE, LETTERS, page_mm, palette, plain, questions, resolve, runs
from .docx_r import L


def C(h):
    return colors.HexColor("#" + h)


def mk(text, pal):
    """Inline markup -> reportlab paragraph markup."""
    out = []
    for t, b, i, url in runs(text):
        s = escape(t)
        if url == CODE:
            s = f'<font name="Courier">{s}</font>'
        elif url:
            s = f'<a href="{escape(url)}" color="#{pal["primary"]}"><u>{s}</u></a>'
        if b:
            s = f"<b>{s}</b>"
        if i:
            s = f"<i>{s}</i>"
        out.append(s)
    return "".join(out)


def styles(spec, pal, fonts):
    big = spec.get("style") == "screen"
    cmp_ = bool(spec.get("compact"))
    body, head = fonts["pdf_body"], fonts["pdf_heading"]
    serif = head.startswith("Times")
    S = {
        "body": ParagraphStyle("body", fontName=body, fontSize=9.8 if cmp_ else 11 if big else 10.5,
                               leading=13 if cmp_ else 15 if big else 14.5, textColor=C(pal["text"]), spaceAfter=4 if cmp_ else 6),
        "title": ParagraphStyle("title", fontName=head, fontSize=20 if cmp_ else 24, leading=24 if cmp_ else 29,
                                textColor=C(pal["primary"]), spaceAfter=4),
        "subtitle": ParagraphStyle("subtitle", fontName=body, fontSize=13, leading=17, textColor=C(pal["accent"]), spaceAfter=2),
        "meta": ParagraphStyle("meta", fontName=body, fontSize=8.5, leading=11, textColor=C(pal["muted"]), spaceAfter=10),
        "h1": ParagraphStyle("h1", fontName=head, fontSize=16, leading=20, textColor=C(pal["primary"]), spaceBefore=8 if cmp_ else 12,
                             spaceAfter=5, keepWithNext=1),
        "h2": ParagraphStyle("h2", fontName=head, fontSize=12.5 if cmp_ else 13, leading=16 if cmp_ else 17, textColor=C(pal["primary"]),
                             spaceBefore=6 if cmp_ else 9, spaceAfter=3 if cmp_ else 4, keepWithNext=1),
        "h3": ParagraphStyle("h3", fontName=head, fontSize=11.5, leading=15, textColor=C(pal["accent"]), spaceBefore=5 if cmp_ else 7,
                             spaceAfter=3, keepWithNext=1),
        "label": ParagraphStyle("label", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=C(pal["primary"]), spaceAfter=3),
        "verse": ParagraphStyle("verse", fontName="Times-Roman" if serif else "Helvetica", fontSize=11.5, leading=16,
                                textColor=C(pal["text"])),
        "ref": ParagraphStyle("ref", fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=C(pal["accent"]), alignment=TA_RIGHT, spaceBefore=4),
        "egw": ParagraphStyle("egw", fontName="Times-Italic", fontSize=10.5, leading=14.5, textColor=C(pal["text"])),
        "egwref": ParagraphStyle("egwref", fontName="Helvetica", fontSize=8.5, leading=11, textColor=C(pal["muted"]), alignment=TA_RIGHT),
        "small": ParagraphStyle("small", fontName=body, fontSize=8.5, leading=11, textColor=C(pal["muted"])),
        "caption": ParagraphStyle("caption", fontName="Helvetica-Oblique", fontSize=8.5, leading=11, textColor=C(pal["muted"]),
                                  alignment=TA_CENTER, spaceAfter=8),
        "cell": ParagraphStyle("cell", fontName=body, fontSize=9, leading=11.5, textColor=C(pal["text"])),
        "cellh": ParagraphStyle("cellh", fontName="Helvetica-Bold", fontSize=9, leading=11.5, textColor=colors.white),
        "quote": ParagraphStyle("quote", fontName="Helvetica-Oblique", fontSize=10.5, leading=14.5, leftIndent=12 * mm,
                                rightIndent=12 * mm, textColor=C(pal["text"]), spaceAfter=4),
        "ref_item": ParagraphStyle("ref_item", fontName=body, fontSize=9, leading=12, leftIndent=6 * mm, firstLineIndent=-6 * mm,
                                   textColor=C(pal["text"]), spaceAfter=3),
    }
    S["center"] = ParagraphStyle("center", parent=S["body"], alignment=TA_CENTER)
    S["li"] = ParagraphStyle("li", parent=S["body"], spaceAfter=1 if cmp_ else 3)
    return S


def boxed(flows, width, fill, left, border=None):
    t = Table([[flows]], colWidths=[width])
    st = [("BACKGROUND", (0, 0), (-1, -1), fill), ("LINEBEFORE", (0, 0), (0, -1), 3, left),
          ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
          ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]
    if border:
        st.append(("BOX", (0, 0), (-1, -1), 0.5, border))
        st.append(("LINEBEFORE", (0, 0), (0, -1), 3, left))
    t.setStyle(TableStyle(st))
    return [t, Spacer(1, 6)]


class Doc(BaseDocTemplate):
    def afterFlowable(self, f):
        if isinstance(f, Paragraph) and getattr(f, "_toc", None) is not None:
            self.notify("TOCEntry", (f._toc, f.getPlainText(), self.page))


def numbered_canvas(spec, pal):
    b = spec.get("_brand")
    page_word, of_word = L(spec, "page"), L(spec, "of")

    class NC(rl_canvas.Canvas):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self._saved = []

        def showPage(self):
            self._saved.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            n = len(self._saved)
            for st in self._saved:
                self.__dict__.update(st)
                self.decorate(n)
                super().showPage()
            super().save()

        def decorate(self, total):
            w, h = self._pagesize
            self.setFillColor(C(pal["muted"])); self.setFont("Helvetica", 8)
            x = w - 18 * mm
            if b:
                if b.get("logo"):
                    try:
                        self.drawImage(b["logo"], 18 * mm, h - 15 * mm, height=9 * mm, width=30 * mm,
                                       preserveAspectRatio=True, anchor="w", mask="auto")
                    except Exception:
                        pass
                self.setFillColor(C(pal["primary"])); self.setFont("Helvetica-Bold", 8.5)
                self.drawRightString(x, h - 12 * mm, b.get("name", ""))
                bits = [", ".join(b.get("phones") or []), ", ".join(b.get("emails") or []), b.get("website") or ""]
                line = "  ·  ".join(z for z in bits if z)
                if line:
                    self.setFillColor(C(pal["muted"])); self.setFont("Helvetica", 7.5)
                    self.drawCentredString(w / 2, 13 * mm, line)
            else:
                self.drawRightString(x, h - 12 * mm, plain(spec.get("title", ""))[:90])
            self.setStrokeColor(C(pal["soft"] if spec.get("style") == "screen" else "DDDDDD")); self.setLineWidth(0.5)
            self.line(18 * mm, h - 14.5 * mm, w - 18 * mm, h - 14.5 * mm)
            self.setFillColor(C(pal["muted"])); self.setFont("Helvetica", 8)
            self.drawCentredString(w / 2, 8 * mm, f"{page_word} {self._pageNumber} {of_word} {total}")

    return NC


def render(spec, out):
    pal, fonts = palette(spec)
    S = styles(spec, pal, fonts)
    pw, ph = page_mm(spec)
    W = (pw - 40) * mm
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    doc = Doc(str(out), pagesize=(pw * mm, ph * mm), leftMargin=20 * mm, rightMargin=20 * mm, topMargin=22 * mm,
              bottomMargin=20 * mm, title=plain(spec.get("title", "")), author=spec.get("author") or "",
              subject=plain((spec.get("summary") or {}).get("topic", "")), lang={"sn": "sn-ZW"}.get(spec.get("language"), "en-GB"))
    doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(20 * mm, 20 * mm, W, (ph - 42) * mm, id="f")])])
    F = []
    F.append(Paragraph(mk(spec.get("title", "Untitled"), pal), S["title"]))
    if spec.get("subtitle"):
        F.append(Paragraph(mk(spec["subtitle"], pal), S["subtitle"]))
    meta = "  ·  ".join(x for x in [spec.get("author"), spec.get("date"), spec.get("audience")] if x)
    F.append(Paragraph(escape(meta), S["meta"]) if meta else Spacer(1, 8))

    s = spec.get("summary") or {}
    sm = [Paragraph(L(spec, "summary").upper(), S["label"]),
          Paragraph(f"<b>{L(spec, 'topic')}:</b> " + mk(s.get("topic", ""), pal), S["body"]),
          Paragraph(f"<b>{L(spec, 'points')}:</b>", S["body"]),
          ListFlowable([ListItem(Paragraph(mk(k, pal), S["li"]), leftIndent=10) for k in s.get("key_points", [])],
                       bulletType="bullet", start="•", leftIndent=10, bulletFontSize=10, bulletFontName="Helvetica"),
          Paragraph(f"<b>{L(spec, 'takeaway')}:</b> " + mk(s.get("takeaway", ""), pal), S["body"])]
    F += boxed(sm, W, C(pal["soft"]), C(pal["primary"]))
    if spec.get("disclaimer"):
        F.append(Paragraph("<i>" + mk(spec["disclaimer"], pal) + "</i>", S["small"])); F.append(Spacer(1, 6))

    qn = 0
    for b in spec["blocks"]:
        t = b.get("type")
        if t == "heading":
            lv = min(3, max(1, b.get("level", 1)))
            p = Paragraph(mk(b.get("text", ""), pal), S[f"h{lv}"]); p._toc = lv - 1
            F.append(p)
        elif t == "paragraph":
            F.append(Paragraph(mk(b.get("text", ""), pal), S["center" if b.get("align") == "center" else "body"]))
        elif t in ("bullets", "numbered"):
            items = [ListItem(Paragraph(mk(i, pal), S["li"]), leftIndent=12) for i in b.get("items", [])]
            F.append(ListFlowable(items, bulletType="bullet" if t == "bullets" else "1", start="•" if t == "bullets" else 1,
                                  leftIndent=12 if t == "bullets" else 16, bulletFontSize=10,
                                  bulletFontName="Helvetica", bulletFormat=None if t == "bullets" else "%s."))
            F.append(Spacer(1, 4))
        elif t == "verse":
            F += boxed([Paragraph(mk(b.get("text", ""), pal), S["verse"]),
                        Paragraph(escape(f"{b.get('ref', '')} ({b.get('version', 'KJV')})"), S["ref"])],
                       W, C(pal["soft"]), C(pal["accent"]))
        elif t == "egw":
            tag = L(spec, "egw") + ("" if b.get("verified") else "  (UNVERIFIED)")
            src = escape(f"{b.get('book', '')}, {b.get('ref', '')}".strip(", "))
            if b.get("url"):
                src = f'<a href="{escape(b["url"])}" color="#{pal["primary"]}">{src}</a>'
            F += boxed([Paragraph(escape(tag.upper()), S["label"]),
                        Paragraph("“" + mk(b.get("text", ""), pal) + "”", S["egw"]),
                        Paragraph("— " + src, S["egwref"])], W, colors.white, C(pal["primary"]), border=C(pal["muted"]))
        elif t == "quote":
            F.append(Paragraph(mk(b.get("text", ""), pal), S["quote"]))
            if b.get("source"):
                F.append(Paragraph("— " + mk(b["source"], pal), S["egwref"]))
        elif t == "callout":
            kind = b.get("kind", "note")
            col = {"warning": "B54708", "todo": "1D7A3A", "tip": pal["accent"]}.get(kind, pal["primary"])
            lab = ParagraphStyle("lab", parent=S["label"], textColor=C(col))
            F += boxed([Paragraph(escape((b.get("title") or L(spec, kind if kind in ("note", "warning", "todo", "tip") else "note")).upper()), lab),
                        Paragraph(mk(b.get("text", ""), pal), S["body"])], W, C(pal["soft"]), C(col))
        elif t == "table":
            cols, rows = b.get("columns") or [], b.get("rows") or []
            n = max(len(cols), max((len(r) for r in rows), default=1))
            data = ([[Paragraph(mk(str(c), pal), S["cellh"]) for c in cols]] if cols else []) + \
                   [[Paragraph(mk(str(v), pal), S["cell"]) for v in r] + [""] * (n - len(r)) for r in rows]
            widths = b.get("widths")
            cw = [W * x / sum(widths) for x in widths] if widths and len(widths) == n else [W / n] * n
            tb = Table(data, colWidths=cw, repeatRows=1 if cols else 0)
            st = [("GRID", (0, 0), (-1, -1), 0.4, C("BBBBBB")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                  ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
            if cols:
                st.append(("BACKGROUND", (0, 0), (-1, 0), C(pal["primary"])))
            for i in range(1 if cols else 0, len(data)):
                if (i - (1 if cols else 0)) % 2 == 1:
                    st.append(("BACKGROUND", (0, i), (-1, i), C(pal["soft"])))
            tb.setStyle(TableStyle(st))
            F.append(tb)
            F.append(Paragraph(mk(b["caption"], pal), S["caption"]) if b.get("caption") else Spacer(1, 8))
        elif t == "image":
            p = resolve(spec, b["path"])
            img = Image(p)
            ratio = img.imageHeight / img.imageWidth
            w = W * min(100, b.get("width_pct", 80)) / 100
            h = w * ratio
            if h > 150 * mm:
                h = 150 * mm; w = h / ratio
            img.drawWidth, img.drawHeight = w, h
            cap = b.get("caption", "")
            if b.get("credit"):
                cap = (cap + "  " if cap else "") + f"({b['credit']})"
            F.append(KeepTogether([Spacer(1, 4), img] + ([Paragraph(mk(cap, pal), S["caption"])] if cap else [Spacer(1, 8)])))
        elif t == "question":
            qn += 1
            part = [Paragraph(f"<b>{qn}.</b> " + mk(b.get("q", ""), pal), S["body"])]
            for k, ch in enumerate(b.get("choices", [])):
                part.append(Paragraph(f"{LETTERS[k]})&nbsp;&nbsp;" + mk(ch, pal), ParagraphStyle("ch", parent=S["body"], leftIndent=8 * mm, spaceAfter=2)))
            if not b.get("choices"):
                part += [Paragraph("_" * 95, S["small"]) for _ in range(b.get("lines", 3))]
            F.append(KeepTogether(part + [Spacer(1, 4)]))
        elif t == "pagebreak":
            F.append(PageBreak())
        elif t == "toc":
            F.append(Paragraph(L(spec, "contents"), S["h1"]))
            toc = TableOfContents(); toc.dotsMinLevel = 0
            toc.levelStyles = [ParagraphStyle("t1", fontName=fonts["pdf_body"], fontSize=10, leading=14),
                               ParagraphStyle("t2", fontName=fonts["pdf_body"], fontSize=9.5, leading=13, leftIndent=10 * mm),
                               ParagraphStyle("t3", fontName=fonts["pdf_body"], fontSize=9, leading=12, leftIndent=20 * mm)]
            F.append(toc)

    qs = questions(spec)
    if qs and spec.get("answer_key", True):
        F.append(PageBreak()); F.append(Paragraph(L(spec, "answers"), S["h1"]))
        for k, q in enumerate(qs, 1):
            F.append(Paragraph(f"<b>{k}.</b> {escape(str(q.get('answer', '')))}" + (f" — {mk(q['explain'], pal)}" if q.get("explain") else ""), S["body"]))
    if spec.get("references"):
        F.append(Paragraph(L(spec, "refs"), S["h2"]))
        for k, r in enumerate(spec["references"], 1):
            u = r.get("url")
            link = f' <a href="{escape(u)}" color="#{pal["primary"]}">{escape(u)}</a>' if u else ""
            F.append(Paragraph(f"{k}.&nbsp;&nbsp;" + mk(r.get("text", ""), pal) + link, S["ref_item"]))
    if spec.get("credits"):
        F.append(Paragraph(L(spec, "credits"), S["h2"]))
        for c in spec["credits"]:
            F.append(Paragraph("• " + escape(" — ".join(x for x in [c.get("image"), c.get("author"), c.get("licence"), c.get("source")] if x)), S["ref_item"]))

    doc.multiBuild(F, canvasmaker=numbered_canvas(spec, pal))
    return out
