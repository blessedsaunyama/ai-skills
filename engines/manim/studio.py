"""animation-studio helper for Manim scenes (engine B). Import it at the top of every scene file:

    from studio import *          # also does `from manim import *`

Gives the scene:
  FMT, FW, FH          format key and frame width/height in Manim units (height is always 8)
  SAFE                 dict(left, right, top, bottom) in Manim units: keep text and key objects inside
  C                    colours from the style preset: C.bg, C.ink, C.muted, C.accent, C.good, C.bad, C.box(i), C.box_text,
                       C.highlight, C.on_highlight (never hard-code colours in a scene: every style must work)
  FONT, MONO           font names for Text / Code
  T                    voice timeline: T.start(i), T.end(i) = phrase i times (s); T.duration
  wait_until(scene, t) wait until absolute time t (keeps animations in sync with the voice)
  maths(tex, plain)    MathTex if LaTeX is installed, else Text(plain) (say so in the notes: LATEX = False)
  fit_width(m, frac)   scale a mobject down so it uses at most frac of the safe width
Settings come from environment variables set by engines/manim/render.py (AS_FMT, AS_STYLE, AS_TIMING).
"""
import json, os, re, shutil
from pathlib import Path

from manim import *  # noqa: F401,F403
from manim import Mobject, Text, MathTex, config

SKILL_DIR = Path(__file__).resolve().parents[2]
FMT = os.environ.get("AS_FMT", "16x9")
STYLE = os.environ.get("AS_STYLE", "manim")
_ASPECT = {"9x16": 9 / 16, "16x9": 16 / 9, "1x1": 1.0, "4x5": 4 / 5}[FMT]
FH = 8.0
FW = FH * _ASPECT
config.frame_height = FH
config.frame_width = FW

_SAFE_PX = {"9x16": (220, 420, 60, 140, 1080, 1920), "16x9": (54, 54, 96, 96, 1920, 1080),
            "1x1": (60, 140, 60, 60, 1080, 1080), "4x5": (70, 160, 60, 60, 1080, 1350)}[FMT]
_t, _b, _l, _r, _W, _H = _SAFE_PX
_u = FH / _H
SAFE = dict(left=-FW / 2 + _l * _u, right=FW / 2 - _r * _u, top=FH / 2 - _t * _u, bottom=-FH / 2 + _b * _u)
SAFE["width"] = SAFE["right"] - SAFE["left"]
SAFE["height"] = SAFE["top"] - SAFE["bottom"]
SAFE["cx"] = (SAFE["left"] + SAFE["right"]) / 2
SAFE["cy"] = (SAFE["top"] + SAFE["bottom"]) / 2


def _preset(name):
    p = SKILL_DIR / "styles" / f"{name}.md"
    m = re.search(r"```json\s*\n(.*?)\n```", p.read_text(encoding="utf-8"), re.S)
    return json.loads(m.group(1))


class _Colours:
    def __init__(self, st):
        p = st["palette"]
        m = st.get("manim", {})
        self.bg = m.get("bg", p.get("paper"))
        self.ink = m.get("ink", p.get("title", p.get("ink")))
        self.muted = m.get("muted", p.get("label", p.get("ink")))
        self.accent = m.get("accent", p.get("accent"))
        self.good = m.get("good", "#5fd38d")
        self.bad = m.get("bad", "#ff6b6b")
        self.highlight = m.get("highlight", p.get("highlight", "#ffd166"))
        self._boxes = m.get("boxes", p.get("box", ["#4e8cc2", "#7a9e5a", "#e0a43a", "#c8553d"]))
        self.box_text = m.get("box_text", p.get("box_text", "#ffffff"))        # numbers/labels drawn on boxes
        self.on_highlight = m.get("on_highlight", "#14182b")                     # text on highlight/good fills

    def box(self, i=0):
        return self._boxes[i % len(self._boxes)]


C = _Colours(_preset(STYLE))
config.background_color = C.bg
FONT = "Arial" if os.name == "nt" else ("Helvetica" if os.uname().sysname == "Darwin" else "DejaVu Sans")
MONO = "Consolas" if os.name == "nt" else ("Menlo" if os.uname().sysname == "Darwin" else "DejaVu Sans Mono")
LATEX = os.environ.get("AS_LATEX") == "1" or bool(shutil.which("latex"))   # render.py sets AS_LATEX when it finds LaTeX


class _Timeline:
    def __init__(self, path):
        self.phrases = []
        self.duration = None
        if path and Path(path).exists():
            d = json.loads(Path(path).read_text(encoding="utf-8"))
            self.phrases, self.duration = d["phrases"], d["duration"]

    def start(self, i, default=None):
        return self.phrases[i]["s"] if i < len(self.phrases) else default

    def end(self, i, default=None):
        return self.phrases[i]["e"] if i < len(self.phrases) else default


T = _Timeline(os.environ.get("AS_TIMING"))


def wait_until(scene, t):
    """Wait until absolute time t (seconds from the start). Does nothing if we're already past it."""
    now = scene.renderer.time
    if t is not None and t - now > 1 / 60:
        scene.wait(t - now)


def maths(tex, plain=None, **kw):
    """Typeset maths with LaTeX when available; otherwise plain Text (e.g. 'x² + 1'). Never fails for lack of LaTeX."""
    if LATEX:
        return MathTex(tex, color=kw.pop("color", C.ink), **kw)
    return Text(plain or tex, font=FONT, color=kw.pop("color", C.ink), **kw)


def text(s, size=36, color=None, weight="NORMAL", font=None):
    return Text(s, font=font or FONT, font_size=size, color=color or C.ink, weight=weight)


def fit_width(m: Mobject, frac=0.9):
    if m.width > SAFE["width"] * frac:
        m.scale_to_fit_width(SAFE["width"] * frac)
    return m
