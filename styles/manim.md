# Style: Manim (maths and diagrams)

Precise, calm, mathematical motion on a deep navy background: shapes that transform into each other, numbers that move to where they are used, step-by-step working. Default for Maths/education; also for algorithms, data structures and architecture diagrams in Tech.

- **Engine:** B (`engines/manim`). Speed: fast for simple scenes (≈ 0.1–0.3 s per frame at 720p); heavy 3D scenes are slower.
- **Look:** deep navy background, off-white text, one highlight colour (warm yellow) for "look here", green for correct, coral for rejected. Rounded boxes for data, thin lines, generous spacing.
- **Motion rules:** one idea at a time; transform instead of cutting; ~0.6–1 s per move; pause on each result while the voice explains it.
- **Text:** maths with LaTeX when installed, otherwise plain text with Unicode symbols (×, ÷, ², √, ≤); never fail for lack of LaTeX.
- Other looks: render the same scene with `--style whiteboard` (white board, dark ink) or `--style modern-vector` (Engine B reads the palette of any preset).
- **Don't:** copy the look of a specific well-known maths channel; keep this palette or the user's own.

```json
{
  "name": "manim",
  "engine": "manim",
  "palette": {
    "paper": "#14182b", "ink": "#eef1f8", "title": "#eef1f8", "label": "#9aa3c0", "accent": "#ff7a6b",
    "highlight": "#ffd166", "box": ["#3d6fd1", "#2f9e8f", "#8a5cc7", "#d1823d"],
    "sky": ["#14182b", "#14182b"], "storm_sky": ["#14182b", "#14182b"], "ground": "#14182b"
  },
  "manim": {"bg": "#14182b", "ink": "#eef1f8", "muted": "#9aa3c0", "accent": "#ff7a6b", "good": "#5fd38d", "bad": "#ff7a6b",
            "highlight": "#ffd166", "boxes": ["#3d6fd1", "#2f9e8f", "#8a5cc7", "#d1823d"]},
  "captions": {"size": 56, "color": "#eef1f8", "highlight": "#ffd166", "outline": "#14182b", "outline_w": 0, "box": true, "box_color": "#0b0e1c", "upper": false, "max_words": 5}
}
```
