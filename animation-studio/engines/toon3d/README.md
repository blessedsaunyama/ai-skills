# Engine C: Toon 3D (three.js + Playwright)

2D cartoon character **cards** standing in an inked, painted **3D world**: black ink outlines on the world, toon shading, painted textures, lens blur, gliding cameras. Rendered by three.js r160 inside headless Chromium with CPU WebGL (SwiftShader), so no GPU is needed, but it is slow.

- **Speed (i5-6300U laptop):** ≈ 5–8 s per frame at 720p, more at 1080p. A 5 s preview takes 12–22 min. Always run `shared/estimate.py --engine toon3d` first.
- **Tier limits (enforced by render.py):** LITE: stills only (≤ 6 frames). STANDARD: ≤ 5 s (150 frames) unless `--confirm-long` after the user agreed. POWER (`--power`, when hwcheck says POWER): no limit.
- Needs: node 22.6+, Playwright + Chromium (`npm i -g playwright` then `npx playwright install chromium`). Check: `python shared/setup_check.py --engine toon3d`.

## Smoke test (one command, from the skill folder)
```
python engines/toon3d/render.py examples/bible-shepherd-toon3d --fmt 9x16 --frames 30 --out _smoke_toon3d
```
Expect `_smoke_toon3d/f0030.jpg` (≈ 20–40 s, mostly Chromium warm-up) and a `spf=` line. Delete the folder afterwards.

## Command
```
python engines/toon3d/render.py PROJECT --fmt 9x16|16x9|1x1|4x5 [--quality preview|final] [--out DIR] [--frames 0-149 | 0,75,149]
       [--master 1920x1920] [--confirm-long] [--power] [--force]
```
`PROJECT` is a folder with `story.js` and `world.js` (and any helper `.js`). render.py builds `OUT/_web/` from the engine + `vendor/` + the project, so the project folder stays clean. Frames are written atomically; re-running resumes. One render at a time, low priority, pauses (exit code 4) below 15 % free RAM.

## The project files
**`world.js`** builds the 3D set once:
```js
export function buildWorld(ctx) {
  const { THREE, M, P, T, world, add, tbox, toon, water } = ctx;   // M = painted toon materials, P = textures, T = toon library
  const field = add(new THREE.PlaneGeometry(400, 400), M.grass, 0, 0, 0, world, { cast: false }); field.rotation.x = -Math.PI / 2;
  return { ground: 0, update: (state, f) => {}, clouds: true };     // update gets worldAt(f) from story.js
}
```
`ctx`: `THREE`, `T` (toon library: Pen, BIBLE cast, fx...), `P` (painted canvas textures: stone, plaster, planks, grass, dirt, marble, roof...), `M` (ready materials: grass, dirt, stone, plaster, plaster2, roof, marble, plank, beam, trunk, cypress, pine, bush, hill, hillFar, mount, door, window, wood, iron, bronze...), `scene`, `world` (group), `add(geo, mat, x, y, z, parent, {cast})`, `box`, `tbox(w, h, d, tile)` (world-scaled UVs), `toon({color})`, `texM(canvas)`, `water(w, d, y, x, z)` (animated river), `rx` (deg→rad), `FMT`.

**`story.js`** is the shot plan. It exports `FPS, TOTAL, SHOTS, shotAt(f), LIGHTS, lightFor(S, f), camAt(f), dofAt(f), worldAt(f), actorsAt(f, T), fxAt(f, T)`. See `examples/bible-shepherd-toon3d/story.js` (5 s, two shots) for a complete small example.
- **Cameras:** keys `{ f, pos, look, fov, roll, ease, fovBy }` with `camFromKeys` from `motion.js` (smooth glides, splines with `path`, a gentle push-in on holds, `kicks` for impacts).
- **Actors** are cards: `{ key, draw: (p) => T.bibleFront(p, 'shepherd', opts), x, y, z, s, flip, tint, order, blob, shadow }`. `key` must change only when the drawing changes (round values with `q()`), so the canvas isn't redrawn every frame. Cast: `T.BIBLE` (shepherdBoy, shepherd, prophet, youngProphet, jesus, disciple, woman, womanB, child, villager, king, official, soldierIsr, giant, angel) and `T.OUTFITS` via `romanFront`. Options: `expr, L, R (arm poses), facing, look, blink, tilt, headTilt, bob, step, seed`, Bible extras `wings` (only when the text describes them), `glowK`.
- **Effects:** `T.fxSheep, fxLion, fxGlory (God's presence: light only, never a figure), fxStone, fxSling, fxCloud, fxDust, fxSplash, fxPuff, fxBurst, fxStars...` as cards with `blob: false, shadow: false`.
- **Life:** `idle(f, seed)` (breathing, sway) on every character, `blinkAt(f, seed)`, `walk(f, f0, speed)`.
- Test the cast quickly: `node engines/toon3d/tools/cast.mjs stills/cast.png` (run inside a built `_web` folder, `WEB=<out>/_web`).

## Formats and camera maths
Camera `fov` is the **vertical field of view of a 1080x1920 frame**. `fit=height` (default, BEST mode) keeps that vertical fov in every format, so wider formats see more at the sides: fill them (trees, walls, crowds) or narrow the view per format with `fovBy: { '16x9': 30, '1x1': 36 }` on any key. A shot can also branch on `FMT.key`.
| Format | half-width at 4 m, fov 40 | Staging |
|---|---|---|
| 9:16 | ±0.82 m | one or two characters, staged in depth; vertical moves |
| 4:5 | ±1.16 m | two-shots side by side |
| 1:1 | ±1.46 m | three across, action in the middle |
| 16:9 | ±2.59 m | groups and landscapes; fill the sides |
Previews render at 2/3 size with the same framing (`&scale=` in index.html). **FAST mode:** `--master 1920x1920` (fit=focal) renders one master; crop it with `python shared/formats.py crop`; keep faces and key props inside the centre-safe box (e.g. 1080x1080). Ink width and blur scale with the picture.

## Files and licences
`engine/main.js` (renderer, ink + crease outlines, lens blur, grade, cards, sky, water helper; worlds come from `world.js`) · `engine/paint.js` (painted textures) · `engine/motion.js` (easing, cameras, idle, format maths) · `engine/roman.js`, `engine/biblical.js` (cast built on the toon library) · `engine/index.html` · `tools/render.mjs` (Playwright frame writer) · `tools/cast.mjs` (cast sheet) · `vendor/three.module.js` (three.js r160, MIT, byte-identical to the npm release) · `vendor/toon.ts` (from mromidev/claude-animated-shorts, MIT, unchanged) + their licence files. See THIRD_PARTY_NOTICES.md.
