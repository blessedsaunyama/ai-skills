# Style: Storybook

A warm, painted picture-book look: soft shapes, gentle light-to-shadow shading, a warm brown line instead of black ink, watercolour paper texture and a soft vignette. Default for Bible stories, and lovely for bedtime stories and young audiences.

- **Engine:** A (`engines/py2d`). Speed: medium (the soft shading costs about 1.5× Flat 2D).
- **Look:** rounded shapes, thin warm-brown outline, each character and prop shaded from a soft top light, paper grain, warm vignette, muted earthy palette.
- **Characters:** slightly bigger heads, rounded robes, rosy cheeks, oval eyes. Middle-Eastern skin tones for Bible stories.
- **Motion rules:** slow, gentle eased moves; small walk bounce; no snappy cartoon timing.
- **Don't:** use neon colours, hard black outlines or fast cuts.

```json
{
  "name": "storybook",
  "body": "soft",
  "palette": {
    "sky": ["#9cc3d8", "#f3dfb8"], "storm_sky": ["#59607a", "#a99e96"],
    "sun": "#fff0c2", "ground": "#b8b36a", "ground_line": "#6b4a32",
    "hills": ["#b9c9a8", "#9fb48a", "#86a06f"], "hill_line": false,
    "ink": "#5a3d2b", "paper": "#f6eedd",
    "skin": ["#c48a5c", "#a66e46", "#8c5a38"],
    "cloth": ["#c9a46a", "#7f9cb3", "#b5654a", "#8ea36b", "#efe2c6"], "accent": "#c0552f",
    "wood": "#9a6a40", "wood_line": "#5e3d24", "pitch": "#5a4030",
    "cloud": "#fbf5e8", "storm_cloud": "#7c7a86", "rain": "#dfe8ef",
    "beard": "#f3efe6", "foliage": "#6f9452", "animal": "#f1e8d6", "text_bg": "#4a3324", "text": "#fbf3e2"
  },
  "line": {"width": 2.2, "wobble": 0.6, "boil_every": 0, "outline_all": true},
  "fill": "soft",
  "shade": 0.35,
  "proportions": {"head": 0.24, "limb": 0.075},
  "face": {"eyes": "oval", "blush": true, "mouth": true},
  "texture": {"grain": 0.018, "paper": 0.05, "vignette": 0.28},
  "motion": {"hold": 1, "bounce": 0.03, "ease": "gentle"},
  "fx": {"enter": "fade", "dur": 0.7, "shadow": 0, "float": 3},
  "captions": {"size": 58, "color": "#fff8e8", "highlight": "#ffd88a", "outline": "#4a3324", "outline_w": 4, "box": false, "upper": false, "max_words": 5}
}
```
