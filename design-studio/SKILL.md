---
name: design-studio
description: Make flyers, posters, banners/roll-ups, social posts, certificates, YouTube thumbnails and simple original logos from the user's real logos, photos and text (no AI-generated people), with print-ready PDF, PNG and editable SVG outputs, and edit existing SVG, AI, PDF or CDR designs (change text, colours, pictures). Use for any request to design or edit a flyer, poster, banner, social media post, story/status, certificate, thumbnail or logo.
---

# design-studio

By Blessed Tanaka Saunyama · MIT licence · standalone (needs no other skill).

Composes **real assets** (the user's logos + real photos + text) into designs with an SVG
layout engine, then renders PNG / PDF / JPG. Text is turned into vector outlines with bundled
OFL fonts, so every renderer shows the same result.

`SKILL_DIR` below = the folder this `SKILL.md` is in. Run tools with `python3` (or `python`
if that is the one that has Pillow): `python3 "$SKILL_DIR/tools/<tool>.py" ...`

## Hard rules (never break)
1. **Never AI-generate faces, people or realistic scenes.** Use only the user's uploads and
   openly licensed images (CC0 / public domain / licence that allows reuse); record every credit in the spec's `credits`.
2. **No other brands' logos, no copied designs.** reference/ images guide layout, mood and colour only.
3. **Work on copies.** Never edit, overwrite or move the user's original files.
4. **Ask before installing anything** (run the setup check first and show what is missing).
5. **Validate contacts** (phone, email, URL, handles) before they go on a design. `make.py` refuses invalid ones.
6. Never invent facts (dates, venues, names, prices). Missing info = ask, or leave it out.
7. No machine-specific paths in specs you save for the user; paths in a spec are relative to the spec file.

## Step 0: setup check (first use in a session)
```
python3 "$SKILL_DIR/tools/check_setup.py"
```
Needs Pillow + fontTools + one renderer: cairosvg (fastest), Inkscape, or Chromium via Playwright, used in that order.
rembg (background removal) and psd-tools are optional: offer them only when needed.
If something is missing, show the list with the install command and **ask** before running it.
Windows note: pip's cairosvg needs `libcairo-2.dll`. The tools borrow it automatically from an installed Inkscape
(or the GTK3 runtime), so "Inkscape installed" makes cairosvg work too. Without either, Chromium is used.

## Where files go
- **Inputs:** the user's project folder (the current folder unless told otherwise) with subfolders
  `logos/` (PNG, transparent preferred), `photos/` (real photos), `reference/` (optional inspiration).
  On claude.ai uploads arrive in one folder: `assets.py scan` guesses the role from file names; confirm with the user.
- **Work + output:** `designs/<design-name>/` inside the project folder (on claude.ai: the outputs folder).
  `work/` holds copies and cutouts; the spec JSON sits next to it so the design can be edited later.

## The wizard
Parse the request first and **pre-fill everything it already says**. Ask only what is missing,
**one question at a time**. Use the multiple-choice tool (AskUserQuestion) where it exists,
otherwise numbered options. Always add a free-text "anything else?" at the end. Full question
texts: [references/wizard.md](references/wizard.md).

1. **Type:** Event flyer | Poster | Banner/roll-up | Social post | Certificate | Thumbnail | Logo (→ see *Logos* below).
2. **Event details** (events only): event name, date, start time, end time (optional), venue,
   host line (e.g. "MSU SDA presents"), guest speaker name (+ role).
   **Use the user's own wording exactly** (any language). Dates/times written as words are printed as given;
   ISO dates (2026-11-21) and 24 h times (09:00) are formatted for them ("Saturday 21 November 2026", "9 AM").
3. **Assets:** ask the user to put files into `logos/`, `photos/`, `reference/`, then run
   `python3 "$SKILL_DIR/tools/assets.py" scan <project>` and **list back** what was found (size, transparent or not, notes).
   Offer a background cut-out for speaker photos (see *Photos*).
4. **Logo placement:** per logo: top-left | top-center | top-right | center (big, above the title) | bottom-left | bottom-center | bottom-right.
5. **Contacts:** tick which apply (phone, WhatsApp, email, Facebook, Instagram, TikTok, YouTube, X, website), then ask for each value.
6. **Size / platform:** always show **ratio first, pixels beside it**, e.g. `1:1 square post (1080 x 1080 px)`,
   `9:16 story / WhatsApp status (1080 x 1920 px)`, `A4 flyer (210 x 297 mm, 2480 x 3508 px)`.
   Every rectangle can be portrait or landscape: ask which. Full list: `python3 "$SKILL_DIR/tools/sizes.py"`
   and [references/sizes.md](references/sizes.md). For print sizes ask: **bleed** (3 mm, default yes) and **crop marks** (yes/no).
   One design can be made in several sizes (one spec per size).
7. **Look:** palette (a saved brand, brand colours from the logo via `assets.py palette logos/x.png`, or a mood:
   youthful, modern, formal, elegant, warm, fresh, royal, tech, light), fonts (Montserrat + Open Sans,
   Playfair Display + Lato, Bebas Neue + Poppins, or "choose for me" = match the style), style (formal / modern / youthful / elegant).
8. **Free text:** "Anything else? (extra lines, a paragraph for tech flyers, bullet points, a call to action, things to avoid)".
9. **Plan card** (below) → ask: **Start** | **Change something** | **Give me 3 variations**.

Saved brands: `python3 "$SKILL_DIR/tools/brands.py" list`. If any exist, ask *"Which brand is this for?"* as
part of step 7 (default: ask every time, never assume). A brand fills only what the user did not say.
Offer to save a new brand at the end (stored outside the skill, in the user's app-data folder).

### Plan card (show before building)
```
PLAN: Youth Music Day flyer
Size     A4 portrait (210 x 297 mm, 2480 x 3508 px) + 9:16 story (1080 x 1920 px)
Print    PDF 300 dpi, 3 mm bleed, crop marks
Text     host "MSU SDA Youth presents" / title "Youth Music Day" / sub "Sing • Praise • Connect"
Details  Saturday 21 November 2026 · 9 AM – 4 PM · Main Church Hall, Gweru
Speaker  Guest speaker: <name> (photo: photos/speaker.jpg, background removed)
Logos    youth.png top-left · church.png top-right
Contacts +263 77 212 3456 (phone) · +263 71 234 5678 (WhatsApp) · youth@example.org · FB @...
Look     youthful · purple/gold · Bebas Neue + Poppins
Layout   title + details on the left, speaker cut-out on the right standing on the contact bar
```

## Build
1. Copy assets: `python3 "$SKILL_DIR/tools/assets.py" copy <project> designs/<name>/work`
2. (Optional) cut-out: see *Photos*.
3. Write `designs/<name>/<name>-<size>.json` (fields: [references/spec.md](references/spec.md)).
4. Build:
   ```
   python3 "$SKILL_DIR/tools/make.py" designs/<name>/<name>-a4.json --out designs/<name>/a4 --variations 3
   ```
   Defaults: screen sizes → PNG + SVG; print sizes → PDF (vector, bleed / crop marks as set) + PNG share copy (150 dpi) + SVG.
   Add `--formats png,pdf,svg,jpg` to choose. Thumbnails always get a JPG under 2 MB.
   With several variations a side-by-side sheet `<name>-variations.png` is made: **show it** (open / display the image).
5. Read the JSON summary. Fix every **warning** (text too long, low-resolution photo, missing glyph) before showing,
   or tell the user plainly.
6. Look at the result yourself (view the PNG): check overlaps, cut-off text, contrast, and that text is inside the safe zone.
7. Show the stills and ask: **Pick a variation** | **Change something** | **Done**.

Variations: v1 = the spec as written; v2/v3 change layout (split / hero / bold), photo side or palette.
Build only the chosen one again with `--only N`, or copy its changes into the spec.

## Edit loop
Edit the spec, rebuild, show again. Common phrases → spec changes:

| User says | Change in the spec |
|---|---|
| make the title bigger / smaller | `"title_scale": 1.2` / `0.85` |
| all text bigger | `"text_scale": 1.1` |
| darker background | `"darken": 0.25` (0–0.7) |
| swap the photo side | `"photo_side": "left"` / `"right"` |
| different layout | `"layout": "split"` / `"hero"` / `"bold"` |
| other colours | `"palette": "royal"` or `["#1D3C8F", "#F2B705"]` |
| bigger logos | `"logo_scale": 1.3` |
| highlight another title line | `"highlight_line": 0` (first line; -1 none) |
| photo as background | `"background": {"photo": "work/assets/photos/x.jpg", "overlay": 0.75}` |
| different fonts | `"fonts": "playfair-lato"` / `"montserrat-opensans"` / `"bebas-poppins"` |

Keep earlier versions: write a new output folder (`a4-v2/`) instead of overwriting, unless the user says overwrite is fine.

## Edit an existing design file (SVG, AI, PDF, EPS, CDR)
For files made elsewhere (Canva/Figma SVG export, Illustrator .ai, a PDF, CorelDRAW .cdr, Inkscape SVG):
```
python3 "$SKILL_DIR/tools/edit_file.py" open  <file> --work designs/<name>/work [--page 2]
python3 "$SKILL_DIR/tools/edit_file.py" edit  designs/<name>/work/<file>.svg --out designs/<name>/work/<file>-v2.svg \
        --text ID "new text" --replace "old" "new" --color "#OLD" "#NEW" --image ID new.png --hide ID
python3 "$SKILL_DIR/tools/edit_file.py" export designs/<name>/work/<file>-v2.svg --formats png,pdf [--dpi 300]
```
1. `open` copies (SVG) or converts (AI/PDF/EPS/CDR via Inkscape) to a working SVG and **lists** texts, images,
   colours and fonts with ids. Show the user that list in plain words, then ask what to change.
2. `edit` writes a NEW file each time (keep versions). It reports how many places changed: 0 means nothing matched.
3. `export` renders PNG/PDF. Fonts that aren't installed but are bundled (or sit in a `fonts/` folder next to the
   file) are loaded via Chromium automatically. A font found nowhere → ask the user for the font file, or swap it.
4. Look at the PNG before showing it.

Limits (tell the user plainly):
- Results are SVG / PDF / PNG. It **cannot save back** to .ai, .cdr, .psd or .indd.
- Text that was turned into outlines (common in print PDFs and logos) can be **recoloured, not retyped**.
- **InDesign (.indd)**, Affinity and Figma files can't be read: ask for an SVG, PDF or IDML export.
- AI files need "PDF compatible" saving (Illustrator's default). EPS/PS need Ghostscript (ask before installing).
- PSD → `psd_import.py` (read layers and text), then rebuild as a design-studio spec to edit.
- Multi-page PDFs: one page at a time (`--page N`).

## ArtCraft power tools (optional: only when installed)
If `python3 "$SKILL_DIR/tools/artcraft.py" check` shows VectorCraft / PhotoCraft / DesignCraft, **prefer them for
existing files**: they open AND save back the original format, keep layers, and are fast (1–10 s).
```
python3 "$SKILL_DIR/tools/artcraft.py" info <file>                      # texts / layers / stories, colours, fonts
python3 "$SKILL_DIR/tools/artcraft.py" edit <file> --out designs/<name>/<file>-v2.<ext> --also designs/<name>/<file>-v2.png \
        --replace "old" "new" --text ID "new" --color "#OLD" "#NEW" --font "Missing=Bundled" --hide ID
python3 "$SKILL_DIR/tools/artcraft.py" cmyk <print.pdf> --out <print>-cmyk.pdf [--standard x1a|x4]
```
| File | App | Can do |
|---|---|---|
| .ai .eps .pdf .svg .afdesign .dxf | VectorCraft | find/replace and set text, recolour everything (incl. gradients, images), replace fonts, hide objects, CMYK; save as .ai/.eps/.pdf/.svg/.psd/.png |
| .psd .psb .tif | PhotoCraft | edit type layers, map missing fonts, hide/show layers, CMYK; save back as .psd with layers |
| .idml .designcraft | DesignCraft | set a story's text, find/change, replace fonts; export IDML/PDF/EPUB (InDesign reopens the IDML; .indd itself can't be read) |

- Fonts: run `artcraft.py install-fonts` **once, after asking** (copies the bundled OFL fonts into VectorCraft's
  own Fonts folder). DesignCraft needs no install: the tool puts fonts in a `Document Fonts` folder beside the copy.
  Any font still missing → ask the user for the font file, or map it with `--font "Missing=Montserrat"`.
- IDs come from `info` (VectorCraft object ids, PhotoCraft layer ids, DesignCraft story numbers).
- **CMYK for print shops:** after `make.py`, offer `artcraft.py cmyk` → PDF/X-1a (all CMYK, transparency
  flattened, bleed and crop marks kept; ~1 min and ~20 MB for A4). Use `--standard x4` if the printer wants transparency kept.
- Not installed → use `edit_file.py` (Inkscape) above and say that saving back to .ai/.psd/.eps or CMYK needs ArtCraft (free: getartcraft.com).
- Use only the real CLI commands (`vectorcraft-cli run/info/convert/commands`, `photocraft-cli run/info/convert`,
  `designcraft-cli run`). Check `<app>-cli commands` before using any command not listed here; never guess flags.

## Photos
- **Cut-out (speaker):** offer it when a speaker photo is a normal photo. Needs rembg (ask before installing;
  first run downloads ~170 MB and can take several minutes on a slow PC):
  `python3 "$SKILL_DIR/tools/cutout.py" work/assets/photos/speaker.jpg --out work/speaker-cutout.png [--crop x0,y0,x1,y1]`
  Use `--crop` (fractions) to keep one person. **Look at the result**: rembg keeps objects that touch the person
  (plants, microphones, other people). If it is messy, tell the user and offer the framed (arch) photo instead (just use the original photo).
- A transparent PNG is used as a cut-out (halo + glow, standing on the contact bar); a normal photo goes into an arch frame.
- Print warns when a photo is too small (under ~180 dpi at its printed size).
- **PSD:** `python3 "$SKILL_DIR/tools/psd_import.py" file.psd --out work/psd` exports `flat.png`, image layers and text.
  If it reports COMPLEX, use flat.png as a reference or ask the user for a flattened PNG.
- **reference/ images:** use them for mood, colour (`assets.py palette`) and rough arrangement only. Say so if asked to copy one.
- Stock images: only openly licensed ones the user approves (e.g. Wikimedia Commons CC0/PD, Unsplash, Pexels);
  record title, source and licence in `credits`. Avoid photos with visible brand logos.

## Logos (original, simple)
```
python3 "$SKILL_DIR/tools/logo.py" --name "Harvest Youth Hub" --initials HY --tagline "Grow together" --colors "#1D3C8F,#F2B705" --style modern --out designs/logo
```
Makes 3 concepts (monogram, spark, rise), each as colour / mono / reversed / icon-only (SVG + PNG) and a `logos-sheet.png`.
Before showing, go through [references/logos.md](references/logos.md) (no resemblance to known marks, no church/
denomination emblems, readable small). Tell the user to do a quick reverse-image search before registering a logo.
Never recreate an existing logo (including church or denomination logos): ask for the official file instead.

## Certificates and thumbnails
- Certificate: `type: certificate`, `size: certificate` (A4 landscape): `title`, `subtitle`, `recipient`, `reason`,
  `date`, `signatories` [{name, title}]. Ask for exact name spellings.
- Thumbnail: `type: thumbnail`, `size: youtube`: 2–6 big words (use `\n` for line breaks), optional `badge`,
  a cut-out works best. Text stays left/right of the person and away from the bottom-right time badge.

## Delivery
List the files (PNG for WhatsApp/social, PDF for the printer, `-editable.svg` + `fonts/` for Inkscape/Illustrator,
`CREDITS.txt`). Print tips: PDFs are RGB; most local printers accept them. If a printer asks for CMYK, use `artcraft.py cmyk`
(PDF/X-1a) when ArtCraft is installed, otherwise ask the print shop to convert. Mention roll-ups are rendered at 150 dpi (normal for large format).

## Troubleshooting
- "No SVG renderer found" → `check_setup.py` and ask which to install.
- Chromium render fails → `npx playwright install chromium` (ask first).
- Text warning "does not fit" → shorten text, drop the body, or use a bigger size.
- Fonts: only the bundled OFL fonts in `fonts/` (licences in `fonts/licenses/`). Shona and Ndebele use plain Latin letters: all fonts cover them.
