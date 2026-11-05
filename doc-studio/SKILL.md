---
name: doc-studio
description: Create or edit documents on any topic (Word .docx, PowerPoint .pptx, Excel .xlsx, CSV, PDF) with a short wizard, content packs for SDA/Church, Education, Health, Tech and Business, verified sources and optional branding. Use for any request to write, make, design, format or edit a document, report, study, lesson, worksheet, quiz, slides, newsletter, plan, tracker or CV.
---

# doc-studio

By Blessed Tanaka Saunyama, MIT licence. A **standalone** skill: everything it needs is inside this folder. It turns a request into polished documents (DOCX, PPTX, XLSX, CSV, PDF) and edits existing ones in their own format.

**How it works:** you write the content once as a JSON *spec* (`references/spec-format.md`), then `tools/make_doc.py` renders it to any of the five formats with the same look. Editing uses `tools/edit_doc.py` on a copy.

## Paths and commands
- `SKILL_DIR` = the folder containing this SKILL.md. All tools are at `SKILL_DIR/tools/`. Never hard-code a user's path.
- Run Python as `python3` if it exists, otherwise `python` (Windows often has only `python`). Below, `py` means whichever works.
- **Work folder** for each job: `./documents/<slug>/` in the user's current folder (spec.json, `sources/`, outputs). Never write into SKILL_DIR.

## Golden rules (always)
1. **Never invent** facts, statistics, quotes, Bible verses, EGW quotes, citations, URLs, API names or version numbers. Verify or mark **UNVERIFIED** and tell the user.
2. **Every document opens with a SUMMARY block** (topic, key points, takeaway) and **ends with References** (+ image credits when images are used). `make_doc.py` enforces this.
3. **Edit on a copy.** Never overwrite the user's file without asking (edit_doc.py refuses unless told).
4. **Install nothing without asking.** Run the setup check, show what's missing, ask, then install.
5. **Images:** only the user's own, AI-drawn SVG, or openly licensed images with credits. No Google Images, no other organisations' logos.
6. Plain, simple language with the user. One question at a time, multiple choice where possible.

## Step 0: setup check (first time in a session)
`py SKILL_DIR/tools/setup_check.py` (add `--net` for SDA/health/tech jobs that need web checks). If anything required is missing, show the list and the install command, **ask**, then `py SKILL_DIR/tools/setup_check.py --install`. Optional: `svglib` + `rlPyCairo` for SVG pictures.

## The wizard
First **parse the request** and pre-fill everything it already says. Then ask **only what's missing**, one question at a time. Defaults (use without asking unless the request suggests otherwise): page **A4**, language **English**, **no brand**, **print** style, length to suit the type.

| # | Question | Options |
|---|---|---|
| 1 | New or edit? | New document · Edit an existing one (ask for the file; go to *Editing* below) |
| 2 | Content pack | General · SDA/Church · Education/School · Health · Tech · Business/Report |
| 3 | Document type | study/lesson · report · essay · notes · newsletter · slides · worksheet · quiz · plan/tracker · CV |
| 4 | Topic, audience, length | free text; length as pages / slides / questions / rows |
| 5 | Output format(s) | DOCX · PPTX · XLSX · CSV · PDF (multi-select; suggest the natural one, see `references/doc-types.md`) |
| 6 | Layout | theme (classic · modern · church · school · minimal) × style (print · screen) × page (A4 · Letter · A5, portrait/landscape) |
| 7 | Images | none · my images (`./images/` + `captions.csv`) · AI-drawn SVG |
| 8 | Branding | none · a saved brand (`tools/brand.py list`) · new brand (ask the fields one by one: name, tagline, phone(s), email(s), website, logo file, colours) |
| 9 | Plan card | show it, then **Start** or **Change** |

Language: English by default; Shona (`"language": "sn"`) when asked. Writing in Shona: natural Shona, not word-for-word translation; Scripture only from a published Shona Bible (`tools/bible_fetch_yv.py`), never machine-translated. Ndebele and others: say they aren't supported yet.

**Plan card** (show exactly this shape, then wait):
```
PLAN: <title>
Pack / type : SDA/Church · topical study        Audience: youth, 15-25
Formats     : PDF + DOCX                         Length  : ~4 pages
Layout      : church theme · print · A4          Language: English
Images      : none                               Brand   : none
Sources     : KJV (BibleGateway), EGW (egwwritings.org), <others>
Sections    : Summary · 1 … · 2 … · 3 … · Questions · References
Start, or change something?
```

## Build (after Start)
1. **Research** with the pack rules (table below). Save fetched source text in `documents/<slug>/sources/` (e.g. `scripture.md`, `egw.md`, `notes.md` with URLs you actually opened).
2. **Write `spec.json`** (`references/spec-format.md`): summary, blocks, references, credits; `slides` for decks, `sheets` for spreadsheets. Follow the structure for the type in `references/doc-types.md`.
3. **Check:** `py SKILL_DIR/tools/make_doc.py documents/<slug>/spec.json --check --sources documents/<slug>/sources/*.md` (sources only when there are verses/EGW quotes). Fix every ERROR and every QUOTE NOT FOUND.
4. **Render:** `py SKILL_DIR/tools/make_doc.py documents/<slug>/spec.json --formats pdf,docx --out documents/<slug> [--sources ...]`.
5. **Look at it:** `py SKILL_DIR/tools/preview.py documents/<slug>/<file> --out documents/<slug>/preview --sheet`, then view the `_sheet.png`. Fix overflow, empty slides, bad breaks, tiny text. (If no converter exists, skip and say so.)
6. **Self-check** (end of this file), then **deliver**: list the files with sizes, one line on what each contains, every UNVERIFIED item, and what the user must add themselves (education).

## Editing an existing file
Full guide: `references/editing.md`. In short:
1. `py SKILL_DIR/tools/edit_doc.py inspect FILE` (outline) and `text FILE` (all text). Read before changing.
2. Write `ops.json` (add_section, replace_text, add_slide, add_sheet, append_rows, set_cells).
3. `py SKILL_DIR/tools/edit_doc.py apply FILE ops.json` → writes `<name>_edited.<ext>` next to the original, using the file's own styles. Overwriting the original needs the user's yes + `--overwrite-original` (a `_backup` copy is made).
4. Preview the edited file and report what changed.
PDF and CSV can't be edited in place: read them (Claude can read a PDF directly; CSV with the csv module), then rebuild with make_doc.py as a new file.

## Content packs (rules are mandatory)
| Pack | Read | Key rules |
|---|---|---|
| SDA/Church | `references/bible-rules.md` | KJV fetched from BibleGateway (`tools/bible_fetch.py`); EGW only once verified on egwwritings.org (`tools/egw_fetch.py`), else UNVERIFIED; tag Scripture / Inference / EGW; myths check; never reproduce Sabbath School quarterly text (cite by title only); verse callouts; EGW styled differently |
| Health | `references/packs.md#health` | General information, not medical advice (one-line `disclaimer`, required); reputable sources only (WHO, CDC, NHS, Mayo Clinic, peer-reviewed); never invent statistics; cite every claim |
| Education/School | `references/packs.md#education` | Help the user write *their own* work: structure, draft, explain. Every citation real and checkable. Insert `ADD YOUR …` callouts where their own analysis goes. Never a finished piece meant to be handed in untouched |
| Tech | `references/packs.md#tech` | No invented APIs, flags or versions; check version-specific facts in official docs; code must run as shown or be labelled as a sketch |
| Business/Report | `references/packs.md#business` | No invented figures; label estimates and assumptions; sources for market data |
| General | `references/packs.md#general` | Facts verified or marked UNVERIFIED; cite sources |

## Formats in one line each
- **DOCX:** A4, headings, page X of Y footer, summary box, verse/EGW callouts, tables, images with captions, references. Optional `toc` block (Word fills it on open; F9 to refresh).
- **PDF:** same look as DOCX via reportlab (built-in fonts, works everywhere), clickable links, contents with page numbers.
- **PPTX:** 16:9, title slide, summary slide, then `slides` (layouts: bullets, two-col, section, code, verse, image, table), references slide, slide numbers, speaker notes. Keep ≤ 6 bullets per slide, ≤ 12 words per bullet.
- **XLSX:** Summary sheet first, data sheets with header style, filters, frozen header, number formats, totals; quizzes get a dropdown answer column, automatic marking and a score; references sheet.
- **CSV:** one file per table/sheet (UTF-8 with BOM so Excel shows accents) + `<name>_summary.txt` with the summary and references (CSV can't hold them).

## Images
Details: `references/images.md`. User images go in `./images/` with `captions.csv` (`file,caption,credit,licence,source,own`); make_doc fills captions and credits from it and shrinks big photos. AI-drawn art: write a clean SVG yourself (simple shapes, the document's colours, no text smaller than 14 px, no real logos or real people's likenesses), save it in `documents/<slug>/images/`, set `"own": true` and credit "Illustration: AI-drawn for this document".

## Branding
`py SKILL_DIR/tools/brand.py list | show ID | new ID "Name" | set ID FIELD VALUE | logo ID PATH | validate ID`. Brands live in the user's app-data folder (`brand.py where`), never in this skill. Use only details the user typed. Put `"brand": "ID"` in the spec: logo + name in the header, contacts in the footer, brand colours replace the theme's primary/accent. `sample` is a fictional test brand.

## Self-check before delivering
- [ ] Summary block first; references (and image credits) last
- [ ] `make_doc.py` printed no ERROR; every verse/EGW quote printed QUOTE OK (or is marked UNVERIFIED and you told the user)
- [ ] Pack rules followed (disclaimer for health, `ADD YOUR …` prompts for education, no quarterly text, no invented numbers/APIs)
- [ ] Preview looked at: no overflowing text, no empty or near-empty slides, tables readable, page numbers present
- [ ] Original files untouched (edits went to a copy)
- [ ] Told the user: files + sizes, UNVERIFIED items, what they must add or check

## Files in this skill
| Path | What |
|---|---|
| `tools/make_doc.py` | spec → DOCX / PDF / PPTX / XLSX / CSV, checks, quote verification |
| `tools/edit_doc.py` | inspect / read / edit DOCX, PPTX, XLSX on a copy |
| `tools/preview.py` | pages → PNG + contact sheet (LibreOffice or MS Office + pdftoppm/pypdfium2) |
| `tools/setup_check.py` | computer + library check, installs missing libraries after the user agrees |
| `tools/brand.py` | saved brands in the user folder |
| `tools/bible_fetch.py`, `bible_fetch_yv.py`, `egw_fetch.py`, `check_quotes.py` | verbatim KJV (BibleGateway), Shona Bibles (bible.com), EGW paragraphs, quote checker |
| `tools/docstudio/` | the renderers (docx_r, pdf_r, pptx_r, xlsx_r) and shared code |
| `references/` | spec format, document types and layouts, pack rules, Bible rules, editing, images, EGW indexes |
| `examples/` | one spec per pack + a fictional sample brand |
