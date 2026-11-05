# kit/ (video engine for bible-story-creator)
Adapted from `cartoon-short-kit`: 2D bean-head character cards in an inked, painted 3D world (three.js in headless Chromium, no GPU needed), a synthesized music bed and SFX, and a level-locked mix.
Built on github.com/mromidev/claude-animated-shorts (MIT): toon.ts, look values and readability rules. three.js r160 (MIT) is vendored.

| Path | What it does | Language | Needs |
|---|---|---|---|
| `engine/index.html` | Canvas sized from `?fmt=` / `?w=&h=` (see FORMATS.md); sets `window.FMT` | HTML | Chromium |
| `engine/main.js` | Renderer: world, cards, ink, grade, DOF. Camera fov is mapped per format | JS (three.js) | `lib/three.module.js`, `toon.js` |
| `engine/paint.js` | Painted canvas textures (stone, plaster, wood, marble, banners...) | JS | three.js |
| `engine/roman.js` | Base cast drawing `romanFront()` (Roman-era outfits from the example) | JS | toon.ts |
| `engine/biblical.js` | **Bible-era cast**: `bibleFront()` + `BIBLE` outfits, `fxLion`, `fxSheep`, `fxGlory`, `fxStone`, `fxSling` | JS | roman.js |
| `engine/motion.js` | Easing, spline cameras (`fovBy` aware), idle, blink, walk, **format framing helpers** | JS | — |
| `example/soldier/` | Worked example: `story.js` shot plan, `audio.py` stem synth | JS / Python | numpy, ffmpeg |
| `vendor/` | three.module.js r160 + toon.ts + licences (setup works offline) | — | — |
| `tools/check_setup.py` | ✅/❌ requirement table with Windows/Mac/Linux install commands | Python (stdlib) | — |
| `tools/setup.sh` | New project folder (copies engine + tools, builds `web/toon.js`) | Bash | node 22.6+ |
| `tools/timing.py` | Voice + script → `work/words.json`, `work/phrases.json` | Python | ffmpeg |
| `tools/cast.mjs` | Character test sheet (2D, fast) | Node | Playwright |
| `tools/render.mjs` | Frames → `frames/f0000.jpg` (`FMT=`, `SIZE=`, `FIT=`, `RESUME=1`) | Node | Playwright + Chromium |
| `tools/sheet.py` | Contact sheet, any aspect, `--safe` / `--centre` overlays | Python | Pillow |
| `tools/mix.py` | Voice + music + SFX at locked levels → `mix_raw.wav` | Python | numpy, ffmpeg |
| `tools/finish.sh` | Loudness, H.264/AAC encode, freeze/black/loudness QA, QA sheet | Bash | ffmpeg |
| `tools/formats.py` | Platform table, FAST/BEST plan + time estimate, FAST crops, safe zones | Python | ffmpeg (crop) |
| `tools/srt.py` | Captions from `work/words.json` | Python | — |
| `tools/thumb.py` | Thumbnail from a still + title | Python | Pillow |

Quick start (from the project folder): `bash <kit>/tools/setup.sh <project>` → `python3 timing.py voice.mp3 script.txt --out work` → edit `web/story.js` + the world section of `web/main.js` → `node render.mjs stills/a "..."` → `python3 sheet.py ...` → `python3 audio.py && python3 mix.py voice.mp3 music.wav sfx.wav` → `node render.mjs frames "0-<N-1>"` → `bash finish.sh "Title"`.
