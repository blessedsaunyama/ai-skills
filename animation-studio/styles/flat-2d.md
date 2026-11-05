# Style: Flat 2D

Bright, clean cartoon with solid colour fills and a medium dark outline. The general-purpose default (General story/ad) and a good fit for kids' Bible stories.

- **Engine:** A (`engines/py2d`). Speed: fast.
- **Look:** flat fills, one shade step on big shapes (no gradients on characters), even ink outline, crisp edges, light grain only.
- **Characters:** bean-shaped robe/torso, round head, thick limbs with rounded ends, dot eyes, simple mouth. Middle-Eastern skin tones for Bible stories.
- **Motion rules:** smooth eased moves on ones (30 fps), gentle walk bounce, slight overshoot on gestures.
- **Don't:** add photo textures or soft gradients (that is Storybook or Modern vector).

```json
{
  "name": "flat-2d",
  "body": "bean",
  "palette": {
    "sky": ["#5fb8e8", "#bfe6f5"], "storm_sky": ["#4a5a70", "#8a98a8"],
    "sun": "#ffd25a", "ground": "#8cc062", "ground_line": "#2a2433",
    "hills": ["#a6d38a", "#7fb85f", "#5f9e4a"], "hill_line": false,
    "ink": "#2a2433", "paper": "#ffffff",
    "skin": ["#c98f63", "#a8714b", "#8a5a3a"],
    "cloth": ["#e0a43a", "#4e8cc2", "#c8553d", "#7a9e5a", "#efe4cf"], "accent": "#e4572e",
    "wood": "#8a5a34", "wood_line": "#5e3a20", "pitch": "#4a3426",
    "cloud": "#ffffff", "storm_cloud": "#6b7686", "rain": "#cfe3f5",
    "beard": "#f2f0ea", "foliage": "#4f9a48", "animal": "#f4efe6", "text_bg": "#2a2433", "text": "#ffffff"
  },
  "line": {"width": 3.2, "wobble": 0.0, "boil_every": 0, "outline_all": true},
  "fill": "flat",
  "shade": 0.0,
  "proportions": {"head": 0.21, "limb": 0.07},
  "face": {"eyes": "dot", "blush": false, "mouth": true},
  "texture": {"grain": 0.012, "paper": 0.0, "vignette": 0.12},
  "motion": {"hold": 1, "bounce": 0.04, "ease": "inOut"},
  "fx": {"enter": "pop", "dur": 0.45, "shadow": 0, "float": 4},
  "captions": {"size": 64, "color": "#ffffff", "highlight": "#ffd25a", "outline": "#2a2433", "outline_w": 5, "box": false, "upper": true, "max_words": 4}
}
```
