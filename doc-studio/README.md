# doc-studio

An Agent Skill for Claude by **Blessed Tanaka Saunyama** (MIT licence). It creates and edits documents on any topic: Word (.docx), PowerPoint (.pptx), Excel (.xlsx), CSV and PDF.

- A short wizard: new or edit → content pack → document type → topic → formats → layout → images → branding → plan card.
- Content packs with strict rules: **SDA/Church** (KJV fetched from BibleGateway, Ellen G. White quotes verified on egwwritings.org, Shona Bibles from bible.com), **Health** (reputable sources, disclaimer), **Education** (the student's own work, real citations), **Tech**, **Business**, **General**.
- Every document opens with a summary and ends with references (and image credits).
- Edits always go to a copy, in the original's own format and styles.
- Standalone: everything is in this folder. Brands are stored in your user folder, never in the skill.

## Install
Claude Code: copy this folder to `~/.claude/skills/doc-studio/`. claude.ai: upload the zip of this folder as a skill.
Libraries: `python tools/setup_check.py` shows what's missing and installs it after you agree (`requirements.txt` lists them).

## Try it
```
python tools/make_doc.py examples/sda-topical-study.json --formats pdf,docx --out out
python tools/make_doc.py examples/tech-deck.json --formats pptx --out out
python tools/make_doc.py examples/sda-quiz.json --formats xlsx,csv --out out
python tools/edit_doc.py inspect out/the-sabbath-gods-gift-of-rest.docx
```
See `SKILL.md` for the full workflow and `references/` for the spec format and the pack rules.
