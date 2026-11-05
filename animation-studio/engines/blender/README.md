# Engine D: Blender (background mode)

Cinematic 3D from a `scene.json`: procedural landscapes and props, a physical sky with a low sun, soft shadows, depth of field and AgX colour. Blender runs headless (`blender -b`) from Python scripts; nothing is ever opened on screen. Blender is GPL and is **called, never bundled**.

- **Eevee** (`--engine eevee`, default): fast GPU raster, used for previews and on STANDARD computers. Works on integrated graphics (tested: Intel HD 520).
- **Cycles** (`--engine cycles`): path tracing on the GPU (OptiX/CUDA/HIP/Metal/oneAPI picked automatically), for finals on POWER computers. Adds atmospheric haze (a world volume), which is skipped in Eevee because it can black out frames on some GPUs.
- **Speed (i5-6300U + HD 520, 720p Eevee, 12 samples):** ≈ 70–90 s to build the scene, then ≈ 10–12 s per frame. A 3 s shot ≈ 16 min. Always run `shared/estimate.py --engine blender` first.

| Tier | Allowed |
|---|---|
| LITE | stills only (≤ 6 frames), 720p, Eevee |
| STANDARD | Eevee only, ≤ 5 s (150 frames), ≤ 720p, 12 samples (preview) / 32 (final) |
| POWER | Eevee or Cycles on the GPU, any length and size; Cycles 128 samples |
`--override-limits` lifts them only after the user accepted a clear warning. render.py detects the tier with `shared/hwcheck.py` (or pass `--tier`).

## Smoke test (one command, from the skill folder)
```
python engines/blender/render.py examples/bible-tomb-blender/scene.json --fmt 16x9 --frames 0 --out _smoke_blender
```
Expect `_smoke_blender/f0000.jpg` after about 1–2 minutes. Delete the folder afterwards.

## Command
```
python engines/blender/render.py SCENE.json --fmt 16x9|9x16|1x1|4x5 [--quality preview|final] [--engine eevee|cycles] [--samples N]
       [--out DIR] [--frames 0-89 | 0,45,89] [--tier STANDARD] [--override-limits] [--force] [--save-blend scene.blend]
```
Only missing frames are rendered (re-run = resume; frames are written atomically). One render at a time, low CPU priority, pauses (exit code 4) below 15 % free RAM. `--save-blend` writes the built scene so the user can open it in Blender.

## scene.json
Coordinates are Blender's: metres, **Z is up**.
```json
{
  "fps": 30, "duration": 3, "style": "cinematic-3d", "light": "dawn",
  "camera": [{"t": 0, "pos": [1.6, -9.5, 1.6], "look": [0.9, 3, 1.35], "lens": 30}, {"t": 3, "pos": [1.2, -7.4, 1.5], "look": [0.8, 3, 1.3], "lens": 32}],
  "camera_9x16": [ ... ],
  "dof": {"focus": [0.8, 3, 1.2], "fstop": 4.0},
  "elements": [ {"type": "ground"}, {"type": "cliff", "openings": [ ... ]}, {"type": "disc"}, {"type": "tree"} ]
}
```
- **Camera:** keys with smootherstep easing; `lens` in mm on a 24 mm-high sensor (vertical fit), so every format keeps the same vertical view and wider formats see more at the sides. `camera_<fmt>` reframes a format.
- **Light:** a preset name from the style (`dawn`, `day`, `dusk`, `night`) + optional `light_override` (sun_elev, sun_azim, sun_strength, sun_color, sky_strength, haze, exposure).
| Element | Properties |
|---|---|
| `ground` | `size, bumps, bump_size, material` (displaced grid) |
| `cliff` | `pos, size [x, y, z], rough, rough_size, material, openings: [{pos, radius, depth, rot, scale}]` (rock face; openings are cut with a boolean and lined with a dark void) |
| `disc` | `pos, rot, radius, thickness, material` (a rolling stone, millstone, wheel) |
| `rock` | `pos, size, seed, material` |
| `tree` | `pos, height, seed` (olive-like) |
| `box`, `cylinder`, `sphere` | `pos, rot, size, bevel, material` (walls, houses, altars, props) |
- **Materials** are names from the style preset (`rock, rock_light, ground, grass, bark, foliage, plaster, cloth, dark, gold`) or a hex colour. All procedural: no image files, nothing to license.

## Files
`render.py` (runs on the user's Python: tier limits, lock, priority, RAM guard, resume, progress) · `build_scene.py` (runs inside Blender: builds the scene, renders the frames). Tested with Blender 5.2.3 LTS; version-specific names (Eevee id, sky type, colour looks) are set with fallbacks.
