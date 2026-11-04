# Content pack: Tech / programming

Load this file when CONTENT = Tech/programming. Default style: **Modern vector** (Whiteboard for slower teaching; Manim diagrams for algorithms and architecture once engine B ships). Worked example: `examples/tech-python-lists/`.

## 1. Accuracy rules (non-negotiable)
1. **Never invent an API, function, flag, option, error message, version number or benchmark.** If you're not sure it exists exactly as written, check it.
2. **Anything version-specific must be checked against the current official docs on the web** (python.org/docs, developer.mozilla.org, nodejs.org/api, the project's own docs or changelog). Note the URL and date in `sources.md`. Never cite a blog as the authority on an API.
3. **Run every snippet before it appears on screen.** Save it as `videos/<slug>/code/<name>.<ext>`, run it, and paste the **real output** into the terminal element. If you can't run it (missing toolchain, needs a server, paid API), show it as a code card labelled "not run" in the script notes and mark the claim **UNVERIFIED**, or choose a snippet you can run.
4. **Show the language and version on screen**: the code card's `label` (e.g. "Python 3.14.8" from `python --version`, "Node 24.21" from `node --version`). Use the version you actually ran.
5. **Keep code small enough to read on a phone:** ≤ 6 lines per card and ≤ 34 characters per line for 9:16 (≤ 50 for 16:9). Split long examples across shots.
6. **No secrets on screen:** no real API keys, tokens, passwords, personal paths or email addresses. Use obvious placeholders (`YOUR_API_KEY`).
7. Security topics: explain defences and concepts; don't show working exploit chains.
8. **Prefer diagrams for architecture and algorithms** (boxes + arrows now; Manim when available). Code cards are for syntax, not for explaining flow.

## 2. Script
Length ≈ 3.7 words/s (Piper's default voice reads about 2.5 words/s: use `--speed 0.8` for a normal pace, or plan longer).
1. **Hook:** the problem or a surprising result ("Three lines, and Python counts your list for you.").
2. **Concept** in one plain sentence (what it is, not its history).
3. **Show it:** code types in sync with the words that describe it; highlight the line being spoken.
4. **Run it:** the terminal shows the real output.
5. **Takeaway:** one sentence + when to use it (or one common mistake).
Say code the way a person reads it aloud ("fruits dot append", "len of fruits"), but keep the on-screen code exact. Don't read punctuation out.

## 3. Shot list and scene
`shotlist.md` columns: `| # | Time (s) | Script words | Visual (code line / diagram / output) | Highlight | SFX |`.
In `scene.json`: use screen-anchored `title`, `box`, `text`, `code` (with `label`, keyframed `typing`, `highlight`) and `terminal` elements, with per-format overrides (`screen_16x9`, `w_16x9`...) so each format has its own layout. Leave the bottom ~20 % free for burned-in captions. Sound: `sound.py music --mood tech`, `type` SFX while code types, `pop` on entrances, `success` on correct output.

## 4. Deliverables
`script.txt` (copyable block, word count, length) · `shotlist.md` · `code/` (the exact snippets that ran) + `run-log.txt` (command, version, real output) · `sources.md` (official docs URLs checked, with the date) · captions `.srt` · the MP4(s).

## 5. Self-check
- [ ] Every snippet on screen ran, and the output shown is the real output (`run-log.txt`)
- [ ] Language + version on screen match the run
- [ ] Every API/flag/version claim is backed by an official-docs URL in `sources.md`, or marked UNVERIFIED
- [ ] No secrets or personal data on screen; code readable at phone size
- [ ] Captions don't cover code (check the contact sheet for every format)
