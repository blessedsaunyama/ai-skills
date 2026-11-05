# Brand kit

Put a business's logo, colours, font and contact details on any video, in every format, without covering the platform's buttons.

## Where brands live
- **Your brands:** the user folder, never inside the skill (so private details are never published or zipped):
  Windows `%LOCALAPPDATA%\animation-studio\brands\<id>\` · macOS `~/Library/Application Support/animation-studio/brands/<id>/` · Linux `~/.local/share/animation-studio/brands/<id>/`
- **Shipped with the skill:** `brands/_template.yaml` and `brands/sample/` (a fictional bakery with reserved example contacts).
- One folder per brand: `brand.yaml`, `logo.png` (transparent, trimmed), optional `fonts/` (OFL font + `OFL.txt`).

## brand.yaml
| Field | Example | Rule |
|---|---|---|
| `name` | Sunrise Bakery | required |
| `tagline` | Fresh bread every morning | optional |
| `website` | https://example.com | must be a valid http(s) URL (https:// is added if missing) |
| `logo` | logo.png | PNG/SVG converted to a transparent, trimmed PNG by `brand.py logo` |
| `phones` | `- +1 202 555 0143 \| Orders` | international format (+country code); text after `\|` is a label |
| `whatsapp` | +1 202 555 0178 | international format; the wa.me link is derived |
| `emails` | `- hello@example.com` | name@domain.tld |
| `socials` | `- https://linkedin.com/company/...` | valid URLs |
| `colours` | primary / secondary / accent | `#rrggbb` |
| `font` | name, file, licence | **SIL Open Font License only** (checked inside the font file); otherwise system fonts are used |
| `cta` | Order today | default call to action on the end card |

**Never invent contact details.** Use only what the owner typed, or what they confirmed from their own website. Leave a field empty rather than guess.

## Commands
```
python shared/brand.py list
python shared/brand.py new mybrand                       # then one field at a time:
python shared/brand.py set mybrand name "My Company"
python shared/brand.py set mybrand phones+ "+263 77 000 0000 | Calls only"
python shared/brand.py logo mybrand path/to/logo.png      # transparent background, trimmed
python shared/brand.py font mybrand "Space Grotesk"       # only from google/fonts' OFL folder
python shared/brand.py validate mybrand
python shared/brand.py recolor mybrand --style modern-vector --out style_mybrand.md   # use as "style" in scene.json
python shared/brand.py apply mybrand frames_9x16 branded_9x16 --fmt 9x16 --watermark tr,9,90,logo --lower-third 0.6,3.6 --end-card 2.5 --captions
```
`apply` works on the frames of **any engine** (2D, Manim, Toon 3D, Blender). With an end card the video gets longer: mix the audio with `mix.py --seconds <new length>`.

## Options (asked in the wizard)
| Option | Values | Notes |
|---|---|---|
| Watermark | on/off · corner `tl/tr/bl/br` · size % of the short side · opacity % · `logo` or `logo+name` | placed inside the safe zone; a soft contrast plate is added automatically when the scene behind is too similar |
| Lower third | start, end (s) | brand bar with logo, name and WhatsApp/phone; sits above the caption band when captions are burned in |
| End card | duration (s), CTA text | logo, name, tagline, CTA button and contacts; measured and centred inside the safe zone, shrunk if needed |
| Recolour the style | yes/no | backgrounds, boxes, highlights and captions in the brand colours |

## Defaults by content
| Content | Watermark | End card |
|---|---|---|
| Ad / promo (General story/ad used for a business) | ON | ON |
| General story (not an ad) | off (ask) | off (ask) |
| Bible story | OFF | off (ask) |
| Tech / Maths education | OFF | off (ask) |

The brand end card belongs to the user's business. It is separate from the optional "Made with animation-studio" card (off by default).

## Safe zones
Text and logos stay inside each format's UI safe zone (`shared/formats.md`): 9:16 keeps clear of the TikTok/Reels/Shorts side buttons and the caption area at the bottom; 16:9 keeps 5 % title-safe margins for TVs and projectors.
