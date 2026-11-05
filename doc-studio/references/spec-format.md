# The spec (spec.json)

One JSON file describes the whole document. `make_doc.py` renders it to every format with the same look. Paths (images) are relative to the spec file. Text fields accept `**bold**`, `*italic*` and `[link text](https://…)`.

## Top level
| Key | Required | Meaning |
|---|---|---|
| `title` | yes | Document title |
| `subtitle`, `author`, `date`, `audience` | no | Shown under the title (and on the title slide) |
| `pack` | yes | `general` · `sda` · `education` · `health` · `tech` · `business` |
| `doc_type` | no | study, report, essay, notes, newsletter, slides, worksheet, quiz, plan, cv (for your own planning) |
| `language` | no | `en` (default) or `sn` (Shona: labels such as "Pfupiso" are translated) |
| `page` / `orientation` | no | `A4` (default), `A5`, `Letter`, `Legal` / `portrait` (default) or `landscape` |
| `style` | no | `print` (default: ink-saving) or `screen` (more colour, slightly bigger text) |
| `theme` | no | `classic` · `modern` · `church` · `school` · `minimal` (default follows the pack) |
| `brand` | no | saved brand id (`tools/brand.py list`) |
| `formats` | no | default formats if `--formats` isn't given, e.g. `["pdf","docx"]` |
| `summary` | **yes** | `{"topic": "...", "key_points": ["...", "..."], "takeaway": "..."}` |
| `disclaimer` | health: yes | one line, shown right after the summary |
| `blocks` | yes | the body, in order (below) |
| `slides` | no | explicit slides for PPTX (otherwise slides are built from the blocks) |
| `sheets` | no | explicit sheets for XLSX/CSV (otherwise each `table` block becomes a sheet) |
| `references` | yes | `[{"text": "Author, *Title* (Publisher, Year)", "url": "https://…"}]`: only sources you actually opened |
| `credits` | if images | `[{"image": "file.jpg", "author": "…", "licence": "CC BY-SA 4.0", "source": "https://…"}]` |
| `answer_key` | no | `false` hides the quiz answer key in DOCX/PDF (it is always a separate sheet in XLSX) |

## Blocks
```json
{"type": "heading", "text": "1. The Sabbath in Creation", "level": 1}
{"type": "paragraph", "text": "Plain text with **bold**.", "align": "center"}
{"type": "bullets", "items": ["one", "two"]}
{"type": "numbered", "items": ["first", "second"]}
{"type": "verse", "ref": "Genesis 2:2-3", "version": "KJV", "text": "<exact text from bible_fetch.py>"}
{"type": "egw", "ref": "PP 47.1", "book": "Patriarchs and Prophets", "text": "<exact paragraph text>", "url": "https://text.egwwritings.org/read/84.230#...", "verified": true}
{"type": "quote", "text": "…", "source": "Name, Work"}
{"type": "callout", "kind": "note|tip|warning|todo", "title": "optional label", "text": "…"}
{"type": "table", "columns": ["Item", "Cost"], "rows": [["Paper", 12.5]], "caption": "Table 1", "widths": [3, 1]}
{"type": "image", "path": "images/map.png", "caption": "…", "credit": "Photo: Name, CC BY 4.0", "width_pct": 80, "own": false}
{"type": "question", "q": "Which day…?", "choices": ["A text", "B text", "C text", "D text"], "answer": "B", "explain": "Gen 2:3"}
{"type": "question", "q": "Explain in your own words…", "lines": 4}
{"type": "toc"}
{"type": "pagebreak"}
```
- `verse` and `egw` text must be **copied from the fetched source file**; `--sources` checks it word for word (`...` may shorten a quote).
- `egw` with `"verified": false` (or missing) is printed with an **UNVERIFIED** label.
- `callout` kind `todo` is for "ADD YOUR …" prompts (education pack).
- `question` blocks become a numbered quiz, an answer key (DOCX/PDF), a marked Quiz sheet (XLSX) and `quiz.csv`.
- `image` with `"own": true` needs no credit (the user's own photo or AI-drawn art).

## Slides (PPTX)
If `slides` is present, the deck is: title slide → summary slide → your slides → references slide. Layouts:
```json
{"layout": "section", "title": "Part 2", "text": "optional subtitle"}
{"layout": "bullets", "title": "…", "subtitle": "…", "text": "optional intro line", "bullets": ["…", "  sub-point (two leading spaces)"], "image": "images/x.png", "notes": "speaker notes"}
{"layout": "two-col", "title": "…", "left_title": "Before", "left": ["…"], "right_title": "After", "right": ["…"]}
{"layout": "code", "title": "…", "text": "one line of context", "code": "print('hi')", "caption": "Python 3.12"}
{"layout": "verse", "kind": "verse|egw", "text": "…", "ref": "John 3:16 (KJV)"}
{"layout": "image", "title": "…", "image": "images/x.png", "caption": "credit"}
{"layout": "table", "title": "…", "columns": ["…"], "rows": [["…"]]}
```
Rules: ≤ 6 bullets, ≤ 12 words each; put detail in `notes`. A 10-slide deck = title + summary + 7 content + references.

## Sheets (XLSX / CSV)
```json
{"name": "Budget", "columns": ["Item", "Qty", "Unit cost", "Total"],
 "rows": [["Paper", 10, 2.5, "=B2*C2"], ["Ink", 2, 15, "=B3*C3"]],
 "widths": [24, 8, 12, 12], "number_formats": [null, "0", "#,##0.00", "#,##0.00"],
 "totals": [{"label": "Total", "column": "D", "func": "SUM"}]}
```
Formulas start with `=` and are kept as live Excel formulas (CSV writes them as text, so prefer values in CSV-only jobs).
