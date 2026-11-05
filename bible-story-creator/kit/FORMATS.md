# Multi-format rendering

The engine renders any of four formats. The format is a URL setting read by `engine/index.html` and passed by `tools/render.mjs`:

| Key | Size | `render.mjs` | Best for |
|---|---|---|---|
| `9x16` | 1080x1920 | `FMT=9x16` (default) | WhatsApp Status, TikTok, Reels, Shorts |
| `16x9` | 1920x1080 | `FMT=16x9` | YouTube, church projector / TV |
| `1x1` | 1080x1080 | `FMT=1x1` | Facebook/Instagram feed, WhatsApp chats |
| `4x5` | 1080x1350 | `FMT=4x5` | Instagram/Facebook feed (largest feed size) |
| master | any WxH | `SIZE=1920x1920` | FAST-mode master (crops come out of it) |

`python3 formats.py table` prints this table, and `python3 formats.py plan 9x16,16x9 --seconds 45 --spf <measured>` gives the FAST and BEST sizes and time estimates.

## Camera maths
Camera keys in `story.js` keep their `fov` = **the vertical field of view of a 1080x1920 frame**, so existing shot plans still work. `main.js` maps it to the real canvas:

- `fit=height` (BEST default): the vertical fov stays the same, and a wider format reveals more world at the sides. Nothing is cut at the top or bottom, so build the world wide enough.
- `fit=focal` (FAST master): the focal length in pixels stays the same, so the canvas is an exact centre extension of the 9:16 frame and every crop matches it pixel for pixel. `tan(v/2) = tan(fov/2) · H / 1920`.

Horizontal coverage: `hfov = 2·atan(tan(vfov/2)·aspect)`, and the visible half-width at distance d is `d·tan(hfov/2)`. Helpers in `motion.js`: `halfWidth(d, fov)`, `halfHeight`, `distForWidth(hw, fov)`, `fmtPick({...})` and `FMT`.

| Format | half-width at 4 m, fov 40 | Staging consequence |
|---|---|---|
| 9:16 | ±0.82 m | Stage characters in depth, one or two per shot, use vertical moves (crane, tilt) |
| 4:5 | ±1.16 m | Two-shots fit side by side |
| 1:1 | ±1.46 m | Three people across. Keep the action in the middle |
| 16:9 | ±2.59 m | Groups and wide landscapes. Fill the sides (crowds, trees, walls) or it looks empty |

**BEST framing per format:** any camera key may carry `fovBy: { '16x9': 30, '1x1': 36 }`, which `camFromKeys` interpolates and adds to the push-in creep. A shot can also branch on `FMT.key` (from `motion.js`) to move the camera, e.g. pull back in 9:16 so a two-shot fits.

Ink width and DOF blur scale with the picture: ink is 2.5 px at 1080 on the short side, and blur is multiplied by H/1920 under `fit=height`.

## FAST vs BEST
- **FAST:** one render at the master size, which is the **max width × max height** of the chosen formats (e.g. 9:16 + 16:9 → 1920x1920; 9:16 + 4:5 + 1:1 → 1080x1920), with `fit=focal`. Then `python3 formats.py crop out/Title_master.mp4 <list>` makes centre crops at native resolution with no scaling. **Everything that matters (faces, hands, the key prop, diegetic text) must sit inside the centre-safe box**, which is min width × min height (e.g. 1080x1080). Check it with `python3 sheet.py stills/a stills/sheet.jpg --centre 1080x1080 --crops 9x16,16x9`.
- **BEST:** one render per format (`FMT=<key> node render.mjs frames_<key> ...`), each framed for its own shape with `fovBy` or `FMT.key` branches. Cost = the sum of the formats' pixel counts. Finish each with `bash finish.sh "Title" frames_<key> <key>`.

## Safe zones (platform UI), in px at native size
| Format | top | bottom | left | right | Why |
|---|---|---|---|---|---|
| 9x16 | 220 | 420 | 60 | 140 | status/top bar, caption + buttons, like/share column |
| 16x9 | 54 | 54 | 96 | 96 | 90 % title-safe (projectors and TVs overscan) |
| 1x1 | 60 | 140 | 60 | 60 | feed caption bar |
| 4x5 | 70 | 160 | 60 | 60 | feed caption bar |

`python3 sheet.py stills/a stills/sheet.jpg --safe 9x16` draws the zone in red on every tile. Keep faces and diegetic text inside it.
