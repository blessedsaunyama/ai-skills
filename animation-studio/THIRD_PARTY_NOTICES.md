# Third-party notices

animation-studio is MIT-licensed (see LICENSE). This file lists third-party material that is **bundled** or **called**.

## Bundled code
| File | Origin | Licence | Changes |
|---|---|---|---|
| `engines/toon3d/vendor/three.module.js` | three.js r160 (npm `three@0.160.0`, build/three.module.js) | MIT | none: byte-identical (SHA-256 76dea815...a495) |
| `engines/toon3d/vendor/toon.ts` | mromidev/claude-animated-shorts, `templates/bridge/toon.ts` | MIT | none: identical to upstream (checked line by line, commit e3b817b) |

The rest of `engines/toon3d/` (main.js, paint.js, motion.js, roman.js, biblical.js, index.html, render.mjs, cast.mjs) was written for the author's earlier cartoon-short kit **on top of** the toon library and the look values documented in mromidev/claude-animated-shorts (a line-by-line comparison found no other copied code). It is released here under this project's MIT licence, with credit to that project. The upstream repository's reference frames (taken from a third-party channel) are **not** included in any form.

### three.js licence
```
The MIT License

Copyright © 2010-2023 three.js authors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

### claude-animated-shorts licence (toon.ts)
```
MIT License

Copyright (c) 2026 Mr omi

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files
(the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

## Programs called, not bundled (installed by the user)
| Program | Licence | Used for |
|---|---|---|
| Python | PSF License | runs every tool |
| numpy | BSD-3-Clause | image maths (pip, inside the skill's .venv) |
| Pillow | MIT-CMU (HPND) | drawing (pip, inside the skill's .venv) |
| FFmpeg | LGPL/GPL (depends on the build) | encoding, audio, captions (libass), QA |
| piper-tts (optional) | GPL-3.0-or-later | free local voice; installed by the user into the skill's .venv, imported only by `shared/voice.py`. animation-studio does not bundle or modify it |
| onnxruntime (optional, Piper dependency) | MIT | runs the Piper voice model |
| Manim Community (optional, engine B) | MIT | maths/diagram animation, installed into the skill's .venv |
| Manim's dependencies (pycairo, ManimPango, scipy, PyAV, skia-pathops, moderngl, ...) | LGPL-2.1/MPL-1.1 (pycairo), MIT, BSD | installed by pip with Manim; never bundled |
| LaTeX (optional: MiKTeX / MacTeX / TeX Live) | LPPL and others | nicer maths typesetting; Manim falls back to plain text without it |
| espeak-ng data (inside piper-tts) | GPL-3.0 | phonemes for Piper |
| Node.js (engine C) | MIT | runs the Toon 3D frame writer |
| Blender (engine D) | GPL-2.0-or-later (GPL-3.0 as a whole) | called in background mode with our scripts; installed by the user, never bundled. Our scripts only use Blender's Python API at run time |
| Playwright + Chromium (engine C) | Apache-2.0 (Playwright), BSD and others (Chromium) | headless browser that renders the three.js scenes; installed by the user with npm |

## Voice models (downloaded by the user, never bundled)
Piper voices come from huggingface.co/rhasspy/piper-voices (models: MIT). Each voice also inherits the licence of its **training data**. `shared/voice.py` only allows voices whose data licence was checked:
| Voice | Training data licence |
|---|---|
| en_US-ljspeech-medium / -high (default) | LJ Speech: public domain |
Voices such as en_US-lessac (research-only licence) and en_US-ryan (CC BY-NC-SA) are refused by default because published videos may break their terms.

## Content
- Bible text is fetched at run time from BibleGateway (KJV, public domain) and is not bundled.
- Ellen G. White text is fetched at run time from egwwritings.org and is not bundled. The reference lists in `content/bible/` contain only titles, chapter names and links.
- No fonts, images, music or sound files are bundled. Text uses the user's system fonts; music and SFX are synthesized in code.

## Origin of the code
All code in this folder was written for this project by Blessed Tanaka Saunyama with AI assistance (Claude), including `shared/timing.py`, `shared/mix.py`, `shared/srt.py` and the Bible tools, which were adapted from the author's earlier cartoon-short and Bible-story kits.
