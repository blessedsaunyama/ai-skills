# Style: Toon 3D

Hand-drawn 2D cartoon characters (bean bodies, round heads, thick-and-thin ink) standing in a colourful 3D world with black ink outlines, toon shading, painted textures, soft shadows and a shallow depth of field. Cinematic camera glides. Great for Bible stories, history moments and kids' stories when the computer can afford it.

- **Engine:** C (`engines/toon3d`). Speed: **slow** (CPU WebGL: ≈ 5–8 s per frame at 720p on a 4-thread laptop). LITE computers get stills only; STANDARD gets 5 s previews unless the user confirms a longer render. Suggest Storybook or Flat 2D when time matters.
- **Look:** saturated but warm colours, black world ink (~2.5 px at 1080), cel-shaded 3D, painted stone/plaster/wood/grass textures, golden-hour or day light presets, vignette, lens blur on backgrounds.
- **Characters:** 2D cards from the toon library: the Bible cast (`T.BIBLE`) or the generic cast. Middle-Eastern skin tones for Bible stories; God the Father is never a figure (`fxGlory` light only); angels without wings unless the text describes them.
- **Motion rules:** every shot has camera movement (glide, push-in, crane); every character breathes (`idle`) and blinks; one or two characters per 9:16 shot, staged in depth.
- **Don't:** fill 16:9 shots with empty sides (add trees, walls, people), or cut faster than ~1.5 s per shot.

Presets for this engine live in the project's `story.js` (`LIGHTS`) and `world.js` (materials), not in this file. The block below is read by the shared tools (captions).

```json
{
  "name": "toon-3d",
  "engine": "toon3d",
  "palette": {"paper": "#f2e6d0", "ink": "#241726", "title": "#ffffff", "label": "#f2e6d0", "accent": "#e4572e", "highlight": "#ffd25a"},
  "captions": {"size": 62, "color": "#ffffff", "highlight": "#ffd25a", "outline": "#241726", "outline_w": 5, "box": false, "upper": false, "max_words": 4}
}
```
