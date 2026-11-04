"""Engine A drawing layer: world coordinates -> pixels, style-aware primitives, layers and finishing.

Backend: Pillow + numpy (always available). Shapes are point lists, so a skia/cairo backend can be added
later by re-implementing Canvas.fill / Canvas.stroke / layers only.
World units: 1 unit ~ 1 metre, y points UP, the ground is y = 0.
"""
import json, math, random, re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ENGINE_DIR = Path(__file__).resolve().parent
SKILL_DIR = ENGINE_DIR.parents[1]


# ---------- colours ----------
def rgb(c):
    if isinstance(c, (tuple, list)):
        return tuple(int(v) for v in c[:3])
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    a, b = rgb(a), rgb(b)
    t = max(0.0, min(1.0, t))
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def scale(c, f):
    return tuple(max(0, min(255, int(round(v * f)))) for v in rgb(c))


# ---------- style presets (data in styles/<name>.md) ----------
PALETTE_DEFAULTS = {   # used when a preset leaves a key out (keeps old presets working)
    "code_bg": "#1e2230", "code_bar": "#2b3042", "code_text": "#e6e9f2", "code_kw": "#c792ea", "code_str": "#c3e88d",
    "code_num": "#f78c6c", "code_com": "#7f8aa3", "code_fn": "#82aaff", "term_bg": "#11131a", "term_text": "#d7dae0",
    "term_prompt": "#7fd88f", "hair": ["#2a1d17", "#4a3020", "#1b1b1b"], "shirt": ["#4e8cc2", "#e0a43a", "#c8553d", "#7a9e5a"],
    "pants": ["#3a3f55", "#5a4636", "#2f4a5e"], "wall": "#efe1c8", "roof": "#b5543c", "window": "#a8d4ea",
    "box": ["#4e8cc2", "#7a9e5a", "#e0a43a", "#c8553d"], "box_text": "#ffffff", "highlight": "#ffd25a", "shadow": "#000000",
}

def load_style(name):
    p = Path(name) if str(name).endswith(".md") and Path(name).exists() else SKILL_DIR / "styles" / f"{name}.md"   # preset name or a style file (e.g. brand-recoloured)
    if not p.exists():
        raise SystemExit(f"unknown style '{name}' (no {p.name} in styles/)")
    m = re.search(r"```json\s*\n(.*?)\n```", p.read_text(encoding="utf-8"), re.S)
    if not m:
        raise SystemExit(f"{p.name} has no ```json preset block")
    st = json.loads(m.group(1))
    for k, v in PALETTE_DEFAULTS.items():
        st["palette"].setdefault(k, v)
    st["palette"].setdefault("title", st["palette"]["ink"])     # big headings: must contrast with the background
    st["palette"].setdefault("label", st["palette"]["ink"])     # small labels
    st.setdefault("fx", {})
    return st


# ---------- easing + keyframes ----------
EASE = {
    "linear": lambda u: u,
    "inOut": lambda u: u * u * (3 - 2 * u),
    "gentle": lambda u: 0.5 - 0.5 * math.cos(math.pi * u),
    "snap": lambda u: 1 - (1 - u) ** 3,
    "back": lambda u: 1 + 2.70158 * (u - 1) ** 3 + 1.70158 * (u - 1) ** 2,
}


def _alpha(im, k):
    if k >= 1:
        return im
    a = np.asarray(im, np.float32).copy(); a[..., 3] *= max(0.0, k)
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def val(v, t, ease="inOut", default=None):
    """A value can be a number/str or keyframes [[t, v], ...] (numbers or [x, y] lists)."""
    if v is None:
        return default
    if not (isinstance(v, list) and v and isinstance(v[0], list) and len(v[0]) == 2 and isinstance(v[0][0], (int, float))):
        return v
    if t <= v[0][0]:
        return v[0][1]
    if not isinstance(v[0][1], (int, float, list)):          # text values (e.g. poses) switch, they don't blend
        cur = v[0][1]
        for tk, vk in v:
            if t >= tk:
                cur = vk
        return cur
    for (t0, a), (t1, b) in zip(v, v[1:]):
        if t <= t1:
            u = EASE.get(ease, EASE["inOut"])((t - t0) / max(1e-9, t1 - t0))
            if isinstance(a, (int, float)):
                return a + (b - a) * u
            return [x + (y - x) * u for x, y in zip(a, b)]
    return v[-1][1]


def ellipse_pts(cx, cy, rx, ry, n=None, rot=0.0, a0=0.0, a1=2 * math.pi):
    n = n or max(16, int(28 + 6 * max(rx, ry)))
    cr, sr = math.cos(rot), math.sin(rot)
    out = []
    for i in range(n):
        a = a0 + (a1 - a0) * i / (n if a1 - a0 >= 2 * math.pi - 1e-6 else n - 1)
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + x * cr - y * sr, cy + x * sr + y * cr))
    return out


# ---------- fonts (system fonts only; nothing bundled) ----------
_FONT_CACHE = {}
FONT_CANDIDATES = ["DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf", "segoeuib.ttf",
                   "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
                   "LiberationSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]


MONO_CANDIDATES = ["consolab.ttf", "consola.ttf", "DejaVuSansMono-Bold.ttf", "DejaVuSansMono.ttf", "/System/Library/Fonts/Menlo.ttc",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
                   "LiberationMono-Regular.ttf", "cour.ttf"]
REG_CANDIDATES = ["DejaVuSans.ttf", "arial.ttf", "Arial.ttf", "segoeui.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "LiberationSans-Regular.ttf"]


def font(size, kind="bold"):
    size = max(8, int(size))
    key = (size, kind)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    f = None
    for c in {"bold": FONT_CANDIDATES, "mono": MONO_CANDIDATES, "regular": REG_CANDIDATES}[kind]:
        try:
            f = ImageFont.truetype(c, size); break
        except Exception:
            continue
    if f is None:
        try:
            f = ImageFont.load_default(size=size)
        except TypeError:
            f = ImageFont.load_default()
    _FONT_CACHE[key] = f
    return f


# ---------- texture caches (per process) ----------
_TEX = {}


def _paper(W, H):
    key = ("paper", W, H)
    if key not in _TEX:
        r = np.random.default_rng(7)
        coarse = Image.fromarray((r.random((max(2, H // 24), max(2, W // 24))) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
        fine = Image.fromarray((r.random((max(2, H // 3), max(2, W // 3))) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
        n = (np.asarray(coarse, np.float32) * 0.6 + np.asarray(fine, np.float32) * 0.4) / 255.0 - 0.5
        _TEX[key] = n[..., None]
    return _TEX[key]


def _vignette(W, H):
    key = ("vig", W, H)
    if key not in _TEX:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        d = ((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2
        _TEX[key] = np.clip(d / 2.0, 0, 1)[..., None]
    return _TEX[key]


class Canvas:
    def __init__(self, W, H, ss, cam, style, frame, t):
        self.W, self.H, self.ss = W, H, ss
        self.Wp, self.Hp = W * ss, H * ss
        self.cx, self.cy = cam["x"], cam["y"]
        self.k = cam["k"] * ss                      # pixels per world unit (supersampled)
        self.style, self.pal = style, style["palette"]
        self.frame, self.t = frame, t
        self.u = min(W, H) / 1080 * ss             # one "style pixel" (preset widths are px at 1080)
        be = style["line"].get("boil_every", 0)
        self.boil = frame // be if be else 0
        self.img = Image.new("RGB", (self.Wp, self.Hp), rgb(self.pal["paper"]))
        self.d = ImageDraw.Draw(self.img)
        self.stack = []
        self.storm = 0.0

    # colour lookup: palette name, list index ("cloth:1") or hex
    def c(self, name, i=0):
        if isinstance(name, (tuple, list)) and len(name) == 3 and all(isinstance(v, int) for v in name):
            return tuple(name)
        if isinstance(name, str) and name.startswith("#"):
            return rgb(name)
        if isinstance(name, str) and ":" in name:
            name, i = name.split(":"); i = int(i)
        v = self.pal[name]
        return rgb(v[i % len(v)] if isinstance(v, list) else v)

    @property
    def outline(self):
        return self.style["line"]["width"] > 0

    @property
    def lw(self):
        return self.style["line"]["width"] * self.u

    # world -> pixel
    def P(self, x, y, par=1.0):
        return ((x - self.cx * par) * self.k + self.Wp / 2, self.Hp / 2 - (y - self.cy * par) * self.k)

    def world_x_range(self, par=1.0):
        half = self.Wp / 2 / self.k
        return self.cx * par - half, self.cx * par + half

    def world_y_range(self, par=1.0):
        half = self.Hp / 2 / self.k
        return self.cy * par - half, self.cy * par + half

    def wob(self, px, seed):
        a = self.style["line"].get("wobble", 0) * self.u
        if a <= 0 or len(px) < 3:
            return px
        r = random.Random(int(seed) * 7919 + self.boil * 104729)
        p1, p2, p3, p4 = (r.uniform(0, 6.283) for _ in range(4))
        f = 0.9 / max(4, len(px)) * 6.283 * 3
        return [(x + a * math.sin(i * f * 7 + p1) + 0.5 * a * math.sin(i * f * 17 + p2),
                 y + a * math.sin(i * f * 7 + p3) + 0.5 * a * math.sin(i * f * 17 + p4)) for i, (x, y) in enumerate(px)]

    # ---------- primitives ----------
    def fill(self, pts, color, line=True, lw=1.0, seed=0, par=1.0, line_color=None):
        px = self.wob([self.P(x, y, par) for x, y in pts], seed)
        if len(px) < 3:
            return
        self.d.polygon(px, fill=self.c(color))
        if line and self.outline and lw > 0:
            self.d.line(px + [px[0], px[1]], fill=self.c(line_color or "ink"), width=max(1, int(round(self.lw * lw))), joint="curve")

    def stroke(self, pts, color, width_px, seed=0, par=1.0, closed=False):
        """width_px in style pixels (scaled with output size). Round caps and joins."""
        px = self.wob([self.P(x, y, par) for x, y in pts], seed)
        if closed:
            px = px + [px[0]]
        w = max(1, int(round(width_px * self.u)))
        col = self.c(color)
        self.d.line(px, fill=col, width=w, joint="curve")
        r = w / 2
        for x, y in (px[0], px[-1]):
            self.d.ellipse([x - r, y - r, x + r, y + r], fill=col)

    def wstroke(self, pts, color, width_units, seed=0, par=1.0):
        """A limb: width in world units, with an ink outline when the style has one."""
        wpx = width_units * self.k / self.u
        if self.outline:
            self.stroke(pts, "ink", wpx + 2 * self.style["line"]["width"], seed, par)
        self.stroke(pts, color, wpx, seed, par)

    def circle(self, x, y, r, color, line=True, lw=1.0, seed=0, par=1.0):
        self.fill(ellipse_pts(x, y, r, r, n=max(18, int(r * self.k / self.ss / 2))), color, line, lw, seed, par)

    def blob(self, circles, color, seed=0, par=1.0, lw=1.0, line=True):
        """Union of circles [(x, y, r)] with ONE outline around the union (clouds, wool, foliage)."""
        if line and self.outline:
            e = self.lw * lw / self.k
            for i, (x, y, r) in enumerate(circles):
                self.fill(ellipse_pts(x, y, r + e, r + e, n=36), "ink", False, seed=seed + i, par=par)
        for i, (x, y, r) in enumerate(circles):
            self.fill(ellipse_pts(x, y, r, r, n=36), color, False, seed=seed + i, par=par)

    def text(self, xy_px, s, size_px, color, anchor="mm"):
        self.d.text(xy_px, s, font=font(size_px * self.u), fill=self.c(color), anchor=anchor)

    # ---------- layers ----------
    def begin(self):
        self.stack.append((self.img, self.d))
        self.img = Image.new("RGBA", (self.Wp, self.Hp), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def end(self, shade=0.0, blur=0.0, alpha=1.0, clip_left_x=None, clip_rect=None, fx=None, shadow=0.0):
        layer = self.img
        self.img, self.d = self.stack.pop()
        if clip_left_x is not None:                      # erase everything left of a world x (e.g. inside a doorway)
            xpx = int(max(0, min(self.Wp, self.P(clip_left_x, 0)[0])))
            if xpx > 0:
                layer.paste((0, 0, 0, 0), (0, 0, xpx, self.Hp))
        bbox = layer.getbbox()
        if not bbox:
            return
        crop = layer.crop(bbox)
        if shade > 0 or alpha < 1:
            a = np.asarray(crop, np.float32).copy()
            if shade > 0:
                h, w = a.shape[:2]
                gy = np.linspace(1 + 0.18 * shade, 1 - 0.55 * shade, h, dtype=np.float32)[:, None, None]
                gx = np.linspace(1 + 0.08 * shade, 1 - 0.18 * shade, w, dtype=np.float32)[None, :, None]
                g = gy * gx                                                   # soft top-left light
                a[..., :3] *= g ** np.array([0.9, 1.0, 1.25], np.float32)    # shadows lean warm (painted look)
            if alpha < 1:
                a[..., 3] *= alpha
            crop = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
        if blur > 0:
            crop = crop.filter(ImageFilter.GaussianBlur(blur * self.u))
        dest = bbox[:2]
        pen = None
        if fx:                                              # entrance effects: fade, pop, slide, draw (whiteboard wipe + pen)
            kind, u = fx
            if kind == "fade":
                crop = _alpha(crop, u)
            elif kind == "pop":
                k = max(0.02, EASE["back"](u))
                w0, h0 = crop.size
                nw, nh = max(1, int(w0 * k)), max(1, int(h0 * k))
                cx, cy = bbox[0] + w0 / 2, bbox[1] + h0 / 2
                crop = _alpha(crop.resize((nw, nh), Image.BILINEAR), min(1, u * 3))
                dest = (int(cx - nw / 2), int(cy - nh / 2))
            elif kind == "slide":
                e = EASE["snap"](u)
                dest = (bbox[0], int(bbox[1] + (1 - e) * 0.08 * self.Hp))
                crop = _alpha(crop, e)
            elif kind == "draw" and u < 1:
                w0, h0 = crop.size
                front = int(w0 * u)
                m = np.zeros((h0, w0), np.float32)
                m[:, :front] = 1
                edge = max(2, int(10 * self.u))
                ramp = np.linspace(1, 0, edge, dtype=np.float32)
                m[:, front:front + edge] = ramp[: max(0, min(edge, w0 - front))]
                a = np.asarray(crop, np.float32).copy(); a[..., 3] *= m
                crop = Image.fromarray(a.astype(np.uint8), "RGBA")
                pen = (bbox[0] + front, bbox[1] + h0 * (0.5 + 0.38 * math.sin(u * 23)))
        if shadow > 0:                                      # soft drop shadow (modern vector)
            sh = Image.new("RGBA", crop.size, rgb(self.pal.get("shadow", "#000000")) + (0,))
            sh.putalpha(crop.getchannel("A").point(lambda v: int(v * shadow)))
            sh = sh.filter(ImageFilter.GaussianBlur(10 * self.u))
            off = int(9 * self.u)
            self._put(sh, (dest[0] + off // 2, dest[1] + off))
        self._put(crop, dest)
        self.d = ImageDraw.Draw(self.img)
        if pen:
            self.marker(*pen)

    def _put(self, im, dest):
        if self.img.mode == "RGBA":
            base = Image.new("RGBA", self.img.size, (0, 0, 0, 0)); base.paste(im, dest)
            self.img.alpha_composite(base)
        else:
            self.img.paste(im, dest, im)

    def marker(self, x, y):
        """A whiteboard marker whose tip is at (x, y) pixels."""
        L, W = 150 * self.u, 26 * self.u
        ang = math.radians(35)
        dx, dy = math.cos(ang), math.sin(ang)
        tip = (x, y); a = (x + dx * 18 * self.u, y + dy * 18 * self.u)
        end = (a[0] + dx * L, a[1] + dy * L)
        self.d.line([tip, a], fill=(40, 40, 40), width=int(W * 0.5))
        self.d.line([a, end], fill=(38, 92, 170), width=int(W))
        self.d.line([(a[0] + dx * L * 0.62, a[1] + dy * L * 0.62), end], fill=(235, 235, 235), width=int(W * 0.9))

    # ---------- background helpers ----------
    def sky(self, top, bottom):
        a, b = np.array(rgb(top), np.float32), np.array(rgb(bottom), np.float32)
        y = np.linspace(0, 1, self.Hp, dtype=np.float32)[:, None]
        col = (a[None, :] * (1 - y) + b[None, :] * y).astype(np.uint8)          # (H, 3)
        self.img = Image.fromarray(np.repeat(col[:, None, :], self.Wp, axis=1), "RGB")
        self.d = ImageDraw.Draw(self.img)

    # ---------- finishing ----------
    def finish(self, grade=None):
        img = self.img.resize((self.W, self.H), Image.LANCZOS) if self.ss > 1 else self.img
        tex = self.style.get("texture", {})
        a = np.asarray(img, np.float32)
        if grade is not None:
            a *= np.array(grade, np.float32)[None, None, :]
        if tex.get("paper"):
            a *= 1 + tex["paper"] * 1.6 * _paper(self.W, self.H)
        if tex.get("vignette"):
            a *= 1 - tex["vignette"] * _vignette(self.W, self.H) * np.array([1.0, 1.04, 1.12], np.float32)
        if tex.get("grain"):
            r = np.random.default_rng(1000 + (self.boil if self.style["line"].get("boil_every") else self.frame))
            a += r.normal(0, tex["grain"] * 255, (self.H, self.W, 1)).astype(np.float32)
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
