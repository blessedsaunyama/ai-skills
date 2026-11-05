"""Turn a design spec (JSON) into SVG: outlined text (for rendering) + editable text.

Used by make.py. Layouts: event/poster/social/banner -> split | hero | bold,
thumbnail, certificate. See references/spec.md for every field.
"""
import base64
import io
import math
import random
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageFilter, ImageOps

import sizes
import styles
import textpath as tp

# ------------------------------------------------------------------ icons (24 x 24, stroke)
ICONS = {
    "calendar": "M5 6h14v13H5z M5 10h14 M9 4v4 M15 4v4",
    "clock": "M5 12a7 7 0 1 0 14 0a7 7 0 1 0 -14 0 M12 8v4l3 2",
    "pin": "M12 21s-6-5.5-6-10a6 6 0 0 1 12 0c0 4.5-6 10-6 10z M10.2 11a1.8 1.8 0 1 0 3.6 0a1.8 1.8 0 1 0 -3.6 0",
    "phone": "M8 3h8v18H8z M11 18h2",
    "chat": "M12 5c4.4 0 8 2.9 8 6.5S16.4 18 12 18c-1 0-2-.1-2.9-.4L5 19l1.3-3.2C4.9 14.6 4 13.1 4 11.5 4 7.9 7.6 5 12 5z",
    "mail": "M4 6h16v12H4z M4 7l8 6 8-6",
    "globe": "M4 12a8 8 0 1 0 16 0a8 8 0 1 0 -16 0 M4 12h16 M12 4c2.5 2.2 3.5 5 3.5 8s-1 5.8-3.5 8c-2.5-2.2-3.5-5-3.5-8s1-5.8 3.5-8z",
    "at": "M15.5 12a3.5 3.5 0 1 1 -7 0a3.5 3.5 0 1 1 7 0z M15.5 12v1.5a2.5 2.5 0 0 0 5 0V12a8.5 8.5 0 1 0 -3.3 6.7",
    "mic": "M9.5 4h5v8.5a2.5 2.5 0 0 1 -5 0z M6.5 11.5a5.5 5.5 0 0 0 11 0 M12 17v3 M9 20h6",
    "user": "M8.5 8a3.5 3.5 0 1 0 7 0a3.5 3.5 0 1 0 -7 0 M5 20c0-3.9 3.1-6.5 7-6.5s7 2.6 7 6.5",
    "ticket": "M4 7h16v3a2 2 0 0 0 0 4v3H4v-3a2 2 0 0 0 0-4z M14 7v10",
}
CONTACT_ICON = {"phone": "phone", "whatsapp": "chat", "email": "mail", "website": "globe", "url": "globe",
                "facebook": "at", "instagram": "at", "tiktok": "at", "x": "at", "youtube": "at", "social": "at", "person": "user"}
SOCIAL_PREFIX = {"facebook": "FB", "instagram": "IG", "tiktok": "TikTok", "x": "X", "youtube": "YouTube"}


# ------------------------------------------------------------------ canvas
class Canvas:
    def __init__(self, W, H, bleed=0.0, mark=0.0, px_per_mm=None):
        self.W, self.H, self.bleed, self.mark, self.ppmm = W, H, bleed, mark, px_per_mm
        self.defs, self.els, self.n, self.fonts, self.warn = [], [], 0, set(), []

    def uid(self, p="i"):
        self.n += 1
        return f"{p}{self.n}"

    def raw(self, s):
        self.els.append((s, s))

    def defn(self, s):
        self.defs.append(s)

    def text(self, s, fam, wt, size, x, y, fill, anchor="start", tracking=0.0, opacity=1.0, stroke=None, sw=0.0, shadow=None):
        if not s:
            return 0.0
        miss = tp.missing_chars(s, fam, wt)
        if miss:
            self.warn.append(f"font {fam} lacks {''.join(miss)} (used fallback)")
        d, w = tp.outline(s, fam, wt, size, x, y, anchor, tracking)
        real_w = tp.font(fam, wt).weight
        op = f' opacity="{opacity:.3f}"' if opacity < 1 else ""

        def live(dx, dy, attrs):
            return (f'<text x="{x + dx:.1f}" y="{y + dy:.1f}" font-family="{fam}" font-weight="{real_w}" '
                    f'font-size="{size:.1f}" letter-spacing="{tracking * size:.2f}" text-anchor="{anchor}" {attrs}>{escape(s)}</text>')
        out, lv = [], []
        if shadow:
            dx, dy, col, so = shadow
            d2, _ = tp.outline(s, fam, wt, size, x + dx, y + dy, anchor, tracking)
            out.append(f'<path d="{d2}" fill="{col}" opacity="{so}"/>')
            lv.append(live(dx, dy, f'fill="{col}" opacity="{so}"'))
        if stroke:
            out.append(f'<path d="{d}" fill="{stroke}" stroke="{stroke}" stroke-width="{sw:.1f}" stroke-linejoin="round"{op}/>')
            lv.append(live(0, 0, f'fill="{stroke}" stroke="{stroke}" stroke-width="{sw:.1f}" stroke-linejoin="round"{op}'))
        out.append(f'<path d="{d}" fill="{fill}"{op}/>')
        lv.append(live(0, 0, f'fill="{fill}"{op}'))
        self.els.append(("\n".join(out), "\n".join(lv)))
        self.fonts.add((fam, real_w))
        return w

    def image(self, im, x, y, w, h, clip=None, opacity=1.0):
        uri = img_uri(im)
        c = f' clip-path="url(#{clip})"' if clip else ""
        o = f' opacity="{opacity}"' if opacity < 1 else ""
        self.raw(f'<image x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" preserveAspectRatio="none" xlink:href="{uri}"{c}{o}/>')

    def icon(self, name, cx, cy, r, bg, fg):
        if bg:
            self.raw(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{bg}"/>')
        s = r * 1.15 / 12
        self.raw(f'<path d="{ICONS[name]}" fill="none" stroke="{fg}" stroke-width="{2.0:.2f}" stroke-linecap="round" '
                 f'stroke-linejoin="round" transform="translate({cx - 12 * s:.1f} {cy - 12 * s:.1f}) scale({s:.4f})"/>')

    def svg(self, mode="outlined", view="trim", out_w=None, out_h=None, font_css=""):
        """view: trim (exact size) | bleed (trim + bleed) | marks (bleed + crop marks)."""
        W, H, b = self.W, self.H, self.bleed
        off = {"trim": 0, "bleed": b, "marks": b + self.mark}[view]
        vw, vh = W + 2 * off, H + 2 * off
        if out_w:
            size = f'width="{out_w}" height="{out_h}"'
        elif self.ppmm:
            size = f'width="{vw / self.ppmm:.3f}mm" height="{vh / self.ppmm:.3f}mm"'
        else:
            size = f'width="{vw:.0f}" height="{vh:.0f}"'
        body = "\n".join(e[0] if mode == "outlined" else e[1] for e in self.els)
        marks = self._marks() if view == "marks" else ""
        style = f"<style>{font_css}</style>" if (mode != "outlined" and font_css) else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" {size} '
                f'viewBox="{-off:.2f} {-off:.2f} {vw:.2f} {vh:.2f}">\n{style}<defs>{"".join(self.defs)}'
                f'<clipPath id="artclip"><rect x="{-b:.2f}" y="{-b:.2f}" width="{W + 2 * b:.2f}" height="{H + 2 * b:.2f}"/></clipPath></defs>\n'
                f'<g clip-path="url(#artclip)">\n{body}\n</g>{marks}\n</svg>\n')

    def _marks(self):
        b, m, W, H = self.bleed, self.mark, self.W, self.H
        sw = max(1.0, (self.ppmm or 1) * 0.1)
        ls = []
        for x in (0, W):
            for y in (0, H):
                sx = -1 if x == 0 else 1
                sy = -1 if y == 0 else 1
                ls.append(f'M{x + sx * (b + 1 * (self.ppmm or 1)):.1f} {y:.1f}H{x + sx * (b + m):.1f}')
                ls.append(f'M{x:.1f} {y + sy * (b + 1 * (self.ppmm or 1)):.1f}V{y + sy * (b + m):.1f}')
        return f'<path d="{" ".join(ls)}" stroke="#000" stroke-width="{sw:.2f}" fill="none"/>'


# ------------------------------------------------------------------ image helpers
def load_image(path):
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)
    return im.convert("RGBA")


def is_cutout(im):
    if im.mode != "RGBA":
        return False
    h = im.getchannel("A").histogram()
    return sum(h[:16]) > 0.05 * im.width * im.height


def trim_alpha(im):
    bb = im.getchannel("A").point(lambda v: 255 if v > 12 else 0).getbbox()
    return im.crop(bb) if bb else im


def needs_chip(im):
    a = im.getchannel("A")
    corners = [a.getpixel(p) for p in ((0, 0), (im.width - 1, 0), (0, im.height - 1), (im.width - 1, im.height - 1))]
    return min(corners) > 200


def cover(im, tw, th, focus_y=0.3):
    tw, th = max(1, int(tw)), max(1, int(th))
    r = max(tw / im.width, th / im.height)
    nw, nh = math.ceil(im.width * r), math.ceil(im.height * r)
    if r < 1:
        im = im.resize((nw, nh), Image.LANCZOS)
        r2 = 1
    else:
        r2 = r  # don't upscale pixels; place larger instead
    cw, ch = tw / r2, th / r2
    x0 = (im.width - cw) / 2
    y0 = (im.height - ch) * focus_y
    return im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch)))


def shrink(im, w, h):
    if im.width > w * 1.02 or im.height > h * 1.02:
        return im.resize((max(1, int(w)), max(1, int(h))), Image.LANCZOS)
    return im


def img_uri(im):
    buf = io.BytesIO()
    if im.mode == "RGBA" and im.getchannel("A").getextrema()[0] < 255:
        im.save(buf, "PNG", optimize=False, compress_level=6)
        kind = "png"
    else:
        im.convert("RGB").save(buf, "JPEG", quality=90)
        kind = "jpeg"
    return f"data:image/{kind};base64," + base64.b64encode(buf.getvalue()).decode()


def soft_layer(im, color, radius, grow=0):
    """Blurred silhouette (glow) or solid outline of a cutout. Computed small for speed."""
    k = max(1, int(max(im.size) / 600))
    a = im.getchannel("A").resize((max(1, im.width // k), max(1, im.height // k)))
    pad = int(radius * 2 / k) + int(grow / k) + 2
    big = Image.new("L", (a.width + 2 * pad, a.height + 2 * pad), 0)
    big.paste(a, (pad, pad))
    if grow:
        big = big.filter(ImageFilter.GaussianBlur(grow / k / 2)).point(lambda v: 255 if v > 10 else 0)
        big = big.filter(ImageFilter.GaussianBlur(1))
    if radius:
        big = big.filter(ImageFilter.GaussianBlur(radius / k)).point(lambda v: min(255, int(v * 1.3)))
    big = big.resize((big.width * k, big.height * k), Image.BILINEAR)
    layer = Image.new("RGBA", big.size, styles.hex_rgb(color) + (255,))
    layer.putalpha(big)
    return layer, pad * k


def fade_bottom(im, frac=0.14):
    a = im.getchannel("A")
    h0 = int(im.height * (1 - frac))
    grad = Image.new("L", (1, im.height), 255)
    for y in range(h0, im.height):
        grad.putpixel((0, y), int(255 * (1 - (y - h0) / max(1, im.height - h0))))
    grad = grad.resize(im.size)
    from PIL import ImageChops
    im = im.copy()
    im.putalpha(ImageChops.multiply(a, grad))
    return im


# ------------------------------------------------------------------ context
class Ctx:
    def __init__(self, spec, base_dir):
        self.spec, self.base = spec, Path(base_dir)
        sz = spec.get("size", "a4")
        if isinstance(sz, dict):
            self.size = sizes.get("custom", custom=(sz["w"], sz["h"], sz.get("unit", "px")))
        else:
            self.size = sizes.get(sz, {"landscape": True, "portrait": False}.get(spec.get("orientation")))
        s = self.size
        self.print = s["kind"] == "print"
        self.W, self.H = s["px_w"], s["px_h"]
        self.ppmm = s["dpi"] / 25.4 if self.print else None
        pr = spec.get("print", {})
        bleed = pr.get("bleed_mm", 3) * self.ppmm if self.print else 0
        mark = 8 * self.ppmm if self.print else 0
        self.cv = Canvas(self.W, self.H, bleed, mark, self.ppmm)
        self.u = min(self.W, self.H) / 100
        sf = s["safe"]
        self.sx0, self.sx1 = sf["left"] * self.W, self.W - sf["right"] * self.W
        self.sy0, self.sy1 = sf["top"] * self.H, self.H - sf["bottom"] * self.H
        self.safe_bottom_frac = sf["bottom"]
        self.pal, pair, self.deco = styles.resolve(spec)
        self.D, self.DW, self.B, self.BW, self.BB, self.upper = pair
        self.lang = spec.get("language", "en")
        self.rng = random.Random(spec.get("seed", spec.get("title", "x")))
        self.aspect = self.W / self.H
        self.ts = spec.get("title_scale", 1.0)
        self.xs = spec.get("text_scale", 1.0)

    def path(self, p):
        q = Path(p)
        return q if q.is_absolute() else self.base / q

    def up(self, s):
        return s.upper() if self.upper else s


# ------------------------------------------------------------------ blocks
class Block:
    flex = 0
    gap = 2.2  # u after the block

    def measure(self, c, w, k):
        return 0

    def draw(self, c, x, y, w, k, align, h=None):
        pass


class Spacer(Block):
    gap = 0

    def __init__(self, weight=1, cap=10):
        self.flex, self.cap = weight, cap


class Text(Block):
    """role: host | sub | label | body | small"""
    ROLES = {"host": (3.0, "BB", "accent", 0.16, True, 2), "sub": (4.3, "BB", "text", 0.02, False, 3),
             "label": (2.5, "BB", "accent", 0.22, True, 1), "body": (3.0, "B", "text", 0, False, 8),
             "small": (2.4, "B", "muted", 0.04, False, 3)}

    def __init__(self, text, role="body", color=None, gap=None, max_lines=None):
        self.t, self.role, self.color = text, role, color
        base, self.wk, ck, self.trk, self.caps, ml = self.ROLES[role]
        self.base, self.ck, self.ml = base, ck, max_lines or ml
        if gap is not None:
            self.gap = gap

    def _fw(self, c):
        return (c.B, c.BB) if self.wk == "BB" else (c.B, c.BW)

    def _lines(self, c, w, k):
        fam, wt = self._fw(c)
        size = self.base * c.u * k * c.xs
        t = self.t.upper() if self.caps else self.t
        return size, tp.wrap(t, fam, wt, size, w, self.trk, self.ml)

    def measure(self, c, w, k):
        size, ls = self._lines(c, w, k)
        return size * (1.0 + 1.32 * (len(ls) - 1)) + size * 0.25

    def draw(self, c, x, y, w, k, align, h=None):
        size, ls = self._lines(c, w, k)
        fam, wt = self._fw(c)
        col = self.color or c.pal[self.ck]
        ax = x + w / 2 if align == "middle" else x
        for i, l in enumerate(ls):
            c.cv.text(l, fam, wt, size, ax, y + size * 0.95 + i * size * 1.32, col, align, self.trk)


class Title(Block):
    gap = 2.0

    def __init__(self, text, base=17, max_lines=3, highlight=None):
        self.t, self.base, self.ml, self.hl = text, base, max_lines, highlight

    def _fit(self, c, w, k):
        t = c.up(self.t)
        cap_h = (c.sy1 - c.sy0) * 0.34 * c.ts  # a title never takes more than ~1/3 of the height
        lh = 0.98 if c.upper else 1.2
        best = None
        if "\n" in t:
            options = [t.split("\n")]
        else:
            options = [tp.balanced_lines(t, c.D, c.DW, 100, n) for n in range(1, self.ml + 1)]
        for ls in options:
            widest = max(tp.measure(l, c.D, c.DW, 100) for l in ls) / 100
            size = min(self.base * c.u * k * c.ts, w / widest, cap_h / (len(ls) * lh))
            if best is None or size > best[0] * 1.15:  # an extra line only if clearly bigger
                best = (size, ls)
        size, ls = best
        return max(size, 5 * c.u * k), ls

    def _top(self, c, size):
        m = tp.metrics(c.D, c.DW, size)
        return m["cap"] if c.upper else m["cap"] * 1.12  # lowercase ascenders rise above caps

    def measure(self, c, w, k):
        size, ls = self._fit(c, w, k)
        lh = size * (0.98 if c.upper else 1.12)
        desc = size * 0.12 if c.upper else size * 0.26
        return self._top(c, size) + (len(ls) - 1) * lh + desc

    def draw(self, c, x, y, w, k, align, h=None):
        size, ls = self._fit(c, w, k)
        top = self._top(c, size)
        lh = size * (0.98 if c.upper else 1.12)
        hl = self.hl if self.hl is not None else (len(ls) - 1 if len(ls) > 1 and c.deco in ("orbs", "rings") else -1)
        ax = x + w / 2 if align == "middle" else x
        for i, l in enumerate(ls):
            col = c.pal["accent"] if i == hl else c.pal["title"]
            c.cv.text(l, c.D, c.DW, size, ax, y + top + i * lh, col, align, 0.01 if c.upper else 0)


class Pill(Block):
    """Text inside a rounded box (subtitle / theme / call to action)."""

    def __init__(self, text, base=3.4, fill=None, color=None):
        self.t, self.base, self.fill, self.color = text, base, fill, color

    def measure(self, c, w, k):
        size = self.base * c.u * k * c.xs
        return size * 2.1

    def draw(self, c, x, y, w, k, align, h=None):
        size = self.base * c.u * k * c.xs
        t = self.t.upper()
        tw = min(tp.measure(t, c.B, c.BB, size, 0.08), w - size * 1.6)
        while tp.measure(t, c.B, c.BB, size, 0.08) > w - size * 1.6 and size > 4:
            size *= 0.95
        tw = tp.measure(t, c.B, c.BB, size, 0.08)
        bw, bh = tw + size * 1.6, size * 2.1
        bx = x + (w - bw) / 2 if align == "middle" else x
        c.cv.raw(f'<rect x="{bx:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="{bh / 2:.1f}" fill="{self.fill or c.pal["accent"]}"/>')
        c.cv.text(t, c.B, c.BB, size, bx + bw / 2, y + bh / 2 + size * 0.36, self.color or c.pal["on_band"], "middle", 0.08)


class Speaker(Block):
    def __init__(self, name, label="Guest speaker", role=None, photo_im=None):
        self.name, self.label, self.role, self.photo = name, label, role, photo_im

    def _sizes(self, c, k):
        return 2.5 * c.u * k * c.xs, 5.0 * c.u * k * c.xs, 2.7 * c.u * k * c.xs

    def measure(self, c, w, k):
        ls, ns, rs = self._sizes(c, k)
        h = ls * 1.6 + ns * 1.05 + (rs * 1.5 if self.role else 0)
        return max(h, ns * 2.6) if self.photo else h

    def draw(self, c, x, y, w, k, align, h=None):
        ls, ns, rs = self._sizes(c, k)
        tx, tw = x, w
        if self.photo is not None:  # small round photo next to the name
            d = ns * 2.6
            cx = x + d / 2 if align != "middle" else x + w / 2 - (d / 2 + ns * 0.4 + tp.measure(c.up(self.name), c.B, c.BB, ns) / 2)
            cid = c.cv.uid("cp")
            c.cv.defn(f'<clipPath id="{cid}"><circle cx="{cx:.1f}" cy="{y + d / 2:.1f}" r="{d / 2:.1f}"/></clipPath>')
            im = shrink(cover(self.photo.convert("RGBA"), d, d, 0.2), d, d)
            c.cv.raw(f'<circle cx="{cx:.1f}" cy="{y + d / 2:.1f}" r="{d / 2 + c.u * 0.5:.1f}" fill="{c.pal["accent"]}"/>')
            c.cv.image(im, cx - d / 2, y, d, d, clip=cid)
            tx = cx + d / 2 + ns * 0.5
            tw = w - (tx - x)
            align = "start"
            y += (d - (ls * 1.6 + ns * 1.05 + (rs * 1.5 if self.role else 0))) / 2
        ax = tx + tw / 2 if align == "middle" else tx
        c.cv.text(self.label.upper(), c.B, c.BB, ls, ax, y + ls, c.pal["accent"], align, 0.22)
        nm = c.up(self.name)
        ns2 = min(ns, ns * tw / max(1, tp.measure(nm, c.D if c.upper else c.B, c.DW if c.upper else c.BB, ns)))
        c.cv.text(nm, c.D if c.upper else c.B, c.DW if c.upper else c.BB, ns2, ax, y + ls * 1.6 + ns2 * 0.85, c.pal["title"], align, 0.01)
        if self.role:
            c.cv.text(self.role, c.B, c.BW, rs, ax, y + ls * 1.6 + ns2 * 1.05 + rs * 1.15, c.pal["muted"], align)


class Info(Block):
    """Date / time / venue rows with icons. inline=True puts them in one row with dots."""

    def __init__(self, items, inline=False, cards=False):
        self.items, self.inline, self.cards = items, inline, cards

    def _fs(self, c, k):
        return 3.4 * c.u * k * c.xs

    def _rows(self, c, w, k):
        fs = self._fs(c, k)
        r = fs * 0.78
        out = []
        for ic, t in self.items:
            ls = tp.wrap(t, c.B, c.BB, fs, w - r * 2 - fs * 0.6, 0, 2)
            out.append((ic, ls))
        return fs, r, out

    def measure(self, c, w, k):
        fs, r, rows = self._rows(c, w, k)
        if self.cards:
            return fs * 5.2 if self._cards_fit(c, w, k) else sum(fs * (2.2 + 1.3 * (len(l) - 1)) for _, l in rows) + fs * 0.4 * len(rows)
        if self.inline and self._inline_w(c, k) <= w:
            return fs * 1.6
        return sum(max(r * 2, fs * (1.25 + 1.3 * (len(l) - 1))) + fs * 0.55 for _, l in rows)

    def _inline_w(self, c, k):
        fs = self._fs(c, k)
        return sum(tp.measure(t, c.B, c.BB, fs) for _, t in self.items) + fs * 2.4 * (len(self.items) - 1)

    def _cards_fit(self, c, w, k):
        fs = self._fs(c, k)
        n = len(self.items)
        cw = (w - fs * 0.8 * (n - 1)) / n
        return all(tp.measure(t, c.B, c.BB, fs * 0.92) <= cw * 2 - fs * 2 for _, t in self.items) and cw > fs * 7

    def draw(self, c, x, y, w, k, align, h=None):
        fs, r, rows = self._rows(c, w, k)
        P = c.pal
        if self.cards and self._cards_fit(c, w, k):
            n = len(self.items)
            g = fs * 0.8
            cw = (w - g * (n - 1)) / n
            for i, (ic, t) in enumerate(self.items):
                cx = x + i * (cw + g)
                c.cv.raw(f'<rect x="{cx:.1f}" y="{y:.1f}" width="{cw:.1f}" height="{fs * 5.2:.1f}" rx="{fs * 0.6:.1f}" fill="{P["title"]}" fill-opacity="0.08" stroke="{P["accent"]}" stroke-width="{c.u * 0.3:.1f}"/>')
                c.cv.icon(ic, cx + cw / 2, y + fs * 1.15, r * 0.8, P["accent"], P["on_band"])
                ls = tp.wrap(t, c.B, c.BB, fs * 0.92, cw - fs * 1.0, 0, 2)
                for j, l in enumerate(ls):
                    c.cv.text(l, c.B, c.BB, fs * 0.92 * (0.9 if len(ls) > 1 else 1), cx + cw / 2, y + fs * (3.35 + j * 1.15) - (fs * 0.35 if len(ls) > 1 else 0), P["title"], "middle")
            return
        if self.inline and self._inline_w(c, k) <= w:
            tot = self._inline_w(c, k)
            cx = x + (w - tot) / 2 if align == "middle" else x
            for i, (ic, t) in enumerate(self.items):
                tw = c.cv.text(t, c.B, c.BB, fs, cx, y + fs * 1.1, P["title"])
                cx += tw
                if i < len(self.items) - 1:
                    c.cv.raw(f'<circle cx="{cx + fs * 1.2:.1f}" cy="{y + fs * 0.75:.1f}" r="{fs * 0.18:.1f}" fill="{P["accent"]}"/>')
                    cx += fs * 2.4
            return
        cy = y
        for ic, ls in rows:
            hgt = max(r * 2, fs * (1.25 + 1.3 * (len(ls) - 1)))
            if align == "middle":
                lw = max(tp.measure(l, c.B, c.BB, fs) for l in ls) + r * 2 + fs * 0.6
                ix = x + (w - lw) / 2
            else:
                ix = x
            c.cv.icon(ic, ix + r, cy + hgt / 2, r, P["accent"], P["on_band"])
            ty = cy + hgt / 2 - (len(ls) - 1) * fs * 0.65 + fs * 0.36
            for j, l in enumerate(ls):
                c.cv.text(l, c.B, c.BB, fs, ix + r * 2 + fs * 0.6, ty + j * fs * 1.3, P["title"])
            cy += hgt + fs * 0.55


class Bullets(Block):
    def __init__(self, items):
        self.items = items

    def _fs(self, c, k):
        return 3.0 * c.u * k * c.xs

    def measure(self, c, w, k):
        fs = self._fs(c, k)
        n = sum(len(tp.wrap(t, c.B, c.BW, fs, w - fs * 1.6, 0, 3)) for t in self.items)
        return n * fs * 1.35 + len(self.items) * fs * 0.35

    def draw(self, c, x, y, w, k, align, h=None):
        fs = self._fs(c, k)
        cy = y
        for t in self.items:
            ls = tp.wrap(t, c.B, c.BW, fs, w - fs * 1.6, 0, 3)
            c.cv.raw(f'<rect x="{x:.1f}" y="{cy + fs * 0.42:.1f}" width="{fs * 0.55:.1f}" height="{fs * 0.55:.1f}" rx="{fs * 0.12:.1f}" fill="{c.pal["accent"]}"/>')
            for j, l in enumerate(ls):
                c.cv.text(l, c.B, c.BW, fs, x + fs * 1.4, cy + fs * 0.95 + j * fs * 1.35, c.pal["text"])
            cy += len(ls) * fs * 1.35 + fs * 0.35


class Photo(Block):
    """Flexible photo block for stacked layouts (takes the free height)."""
    flex = 12
    gap = 3.6

    def __init__(self, im, speaker=None, minfrac=0.24):
        self.im, self.speaker, self.minfrac = im, speaker, minfrac

    def measure(self, c, w, k):
        return (c.sy1 - c.sy0) * self.minfrac

    def draw(self, c, x, y, w, k, align, h=None):
        draw_photo(c, self.im, x, y, w, h, "center", stacked=True, speaker=self.speaker, k=k)


def stack(c, blocks, x, y, w, h, align="start", kmax=1.25, kmin=0.5, valign="center"):
    k = kmax
    while True:
        heights = [b.measure(c, w, k) for b in blocks]
        total = sum(heights) + sum(b.gap * c.u * k for b in blocks[:-1])
        if total <= h or k <= kmin:
            break
        k -= 0.04
    if total > h * 1.01:
        c.cv.warn.append(f"text does not fit at minimum size (needs {total / h:.0%} of the space): shorten text")
    free = max(0, h - total)
    flex = [b for b in blocks if b.flex]
    extra = {}
    if flex:
        tw = sum(b.flex for b in flex)
        for b in flex:
            e = free * b.flex / tw
            if isinstance(b, Spacer):
                e = min(e, b.cap * c.u)
            extra[id(b)] = e
        free -= sum(extra.values())
    cy = y + (free / 2 if valign == "center" else (free if valign == "bottom" else 0))
    for b, bh in zip(blocks, heights):
        bh2 = bh + extra.get(id(b), 0)
        b.draw(c, x, cy, w, k, align, bh2)
        cy += bh2 + b.gap * c.u * k
    return k


# ------------------------------------------------------------------ pieces
def background(c):
    P, cv, W, H, b = c.pal, c.cv, c.W, c.H, c.cv.bleed
    gid = cv.uid("bg")
    ang = {"orbs": (0, 0, 1, 1), "rings": (0, 0, 0, 1), "border": (0, 0, 0, 1), "arcs": (0, 0, 1, 1)}.get(c.deco, (0, 0, 1, 1))
    cv.defn(f'<linearGradient id="{gid}" x1="{ang[0]}" y1="{ang[1]}" x2="{ang[2]}" y2="{ang[3]}"><stop offset="0" stop-color="{P["bg"]}"/><stop offset="1" stop-color="{P["bg2"]}"/></linearGradient>')
    cv.raw(f'<rect x="{-b:.1f}" y="{-b:.1f}" width="{W + 2 * b:.1f}" height="{H + 2 * b:.1f}" fill="url(#{gid})"/>')
    bgs = c.spec.get("background", {})
    if bgs.get("photo"):
        im = load_image(c.path(bgs["photo"]))
        im = cover(im, W + 2 * b, H + 2 * b, bgs.get("focus_y", 0.4))
        cv.image(im, -b, -b, W + 2 * b, H + 2 * b)
        oid = cv.uid("ov")
        o = bgs.get("overlay", 0.72)
        cv.defn(f'<linearGradient id="{oid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{P["bg"]}" stop-opacity="{o}"/><stop offset="1" stop-color="{P["bg2"]}" stop-opacity="{min(1, o + 0.15)}"/></linearGradient>')
        cv.raw(f'<rect x="{-b:.1f}" y="{-b:.1f}" width="{W + 2 * b:.1f}" height="{H + 2 * b:.1f}" fill="url(#{oid})"/>')
    decorate(c)
    dk = c.spec.get("darken", 0)
    if dk:
        cv.raw(f'<rect x="{-b:.1f}" y="{-b:.1f}" width="{W + 2 * b:.1f}" height="{H + 2 * b:.1f}" fill="#000" opacity="{dk}"/>')


def glow_circle(c, cx, cy, r, color, op=0.6):
    gid = c.cv.uid("gl")
    c.cv.defn(f'<radialGradient id="{gid}"><stop offset="0" stop-color="{color}" stop-opacity="{op}"/><stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient>')
    c.cv.raw(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="url(#{gid})"/>')


def decorate(c):
    P, W, H, u, R = c.pal, c.W, c.H, c.u, c.rng
    side = c.spec.get("photo_side", "right")
    fx = (lambda v: W - v) if side == "left" else (lambda v: v)
    if c.deco == "orbs":
        glow_circle(c, fx(W * 0.9), H * 0.08, max(W, H) * 0.45, P["pop"], 0.55)
        glow_circle(c, fx(W * 0.05), H * 0.95, max(W, H) * 0.5, P["accent"], 0.28)
        glow_circle(c, fx(W * 0.15), H * 0.3, max(W, H) * 0.25, P["bg2"], 0.6)
        pts = []
        for _ in range(22):  # confetti only in the outer edges, never behind text
            if R.random() < 0.5:
                x, y = R.choice([R.uniform(0, W * 0.05), R.uniform(W * 0.95, W)]), R.uniform(0, H)
            else:
                x, y = R.uniform(0, W), R.choice([R.uniform(0, H * 0.035), R.uniform(H * 0.965, H)])
            r = R.uniform(0.25, 0.8) * u
            pts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{R.choice([P["accent"], P["pop"], P["title"]])}" opacity="{R.uniform(.25, .7):.2f}"/>')
        c.cv.raw("".join(pts))
        sw = u * 6
        c.cv.raw(f'<path d="M{fx(-W * .1):.1f} {H * .62:.1f} L{fx(W * 1.1):.1f} {H * .40:.1f}" stroke="{P["pop"]}" stroke-width="{sw:.1f}" opacity="0.10"/>')
    elif c.deco == "rings":
        cx, cy = fx(W * 0.92), H * 0.1
        for i in range(5):
            c.cv.raw(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{(14 + i * 7) * u:.1f}" fill="none" stroke="{P["accent"]}" stroke-width="{u * 0.35:.1f}" opacity="{0.35 - i * 0.05:.2f}"/>')
        glow_circle(c, fx(W * 0.1), H * 0.85, max(W, H) * 0.4, P["accent"], 0.18)
        dots = []
        for i in range(6):
            for j in range(6):
                dots.append(f'<circle cx="{fx(W * 0.06 + i * 2.6 * u):.1f}" cy="{H * 0.5 + j * 2.6 * u:.1f}" r="{u * 0.32:.1f}" fill="{P["muted"]}" opacity="0.35"/>')
        c.cv.raw("".join(dots))
    elif c.deco == "border":
        glow_circle(c, W / 2, H * 0.35, max(W, H) * 0.6, P["bg2"], 0.8)
        for inset, sw in ((2.2, 0.35), (3.0, 0.15)):
            c.cv.raw(f'<rect x="{inset * u:.1f}" y="{inset * u:.1f}" width="{W - 2 * inset * u:.1f}" height="{H - 2 * inset * u:.1f}" fill="none" stroke="{P["accent"]}" stroke-width="{sw * u:.1f}"/>')
        for x, y in ((2.6 * u, 2.6 * u), (W - 2.6 * u, 2.6 * u), (2.6 * u, H - 2.6 * u), (W - 2.6 * u, H - 2.6 * u)):
            s = 1.6 * u
            c.cv.raw(f'<path d="M{x:.1f} {y - s:.1f}L{x + s:.1f} {y:.1f}L{x:.1f} {y + s:.1f}L{x - s:.1f} {y:.1f}z" fill="{P["accent"]}"/>')
    elif c.deco == "arcs":
        c.cv.raw(f'<circle cx="{fx(W * 1.0):.1f}" cy="{H * 0.0:.1f}" r="{max(W, H) * 0.42:.1f}" fill="{P["bg2"]}"/>')
        for i in range(3):
            c.cv.raw(f'<circle cx="{fx(W * 1.0):.1f}" cy="{0:.1f}" r="{max(W, H) * (0.46 + i * 0.035):.1f}" fill="none" stroke="{P["accent"]}" stroke-width="{u * 0.2:.1f}" opacity="{0.6 - i * 0.15:.2f}"/>')
        c.cv.raw(f'<circle cx="{fx(0):.1f}" cy="{H:.1f}" r="{max(W, H) * 0.25:.1f}" fill="{P["accent"]}" opacity="0.10"/>')


def place_logos(c, top_y, bottom_y, which="top"):
    """Draw the top (or bottom) logos by position. Returns (height used at top, height used at bottom)."""
    logos = [l for l in c.spec.get("logos", []) if l.get("pos", "top-left").startswith("bottom") == (which == "bottom")]
    if not logos:
        return 0, 0
    lh = 7.5 * c.u * c.spec.get("logo_scale", 1.0)
    groups = {}
    for lg in logos:
        groups.setdefault(lg.get("pos", "top-left"), []).append(lg)
    used_top = used_bot = 0
    for pos, items in groups.items():
        big = 1.6 if pos == "center" else 1.0
        h = lh * big
        ims = []
        for lg in items:
            im = trim_alpha(load_image(c.path(lg["file"])))
            sc = lg.get("scale", 1.0)
            hh = h * sc
            ww = im.width * hh / im.height
            if ww > (c.sx1 - c.sx0) * 0.4:  # very wide logo
                ww = (c.sx1 - c.sx0) * 0.4
                hh = im.height * ww / im.width
            ims.append((im, ww, hh, needs_chip(im)))
        gap = 2 * c.u
        tot = sum(w for _, w, _, _ in ims) + gap * (len(ims) - 1)
        hmax = max(hh for _, _, hh, _ in ims)
        if pos in ("top-left", "bottom-left"):
            x = c.sx0
        elif pos in ("top-right", "bottom-right"):
            x = c.sx1 - tot
        else:
            x = (c.W - tot) / 2
        y = top_y if pos.startswith("top") or pos == "center" else bottom_y - hmax
        for im, w, hh, chip in ims:
            yy = y + (hmax - hh) / 2
            if chip:
                p = hh * 0.12
                c.cv.raw(f'<rect x="{x - p:.1f}" y="{yy - p:.1f}" width="{w + 2 * p:.1f}" height="{hh + 2 * p:.1f}" rx="{p:.1f}" fill="#FFFFFF"/>')
            im2 = shrink(im, w * 1.0, hh * 1.0)
            if im.width < w * 0.6:
                c.cv.warn.append(f"logo {Path(items[0]['file']).name} is low resolution for this size")
            c.cv.image(im2, x, yy, w, hh)
            x += w + gap
        if pos.startswith("top") or pos == "center":
            used_top = max(used_top, hmax + 2.5 * c.u)
        else:
            used_bot = max(used_bot, hmax + 2.0 * c.u)
    return used_top, used_bot


def contact_items(c):
    out = []
    for ct in c.spec.get("contacts", []):
        t = ct["type"]
        v = ct["value"]
        if t in SOCIAL_PREFIX:
            v = f'{SOCIAL_PREFIX[t]} {v}'
        if ct.get("label"):
            v = f'{ct["label"]}: {v}'
        out.append((CONTACT_ICON.get(t, "at"), v))
    return out


def contacts_band(c):
    """Draw the contact bar at the bottom; return the y where content must stop."""
    items = contact_items(c)
    if not items:
        return c.sy1
    P, u = c.pal, c.u
    fs = 2.75 * u * c.xs
    r = fs * 0.72
    pad = fs * 0.9
    maxw = c.sx1 - c.sx0 - 2 * pad
    widths = [r * 2 + fs * 0.45 + tp.measure(t, c.B, c.BB, fs) for _, t in items]
    gap = fs * 1.6
    while max(widths) > maxw and fs > u:
        fs *= 0.92
        r = fs * 0.72
        widths = [r * 2 + fs * 0.45 + tp.measure(t, c.B, c.BB, fs) for _, t in items]
    rows, cur, cw = [], [], 0
    for it, w in zip(items, widths):
        if cur and cw + gap + w > maxw:
            rows.append((cur, cw))
            cur, cw = [], 0
        cw += (gap if cur else 0) + w
        cur.append((it, w))
    rows.append((cur, cw))
    row_h = max(r * 2, fs * 1.4) + fs * 0.5
    content_h = len(rows) * row_h - fs * 0.5
    pill = c.safe_bottom_frac > 0.1
    b = c.cv.bleed
    if pill:
        top = c.sy1 - content_h - 2 * pad
        c.cv.raw(f'<rect x="{c.sx0:.1f}" y="{top:.1f}" width="{c.sx1 - c.sx0:.1f}" height="{content_h + 2 * pad:.1f}" rx="{pad:.1f}" fill="{P["band"]}"/>')
    else:
        top = c.H - max(pad * 1.6, (c.H - c.sy1) * 0.55) - content_h - pad
        c.cv.raw(f'<rect x="{-b:.1f}" y="{top - pad:.1f}" width="{c.W + 2 * b:.1f}" height="{c.H - top + pad + b:.1f}" fill="{P["band"]}"/>')
        c.cv.raw(f'<rect x="{-b:.1f}" y="{top - pad - u * 0.6:.1f}" width="{c.W + 2 * b:.1f}" height="{u * 0.6:.1f}" fill="{P["pop"]}"/>')
        top -= pad
    y = top + pad
    for row, rw in rows:
        x = (c.W - rw) / 2
        for (ic, t), w in row:
            c.cv.icon(ic, x + r, y + row_h / 2 - fs * 0.25, r, P["on_band"], P["band"])
            c.cv.text(t, c.B, c.BB, fs, x + r * 2 + fs * 0.45, y + row_h / 2 - fs * 0.25 + fs * 0.36, P["on_band"])
            x += w + gap
        y += row_h
    return top - 2 * u


def draw_photo(c, im, x, y, w, h, side, stacked=False, speaker=None, k=1.0, anchor_bottom=None):
    """Cutout -> halo + glow + person. Normal photo -> arch frame."""
    P, u = c.pal, c.u
    if im is None:
        return
    if is_cutout(im):
        im = trim_alpha(im)
        sc = min(w / im.width, h / im.height)
        dw, dh = im.width * sc, im.height * sc
        px = x + (w - dw) / 2 if side == "center" else (x + w - dw if side == "right" else x)
        py = y + h - dh
        hr = min(dw * 0.5, dh * 0.42)
        hcx, hcy = px + dw / 2, py + dh * 0.45
        c.cv.raw(f'<circle cx="{hcx:.1f}" cy="{hcy:.1f}" r="{hr:.1f}" fill="{P["pop"]}" opacity="0.92"/>')
        c.cv.raw(f'<circle cx="{hcx:.1f}" cy="{hcy:.1f}" r="{hr * 1.08:.1f}" fill="none" stroke="{P["accent"]}" stroke-width="{u * 0.45:.1f}"/>')
        if stacked:
            im = fade_bottom(im, 0.10)
        if im.width < dw * 0.6:
            c.cv.warn.append("speaker photo is low resolution for this size (print may look soft)")
        gl, pad = soft_layer(im, P["accent"], max(4, dw * 0.025))
        s2 = dw / im.width
        c.cv.image(shrink(gl, gl.width * s2, gl.height * s2), px - pad * s2, py - pad * s2, gl.width * s2, gl.height * s2, opacity=0.55)
        c.cv.image(shrink(im, dw, dh), px, py, dw, dh)
        bottom = py + dh
    else:
        ar = 0.8
        fw, fh = (w, w / ar) if w / ar <= h else (h * ar, h)
        fx = x + (w - fw) / 2 if side == "center" else (x + w - fw if side == "right" else x)
        fy = y + (h - fh) / 2 if stacked else y + h - fh
        rad = fw / 2
        cid = c.cv.uid("ph")
        d = f"M{fx:.1f} {fy + fh:.1f}V{fy + rad:.1f}A{rad:.1f} {rad:.1f} 0 0 1 {fx + fw:.1f} {fy + rad:.1f}V{fy + fh:.1f}z"
        c.cv.raw(f'<path d="{d}" fill="none" stroke="{P["accent"]}" stroke-width="{u * 0.9:.1f}" transform="translate({u * 1.2:.1f} {-u * 1.2:.1f})"/>')
        c.cv.defn(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
        crop = cover(im, fw, fh, 0.25)
        if crop.width < fw * 0.6:
            c.cv.warn.append("speaker photo is low resolution for this size (print may look soft)")
        c.cv.image(shrink(crop, fw, fh), fx, fy, fw, fh, clip=cid)
        bottom = fy + fh
        px, dw = fx, fw
    if speaker and stacked:  # name ribbon over the bottom of the photo
        ls, ns = 2.3 * u * k * c.xs, 4.4 * u * k * c.xs
        nm = c.up(speaker["name"])
        fam, wt = (c.D, c.DW) if c.upper else (c.B, c.BB)
        tw = max(tp.measure(nm, fam, wt, ns), tp.measure(speaker.get("label", "Guest speaker").upper(), c.B, c.BB, ls, 0.22))
        bw = min(tw + ns * 1.6, c.sx1 - c.sx0)
        if tw + ns * 1.6 > bw:
            ns *= (bw - ns * 1.6) / tw
        bh = ls * 1.5 + ns * 1.25
        bx = px + dw / 2 - bw / 2
        bx = max(c.sx0, min(bx, c.sx1 - bw))
        by = bottom - bh * 0.85
        c.cv.raw(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="{u * 1.2:.1f}" fill="{P["band"]}"/>')
        c.cv.text(speaker.get("label", "Guest speaker").upper(), c.B, c.BB, ls, bx + bw / 2, by + ls * 1.35, P["on_band"], "middle", 0.22, opacity=0.85)
        c.cv.text(nm, fam, wt, ns, bx + bw / 2, by + ls * 1.5 + ns * 0.95, P["on_band"], "middle")


# ------------------------------------------------------------------ layouts
def info_items(c, short=False):
    s = c.spec
    items = []
    if s.get("date"):
        dt = styles.format_date(s["date"], c.lang, short)
        items.append(("calendar", c.up(dt)))
    if s.get("start"):
        items.append(("clock", styles.format_time(s["start"], s.get("end"), s.get("time_format", "12h"))))
    if s.get("venue"):
        items.append(("pin", s["venue"]))
    for extra in s.get("extra_info", []):
        items.append((extra.get("icon", "ticket"), extra["text"]))
    return items


def speaker_photo(c):
    sp = c.spec.get("speaker") or {}
    if sp.get("photo"):
        return load_image(c.path(sp["photo"]))
    return None


def head_blocks(c, sub_as_pill):
    s = c.spec
    bl = []
    if s.get("host_line"):
        bl.append(Text(s["host_line"], "host", gap=1.4))
    bl.append(Title(s.get("title", "Title"), highlight=s.get("highlight_line")))
    if s.get("subtitle"):
        bl.append(Pill(s["subtitle"]) if sub_as_pill else Text(s["subtitle"], "sub"))
    return bl


def tail_blocks(c, inline=False, cards=False, short=False):
    s = c.spec
    bl = []
    items = info_items(c, short)
    if items:
        bl.append(Info(items, inline=inline, cards=cards))
    if s.get("body"):
        bl.append(Text(s["body"], "body"))
    if s.get("bullets"):
        bl.append(Bullets(s["bullets"]))
    if s.get("cta"):
        bl.append(Pill(s["cta"], 3.2, fill=c.pal["pop"], color=styles.readable_on(c.pal["pop"], "#FFFFFF")))
    return bl


def layout_event(c):
    s = c.spec
    background(c)
    top_used, _ = place_logos(c, c.sy0, 0)
    bottom = contacts_band(c)
    _, bot_used = place_logos_bottom(c, bottom)
    bottom -= bot_used
    top = c.sy0 + top_used
    lay = s.get("layout", "split")
    photo = speaker_photo(c)
    sp = s.get("speaker")
    side = s.get("photo_side", "right")
    youthful = c.deco in ("orbs",)
    if lay == "split" and photo is not None:
        tall = c.aspect < 0.62
        if tall:  # header across the top, then text + photo side by side
            hb = head_blocks(c, youthful)
            hh_k = stack_measure(c, hb, c.sx1 - c.sx0, (bottom - top) * 0.42)
            stack(c, hb, c.sx0, top, c.sx1 - c.sx0, hh_k, "start", valign="top")
            top += hh_k + 2 * c.u
        colw = (c.sx1 - c.sx0) * (0.52 if tall else 0.54)
        pw = c.W * (0.5 if tall else 0.46)
        if side == "right":
            px = c.W - pw
            tx = c.sx0
            colw = min(colw, px - c.u * 2 - tx)
        else:
            px = 0
            colw = min(colw, c.sx1 - (pw + c.u * 2))
            tx = c.sx1 - colw
        # photo sits on the contact band, may run to the trim edge
        pbottom = (bottom + 2 * c.u) if contact_items(c) else (c.H + c.cv.bleed)  # sit on the band or the edge
        draw_photo(c, photo, px, top, pw, pbottom - top, side)
        blocks = ([] if tall else head_blocks(c, youthful) + [Spacer(1, 6)])
        if sp:
            blocks.append(Speaker(sp["name"], sp.get("label", "Guest speaker"), sp.get("role")))
            blocks.append(Spacer(1, 4))
        narrow = colw < 48 * c.u
        blocks += tail_blocks(c, short=narrow)
        stack(c, blocks, tx, top, colw, bottom - top, "start")
    elif lay == "bold" or photo is None:
        blocks = head_blocks(c, True)
        blocks[-1].gap = 3
        blocks.append(Spacer(1, 6))
        if sp:
            blocks.append(Speaker(sp["name"], sp.get("label", "Guest speaker"), sp.get("role"), photo_im=photo))
            blocks.append(Spacer(1, 4))
        blocks += tail_blocks(c, cards=True, short=True)
        for b in blocks:
            if isinstance(b, Title):
                b.base = 22
        stack(c, blocks, c.sx0, top, c.sx1 - c.sx0, bottom - top, "middle")
    else:  # hero
        blocks = head_blocks(c, youthful)
        blocks.append(Photo(photo, speaker=sp))
        blocks += tail_blocks(c, inline=c.aspect > 0.9)
        stack(c, blocks, c.sx0, top, c.sx1 - c.sx0, bottom - top, "middle")


def stack_measure(c, blocks, w, maxh):
    k = 1.25
    while k > 0.5:
        tot = sum(b.measure(c, w, k) for b in blocks) + sum(b.gap * c.u * k for b in blocks[:-1])
        if tot <= maxh:
            return tot
        k -= 0.04
    return maxh


def place_logos_bottom(c, bottom):
    return place_logos(c, 0, bottom, "bottom")


def layout_thumbnail(c):
    s, P, u, W, H = c.spec, c.pal, c.u, c.W, c.H
    background(c)
    side = s.get("photo_side", "right")
    photo = speaker_photo(c)
    if photo is not None:
        im = trim_alpha(photo) if is_cutout(photo) else photo
        ph = H * 0.98
        sc = ph / im.height
        pw = min(im.width * sc, W * 0.52)
        sc = pw / im.width
        ph = im.height * sc
        px = W - pw - W * 0.01 if side == "right" else W * 0.01
        glow_circle(c, px + pw / 2, H - ph * 0.55, max(pw, ph) * 0.62, P["pop"], 0.75)
        if is_cutout(photo):
            ol, pad = soft_layer(im, "#FFFFFF", 0, grow=max(6, pw * 0.02))
            sh, pad2 = soft_layer(im, "#000000", max(6, pw * 0.03))
            k2 = pw / im.width
            c.cv.image(shrink(sh, sh.width * k2, sh.height * k2), px - pad2 * k2 + u, H - ph - pad2 * k2 + u, sh.width * k2, sh.height * k2, opacity=0.5)
            c.cv.image(shrink(ol, ol.width * k2, ol.height * k2), px - pad * k2, H - ph - pad * k2, ol.width * k2, ol.height * k2)
            c.cv.image(shrink(im, pw, ph), px, H - ph, pw, ph)
        else:
            crop = cover(im, pw, H, 0.3)
            c.cv.image(shrink(crop, pw, H), px, 0, pw, H)
    top_used, _ = place_logos(c, c.sy0, 0)
    tx0 = c.sx0 if side == "right" else W * 0.48
    tx1 = W * 0.56 if side == "right" else c.sx1
    tw = tx1 - tx0
    lines = s.get("title", "BIG IDEA").split("\n") if "\n" in s.get("title", "") else None
    t = c.up(s.get("title", "BIG IDEA"))
    size, ls = tp.fit_title(t, c.D, c.DW, tw, 30 * u * c.ts, 8 * u, 3) if not lines else tp.fit_title(c.up(s["title"]), c.D, c.DW, tw, 30 * u * c.ts, 8 * u, 3)
    m = tp.metrics(c.D, c.DW, size)
    lh = m["cap"] * 1.32
    hl = s.get("highlight_line", len(ls) - 1 if len(ls) > 1 else -1)
    badge_h = 0
    if s.get("badge"):
        badge_h = 7 * u
    block_h = len(ls) * lh + badge_h + (5 * u if s.get("subtitle") else 0)
    y = max(c.sy0 + top_used, (H - block_h) / 2 - H * 0.04)
    if s.get("badge"):
        bt = s["badge"].upper()
        bs = 3.4 * u
        bw = tp.measure(bt, c.B, c.BB, bs, 0.1) + bs * 1.6
        c.cv.raw(f'<rect x="{tx0:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bs * 1.9:.1f}" rx="{bs * 0.35:.1f}" fill="{P["pop"]}"/>')
        c.cv.text(bt, c.B, c.BB, bs, tx0 + bw / 2, y + bs * 1.3, styles.readable_on(P["pop"], "#FFFFFF"), "middle", 0.1)
        y += badge_h
    for i, l in enumerate(ls):
        base = y + m["cap"] + i * lh
        lw = tp.measure(l, c.D, c.DW, size, 0.01)
        if i == hl:
            padx = size * 0.12
            c.cv.raw(f'<rect x="{tx0 - padx:.1f}" y="{base - m["cap"] - size * 0.09:.1f}" width="{lw + 2 * padx:.1f}" height="{m["cap"] + size * 0.18:.1f}" rx="{size * 0.05:.1f}" fill="{P["accent"]}" transform="rotate(-1.5 {tx0 + lw / 2:.1f} {base:.1f})"/>')
            c.cv.text(l, c.D, c.DW, size, tx0, base, styles.readable_on(P["accent"], P["bg"]), "start", 0.01)
        else:
            c.cv.text(l, c.D, c.DW, size, tx0, base, P["title"], "start", 0.01, stroke=P["bg"], sw=size * 0.09, shadow=(u * 0.5, u * 0.7, "#000000", 0.45))
    if s.get("subtitle"):
        c.cv.text(s["subtitle"], c.B, c.BB, 3.8 * u, tx0, y + len(ls) * lh + 4.2 * u, P["text"], "start", 0.02)


def layout_certificate(c):
    s, P, u, W, H = c.spec, c.pal, c.u, c.W, c.H
    b = c.cv.bleed
    dark = P["bg"] if styles.luminance(P["bg"]) < 0.3 else P["title"]
    paper = s.get("paper", "#FFFDF7")
    c.cv.raw(f'<rect x="{-b:.1f}" y="{-b:.1f}" width="{W + 2 * b:.1f}" height="{H + 2 * b:.1f}" fill="{dark}"/>')
    m = 4 * u
    c.cv.raw(f'<rect x="{m:.1f}" y="{m:.1f}" width="{W - 2 * m:.1f}" height="{H - 2 * m:.1f}" fill="{paper}"/>')
    for inset, sw in ((m + 1.6 * u, 0.4), (m + 2.4 * u, 0.15)):
        c.cv.raw(f'<rect x="{inset:.1f}" y="{inset:.1f}" width="{W - 2 * inset:.1f}" height="{H - 2 * inset:.1f}" fill="none" stroke="{P["accent"]}" stroke-width="{sw * u:.1f}"/>')
    for x, y in ((m + 1.6 * u, m + 1.6 * u), (W - m - 1.6 * u, m + 1.6 * u), (m + 1.6 * u, H - m - 1.6 * u), (W - m - 1.6 * u, H - m - 1.6 * u)):
        q = 2.2 * u
        c.cv.raw(f'<path d="M{x:.1f} {y - q:.1f}L{x + q:.1f} {y:.1f}L{x:.1f} {y + q:.1f}L{x - q:.1f} {y:.1f}z" fill="{P["accent"]}"/>')
    ink = dark
    cpal = dict(P, title=ink, text="#333333", muted="#666666", accent=P["accent"])
    c.pal = cpal
    c.sx0, c.sx1, c.sy0, c.sy1 = m + 7 * u, W - m - 7 * u, m + 5 * u, H - m - 5 * u
    top_used, _ = place_logos(c, c.sy0, 0)
    cx = W / 2
    y = c.sy0 + top_used + 3 * u
    title = s.get("title", "Certificate").upper()
    ts = min(11 * u, (c.sx1 - c.sx0) * 0.8 / max(1, tp.measure(title, c.D, c.DW, 1, 0.12)))
    c.cv.text(title, c.D, c.DW, ts, cx, y + ts * 0.8, ink, "middle", 0.12)
    y += ts * 1.1
    if s.get("subtitle"):
        c.cv.text(s["subtitle"].upper(), c.B, c.BB, 3.4 * u, cx, y + 3.4 * u, P["accent"], "middle", 0.3)
        y += 6.5 * u
    c.cv.text(s.get("presented_line", "This certificate is proudly presented to"), c.B, c.BW, 3.2 * u, cx, y + 4 * u, "#555555", "middle")
    y += 6 * u
    name = s.get("recipient", "Full Name")
    nf = ("Playfair Display", 700)
    ns = min(10 * u, (c.sx1 - c.sx0) * 0.8 / max(1, tp.measure(name, *nf, 1)))
    c.cv.text(name, nf[0], nf[1], ns, cx, y + ns * 0.85, P["accent"] if styles.contrast(P["accent"], paper) > 3 else ink, "middle")
    y += ns * 1.15
    c.cv.raw(f'<rect x="{cx - 30 * u:.1f}" y="{y:.1f}" width="{60 * u:.1f}" height="{u * 0.25:.1f}" fill="{P["accent"]}"/>')
    y += 3 * u
    if s.get("reason"):
        for i, l in enumerate(tp.wrap(s["reason"], c.B, c.BW, 3.1 * u, (c.sx1 - c.sx0) * 0.75, 0, 3)):
            c.cv.text(l, c.B, c.BW, 3.1 * u, cx, y + 3.4 * u + i * 4.3 * u, "#333333", "middle")
    sigs = s.get("signatories", [])
    by = c.sy1 - 3 * u
    slots = ([("date", s["date"])] if s.get("date") else []) + [("sig", g) for g in sigs]
    if slots:
        n = len(slots) + 1  # +1 for the seal in the middle
        sw = (c.sx1 - c.sx0) / n
        mid = n // 2
        i2 = 0
        for i in range(n):
            x0 = c.sx0 + i * sw
            if i == mid:
                seal(c, x0 + sw / 2, by - 6 * u, 6.5 * u)
                continue
            kind, val = slots[i2]
            i2 += 1
            c.cv.raw(f'<rect x="{x0 + sw * 0.12:.1f}" y="{by - 5 * u:.1f}" width="{sw * 0.76:.1f}" height="{u * 0.2:.1f}" fill="#444444"/>')
            if kind == "date":
                c.cv.text(styles.format_date(val, c.lang), c.B, c.BB, 2.6 * u, x0 + sw / 2, by - 6.2 * u, "#333333", "middle")
                c.cv.text("Date", c.B, c.BW, 2.3 * u, x0 + sw / 2, by - 2.2 * u, "#666666", "middle")
            else:
                c.cv.text(val["name"], c.B, c.BB, 2.6 * u, x0 + sw / 2, by - 2.0 * u, "#333333", "middle")
                if val.get("title"):
                    c.cv.text(val["title"], c.B, c.BW, 2.2 * u, x0 + sw / 2, by + 1.0 * u, "#666666", "middle")
    else:
        seal(c, W / 2, by - 6 * u, 6.5 * u)


def seal(c, cx, cy, r):
    P = c.pal
    pts = []
    n = 24
    for i in range(n * 2):
        a = math.pi * i / n
        rr = r if i % 2 == 0 else r * 0.86
        pts.append(f"{cx + rr * math.cos(a):.1f},{cy + rr * math.sin(a):.1f}")
    c.cv.raw(f'<polygon points="{" ".join(pts)}" fill="{P["accent"]}"/>')
    c.cv.raw(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 0.72:.1f}" fill="none" stroke="#FFFFFF" stroke-width="{r * 0.04:.1f}" opacity="0.8"/>')
    c.cv.raw(f'<path d="M{cx - r * .3:.1f} {cy:.1f}l{r * .2:.1f} {r * .22:.1f}l{r * .42:.1f} {-r * .45:.1f}" stroke="#FFFFFF" stroke-width="{r * .1:.1f}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')


LAYOUTS = {"event": layout_event, "flyer": layout_event, "poster": layout_event, "social": layout_event,
           "banner": layout_event, "thumbnail": layout_thumbnail, "certificate": layout_certificate}


def compose(spec, base_dir):
    c = Ctx(spec, base_dir)
    LAYOUTS.get(spec.get("type", "event"), layout_event)(c)
    return c
