# Design spec (JSON) – every field

One spec = one design at one size. Paths are relative to the spec file. Only `type`, `size`
and `title` are needed; everything else is optional. (The `//` comments below are explanations only: real JSON files have no comments.)

```json
{
  "name": "music-day-a4",                 // output file names
  "type": "event",                        // event | flyer | poster | social | banner | thumbnail | certificate
  "size": "a4",                           // key from sizes.md, "a4:landscape", or {"w":..,"h":..,"unit":"px|mm"}
  "orientation": "portrait",              // or "landscape" (flips any rectangle)
  "print": {"bleed_mm": 3, "crop_marks": true},   // print sizes only
  "brand": "msu-sda-youth",               // saved brand (tools/brands.py): fills missing fields
  "style": "youthful",                    // youthful | modern | formal | elegant (sets palette, fonts, decoration)
  "palette": "youthful",                  // mood name, OR ["#main", "#accent", "#pop"], OR {"bg": "#..", "accent": "#.."}
  "fonts": "bebas-poppins",               // montserrat-opensans | playfair-lato | bebas-poppins
  "decoration": "orbs",                   // orbs | rings | border | arcs (normally set by style)
  "layout": "split",                      // split | hero | bold (event types)
  "photo_side": "right",                  // left | right
  "language": "en",                       // optional: en | sn | nd day/month names for ISO dates (default en)

  "host_line": "MSU SDA Youth presents",
  "title": "Youth Music Day",             // "\n" forces a line break
  "subtitle": "Sing • Praise • Connect",
  "highlight_line": 1,                    // title line in accent colour (-1 none)
  "date": "2026-11-21",                   // ISO -> "Saturday 21 November 2026"; any other text is used as written
  "start": "09:00", "end": "16:00",       // "09:00" -> "9 AM"; any other text ("9am till late") is used as written
  "time_format": "12h",                   // 12h -> "9 AM – 4 PM", 24h -> "09:00 – 16:00"
  "venue": "Main Church Hall, Gweru",
  "extra_info": [{"icon": "ticket", "text": "Entry free"}],   // icons: calendar clock pin phone chat mail globe at mic user ticket
  "speaker": {"name": "…", "label": "Guest speaker", "role": "Youth Leader", "photo": "work/speaker-cutout.png"},
  "body": "A paragraph (good for tech flyers).",
  "bullets": ["Point one", "Point two"],
  "cta": "Register: example.org/join",

  "logos": [{"file": "work/assets/logos/youth.png", "pos": "top-left", "scale": 1.0}],
           // pos: top-left top-center top-right center bottom-left bottom-center bottom-right
  "contacts": [{"type": "phone", "value": "0772 123 456"}, {"type": "whatsapp", "value": "..."},
               {"type": "email", "value": "..."}, {"type": "website", "value": "..."},
               {"type": "facebook", "value": "PageName"}, {"type": "instagram", "value": "handle"}],
           // optional "label": "Info" -> "Info: +263 ..."
  "background": {"photo": "work/assets/photos/hall.jpg", "overlay": 0.75, "focus_y": 0.4},

  "title_scale": 1.0, "text_scale": 1.0, "logo_scale": 1.0, "darken": 0,
  "seed": 3,                              // changes the confetti / dots pattern
  "credits": ["Photo: <title>, <source>, <licence>"]
}
```

## Thumbnail extras
`badge` ("Tutorial", "Ep 3"), `title` (2–6 words, use `\n`), `subtitle` (small line), `speaker.photo` (cut-out best).

## Certificate fields
`title` ("Certificate"), `subtitle` ("of Appreciation"), `presented_line`, `recipient`, `reason`, `date`,
`signatories` [{"name", "title"}], `paper` (inner colour, default warm white), `logos`.

## Layouts
- **split**: text column + speaker cut-out standing on the contact bar (tall sizes: header across the top).
- **hero**: centred title, big photo in the middle with a name ribbon, details under it.
- **bold**: huge title, small round speaker photo next to the name, details as cards.
- Without a speaker photo, event layouts use **bold**.

## Contact checks (tools/validate.py)
Local Zimbabwe numbers (07x…) become +263 7x xxx xxxx; other countries need +code. Emails and web
addresses are checked; handles get an @. `make.py` stops on invalid values and lists them.
