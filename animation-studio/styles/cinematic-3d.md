# Style: Cinematic 3D

Realistic-leaning 3D with film lighting: a physical sky, a low warm sun, soft shadows, atmospheric haze, shallow depth of field and slow, heavy camera moves. Procedural materials (stone, earth, bark, foliage, plaster, cloth) with no image textures, so nothing needs a licence. For solemn Bible moments (dawn at the tomb, a quiet hillside), epic landscapes and product-style hero shots.

- **Engine:** D (`engines/blender`, Blender in background mode). **Eevee** for previews (fast, GPU), **Cycles** for finals on POWER computers (path-traced, GPU).
- **Tier limits:** LITE: stills only. STANDARD: Eevee only, ≤ 5 s at 720p, low samples. POWER: Cycles on the GPU, no length limit (still estimate first).
- **Look:** AgX colour (soft highlights), a slightly warm grade, haze for depth (Cycles only: an Eevee world volume can black out the frame on some GPUs), f/2.8–4 depth of field, 35–50 mm lenses, a vignette from the lighting rather than post.
- **Characters:** this engine is for places, objects and light. People, if needed, appear as distant silhouettes; close character acting belongs to Toon 3D or the 2D styles. Never a figure for God the Father: light, cloud, sky.
- **Motion rules:** one slow move per shot (dolly, crane, orbit ≤ 15°), eased in and out; no handheld shake; hold 3–6 s per shot.

```json
{
  "name": "cinematic-3d",
  "engine": "blender",
  "palette": {"paper": "#1a1612", "ink": "#f2e8d8", "title": "#f7efe2", "label": "#d8ccb8", "accent": "#e0a458", "highlight": "#f5c77a"},
  "materials": {
    "rock":       {"color": "#8c7a62", "roughness": 0.92, "noise": 3.0, "var": 0.22, "bump": 0.7},
    "rock_light": {"color": "#a8977e", "roughness": 0.85, "noise": 4.0, "var": 0.12, "bump": 0.45},
    "ground":     {"color": "#7d6f52", "roughness": 0.95, "noise": 1.5, "var": 0.22, "bump": 0.3},
    "grass":      {"color": "#5d6b34", "roughness": 0.9, "noise": 6.0, "var": 0.25, "bump": 0.2},
    "bark":       {"color": "#4a3a2c", "roughness": 0.9, "noise": 8.0, "var": 0.2, "bump": 0.5},
    "foliage":    {"color": "#5f7041", "roughness": 0.8, "noise": 5.0, "var": 0.25, "bump": 0.15, "subsurface": 0.1},
    "plaster":    {"color": "#d8c8ac", "roughness": 0.85, "noise": 2.0, "var": 0.1, "bump": 0.15},
    "cloth":      {"color": "#8a6a4a", "roughness": 0.95, "noise": 10.0, "var": 0.08, "bump": 0.1, "sheen": 0.4},
    "dark":       {"color": "#0b0907", "roughness": 1.0},
    "gold":       {"color": "#d9a845", "roughness": 0.3, "metallic": 1.0}
  },
  "lights": {
    "dawn":  {"sun_elev": 6.0, "sun_azim": 70, "sun_strength": 5.5, "sun_color": "#ffbe80", "sky_strength": 0.35, "haze": 0.004, "haze_color": "#f0c8a0", "exposure": -0.2},
    "day":   {"sun_elev": 45, "sun_azim": 140, "sun_strength": 5.0, "sun_color": "#fff4e6", "sky_strength": 1.0, "haze": 0.004, "haze_color": "#dfe8f2", "exposure": 0.0},
    "dusk":  {"sun_elev": 3.0, "sun_azim": 260, "sun_strength": 3.5, "sun_color": "#ff9a5a", "sky_strength": 0.5, "haze": 0.015, "haze_color": "#e8a080", "exposure": 0.4},
    "night": {"sun_elev": -8, "sun_azim": 200, "sun_strength": 0.0, "sun_color": "#9ab0ff", "sky_strength": 0.05, "haze": 0.006, "haze_color": "#1a2238", "exposure": 1.5, "moon": 0.4}
  },
  "grade": {"view": "AgX", "look": "AgX - Medium High Contrast"},
  "captions": {"size": 56, "color": "#f7efe2", "highlight": "#f5c77a", "outline": "#1a1612", "outline_w": 4, "box": false, "upper": false, "max_words": 5}
}
```
