# Engine B: Manim Community

Precise maths, algorithm and diagram animation with [Manim Community](https://www.manim.community) (MIT). Runs inside the skill's `.venv`; LaTeX is optional.

- Install (ask the user first): `python shared/setup_check.py --engine manim --install` (about 150–200 MB in `.venv`).
- Speed (i5-6300U laptop): ≈ 0.13 s/frame at 720p, ≈ 0.2 s/frame at 1080p for a simple 2D scene. Manim uses one process.
- Output: Manim writes an MP4 into `OUT/_manim/` (finished animations are cached, so a re-run resumes), then `render.py` extracts `OUT/f0000.jpg ...`, so `sheet.py`, `captions.py` and `finish.py` work like they do for every engine.

## Smoke test (one command, from the skill folder)
```
python engines/manim/render.py examples/maths-binary-search/binary_search.py BinarySearch --fmt 16x9 --frames 0,80,160 --out _smoke_manim
```
Expect 3 JPGs in `_smoke_manim/` and a `spf=` line. (Without `--timing` the scene uses its built-in fallback times.) Delete the folder afterwards.

## Command
```
python engines/manim/render.py SCENE.py SceneName --fmt 9x16|16x9|1x1|4x5 [--quality preview|final] [--style manim|whiteboard|modern-vector|...]
       [--timing work/phrases.json] [--out DIR] [--frames 0,60,120] [--force]
```
`--frames` is a look check: Manim can't render a single frame of an animation, so the whole scene renders at preview size and only those frames are kept. `--force` clears the cache. Low CPU priority, one render at a time, pauses (exit code 4) below 15 % free RAM.
Estimate first: `python shared/estimate.py --engine manim SCENE.py --name SceneName --fmt 9x16 --quality final --timing work/phrases.json`.

## Writing a scene
```python
from studio import *                      # also imports everything from manim

class MyScene(Scene):
    def construct(self):
        title = text("Fractions", 52, weight="BOLD").move_to([SAFE["cx"], SAFE["top"] - 0.5, 0])
        self.add(title)                                   # frame 0 = the hook
        wait_until(self, T.start(1, 1.0))                 # phrase 1 of the voice (fallback 1.0 s)
        eq = maths(r"\frac{1}{2} + \frac{1}{4} = \frac{3}{4}", "1/2 + 1/4 = 3/4")
        self.play(Write(fit_width(eq, 0.8)), run_time=0.8)
        wait_until(self, T.duration or 4)
```
| Helper | What it gives |
|---|---|
| `FMT, FW, FH` | the format key and frame size in Manim units (height 8; width 4.5 for 9:16, 14.2 for 16:9) |
| `SAFE` | `left, right, top, bottom, width, height, cx, cy` of the platform safe zone (Manim units) |
| `C` | style colours: `bg, ink, muted, accent, good, bad, highlight, on_highlight, box(i), box_text` (from the preset's `manim` block or its palette) |
| `text(s, size, color, weight)` | `Text` in the system font |
| `maths(tex, plain)` | LaTeX `MathTex` when LaTeX is installed, else `Text(plain)`; `LATEX` tells you which |
| `fit_width(m, frac)` | shrink to fit a fraction of the safe width |
| `T.start(i, fallback)`, `T.end(i)`, `T.duration` | voice phrase times from `--timing` |
| `wait_until(self, t)` | wait until absolute time t (sync to the voice) |
Rules: never hard-code colours (every style must work); keep text inside `SAFE`; compute values in the scene and `assert` the answer; portrait formats (`FW < FH`) need fewer items per row.
