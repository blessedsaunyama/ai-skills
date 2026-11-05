# Sizes (ratio first, pixels beside it)

Generated from `tools/sizes.py`. Use the key in a spec: `"size": "story"`. Add `"orientation": "landscape"` (or write `a4:landscape`) to flip any rectangle.

```
SCREEN (pixels)
  square       1:1 square post                1080 x 1080 px   - Instagram / Facebook / WhatsApp post
  portrait     4:5 portrait post              1080 x 1350 px   - Instagram / Facebook feed (largest in feed)
  3x4          3:4 portrait                   1080 x 1440 px   - Instagram new grid / general portrait
  2x3          2:3 tall portrait              1080 x 1620 px   - Pinterest / tall poster post
  story        9:16 story / status            1080 x 1920 px   - IG / FB story, WhatsApp status, TikTok, Reels (top 250 px and bottom 340 px are covered by the app)
  landscape    16:9 landscape                 1920 x 1080 px   - Projector slide, TV screen, YouTube banner art, X post
  4x3          4:3 landscape                  1440 x 1080 px   - Older projectors, tablets
  5x4          5:4 landscape                  1350 x 1080 px   - Near-square landscape
  3x2          3:2 landscape                  1620 x 1080 px   - Photo-style landscape
  youtube      16:9 YouTube thumbnail         1280 x 720 px   - Keep text away from the bottom-right corner (video length badge). Must be under 2 MB
  link         1.91:1 link preview            1200 x 630 px   - Website / WhatsApp link preview, FB link post
  fb-cover     2.63:1 Facebook page cover     1640 x 624 px   - Phones crop the sides: keep text in the middle 66 %
  fb-event     1.91:1 Facebook event cover    1920 x 1005 px   - Facebook event header
  x-header     3:1 X / Twitter header         1500 x 500 px   - Profile photo covers bottom-left
  linkedin     4:1 LinkedIn banner            1584 x 396 px   - Profile photo covers the left

PRINT (mm, rendered at the dpi shown)
  a5           A5 flyer (148 x 210 mm)        1748 x 2480 px @ 300 dpi - Handout flyer
  a4           A4 flyer / poster (210 x 297 mm) 2480 x 3508 px @ 300 dpi - Standard flyer, notice board
  a3           A3 poster (297 x 420 mm)       3508 x 4961 px @ 300 dpi - Poster
  a2           A2 poster (420 x 594 mm)       3307 x 4677 px @ 200 dpi - Large poster
  certificate  A4 landscape certificate       3508 x 2480 px @ 300 dpi - Certificate (A4 sideways)
  rollup       Roll-up banner 85 x 200 cm     5020 x 11811 px @ 150 dpi - Bottom ~20 cm sits low / in the stand: keep key info above it
  rollup-100   Roll-up banner 100 x 200 cm    5906 x 11811 px @ 150 dpi - Wide roll-up
  banner-3x1   3:1 PVC banner 3 x 1 m         11811 x 3937 px @ 100 dpi - Outdoor banner (eyelets near edges)
  banner-2x1   2:1 PVC banner 2 x 1 m         7874 x 3937 px @ 100 dpi - Outdoor banner

Any rectangle can be flipped: add --landscape / --portrait (e.g. a4:landscape, story -> 16:9).
```

Custom size: `"size": {"w": 1200, "h": 1500, "unit": "px"}` or `{"w": 100, "h": 150, "unit": "mm"}` (300 dpi).

## Safe zones
- Stories (9:16): top ~13 % and bottom ~18 % are covered by the app (profile, reply bar). Contacts become a rounded box above that.
- YouTube thumbnail: bottom-right corner shows the video length.
- Facebook cover: phones crop the sides; text stays in the middle two-thirds.
- Print: keep text 4-5 % inside the edge; background runs into the 3 mm bleed.
- Roll-up: the bottom ~20 cm is low and often hidden by the stand base: no key info there.
