# Style: Stickman

Hand-drawn stick figures on off-white paper. Clear, fast, funny and cheap to render. Good for explainers, tech, quick stories, and young audiences when the subject is light. For a solemn Bible moment, slow the motion and use fewer jokes.

- **Engine:** A (`engines/py2d`). Speed: fastest of all styles.
- **Look:** ink lines with a slight wobble that "boils" (redraws) every 2 frames; animated on twos (12 fps feel); a single accent colour per scene; paper texture and light grain; no fills except the sky wash and the accent.
- **Characters:** circle head, single-line body and limbs, dot eyes. Identify people with one prop or accent (Noah = white beard + headcloth line).
- **Motion rules:** snappy, with small anticipation; hold poses on twos; no smooth gradients.
- **Don't:** use it for violent or very sad scenes (stick figures make them feel flippant).

The JSON block below is the preset the engine reads. Edit values here, not in code.

```json
{
  "name": "stickman",
  "body": "stick",
  "palette": {
    "sky": ["#f4f1e8", "#f4f1e8"], "storm_sky": ["#d9d6cf", "#e9e6de"],
    "sun": "#f2c14e", "ground": "#f4f1e8", "ground_line": "#2b2b2b",
    "hills": ["#e7e3d8", "#dedad0", "#d3cfc4"], "hill_line": true,
    "ink": "#2b2b2b", "paper": "#f4f1e8",
    "skin": ["#f4f1e8"], "cloth": ["#2b2b2b"], "accent": "#e4572e",
    "wood": "#f4f1e8", "wood_line": "#2b2b2b", "pitch": "#f4f1e8",
    "cloud": "#f4f1e8", "storm_cloud": "#cfcbc2", "rain": "#4a6fa5",
    "beard": "#f4f1e8", "foliage": "#f4f1e8", "animal": "#f4f1e8", "text_bg": "#2b2b2b", "text": "#f4f1e8"
  },
  "line": {"width": 4.5, "wobble": 1.6, "boil_every": 2, "outline_all": true},
  "fill": "paper",
  "shade": 0.0,
  "proportions": {"head": 0.17, "limb": 0.0},
  "face": {"eyes": "dot", "blush": false, "mouth": true},
  "texture": {"grain": 0.035, "paper": 0.05, "vignette": 0.0},
  "motion": {"hold": 2, "bounce": 0.05, "ease": "snap"},
  "fx": {"enter": "fade", "dur": 0.4, "shadow": 0, "float": 0},
  "captions": {"size": 58, "color": "#2b2b2b", "highlight": "#e4572e", "outline": "#ffffff", "outline_w": 0, "box": true, "box_color": "#ffffff", "upper": false, "max_words": 4}
}
```
