# SDA / Church pack: Bible rules

Load this for every SDA/Church document (studies, lessons, sermons notes, newsletters, quizzes, slides). Self-contained: tools are in `SKILL_DIR/tools/`. The document **never says the Bible says something it doesn't say.**

## 1. Non-negotiable rules
1. **Scripture is the authority.** Ellen G. White (EGW) is supporting commentary from an Adventist perspective; it never replaces or contradicts the text.
2. **Never quote from memory.** Every verse and every EGW sentence is fetched first, then copied exactly.
   - KJV (default, public domain): `py tools/bible_fetch.py "Genesis 2:1-3" --out documents/<slug>/sources/scripture.md`
     (append more passages: run again with a different `--out` file, or collect them in one file by hand)
   - Other English versions: `--version NKJV` (keep quotes short, name the version).
   - **Shona:** `py tools/bible_fetch_yv.py "John 3:16" --version SNA2002 --out documents/<slug>/sources/scripture-sn.md` (`--list` shows versions). BibleGateway has no Shona Bible. Never machine-translate a verse; if the fetch fails the verse is UNVERIFIED.
   - EGW: find the book and chapter in [egw-books.md](egw-books.md) / [egw-chapter-index.md](egw-chapter-index.md), then `py tools/egw_fetch.py <id> --grep word,word --out documents/<slug>/sources/egw.md`. WebFetch on egwwritings.org usually gets HTTP 403: use the tool.
   - If a fetch fails: paraphrase without quotation marks and label it **UNVERIFIED**, or leave it out. Never invent a reference code, page number, chapter title or link.
3. **Verify before rendering:** `make_doc.py … --sources documents/<slug>/sources/*.md` must print `QUOTE OK` for every `verse` and `egw` block.
4. **Tag every teaching point** in study/lesson notes (in the text or a fidelity table at the end):
   - 📖 **Scripture**: stated in the text (give the reference)
   - 🔎 **Inference**: a reasonable conclusion from the text (show the verses it rests on)
   - 📚 **EGW**: from a verified EGW passage (reference code)
   In DOCX/PDF you may write the tags as words in brackets, e.g. "(Scripture: Gen 2:3)", "(Inference from Ex 20:8-11)", "(EGW: PP 48.1)", so they print on any font.
5. **Sabbath School quarterly:** never reproduce its text, questions or daily outlines (copyrighted). Write original material on the same passage and cite the quarterly **by title only** ("Adult Bible Study Guide, Q4 2026: <title>"). Same for any copyrighted book: short quotes with citation only.
6. **Don't over-claim.** When the Bible is silent (how many wise men, the fruit's species), say so.
7. **Reverence:** no jokes about God or sacred things; God the Father is never drawn as a human figure (AI-drawn art: light, cloud, open Bible, symbols); Jesus with dignity; no gore.

## 2. Styling (built into the renderers)
- `verse` block → **verse callout box** (soft fill, accent bar, reference + version bottom right). Use it for key texts; short references inside sentences stay plain text ("see Exodus 20:8").
- `egw` block → **different style from Scripture**: white box with a thin border, italic serif, "ELLEN G. WHITE" label, book + reference code with link. Unverified → "UNVERIFIED" in the label.
- Memory verse: a `verse` block right after the summary, or a `callout` titled "Memory verse" containing the exact fetched text.

## 3. Common myths: never state these as fact
| Myth | What the Bible says |
|---|---|
| Adam and Eve ate an apple | "the fruit": no species named (Gen 3:6) |
| Three wise men | three gifts; the number of men isn't given (Matt 2:1-11) |
| Wise men at the manger | they came into "the house" and saw "the young child" (Matt 2:11) |
| Jonah swallowed by a whale | "a great fish" (Jonah 1:17) |
| Only two of every animal on the ark | clean beasts "by sevens" (Gen 7:2-3); they went in "two and two" (Gen 7:9) |
| Mary Magdalene was a prostitute | not stated; "seven devils" went out of her (Luke 8:2) |
| Moses had horns | a mistranslation; "the skin of his face shone" (Ex 34:29-30) |
| The innkeeper turned them away | no innkeeper is mentioned (Luke 2:7) |
| "God helps those who help themselves" is in the Bible | not a Bible verse |
| "Cleanliness is next to godliness" is in the Bible | not a Bible verse |
| The Sabbath was changed to Sunday in the Bible | no text records a change; the fourth commandment names "the seventh day" (Ex 20:10) |
| Lucifer is named in Isaiah 14 as Satan (as a quoted fact) | "Lucifer" (KJV, Isa 14:12) addresses the king of Babylon; applying it to Satan is an 🔎 inference (with EGW support in PP ch. 1, if verified) |
| Money is the root of all evil | "the **love of** money is the root of all evil" (1 Tim 6:10) |

## 4. Structures that work
- **Topical study:** Summary → memory verse → 3-5 numbered points, each = heading + explanation + 1-2 verse callouts + (optional) one verified EGW quote → "What it means for me" (application) → discussion questions → References.
- **Sabbath School lesson helper (original):** title, memory verse, passage, 3 points with verses, an EGW thought (verified or none), application, activity, closing prayer idea. Cite the quarterly by title only.
- **Church newsletter:** summary, pastor's note (user's own words: `ADD YOUR …` callout if not given), upcoming events table (user's data only), memory verse, contacts (brand footer).
- **Bible quiz:** questions whose answers are in fetched verses; put the reference in `explain`.

## 5. References section (always)
List BibleGateway / bible.com links actually loaded, EGW links loaded (or "UNVERIFIED"), the quarterly by title only, and any other source opened. Example:
- "Genesis 2:1-3; Exodus 20:8-11, King James Version", https://www.biblegateway.com/passage/?search=Genesis+2%3A1-3&version=KJV
- "Ellen G. White, *Patriarchs and Prophets*, ch. 2", https://text.egwwritings.org/read/84.…
