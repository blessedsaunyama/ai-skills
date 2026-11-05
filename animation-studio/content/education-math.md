# Content pack: Maths / education

Load this file when CONTENT = Maths/education (maths, algorithms, science processes, any step-by-step lesson). Default style: **Manim** (engine B, `styles/manim.md`); Whiteboard or Modern vector via `--style`. Worked example: `examples/maths-binary-search/`.

## 1. Accuracy rules (non-negotiable)
1. **Verify every calculation by running it in Python** before it appears in the script or on screen. Save the check as `videos/<slug>/verify.py` and its output as `run-log.txt`. Use exact arithmetic where it matters (`fractions.Fraction`, `decimal.Decimal`, integers) and say when a value is rounded ("about 3.14").
2. **Better still, compute in the scene:** let the Manim scene calculate the steps (as `binary_search.py` does) and `assert` the final answer, so the picture can never disagree with the maths.
3. **Definitions and facts** (formulas, theorems, named results, constants, science facts) must match a reliable source (a textbook, the curriculum document, an encyclopaedia, official docs for algorithms in a library); list it in `sources.md`. Don't invent a theorem name or attribute a result to a person without a source.
4. **Show worked steps one at a time.** One operation per step; the narration says what changed and why ("subtract three from both sides"). Keep the previous line visible, so learners can follow.
5. **Notation:** use the curriculum's notation if the user names one (e.g. ZIMSEC, Cambridge, Common Core). Units on every quantity in word problems.
6. **LaTeX:** when it is installed, `maths(r"x^2 + 1", "x² + 1")` typesets with LaTeX. When it is missing, the same call falls back to plain text with Unicode symbols (×, ÷, ², ³, √, ≤, ≥, π, ½). **Say so in the notes** ("rendered without LaTeX: plain-text maths"). Offer to install LaTeX (MiKTeX/MacTeX/TeX Live, about 1 GB) only if the user wants textbook-quality typesetting; ask first.
7. Don't over-claim: say "for this example" when a shortcut doesn't always work; mention the condition (binary search needs a **sorted** list).

## 2. Script
≈ 3.7 words/s for adults, 3.2 for children. Short sentences; numbers as words in `script.txt`, digits on screen.
1. **Hook:** the question or the surprising result, shown on screen from frame 0 ("Find 26 in two steps").
2. **Setup:** the givens, once.
3. **Steps:** one per phrase, each with its visual change.
4. **Result:** highlighted (green = correct), with a check ("8 halves to 4, then 2...").
5. **Takeaway:** the rule or pattern in one sentence; for lessons, one practice question for the viewer (answer verified in `verify.py`).

## 3. Scene (engine B)
Write `videos/<slug>/<name>.py` starting with `from studio import *` and a `Scene` subclass. Use `SAFE` for layout (every format), `C.*` colours (never hex codes), `text()` / `maths()` for text, `fit_width()` for long rows, and `wait_until(self, T.start(i))` to start each step with phrase *i* of the voice. Portrait formats (`FW < FH`) need fewer items per row or a vertical layout. See `engines/manim/README.md`.
Sound: `sound.py music --mood calm` (or `tech`), `click` on each step, `success` on the answer. Captions: `captions.py ... --style manim`.

## 4. Deliverables
`script.txt` · `shotlist.md` (`| # | Time | Words | Step shown | Highlight |`) · `verify.py` + `run-log.txt` · `sources.md` · the scene `.py` · captions `.srt` · the MP4(s) · optional practice question with its verified answer.

## 5. Self-check
- [ ] Every number on screen and in the narration came out of `verify.py` (or is computed and asserted in the scene)
- [ ] One step at a time; each step's change is highlighted and spoken
- [ ] Conditions stated (sorted list, x ≠ 0, units...)
- [ ] If LaTeX was missing, the notes say plain-text maths was used
- [ ] Text readable at phone size in every chosen format (contact sheet checked)
