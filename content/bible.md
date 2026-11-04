# Content pack: Bible story

Load this file when CONTENT = Bible story. It adds research, writing and reverence rules on top of SKILL.md. The video **never says something the Bible doesn't say**: every line traces to Scripture or a cited Ellen G. White (EGW) passage, or is openly marked as artistic detail.

Tools (standard library only; paths relative to the skill folder):
- `content/bible/tools/bible_fetch.py "Genesis 7:1-16" [--version NKJV] [--out FILE]`: prints each verse **verbatim** from BibleGateway and the URL it loaded. Exit code 3 = could not load.
- `content/bible/tools/egw_fetch.py <egwwritings link or id> [--grep word,word] [--out FILE]`: EGW paragraphs verbatim with reference codes (WebFetch on egwwritings.org usually gets HTTP 403; use this tool).
- `content/bible/tools/check_quotes.py script.txt scripture.md [egw.md]`: proves every quoted string matches the fetched text.
- References: [egw-books.md](bible/egw-books.md) and [egw-chapter-index.md](bible/egw-chapter-index.md) (find the matching chapter), [voiceover.md](bible/voiceover.md) (recording hand-off + name pronunciations).

## 1. Core rules (non-negotiable)
1. **Scripture is the authority.** EGW writings are supporting commentary from an Adventist perspective. They never replace or contradict the text.
2. **No invented words in a biblical character's mouth as if quoted.** Dialogue is either verbatim Scripture with its reference, or narration. A dramatised line must closely restate the verse and is tagged 🔎.
3. **Never quote from memory.** Fetch every verse and every EGW quote with the tools before using it. If it can't be fetched and verified, paraphrase and mark it **UNVERIFIED**, or leave it out. Never invent a page number, reference code, chapter title or URL.
4. **Label every script line** with exactly one tag:
   - 📖 **Scripture**: stated in the text (give the reference)
   - 🔎 **Inference**: a reasonable reading of the text (explain in one line)
   - 📚 **EGW**: from a cited EGW passage (give the reference code)
   - 🎨 **Artistic**: visual or emotional detail the text doesn't give. Allowed only if it doesn't contradict Scripture.
   - Mixed lines: split them, or give the **weakest** tag that applies (📖 > 📚 > 🔎 > 🎨) and say which part is which. Lesson lines ("God is with us too") are 🔎 with the verses they come from.
5. **Reverence:** see §3. Humour is fine for children, but never at God's expense or about sacred things.
6. **Violence is implied only:** see §4.
7. **Don't over-claim.** When Scripture is silent (how many wise men, what fruit), say so instead of filling the gap.
8. **Translation:** quote the **KJV** word for word by default (public domain). If the user picks NKJV, ESV or NIV, keep quotes short and name the version.
9. **EGW stays out of the video.** EGW references go only in `study-notes.md` and the "Further reading" line of the description. An end card only if the user asks; never a narrator mention.
10. **English only in v1.** (Shona/Ndebele are planned; never machine-translate Scripture: use a published translation that the tools can fetch.)

## 2. Audience settings (ask at intake)
| Audience | Words / sentence | Vocabulary | Pace | Humour | Danger / sorrow | Close with |
|---|---|---|---|---|---|---|
| Young children 3–7 | 5–9 | Everyday words; explain "den", "decree" in a phrase | 3.2 words/s | Gentle (animals, faces) | Off-screen; show safety and God's care right away | One short memory verse + "God loves/helps you" |
| Kids 8–12 | 8–13 | Simple, KJV quotes kept short | 3.7 words/s | Light, never at sacred things | Implied (shadows, reactions, sound) | Memory verse + one challenge |
| Youth / teens | 10–16 | Fuller, honest about fear and courage | 3.8–4 words/s | Wry at most | Implied, emotionally real | A question to think about + verse |
| Whole congregation | 9–15 | Clear and dignified, KJV quotes welcome | 3.5 words/s | Very little | Implied, solemn | Verse + short appeal |

Loose wording maps without re-asking: "kids" → Kids 8–12, "little ones/preschool" → Young children, "teens/young people" → Youth, "church/everyone" → Whole congregation. Say which you assumed.

## 3. Depicting sacred persons (every style)
| Subject | How | In the engines |
|---|---|---|
| **God the Father** | **Never** a human figure, face or body. Light, glory, a cloud, fire, wind, or a voice | A light burst, glowing cloud or warm light change + a soft chord/rumble |
| **Jesus** | A full character with dignity: Middle-Eastern features, simple robe, warm and kind. Never comic, clumsy or the butt of a joke. No halo needed | Calm poses (stand, gesture, pray); no comic expressions or slapstick motion |
| **Angels** | Majestic men in shining white. No baby cherubs. Wings only where the text describes winged beings (Isa 6:2; Ezek 1; 10). "Appeared as a man" → no wings | White robe + soft glow; wings only with a verse, tagged 🎨 |
| **Holy Spirit** | Only the text's forms: a dove (Matt 3:16), tongues of fire, a mighty wind (Acts 2) | Dove / flame effect, wind sound |
| **Satan / the serpent** | Never the comic hero, never cute or glamorous. Short screen time | Dark tint, shadow, low angle |
| **Prophets and heroes** | Real people with real fear and faith, not superheroes | Normal expressions |
| **Prayer, worship** | Unhurried, respectful framing; no jokes in the same shot | `pray` pose, soft light |

Stickman style is allowed for Bible stories only for light, child-friendly passages. Suggest Storybook or Flat 2D for solemn ones (the cross, death, judgment).

## 4. Violence, danger and death: implied only
Show the cause and the result, never the impact: a cutaway to watchers' faces, a shadow on a wall, a sound off-screen, then the aftermath far away. No blood, wounds, visible killing or close-up corpses. Executions and the deaths of children or families (e.g. Dan 6:24) are **told in one restrained line, or left out** for young audiences, and the accuracy notes say so.

## 5. Setting and costume (Ancient Near East, tagged 🎨)
Long robes and tunics, sashes, head-cloths with a band, mantles, sandals. Kings: mantle, rich colour, simple crown. Soldiers: leather or bronze, not Roman armour (except New Testament Judea). Flat-roofed mud-brick houses, stone walls, palms and olives, dry hills, wells. Skin tones in the Middle-Eastern and African-Asian range; never Europeanise biblical characters by default. Anything the text doesn't state is 🎨 and must not contradict it.

## 6. Research (always, before writing)
1. **Fetch the passage** plus a few verses around it: `python content/bible/tools/bible_fetch.py "Daniel 6" --out videos/<slug>/scripture.md`. If it fails, WebFetch `https://www.biblegateway.com/passage/?search=<Book>+<ch>%3A<vv>&version=KJV` asking for verbatim text. If both fail, every quote is **UNVERIFIED**.
2. **Parallels and cross-references:** fetch parallel accounts (Gospels, Kings/Chronicles) and note differences.
3. **EGW:** find the chapter in the reference files, then `egw_fetch.py <id> --out videos/<slug>/egw.md`. Record exact quotes with codes. Link only URLs the tool loaded.
4. **Myth check** against §11.
5. **Fact sheet** `facts.md`: who, where, when (only as far as the text says), events in biblical order with verse numbers, planned quotes, and what the text leaves unstated.

## 7. Script
Word budget = seconds × the audience pace (3.7 words/s by default: 30 s ≈ 110 words, 60 s ≈ 220). Read-aloud ≈ 2.5 words/s.
1. **Hook** (no setup): a striking fact or short verse.
2. **Setting** in 1–2 lines.
3. **Rising action** in biblical order.
4. **Turning point**: the key verse word for word (gets the musical sting and the push-in).
5. **Resolution and lesson**, the lesson as a clearly separate sentence ("This story shows us...").
6. **Closing memory verse**, quoted exactly with its reference.

Plain spoken English, short sentences, numbers as words (but KJV quotes exactly as printed). Put quotes in their own sentences. In `script.txt` write references as spoken ("Genesis seven, verse nine"); in tables use digits. **Verify before showing:** `check_quotes.py script.txt scripture.md [egw.md]` must print OK for every quote.

Deliver: the narration in a copyable block with word count and length → `script.txt` (narration only), the **fidelity table** → `fidelity.md`, and **accuracy notes** (uncertainties, translation differences, what was simplified or left out).

| # | Script line (short) | Tag | Source / justification |
|---|---|---|---|
| 1 | "There went in two and two..." | 📖 | Gen 7:9 |
| 2 | Storm clouds while the last animals board | 🔎 | Gen 7:10-13: the rain came "after seven days", the same day Noah's family went in |

## 8. Shot list
`shotlist.md`, one row per shot: `| # | Time (s) | Script words | Visual | Camera | Light / mood | Formats note | SFX / music |`. Every shot only illustrates its own line; don't add events that aren't in the fidelity table. Divine moments use light, wind, fire or sound. Solemn beats: slower moves, backlit/silhouette light, no comic motion.

## 9. Package + voiceover hand-off (then STOP and wait)
Write and show: `script.txt`, `fidelity.md` (+ accuracy notes), `shotlist.md`, `study-notes.md` (passage, key verses verbatim, EGW chapter with verified quotes and codes, cross-references, loaded links), `description.txt` (title, one-line summary, "Scripture: <ref> (KJV)", the memory verse, "Further reading: Ellen G. White, *<Book>*, ch. <n>").
Voice: the user's recording (hand-off text in [voiceover.md](bible/voiceover.md)) or Piper TTS (SKILL.md → Voice). Keep the exact final script text; ask for any changed wording.

## 10. Extras (offer once at the end, multiSelect)
Discussion questions (3–5, each with a fetched verse answer and one application question) · Sabbath School lesson (title, memory verse, passage, 3 points with verses, an EGW thought (verified or none), application, activity, closing prayer idea) · Thumbnail (no image of God the Father; text inside the safe zone) · Captions (.srt, always made).
End every output with **References**: BibleGateway links, EGW further reading (only loaded links, or UNVERIFIED), and discussion questions for lessons.

## 11. Common myths: never put these in a script as fact
| Myth | What the Bible says |
|---|---|
| Adam and Eve ate an apple | "The fruit": no species named (Gen 3:6) |
| Three wise men | Three gifts; the number of men isn't given (Matt 2:1-11) |
| Wise men at the manger | They came into "the house" and saw "the young child" (Matt 2:11) |
| Jonah swallowed by a whale | "A great fish" (Jonah 1:17) |
| Only two of every animal on the ark | Clean beasts and fowls "by sevens", unclean "by two" (Gen 7:2-3); they went in "two and two" (Gen 7:9) |
| The ark was a round-bottomed boat with a house on top | A box-like ark: 300 × 50 × 30 cubits, a window "finished above", a door "in the side", three stories (Gen 6:15-16) |
| Mary Magdalene was a prostitute | Not stated; "seven devils" went out of her (Luke 8:2) |
| Moses had horns | A mistranslation; "the skin of his face shone" (Ex 34:29-30) |
| The innkeeper turned them away | No innkeeper is mentioned; "no room for them in the inn" (Luke 2:7) |
| The wise men were kings | "Wise men from the east" (Matt 2:1) |
| All angels have wings and halos | Seraphim have six wings (Isa 6:2); angels often appear as men (Gen 18:2; 19:1) |
| Daniel was a young man in the lions' den | Captive under Jehoiakim (Dan 1:1-6); the den is under Darius (Dan 5:31; 6), decades later. Draw him older (🔎), state no age |
| Goliath was ten feet tall (as fact) | "Six cubits and a span" (1 Sam 17:4): say "about nine feet" and tag 🔎 |
| David killed Goliath with the stone alone | The stone felled him (1 Sam 17:49); then he used Goliath's sword (v. 50-51). Implied, not shown |

## 12. Self-check (before sending anything)
- [ ] `check_quotes.py` printed OK for every quote (notes, lessons and questions too)
- [ ] Every 📖 line was checked against fetched text, or marked UNVERIFIED
- [ ] No invented dialogue presented as a biblical quote
- [ ] Every 📚 quote came from `egw_fetch.py` with its code, and none is in the narration
- [ ] Every 🎨 detail is consistent with Scripture; nothing from §11 appears as fact
- [ ] Reverence (§3) and violence (§4) rules followed in the script AND the visuals (check the contact sheet)
- [ ] Wording suits the audience; length within ±10 % of the word budget
- [ ] Links are real and were loaded
