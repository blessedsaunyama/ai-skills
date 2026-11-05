"""Text measuring + text-to-outline for design-studio (needs fontTools).

Turning text into vector paths means every renderer (Inkscape, cairosvg,
Chromium) shows exactly the bundled font, with no font installation.
"""
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FONT_DIR = Path(__file__).resolve().parent.parent / "fonts"

# family -> {weight: file}. CSS family names are used in the editable SVG.
FAMILIES = {
    "Montserrat":       {400: "Montserrat-Regular.ttf", 600: "Montserrat-SemiBold.ttf", 700: "Montserrat-Bold.ttf", 800: "Montserrat-ExtraBold.ttf", 900: "Montserrat-Black.ttf"},
    "Open Sans":        {400: "OpenSans-Regular.ttf", 600: "OpenSans-SemiBold.ttf", 700: "OpenSans-Bold.ttf"},
    "Playfair Display": {400: "PlayfairDisplay-Regular.ttf", 700: "PlayfairDisplay-Bold.ttf", 900: "PlayfairDisplay-Black.ttf"},
    "Lato":             {400: "Lato-Regular.ttf", 700: "Lato-Bold.ttf"},
    "Bebas Neue":       {400: "BebasNeue-Regular.ttf"},
    "Poppins":          {400: "Poppins-Regular.ttf", 600: "Poppins-SemiBold.ttf", 700: "Poppins-Bold.ttf"},
}
FALLBACK = ("Open Sans", 400)

_cache = {}


class Font:
    def __init__(self, family, weight):
        weights = FAMILIES[family]
        w = min(weights, key=lambda k: abs(k - weight))
        self.family, self.weight = family, w
        self.path = FONT_DIR / weights[w]
        self.tt = TTFont(self.path)
        self.upm = self.tt["head"].unitsPerEm
        self.cmap = self.tt.getBestCmap()
        self.gs = self.tt.getGlyphSet()
        self.hmtx = self.tt["hmtx"]
        hhea = self.tt["hhea"]
        self.ascent, self.descent = hhea.ascent, hhea.descent
        os2 = self.tt["OS/2"]
        self.cap = getattr(os2, "sCapHeight", 0) or int(self.ascent * 0.7)
        self.xh = getattr(os2, "sxHeight", 0) or int(self.cap * 0.7)
        self._kern1, self._kern2 = {}, []
        self._load_kerning()
        self._paths = {}

    # --- kerning (GPOS PairPos, 'kern' feature) ---
    def _load_kerning(self):
        if "GPOS" not in self.tt:
            if "kern" in self.tt:
                for t in self.tt["kern"].kernTables:
                    self._kern1.update(getattr(t, "kernTable", {}))
            return
        gpos = self.tt["GPOS"].table
        if not gpos.FeatureList:
            return
        idx = set()
        for fr in gpos.FeatureList.FeatureRecord:
            if fr.FeatureTag == "kern":
                idx.update(fr.Feature.LookupListIndex)
        for i in sorted(idx):
            lk = gpos.LookupList.Lookup[i]
            for st in lk.SubTable:
                if lk.LookupType == 9:
                    st = st.ExtSubTable
                if getattr(st, "LookupType", 2) != 2:
                    continue
                if st.Format == 1:
                    for g1, ps in zip(st.Coverage.glyphs, st.PairSet):
                        for r in ps.PairValueRecord:
                            v = getattr(r.Value1, "XAdvance", 0) if r.Value1 else 0
                            if v:
                                self._kern1.setdefault((g1, r.SecondGlyph), v)
                elif st.Format == 2:
                    self._kern2.append((set(st.Coverage.glyphs), st.ClassDef1.classDefs, st.ClassDef2.classDefs, st.Class1Record))

    def kern(self, a, b):
        v = self._kern1.get((a, b))
        if v is not None:
            return v
        for cov, cd1, cd2, recs in self._kern2:
            if a in cov:
                c1, c2 = cd1.get(a, 0), cd2.get(b, 0)
                try:
                    val = recs[c1].Class2Record[c2].Value1
                except IndexError:
                    continue
                x = getattr(val, "XAdvance", 0) if val else 0
                if x:
                    return x
                return 0
        return 0

    def glyph(self, ch):
        return self.cmap.get(ord(ch))

    def glyph_path(self, gname):
        if gname not in self._paths:
            pen = SVGPathPen(self.gs)
            self.gs[gname].draw(pen)
            self._paths[gname] = pen.getCommands()
        return self._paths[gname]


def font(family, weight=400):
    key = (family, weight)
    if key not in _cache:
        _cache[key] = Font(family, weight)
    return _cache[key]


def _runs(text, f):
    """Split text into (Font, glyphname, char) with fallback for missing glyphs."""
    out = []
    for ch in text:
        g = f.glyph(ch)
        ff = f
        if g is None:
            ff = font(*FALLBACK)
            g = ff.glyph(ch) or ff.glyph("?")
        out.append((ff, g, ch))
    return out


def measure(text, family, weight, size, tracking=0.0):
    """Width in px of one line. tracking is in em (0.1 = 10 % of size)."""
    f = font(family, weight)
    runs = _runs(text, f)
    w = 0.0
    for i, (ff, g, ch) in enumerate(runs):
        s = size / ff.upm
        w += ff.hmtx[g][0] * s
        if i + 1 < len(runs) and runs[i + 1][0] is ff:
            w += ff.kern(g, runs[i + 1][1]) * s
        if i + 1 < len(runs):
            w += tracking * size
    return w


def outline(text, family, weight, size, x, y, anchor="start", tracking=0.0):
    """SVG path data for one line with its baseline at y. anchor: start|middle|end."""
    width = measure(text, family, weight, size, tracking)
    if anchor == "middle":
        x -= width / 2
    elif anchor == "end":
        x -= width
    f = font(family, weight)
    runs = _runs(text, f)
    parts = []
    cx = x
    for i, (ff, g, ch) in enumerate(runs):
        s = size / ff.upm
        if not ch.isspace():
            d = ff.glyph_path(g)
            if d:
                parts.append(_transform(d, ff, g, s, cx, y))
        cx += ff.hmtx[g][0] * s
        if i + 1 < len(runs) and runs[i + 1][0] is ff:
            cx += ff.kern(g, runs[i + 1][1]) * s
        cx += tracking * size
    return " ".join(parts), width


def _transform(_d, ff, g, s, x, y):
    pen = SVGPathPen(ff.gs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
    ff.gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x, y)))
    return pen.getCommands()


def wrap(text, family, weight, size, max_w, tracking=0.0, max_lines=None):
    """Greedy word wrap; explicit '\\n' forces a break."""
    lines = []
    for para in str(text).split("\n"):
        words = para.split()
        if not words:
            lines.append("")
            continue
        cur = words[0]
        for wd in words[1:]:
            trial = cur + " " + wd
            if measure(trial, family, weight, size, tracking) <= max_w:
                cur = trial
            else:
                lines.append(cur)
                cur = wd
        lines.append(cur)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and measure(last + "…", family, weight, size, tracking) > max_w:
            last = last[:-1]
        lines[-1] = last.rstrip() + "…"
    return lines


def balanced_lines(text, family, weight, size, n, tracking=0.0):
    """Split words into n lines with the smallest longest line (good for titles)."""
    words = str(text).split()
    if n <= 1 or len(words) <= 1:
        return [" ".join(words)]
    n = min(n, len(words))
    best, best_w = None, 1e18
    import itertools
    for cuts in itertools.combinations(range(1, len(words)), n - 1):
        idx = (0,) + cuts + (len(words),)
        ls = [" ".join(words[idx[i]:idx[i + 1]]) for i in range(n)]
        w = max(measure(l, family, weight, size, tracking) for l in ls)
        if w < best_w:
            best, best_w = ls, w
    return best


def fit_title(text, family, weight, max_w, max_size, min_size, max_lines=2, tracking=0.0):
    """Biggest size (<= max_size) where the title fits max_w in <= max_lines balanced lines.
    Returns (size, lines)."""
    if "\n" in str(text):
        ls = str(text).split("\n")
        widest = max(measure(l, family, weight, 100, tracking) for l in ls) / 100
        return max(min_size, min(max_size, max_w / widest)), ls
    best = None
    for n in range(1, max_lines + 1):
        ls = balanced_lines(text, family, weight, 100, n, tracking)
        widest = max(measure(l, family, weight, 100, tracking) for l in ls) / 100
        size = min(max_size, max_w / widest)
        if best is None or size > best[0] * 1.15:  # extra line only if clearly bigger
            best = (size, ls)
    size, ls = best
    return max(min_size, size), ls


def missing_chars(text, family, weight=400):
    f = font(family, weight)
    return sorted({c for c in text if not c.isspace() and f.glyph(c) is None})


def metrics(family, weight, size):
    f = font(family, weight)
    s = size / f.upm
    return {"ascent": f.ascent * s, "descent": -f.descent * s, "cap": f.cap * s, "xh": f.xh * s}
