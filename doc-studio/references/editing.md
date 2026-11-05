# Editing an existing document

The user's file is never changed. Every edit is written to a copy, `<name>_edited.<ext>`, next to it (or `--out`).

## 1. Read it first
```
py tools/edit_doc.py inspect report.docx     # headings with paragraph numbers, styles in use
py tools/edit_doc.py text report.docx        # every paragraph (read the content before writing)
py tools/edit_doc.py inspect deck.pptx       # slide titles + available layouts
py tools/edit_doc.py text deck.pptx          # all slide text
py tools/edit_doc.py inspect data.xlsx       # sheets, sizes, first rows
```
Match the document's voice, heading levels, terminology and citation style. If the change is unclear, ask one question.

## 2. Write ops.json
DOCX: add a section at the end of an existing section (before the next heading of the same level):
```json
[{"op": "add_section", "after_section": "Findings", "heading": "Limitations", "level": 2,
  "blocks": [{"type": "paragraph", "text": "This survey had **42** responses, all from one school."},
             {"type": "bullets", "items": ["Small sample", "One location"]},
             {"type": "table", "columns": ["Group", "Responses"], "rows": [["Form 3", 20], ["Form 4", 22]]}]},
 {"op": "replace_text", "find": "2025", "replace": "2026"}]
```
Anchors: `"after_section": "<heading text>"` · `"before_heading": "<heading text>"` · `"at": "end"`. Heading text matches case-insensitively by "contains".
Block types for DOCX edits: heading, paragraph, quote, bullets, numbered, table, image (`width_mm`), callout, verse. New text uses the document's own Normal / Heading N / List Bullet / Table Grid styles, so it looks like the rest of the document.

PPTX: `{"op": "add_slide", "title": "Questions?", "bullets": ["…"], "after": 9, "notes": "…"}` (uses the deck's own "Title and Content" layout), `replace_text`.
XLSX: `add_sheet`, `append_rows`, `set_cells` (formulas allowed: `"=SUM(B2:B9)"`), `replace_text`.

Content rules still apply: an SDA edit that adds a verse fetches it first; an education edit adds `ADD YOUR …` prompts rather than finished analysis; health edits cite sources.

## 3. Apply, check, report
```
py tools/edit_doc.py apply report.docx ops.json            # -> report_edited.docx
py tools/preview.py report_edited.docx --out preview --sheet
```
- Existing output file → it stops; choose another `--out` or ask the user before adding `--force`.
- Replacing the original needs the user's explicit yes, then `--overwrite-original` (a `_backup` copy is kept).
- Report: what was added/changed (section names, slide numbers), and that the original is untouched.

## PDF and CSV
They can't be edited in place. Read them (Claude can read a PDF directly; CSV with Python's csv module), rebuild the content as a spec, and render a new file with `make_doc.py`. Tell the user the layout is recreated, not the original PDF layout.

## Big changes
For a rewrite or a new structure, it's cleaner to build a new document with `make_doc.py` from the old content (read with `text`). Ask which the user prefers.
