# Style: Whiteboard

A hand-drawn marker explainer on a white board: black marker outlines, light marker colouring, and every element "drawn on" by a marker pen as it appears. Great for teaching, Bible study, step-by-step processes and tech concepts.

- **Engine:** A (`engines/py2d`). Speed: fast (like Flat 2D).
- **Look:** clean white board, thick slightly wobbly black marker line, pastel marker fills, no gradients, no vignette.
- **Characters:** simple outlined figures with light colouring; skin in light warm marker tones (never default to European features for Bible stories).
- **Motion rules:** elements appear by being drawn (a left-to-right wipe with a marker pen at the tip, about 0.9 s each). Keep the camera mostly still; build the picture up piece by piece in narration order.
- **Don't:** move many things at once, or use dark full-screen backgrounds.

```json
{
  "name": "whiteboard",
  "body": "bean",
  "palette": {
    "sky": ["#fdfdfb", "#f4f4f0"], "storm_sky": ["#eceef2", "#e2e5ea"],
    "sun": "#f5c542", "ground": "#fdfdfb", "ground_line": "#1d1d1f",
    "hills": ["#fdfdfb", "#fafaf6", "#f6f6f1"], "hill_line": true,
    "ink": "#1d1d1f", "paper": "#fdfdfb",
    "skin": ["#ecc9a5", "#d6a57a", "#bf8a60"],
    "cloth": ["#9ecbf0", "#f5b971", "#f29e9e", "#b5dc9a", "#ffffff"], "accent": "#e4572e",
    "shirt": ["#9ecbf0", "#f29e9e", "#b5dc9a", "#f5b971"], "pants": ["#8a94a8", "#b0a089", "#7a8c9a"],
    "hair": ["#3a3a3a", "#6a4a30", "#b07a3a"],
    "wood": "#e7c79a", "wood_line": "#1d1d1f", "pitch": "#c9b59a",
    "cloud": "#ffffff", "storm_cloud": "#d9dde3", "rain": "#4a7ab5",
    "beard": "#ffffff", "foliage": "#b5dc9a", "animal": "#ffffff", "text_bg": "#1d1d1f", "text": "#ffffff",
    "code_bg": "#ffffff", "code_bar": "#f0f0ec", "code_text": "#1d1d1f", "code_kw": "#2a5db0", "code_str": "#2e8b57",
    "code_num": "#c0392b", "code_com": "#8a8a8a", "code_fn": "#8e44ad", "term_bg": "#f4f4f0", "term_text": "#1d1d1f", "term_prompt": "#2e8b57",
    "box": ["#9ecbf0", "#b5dc9a", "#f5b971", "#f29e9e"], "box_text": "#1d1d1f", "highlight": "#ffe066",
    "wall": "#ffffff", "roof": "#f29e9e", "window": "#cfe6f7"
  },
  "line": {"width": 4.0, "wobble": 0.9, "boil_every": 0, "outline_all": true},
  "fill": "flat",
  "shade": 0.0,
  "proportions": {"head": 0.2, "limb": 0.06},
  "face": {"eyes": "dot", "blush": false, "mouth": true},
  "texture": {"grain": 0.008, "paper": 0.0, "vignette": 0.04},
  "motion": {"hold": 1, "bounce": 0.03, "ease": "inOut"},
  "fx": {"enter": "draw", "dur": 0.9, "shadow": 0, "float": 0},
  "manim": {"bg": "#fdfdfb", "ink": "#1d1d1f", "muted": "#6b6b6b", "accent": "#2a5db0", "good": "#2e9d5b", "bad": "#d1453b", "highlight": "#f0a500", "boxes": ["#9ecbf0", "#b5dc9a", "#f5b971", "#f29e9e"], "box_text": "#1d1d1f"},
  "captions": {"size": 58, "color": "#1d1d1f", "highlight": "#2a5db0", "outline": "#ffffff", "outline_w": 0, "box": true, "box_color": "#ffffff", "upper": false, "max_words": 5}
}
```
