# Images

Three choices in the wizard: **none**, **my images**, **AI-drawn SVG**. Never Google Images, never another organisation's logo, never a real person's photo unless the user supplied it.

## My images
The user puts pictures in `./images/` (next to where they work, or anywhere they say) plus `captions.csv`:
```csv
file,caption,credit,licence,source,own
church.jpg,Our church on Sabbath morning,,,,yes
map.png,Map of ancient Babylon,Jane Doe,CC BY-SA 4.0,https://commons.wikimedia.org/wiki/File:...,
```
- `own = yes` → the user's own photo (no credit needed). Otherwise fill `credit`, `licence`, `source`.
- In the spec: `{"type": "image", "path": "../../images/church.jpg"}` (paths are relative to spec.json; copying the images into `documents/<slug>/images/` is simpler). make_doc reads captions.csv from the image's folder, fills caption/credit, adds the credit to the Image credits list, and shrinks photos larger than 2000 px.
- No captions.csv → ask the user for caption and source of each image (or whether it's their own).

## Openly licensed images (when the user asks you to find some)
Only from sources with clear licences: Wikimedia Commons, Openverse, Unsplash, Pexels, Pixabay, public-domain government/NASA/NOAA images. Record author, licence and the page URL you opened. Prefer CC0 / public domain / CC BY. Don't use NC (non-commercial) images for business documents. Download only after telling the user what you're taking.

## AI-drawn SVG
Write the SVG yourself, save it as `documents/<slug>/images/<name>.svg`, then use it like any image (`"own": true`). make_doc converts it to PNG (needs svglib + rlPyCairo; the setup check shows them).
- `viewBox` set, width ~1200, simple flat shapes, the document's theme colours (or brand colours), white or transparent background.
- Text: few words, ≥ 28 px at 1200 width, a common font family (`Arial, Helvetica, sans-serif`). Diagrams beat decoration: timelines, flowcharts, labelled diagrams, maps drawn as simple shapes (label as "not to scale").
- Never draw: real logos or trademarks, real people's likenesses, God the Father as a human figure (SDA), gore.
- Credit line in `credits`: `{"image": "<name>.svg", "author": "AI-drawn for this document", "licence": "free to use with this document"}` (or set `"own": true`).
- Look at the converted PNG (in `<out>/.cache/`) before delivering; svglib ignores some advanced SVG features (filters, some CSS): keep to basic shapes, paths, text and linear gradients.
