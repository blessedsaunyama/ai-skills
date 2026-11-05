"""Spec -> PowerPoint .pptx (python-pptx), 16:9. Uses spec["slides"] if given, otherwise builds slides from the blocks."""
from pathlib import Path

from PIL import Image as PILImage
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

from .common import CODE, LETTERS, palette, plain, questions, resolve, rgb, runs
from .docx_r import L

SW, SH = Inches(13.333), Inches(7.5)
MX = Inches(0.6)


def col(h):
    return RGBColor(*rgb(h))


def rect(sl, x, y, w, h, fill, line=None):
    s = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    s.fill.solid(); s.fill.fore_color.rgb = col(fill)
    if line:
        s.line.color.rgb = col(line)
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    return s


def textbox(sl, x, y, w, h, anchor=MSO_ANCHOR.TOP):
    tb = sl.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.08); tf.margin_top = tf.margin_bottom = Inches(0.04)
    return tf


def put(par, text, size, color, font, bold=False, italic=False, link_color=None):
    for t, b, i, url in runs(text):
        r = par.add_run(); r.text = t
        f = r.font; f.size = Pt(size); f.name = "Consolas" if url == CODE else font; f.color.rgb = col(color)
        f.bold = b or bold; f.italic = i or italic
        if url and url != CODE:
            r.hyperlink.address = url
            f.color.rgb = col(link_color or color); f.underline = True


def fit(texts, base, minimum=14, budget=420):
    """Font size so the text fits: `budget` characters fit at `base` size; shrink by sqrt of the overflow."""
    n = sum(len(plain(t)) for t in texts) + 40 * len(texts)
    if n <= budget:
        return base
    return max(minimum, int(base * (budget / n) ** 0.5))


class Deck:
    def __init__(self, spec):
        self.spec = spec
        self.pal, self.fonts = palette(spec)
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = SW, SH
        self.blank = self.prs.slide_layouts[6]
        self.n = 0
        self.dark = self.spec.get("style") == "screen"

    # ---- chrome on every slide ----
    def new(self, notes=None, plain_bg=False):
        sl = self.prs.slides.add_slide(self.blank)
        self.n += 1
        P = self.pal
        if not plain_bg:
            rect(sl, 0, 0, SW, Inches(0.12), P["primary"])
            b = self.spec.get("_brand") or {}
            tf = textbox(sl, MX, SH - Inches(0.45), Inches(9), Inches(0.35), MSO_ANCHOR.MIDDLE)
            put(tf.paragraphs[0], b.get("name") or plain(self.spec.get("title", ""))[:80], 10, P["muted"], self.fonts["body"])
            tf = textbox(sl, SW - MX - Inches(1.5), SH - Inches(0.45), Inches(1.5), Inches(0.35), MSO_ANCHOR.MIDDLE)
            tf.paragraphs[0].alignment = PP_ALIGN.RIGHT
            put(tf.paragraphs[0], str(self.n), 10, P["muted"], self.fonts["body"])
            if b.get("logo"):
                self.logo(sl, b["logo"], SW - MX - Inches(1.6), Inches(0.25), Inches(0.5))
        if notes:
            sl.notes_slide.notes_text_frame.text = plain(notes)
        return sl

    def logo(self, sl, path, x, y, h):
        try:
            w0, h0 = PILImage.open(path).size
            w = int(h * w0 / h0)
            sl.shapes.add_picture(path, x + Inches(1.6) - w, y, height=h)
        except Exception:
            pass

    def title(self, sl, text, sub=None):
        tf = textbox(sl, MX, Inches(0.35), SW - 2 * MX - Inches(1.8), Inches(1.0), MSO_ANCHOR.MIDDLE)
        put(tf.paragraphs[0], text, 30 if len(plain(text)) < 45 else 24, self.pal["primary"], self.fonts["heading"], bold=True)
        if sub:
            p = tf.add_paragraph(); put(p, sub, 14, self.pal["accent"], self.fonts["body"])

    def bullets(self, tf, items, size, color=None):
        first = True
        for it in items:
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            lvl = 1 if str(it).startswith("  ") else 0
            p.level = lvl
            p.space_after = Pt(8)
            put(p, ("•  " if lvl == 0 else "–  ") + str(it).strip(), size - 2 * lvl, color or self.pal["text"], self.fonts["body"])

    # ---- slide types ----
    def s_title(self):
        sp, P = self.spec, self.pal
        sl = self.new(plain_bg=True)
        rect(sl, 0, 0, SW, SH, P["primary"])
        rect(sl, 0, SH - Inches(1.2), SW, Inches(1.2), P["accent"])
        tf = textbox(sl, Inches(0.9), Inches(1.8), SW - Inches(1.8), Inches(2.4), MSO_ANCHOR.BOTTOM)
        put(tf.paragraphs[0], sp.get("title", "Untitled"), 44 if len(plain(sp.get("title", ""))) < 40 else 34, "FFFFFF", self.fonts["heading"], bold=True)
        if sp.get("subtitle"):
            p = tf.add_paragraph(); put(p, sp["subtitle"], 20, "FFFFFF", self.fonts["body"])
        meta = "  ·  ".join(x for x in [sp.get("author"), sp.get("date"), sp.get("audience")] if x)
        if meta:
            tf = textbox(sl, Inches(0.9), SH - Inches(1.05), SW - Inches(1.8), Inches(0.9), MSO_ANCHOR.MIDDLE)
            put(tf.paragraphs[0], meta, 14, "FFFFFF", self.fonts["body"])
        b = sp.get("_brand") or {}
        if b.get("logo"):
            self.logo(sl, b["logo"], SW - Inches(2.4), Inches(0.5), Inches(0.9))

    def s_summary(self):
        s, P = self.spec.get("summary") or {}, self.pal
        sl = self.new(notes=s.get("notes"))
        self.title(sl, L(self.spec, "summary"))
        rect(sl, MX, Inches(1.45), SW - 2 * MX, Inches(5.4), P["soft"])
        rect(sl, MX, Inches(1.45), Inches(0.08), Inches(5.4), P["primary"])
        tf = textbox(sl, MX + Inches(0.35), Inches(1.6), SW - 2 * MX - Inches(0.6), Inches(5.1))
        size = fit([s.get("topic", "")] + s.get("key_points", []) + [s.get("takeaway", "")], 24, 14, 520)
        put(tf.paragraphs[0], f"**{L(self.spec, 'topic')}:** " + s.get("topic", ""), size, P["text"], self.fonts["body"])
        p = tf.add_paragraph(); p.space_before = Pt(10); put(p, f"**{L(self.spec, 'points')}:**", size, P["text"], self.fonts["body"])
        for k in s.get("key_points", []):
            p = tf.add_paragraph(); p.space_after = Pt(4); put(p, "•  " + k, size, P["text"], self.fonts["body"])
        p = tf.add_paragraph(); p.space_before = Pt(10); put(p, f"**{L(self.spec, 'takeaway')}:** " + s.get("takeaway", ""), size, P["primary"], self.fonts["body"])
        if self.spec.get("disclaimer"):
            tf = textbox(sl, MX, SH - Inches(0.85), SW - 2 * MX, Inches(0.35))
            put(tf.paragraphs[0], self.spec["disclaimer"], 11, P["muted"], self.fonts["body"], italic=True)

    def s_section(self, d):
        P = self.pal
        sl = self.new(notes=d.get("notes"))
        rect(sl, 0, Inches(2.6), SW, Inches(2.3), P["soft"])
        rect(sl, MX, Inches(2.6), Inches(0.12), Inches(2.3), P["accent"])
        tf = textbox(sl, MX + Inches(0.4), Inches(2.7), SW - 2 * MX, Inches(2.1), MSO_ANCHOR.MIDDLE)
        put(tf.paragraphs[0], d.get("title", ""), 36, P["primary"], self.fonts["heading"], bold=True)
        if d.get("text"):
            p = tf.add_paragraph(); put(p, d["text"], 18, P["muted"], self.fonts["body"])

    def s_bullets(self, d):
        P = self.pal
        sl = self.new(notes=d.get("notes"))
        self.title(sl, d.get("title", ""), d.get("subtitle"))
        items = d.get("bullets") or []
        img = resolve(self.spec, d.get("image"))
        w = SW - 2 * MX if not img else Inches(7.2)
        top = Inches(1.55)
        if d.get("text"):
            tf = textbox(sl, MX, top, w, Inches(1.0))
            put(tf.paragraphs[0], d["text"], 18, P["text"], self.fonts["body"])
            top += Inches(1.0)
        if items:
            tf = textbox(sl, MX, top, w, SH - top - Inches(0.7))
            self.bullets(tf, items, fit(items, 24 if not img else 20, 14))
        if img:
            self.picture(sl, img, Inches(8.1), Inches(1.5), SW - Inches(8.1) - MX, Inches(5.2), d.get("caption"))

    def s_two(self, d):
        P = self.pal
        sl = self.new(notes=d.get("notes"))
        self.title(sl, d.get("title", ""), d.get("subtitle"))
        cw = (SW - 2 * MX - Inches(0.5)) / 2
        for k, side in enumerate(("left", "right")):
            x = MX + k * (cw + Inches(0.5))
            hd = d.get(side + "_title")
            y = Inches(1.6)
            if hd:
                rect(sl, x, y, cw, Inches(0.6), P["primary"] if k == 0 else P["accent"])
                tf = textbox(sl, x + Inches(0.15), y, cw, Inches(0.6), MSO_ANCHOR.MIDDLE)
                put(tf.paragraphs[0], hd, 18, "FFFFFF", self.fonts["heading"], bold=True)
                y += Inches(0.75)
            tf = textbox(sl, x, y, cw, SH - y - Inches(0.7))
            items = d.get(side) or []
            self.bullets(tf, items, fit(items, 22, 14, 300))

    def s_code(self, d):
        P = self.pal
        sl = self.new(notes=d.get("notes"))
        self.title(sl, d.get("title", ""), d.get("subtitle"))
        code = d.get("code", "")
        top = Inches(1.5)
        if d.get("text"):
            tf = textbox(sl, MX, top, SW - 2 * MX, Inches(0.7)); put(tf.paragraphs[0], d["text"], 16, P["text"], self.fonts["body"])
            top += Inches(0.75)
        h = SH - top - Inches(0.75)
        rect(sl, MX, top, SW - 2 * MX, h, "1E1E1E")
        tf = textbox(sl, MX + Inches(0.25), top + Inches(0.15), SW - 2 * MX - Inches(0.5), h - Inches(0.3))
        lines = code.splitlines() or [""]
        size = 20 if len(lines) <= 8 else 16 if len(lines) <= 14 else 13 if len(lines) <= 20 else 11
        for k, ln in enumerate(lines):
            p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
            r = p.add_run(); r.text = ln or " "
            r.font.name = "Consolas"; r.font.size = Pt(size); r.font.color.rgb = col("D4D4D4")
        if d.get("caption"):
            tf = textbox(sl, MX, SH - Inches(0.75), SW - 2 * MX, Inches(0.3))
            put(tf.paragraphs[0], d["caption"], 11, P["muted"], self.fonts["body"], italic=True)

    def s_verse(self, d):
        P = self.pal
        sl = self.new(notes=d.get("notes"))
        rect(sl, Inches(1.2), Inches(1.4), SW - Inches(2.4), Inches(4.6), P["soft"])
        rect(sl, Inches(1.2), Inches(1.4), Inches(0.12), Inches(4.6), P["accent"])
        tf = textbox(sl, Inches(1.7), Inches(1.6), SW - Inches(3.4), Inches(3.6), MSO_ANCHOR.MIDDLE)
        txt = d.get("text", "")
        egw = d.get("kind") == "egw"
        put(tf.paragraphs[0], ("“" + txt + "”") if egw else txt, 28 if len(txt) < 160 else 22 if len(txt) < 300 else 18,
            P["text"], "Georgia", italic=egw)
        tf = textbox(sl, Inches(1.7), Inches(5.2), SW - Inches(3.4), Inches(0.6))
        tf.paragraphs[0].alignment = PP_ALIGN.RIGHT
        put(tf.paragraphs[0], d.get("ref", ""), 18, P["accent"], self.fonts["body"], bold=True)

    def s_image(self, d):
        sl = self.new(notes=d.get("notes"))
        self.title(sl, d.get("title", ""))
        self.picture(sl, resolve(self.spec, d.get("image")), MX, Inches(1.45), SW - 2 * MX, Inches(5.1), d.get("caption"))

    def s_table(self, d):
        P = self.pal
        sl = self.new(notes=d.get("notes"))
        self.title(sl, d.get("title", ""))
        cols, rows = d.get("columns") or [], d.get("rows") or []
        n = max(len(cols), max((len(r) for r in rows), default=1))
        h = min(Inches(5.2), Inches(0.5) * (len(rows) + 1))
        gt = sl.shapes.add_table(len(rows) + 1, n, MX, Inches(1.6), SW - 2 * MX, h).table
        size = 16 if len(rows) <= 6 else 12
        for j in range(n):
            c = gt.cell(0, j); c.fill.solid(); c.fill.fore_color.rgb = col(P["primary"])
            c.text_frame.paragraphs[0].text = ""
            put(c.text_frame.paragraphs[0], str(cols[j]) if j < len(cols) else "", size, "FFFFFF", self.fonts["body"], bold=True)
        for i, r in enumerate(rows, 1):
            for j in range(n):
                c = gt.cell(i, j); c.fill.solid(); c.fill.fore_color.rgb = col(P["soft"] if i % 2 == 0 else "FFFFFF")
                c.text_frame.paragraphs[0].text = ""
                put(c.text_frame.paragraphs[0], str(r[j]) if j < len(r) else "", size, P["text"], self.fonts["body"])

    def s_refs(self):
        sp, P = self.spec, self.pal
        refs = sp.get("references") or []
        creds = sp.get("credits") or []
        if not refs and not creds:
            return
        items = [f"{k}. {r.get('text', '')}" + (f" [{r['url']}]({r['url']})" if r.get("url") else "") for k, r in enumerate(refs, 1)]
        items += [f"{L(sp, 'credits')}: " + " — ".join(x for x in [c.get('image'), c.get('author'), c.get('licence'), c.get('source')] if x) for c in creds]
        for start in range(0, len(items), 7):
            sl = self.new()
            self.title(sl, L(sp, "refs"))
            tf = textbox(sl, MX, Inches(1.5), SW - 2 * MX, SH - Inches(2.2))
            for k, it in enumerate(items[start:start + 7]):
                p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
                p.space_after = Pt(6)
                put(p, it, 13, P["text"], self.fonts["body"], link_color=P["primary"])

    def picture(self, sl, path, x, y, w, h, caption=None):
        if caption:
            h -= Inches(0.4)
        iw, ih = PILImage.open(path).size
        scale = min(w / iw, h / ih)
        pw, ph = int(iw * scale), int(ih * scale)
        sl.shapes.add_picture(path, x + (w - pw) // 2, y + (h - ph) // 2, pw, ph)
        if caption:
            tf = textbox(sl, x, y + h + Inches(0.05), w, Inches(0.35))
            tf.paragraphs[0].alignment = PP_ALIGN.CENTER
            put(tf.paragraphs[0], caption, 11, self.pal["muted"], self.fonts["body"], italic=True)

    # ---- blocks -> slides ----
    def from_blocks(self):
        slides, cur = [], None

        def flush():
            nonlocal cur
            if cur and (cur.get("bullets") or cur.get("text")):
                slides.append(cur)
            cur = None

        qn, last = 0, ""
        for b in self.spec["blocks"]:
            t = b.get("type")
            if t == "heading" and b.get("level", 1) == 1:
                flush(); slides.append({"layout": "section", "title": b.get("text", "")}); last = b.get("text", "")
            elif t == "heading":
                flush(); cur = {"layout": "bullets", "title": b.get("text", ""), "bullets": []}; last = b.get("text", "")
            elif t in ("paragraph", "bullets", "numbered", "callout", "quote"):
                if cur is None:
                    cur = {"layout": "bullets", "title": last, "bullets": []}
                if t in ("bullets", "numbered"):
                    cur["bullets"] += b.get("items", [])
                else:
                    cur["bullets"].append(b.get("text", ""))
                if len(cur["bullets"]) >= 6:
                    flush()
            elif t in ("verse", "egw"):
                flush(); slides.append({"layout": "verse", "kind": t, "text": b.get("text", ""),
                                        "ref": b.get("ref", "") + (f" ({b.get('version', 'KJV')})" if t == "verse" else "")})
            elif t == "image":
                flush(); slides.append({"layout": "image", "title": b.get("caption", ""), "image": b.get("path"), "caption": b.get("credit")})
            elif t == "table":
                flush(); slides.append({"layout": "table", "title": b.get("caption", ""), "columns": b.get("columns"), "rows": b.get("rows")})
            elif t == "question":
                flush(); qn += 1
                slides.append({"layout": "bullets", "title": f"Q{qn}. {b.get('q', '')}",
                               "bullets": [f"{LETTERS[k]})  {c}" for k, c in enumerate(b.get("choices", []))]})
        flush()
        return slides

    def build(self, out):
        self.s_title()
        self.s_summary()
        for d in self.spec.get("slides") or self.from_blocks():
            lay = d.get("layout", "bullets")
            {"section": self.s_section, "two-col": self.s_two, "code": self.s_code, "verse": self.s_verse,
             "image": self.s_image, "table": self.s_table}.get(lay, self.s_bullets)(d)
        self.s_refs()
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        self.prs.core_properties.title = plain(self.spec.get("title", ""))
        self.prs.core_properties.author = self.spec.get("author") or ""
        self.prs.save(out)
        return out


def render(spec, out):
    return Deck(spec).build(out)
