# Engine A: py2d (Python 2D)

Renders Stickman, Flat 2D, Storybook, Whiteboard and Modern vector from one engine. The style is **data**: the JSON block in `styles/<style>.md` sets the palette, line weight and wobble, fills and shading, proportions, face, textures and motion rules. The same `scene.json` renders in every style and every format.

- Backend: Pillow + numpy (2× supersampling for smooth edges). skia-python/pycairo are optional future backends; the drawing code only uses point lists, so a backend swap touches `canvas.py` only.
- Speed (measured on an i5-6300U laptop, 2 workers, 720p preview): Stickman / Flat 2D ≈ 0.5 s per frame per worker, Storybook ≈ 1.4 s. 1080p costs about 2.2× more.

## Smoke test (one command, from the skill folder)
```
python engines/py2d/render.py examples/bible-noah-preview/scene.json --fmt 9x16 --frames 0,75,149 --out _smoke_py2d
```
Expect 3 JPGs in `_smoke_py2d/` and a final `spf=` line. Delete the folder afterwards.

## Command
```
python engines/py2d/render.py SCENE.json --fmt 9x16|16x9|1x1|4x5 [--quality preview|final] [--style NAME]
       [--out DIR] [--frames 0-149 | 0,75,149] [--workers N] [--force] [--override-limits]
```
Existing frames are skipped (re-run = resume). `--force` re-renders them. The worker count comes from the hardware tier and the free RAM. The engine pauses with exit code 4 if free RAM drops below 15 %.

## scene.json
```json
{
  "title": "...", "fps": 30, "duration": 5, "style": "storybook",
  "storm": [[0, 0], [3.6, 0.85]],
  "camera":      [{"t": 0, "x": 3.6, "y": 2.3, "w": 16, "h": 9}, {"t": 5, "x": 2.6, "y": 1.6, "w": 11, "h": 6.2}],
  "camera_9x16": [{"t": 0, "x": 2.6, "y": 1.9, "w": 8.4, "h": 8}],
  "elements": [ {"type": "sky"}, {"type": "ground"}, {"type": "person", "x": [[0, 2], [3, 5]], "pose": "gesture"} ]
}
```
- **World units:** about 1 m; y points up; the ground is y = 0.
- **Camera keyframes:** `x, y` = the centre; `w, h` = the box that must stay visible. Every format fits that box and shows extra world around it. Add `camera_<fmt>` (e.g. `camera_9x16`) to frame a format differently (BEST mode). Optional `"ease"` per key: linear, inOut, gentle, snap.
- **Keyframes:** any number can be `[[t, value], ...]`. Walkers animate their legs from the distance they travel along `x`.
- `storm` (0–1) darkens the sky, rolls in storm clouds and greys the picture.

| Element | Main properties |
|---|---|
| `sky` | colours from the style (mixes to `storm_sky`) |
| `sun` | `x, y, r, par` (parallax 0 = fixed, 1 = moves with the world) |
| `clouds` | `items: [{x, y, w, storm?, enter?}]`, `drift`, `par` |
| `hills` | `layers: [{par, y, amp}]` (default: 3 layers) |
| `ground` | ground band + grass tufts |
| `tree` | `x, h, par` |
| `ark` | `door_x, height, left, right, ramp_to` (box hull, pitch, window strip, door in the side, ramp) |
| `person` | `x, y, h, facing (1/-1), pose (stand, walk, gesture, pray, point), robe, mantle, sash, skin (index), beard (white/dark), headcloth, old, floor` |
| `animal` | `kind (sheep, goat, ox), x, size, floor, phase, show` |
| `bird` | `x, y` keyframes, `size, show` |
| `rain` | `amount` (0–1 keyframes), `density` |
| `caption` | `text, ref, show: [t0, t1], size` (placed inside the format's safe zone) |
| `clip` | `left` (world x) + `children`: hides children left of x (e.g. animals going in through a door) |
| `house` | `x, w, h, wall, roof, flat_roof` (flat roof + parapet for Ancient Near East) |
| `title` | `text` (put a line break in the string for two lines), `sub`, `size`, `box` (palette colour for a backing plate); screen-anchored |
| `text` | `text`, `size`, `font` (bold/regular/mono), `screen` or `at` |
| `box` | `label`, `color` (`box:0`..), `w, h`, `glow` (keyframes 0–1): diagrams, list items, steps |
| `arrow` | `from, to` (world), `grow: [t0, t1]`, `color, width, head` |
| `bubble` | `at` (world point the tail touches, e.g. a mouth), `text`, `side` (1 right / −1 left), `size` |
| `code` | `lines`, `label` (language + version actually run), `typing` ([t0, t1] or keyframes [[t, chars], ...]), `highlight` ([[t, line], ...]) |
| `terminal` | `lines: [{t, text, prompt?}]` (prompt lines type themselves), `title` |
| `floor` (on walkers) | `[[x, y], ...]` polyline they walk on (ramps, steps) |
| `person` (modern) | `"outfit": "modern"`, `shirt`, `pants`, `hair` (short/long/none), `hair_color` |

**Screen-anchored items** (`title, text, box, code, terminal`): `"screen": [fx, fy]` places the centre at a fraction of the format's SAFE area and `"w"` is a fraction of the safe width, so layouts adapt to every format. Override per format with `screen_16x9`, `w_1x1`, `h_4x5`... Leave the bottom ~20 % free when captions are burned in.

**Entrances and exits (any element):** `"enter": 1.2` uses the style's default effect (Whiteboard: draw-on with a marker pen · Modern vector and Flat 2D: pop · Storybook and Stickman: fade), or `"enter": {"t": 1.2, "kind": "pop|fade|slide|draw", "dur": 0.6}`. `"exit": 3.0` fades out. Text keyframes (e.g. `"pose": [[0, "stand"], [2, "gesture"]]`) switch instead of blending.

**Colours are roles, not hex codes.** Use palette names (`title`, `label`, `text`/`text_bg`, `box:1`, `cloth:2`, `wall`, `roof`, `accent`...) so every style restyles the same scene. `title` and `label` always contrast with the style's background.

Add new actor types in `actors.py` (`DRAW` table). Keep colours in the style presets, never hard-coded per scene.

## Files
`render.py` (CLI, workers, resume, RAM guard, lock) · `canvas.py` (camera, primitives, wobble/boil, layers + soft shading, paper/grain/vignette) · `actors.py` (scenery, people, animals, weather) · `actors_tech.py` (code, terminal, title, text, box, arrow, bubble, house).
