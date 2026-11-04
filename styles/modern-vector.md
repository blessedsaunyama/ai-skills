# Style: Modern vector

Clean, bright, flat-design explainer look: geometric shapes, no outlines, soft gradients and soft drop shadows, smooth "pop" entrances. Default for Tech/programming; great for ads, product and app explainers.

- **Engine:** A (`engines/py2d`). Speed: medium (shadows and gradients cost about 1.5× Flat 2D).
- **Look:** no outlines; gentle top-light gradient on every actor; soft drop shadow; cool indigo/teal palette with a coral accent; no paper texture.
- **Characters:** simple geometric people (round head, pill torso, rounded limbs), modern clothes, short hair; minimal face (dot eyes, small smile).
- **Motion rules:** elements pop in with a slight overshoot (0.5 s); smooth eased camera; quick but never jerky.
- **Text:** bold sans titles, code cards with a dark theme, captions on a dark rounded box.
- **Don't:** add hand-drawn wobble or paper grain (that's Whiteboard or Storybook).

```json
{
  "name": "modern-vector",
  "body": "geo",
  "palette": {
    "sky": ["#6c7cff", "#c3cbff"], "storm_sky": ["#3d4470", "#7f86a8"],
    "sun": "#ffd166", "ground": "#5fc9a8", "ground_line": "#1f2340",
    "hills": ["#a7b3ff", "#8b9af5", "#6f80e6"], "hill_line": false,
    "ink": "#1f2340", "paper": "#f4f6ff",
    "skin": ["#c98f63", "#8a5a3a", "#f1c7a4"],
    "cloth": ["#ff6b6b", "#4ecdc4", "#ffd166", "#6c7cff", "#f4f6ff"], "accent": "#ff6b6b",
    "shirt": ["#ff6b6b", "#4ecdc4", "#6c7cff", "#ffd166"], "pants": ["#1f2340", "#3d4470", "#2b6f77"],
    "hair": ["#1f1a2e", "#5a3a28", "#c9732f"],
    "wood": "#b07a4f", "wood_line": "#6e4a2f", "pitch": "#4a3a46",
    "cloud": "#ffffff", "storm_cloud": "#8890b5", "rain": "#dfe6ff",
    "beard": "#f4f6ff", "foliage": "#3fb58e", "animal": "#f4f6ff", "text_bg": "#1f2340", "text": "#ffffff",
    "box": ["#6c7cff", "#4ecdc4", "#ff6b6b", "#ffd166"], "box_text": "#ffffff", "highlight": "#ffd166",
    "wall": "#f4f6ff", "roof": "#ff6b6b", "window": "#c3cbff", "shadow": "#1f2340", "title": "#ffffff", "label": "#e8ebff"
  },
  "line": {"width": 0, "wobble": 0.0, "boil_every": 0, "outline_all": false},
  "fill": "gradient",
  "shade": 0.22,
  "proportions": {"head": 0.22, "limb": 0.075},
  "face": {"eyes": "dot", "blush": false, "mouth": true},
  "texture": {"grain": 0.0, "paper": 0.0, "vignette": 0.06},
  "motion": {"hold": 1, "bounce": 0.03, "ease": "inOut"},
  "fx": {"enter": "pop", "dur": 0.5, "shadow": 0.28, "float": 5},
  "manim": {"bg": "#5d6cf0", "ink": "#ffffff", "muted": "#dfe3ff", "accent": "#ff6b6b", "good": "#4ecdc4", "bad": "#ff6b6b", "highlight": "#ffd166", "boxes": ["#1f2340", "#2b3170", "#3d4470", "#4ecdc4"], "box_text": "#ffffff"},
  "captions": {"size": 60, "color": "#ffffff", "highlight": "#ffd166", "outline": "#1f2340", "outline_w": 0, "box": true, "box_color": "#1f2340", "upper": false, "max_words": 5}
}
```
