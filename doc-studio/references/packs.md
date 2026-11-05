# Content packs (other than SDA/Church)

SDA/Church has its own file: [bible-rules.md](bible-rules.md). The rules below are mandatory for their pack. In every pack: **never invent** a fact, figure, quote, citation or link. If you can't verify something, write it as UNVERIFIED (or leave it out) and tell the user.

How to verify: open the source (WebFetch/WebSearch or a tool), note the exact URL you opened in `documents/<slug>/sources/notes.md` with the sentence you rely on, and put only those URLs in `references`. A reference you didn't open is not a reference.

## Health
- **One-line disclaimer, required** (`"disclaimer"` in the spec): "General information only, not medical advice. Talk to a qualified health worker about your own situation." Shona: "Ruzivo rwekudzidza chete, kwete zano rechiremba. Taura nemushandi wezveutano nezvemamiriro ako."
- **Sources:** WHO, CDC, NHS, Mayo Clinic, MedlinePlus, national ministries of health (e.g. Zimbabwe MoHCC), Cochrane, peer-reviewed journals. Not blogs, product sites or social media.
- **Statistics:** only with a source, a year and the place it applies to ("WHO, 2024, global"). Never round into something the source doesn't say. No invented percentages, doses or cure rates.
- **No dosing instructions** for prescription medicines; no "stop taking your medicine" advice; no diagnosis. Red-flag symptoms → "seek care urgently" with the source.
- **Tone:** clear, kind, non-alarming; plain words with the medical term in brackets once.
- **Faith + health (SDA health message):** fine to include, but keep health claims sourced like any other; EGW health counsel follows bible-rules.md (verified quotes only) and is clearly labelled as EGW, not as medical evidence.
- One-pager pattern: Summary → What it is → Signs/causes (sourced) → What you can do (sourced) → When to get help → Sources.

## Education / School
The goal is to help the user produce **their own** work, not to hand in work for them.
- **Structure and draft, then flag:** add `callout` blocks with `"kind": "todo"` and text starting **"ADD YOUR …"** wherever the student must add their own analysis, data, opinion, reflection or local example (at least one per main section in reports and essays). `make_doc.py` warns if there are none.
- **Citations must be real and checkable**: books with author, year, publisher (check the catalogue page or publisher page); articles with DOI/URL you opened. Never invent page numbers. If the user's school uses a citation style (APA 7, Harvard, MLA), use it consistently; default APA 7.
- Explain *why* a structure works (a short "How to use this draft" note at the top is fine for drafts).
- If the user clearly asks for a finished piece to submit as-is, say kindly that you'll give a strong draft with the parts they need to write themselves marked, and why (their school's integrity rules).
- Worksheets and quizzes for teachers are fine to make complete: answers go in the answer key.
- School report pattern: Title page info → Summary → Introduction (aim) → Background (sourced) → Method/what was done (`ADD YOUR …`) → Findings (user's data, or `ADD YOUR …`) → Discussion (`ADD YOUR …`) → Conclusion → References.

## Tech
- **No invented APIs, functions, flags, config keys, versions or release dates.** Check version-specific facts in the official docs or release notes, and name the version ("Python 3.12", "React 19").
- Code must be correct for the stated version, or labelled "sketch, not tested". Prefer short, runnable snippets (≤ 15 lines on a slide).
- Benchmarks and numbers need a source; otherwise describe qualitatively.
- Tech deck pattern (10 slides): title → summary → the problem → the idea (two-col before/after) → how it works (bullets or diagram) → code example → common mistakes → when to use / not use (two-col) → next steps → references.

## Business / Report
- **No invented figures.** Market sizes, prices, growth rates: sourced with year and place. User-provided numbers are labelled as such ("figures supplied by the client").
- Estimates and assumptions are labelled ("Assumption: 20 % uptake") and listed in an Assumptions section.
- Report pattern: Summary (executive summary) → Background → Findings → Options/analysis → Recommendation → Next steps → Assumptions → References. Trackers/plans: XLSX with clear columns, totals and dates.
- Never put other companies' logos or trademarks in the document.

## General
- Facts verified or marked UNVERIFIED; quotes exact with the source; references for anything not common knowledge.
- Opinion pieces: clearly the author's view; still no invented facts.
- CVs: only the user's real details. Never invent jobs, dates, qualifications or referees. Ask for missing facts; leave `ADD YOUR …` callouts where something is unknown.
