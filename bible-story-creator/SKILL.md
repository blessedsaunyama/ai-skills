---
name: bible-story-creator
description: Create scripture-faithful animated Bible story videos (script, fidelity table, shot list, KJV and Ellen G. White references, then a rendered MP4 from the user's voiceover in vertical, landscape, square or 4:5 formats). Use for any Bible story, Bible video, children's Bible animation or Sabbath School story request.
---

# Bible story: passage → research → faithful script → shot list → voiceover → video

This skill turns a Bible story into an animated video (or a read-aloud story or lesson) that **never says something the Bible doesn't say**. Every line can be traced to Scripture or a cited Ellen G. White (EGW) passage, or is openly marked as artistic detail. The default flow is: **script package first → the user records the voiceover (ElevenLabs or their own voice) → render the video.**

Folder layout (all paths are relative to this SKILL.md, so nothing is machine-specific):
- `tools/bible_fetch.py`, `tools/egw_fetch.py`: fetch exact verse and EGW text. `tools/check_quotes.py` proves every quote matches (Python standard library only)
- `kit/`: the animation engine and its tools (see `kit/README-kit.md`, `kit/FORMATS.md`)
- `references/`: [egw-books.md](references/egw-books.md), [egw-chapter-index.md](references/egw-chapter-index.md), [animation-styles.md](references/animation-styles.md), [video-pipeline.md](references/video-pipeline.md), [voiceover.md](references/voiceover.md)
- `examples/daniel-lions-den/`: a complete worked example. Read it before writing your first script.

Keep the user informed with a task list. Write every deliverable to the project folder `bible-videos/<slug>/` in the user's working directory (create it), and show the key parts in chat.

## Core rules (non-negotiable)
1. **Scripture is the authority.** EGW writings are supporting commentary from an Adventist perspective. They never replace or contradict the text.
2. **Never put invented words in a biblical character's mouth as if quoted.** Spoken dialogue is either (a) verbatim Scripture with its reference, or (b) narration. A dramatised line must closely restate the verse's meaning and is tagged 🔎 in the fidelity table.
3. **Never quote from memory.** Fetch every Bible verse and every EGW quote with the tools below before using it. If a quote can't be retrieved and verified, paraphrase it and mark it **UNVERIFIED**, or leave it out. Never invent a page number, reference code, chapter title or URL.
4. **Label everything.** Each script line gets exactly one tag:
   - 📖 **Scripture**: stated in the text (give the reference)
   - 🔎 **Inference**: a reasonable reading of the text (explain in one line)
   - 📚 **EGW**: from a cited EGW passage (give the reference code)
   - 🎨 **Artistic**: visual or emotional detail the text doesn't give (clothing, weather, expressions). Allowed only if it doesn't contradict Scripture.
   - If a line mixes sources, either split it into two rows or give it the **weakest** tag that applies (📖 > 📚 > 🔎 > 🎨) and say which part is which. Lesson and application lines ("God is with us too") are 🔎, with the verses they're drawn from.
5. **Reverence.** Humour is fine for children, but never at God's expense or about sacred things. **God the Father is never shown as a human figure**: use light, glory, a cloud, fire, wind or a voice. **Jesus** is a full character shown with dignity and warmth, never comic. **Angels** are majestic men in shining white, with no baby cherubs and wings only where the text describes them. Satan or the serpent is never the comic hero. Details: [animation-styles.md §4](references/animation-styles.md).
6. **Violence is implied only.** Use cutaways, shadows, reactions and sound. No blood, wounds or visible death. Disturbing details (e.g. Dan 6:24) are told in one restrained line or left out for young audiences, and the accuracy notes say so.
7. **Don't over-claim.** When Scripture is silent (the number of wise men, what fruit it was), say so instead of filling the gap.
8. **Translation.** Quote the **KJV** word for word by default (public domain). If the user picks NKJV, ESV or NIV at intake, keep quotes short and name the version. EGW books published before 1929 may be quoted with citations.
9. **EGW stays out of the video.** By the user's choice, EGW references go only in `study-notes.md` and the "Further reading" line of the video description. An end card only if the user asks; never a narrator mention.
10. **English only** (for now).

## Stage 0: Locate tools
`SKILL_DIR` = the folder containing this SKILL.md (Claude Code shows it as the skill's base directory; otherwise see [video-pipeline.md §7.0](references/video-pipeline.md)). Use `"$SKILL_DIR/tools/..."` and `"$SKILL_DIR/kit/..."`, never absolute paths from another machine. Find a working Python (`python3`, `python` or `py`) and call it `PY`. Always quote paths ("$SKILL_DIR/...") because folders often contain spaces.

## Stage 1: Intake
Skip any question the user already answered. Map loose wording instead of re-asking: "kids/children" → Kids 8–12, "little ones/preschool/under 8" → Young children 3–7, "teens/young people" → Youth, "church/everyone" → Whole congregation. Then say which you assumed. Ask with AskUserQuestion (at most 4 questions per call, multiple choice, the user can always type "Other"), or in plain text if that tool is missing.

**Call 1:**
1. **Story or passage?** (skip if given) Offer 3 well-known stories plus "Suggest ideas" (→ Stage 2).
2. **Who is it for?** Young children (3–7) · Kids (8–12) · Youth / teens · Whole congregation. This sets vocabulary, pace, humour and how danger is shown ([animation-styles.md §2](references/animation-styles.md)).
3. **Length?** Supported: 30 s · 45 s · 60 s · 90 s · 2 min · 3 min, or custom. AskUserQuestion allows only 4 options, so offer **30 s · 45 s · 60 s · 2–3 min**, and say in the question text that 90 s or any other length (or "read-aloud, no video") can be typed under "Other".
4. **Format(s)?** (multiSelect) 9:16 vertical · 16:9 landscape · 1:1 square · 4:5 portrait. Always ask unless given. If the user doesn't mind, use 9:16.

Then show the platform table and, if more than one format was picked, the render plan (run `$PY "$SKILL_DIR/kit/tools/formats.py" table` and `$PY "$SKILL_DIR/kit/tools/formats.py" plan <formats> --seconds <length>`):

| Format | Size | Best for |
|---|---|---|
| Vertical 9:16 | 1080x1920 | WhatsApp Status, TikTok, Instagram Reels/Stories, YouTube Shorts, Facebook Reels |
| Landscape 16:9 | 1920x1080 | YouTube, church projector/TV screen |
| Square 1:1 | 1080x1080 | Facebook/Instagram feed, WhatsApp chats |
| Portrait 4:5 | 1080x1350 | Instagram/Facebook feed |

Render time (measured on a 4-core Windows laptop, CPU only) is about **4.5–5 s per frame** at 1080x1920 once warm: 30 s ≈ 1.2 h, 45 s ≈ 1.8 h, 60 s ≈ 2.4 h, 3 min ≈ 7 h per vertical render. 16:9 costs about the same, 1:1 about 60 %, 4:5 about 75 %, and a 1920x1920 FAST master about 1.8×. Slower machines can take twice as long. After the first stills, re-estimate with the measured `s/frame` (`formats.py plan ... --spf <value>`).

**Call 2 (only what applies):**
5. **Render mode** (only if 2+ formats): **FAST**: one master render with a centre-safe composition, then ffmpeg crops to each format (cheaper; framing is a compromise). **BEST**: a separate render per format, each with its own framing (costs the sum of all formats).
6. **Translation:** KJV (default) · NKJV · ESV · NIV. Ask only if the user hinted at another version; otherwise use KJV and say so.
7. **Voiceover:** ElevenLabs · My own voice. (Both work the same way: the skill gives the script, the user uploads the audio.)

Record the answers in `bible-videos/<slug>/brief.md` (slug = short story name, lowercase with hyphens, e.g. `david-goliath`).

## Stage 2: Story ideas (only if asked)
Give 8–10 numbered ideas, mixing Old and New Testament and suited to the audience. For each: the title and passage reference, a hook line taken from the text (fetched), the spiritual lesson, 2–3 big visual moments the kit can animate, and the matching EGW chapter from [egw-books.md](references/egw-books.md). Ask the user to reply with a number.

## Stage 3: Research (always, before writing)
1. **Fetch the passage**, including a few verses before and after:
   `$PY "$SKILL_DIR/tools/bible_fetch.py" "Daniel 6" --out bible-videos/<slug>/scripture.md` (add `--version NKJV` etc. if chosen).
   It prints each verse verbatim plus the BibleGateway URL it loaded. Fallbacks if it fails: WebFetch the BibleGateway URL `https://www.biblegateway.com/passage/?search=<Book>+<chapter>%3A<verses>&version=KJV` and ask for verbatim text. If both fail, every quote is **UNVERIFIED**. Never type a verse from memory.
2. **Cross-references and parallels:** fetch parallel accounts (e.g. Gospel parallels, Kings/Chronicles) and note any differences.
3. **EGW research:** find the chapter in [egw-books.md](references/egw-books.md) or [egw-chapter-index.md](references/egw-chapter-index.md), then run
   `$PY "$SKILL_DIR/tools/egw_fetch.py" <chapter link or id> --out bible-videos/<slug>/egw.md` (`--grep word,word` narrows it). WebFetch on egwwritings.org usually returns HTTP 403, so use this tool. Record exact quotes with their codes. Link only URLs the tool actually loaded.
4. **Myth check:** compare your plan against the [Common myths](#common-myths-never-put-these-in-a-script-as-fact) table.
5. **Fact sheet** (`facts.md`): who, where, when (only as far as the text says), events in biblical order with verse numbers, the exact quotes you plan to use, and what the text leaves unstated.

## Stage 4: Script
Size the narration from the audience's pace ([animation-styles.md §2](references/animation-styles.md)). The default is 3.7 words/s: 30 s ≈ 110 words, 45 s ≈ 165, 60 s ≈ 220, 90 s ≈ 330, 2 min ≈ 440, 3 min ≈ 650. Read-aloud is about 2.5 words/s.

Structure:
1. **Hook** (no setup): a striking fact or short verse from the text.
2. **Setting** in 1–2 lines: who, where, a concrete detail.
3. **Rising action** in biblical order, each beat bigger.
4. **Turning point**: quote the key verse word for word. This replaces the cartoon kit's "ironic twist" and gets the sting and push-in.
5. **Resolution and lesson**: what happened, then the lesson as a clearly separate sentence ("This story shows us...").
6. **Closing memory verse** (short, quoted exactly, with its reference).

Writing rules: plain spoken English with short sentences, numbers written as words (but keep KJV quotes exactly as printed), and never describe what the viewer already sees. Put KJV quotes in their own sentences so the voice reads them clearly. In `script.txt`, write references the way they're spoken ("First Samuel seventeen, verse forty-seven"). In tables and notes, use digits (1 Sam 17:47). A quote may start with a capital letter even when the verse continues mid-sentence; never change any other word.

**Verify before showing:** `$PY "$SKILL_DIR/tools/check_quotes.py" script.txt scripture.md` (add `egw.md` if any EGW wording is quoted anywhere). Every quote must print OK. Fix any NOT FOUND from the source text, or mark it UNVERIFIED.

Deliver:
- The narration in a copyable block, with the word count and estimated length → `script.txt` (narration only: no tags, no stage directions).
- The **fidelity table** (required) → `fidelity.md`:

| # | Script line (short) | Tag | Source / justification |
|---|---|---|---|
| 1 | "Daniel kept praying..." | 📖 | Dan 6:10 |
| 2 | Evening light through the window | 🎨 | Not in text; doesn't contradict |

- **Accuracy notes:** anything uncertain, translation differences, what was simplified or left out for the audience (e.g. Dan 6:24), and what the text leaves unstated.

## Stage 5: Animation plan and shot list
Style: the house style is **flat 2D cartoon** (the kit), switching to the **silhouette / backlit** treatment for solemn beats. Say which beats get silhouette and why. Other styles from [animation-styles.md](references/animation-styles.md) are recommendations only ("needs another tool").

Shot list → `shotlist.md`, one row per shot:

| # | Time (s) | Script words | Visual (characters from `BIBLE`, props, world) | Camera | Light / mood | Formats note | SFX / music |
|---|---|---|---|---|---|---|---|

- Times are **estimates** from the word count. The real frame ranges come from `timing.py` after the voiceover arrives (Stage 7).
- Frame 0 is already the hook image. Usually there is one shot per phrase. Vary shot sizes (wide establishing → medium → close-up on the key object → reaction → push-in on the turning point).
- **Formats note:** for 9:16, stage characters in depth (only ±0.8 m is visible at 4 m). For 16:9, fill the sides. In FAST mode, keep faces and key props inside the centre-safe box (e.g. 1080x1080).
- Divine moments use light, wind, fire or sound (`fxGlory`, a flash, a warm preset). Violence is implied (rule 6). Clothing and settings follow the Ancient Near East (tagged 🎨, [animation-styles.md §6](references/animation-styles.md)).
- Every shot only illustrates its own line. Don't add events that aren't in the fidelity table.

## Stage 6: Script package + voiceover hand-off (then STOP and wait)
Write and show:
- `script.txt` · `fidelity.md` (+ accuracy notes) · `shotlist.md`
- `study-notes.md`: the passage reference, key verses (verbatim), the EGW chapter with verified quotes and codes, cross-references, and links actually loaded
- `description.txt`: a ready-to-paste video description: title, a one-line summary, "Scripture: <reference> (KJV)", the memory verse, and **"Further reading: Ellen G. White, *<Book>*, ch. <n>"** (EGW lives here, not in the video)
Then send the voiceover hand-off from [voiceover.md](references/voiceover.md) (ElevenLabs settings, or own-voice tips, and pronunciation help for names). Ask for the audio file and any wording changes. **Stop here** until the audio arrives. If the user only wanted the script package or a read-aloud, skip to Stage 8.

## Stage 7: Video production (after the audio is uploaded)
Follow [references/video-pipeline.md](references/video-pipeline.md) exactly. In short:
1. **Setup check:** `$PY "$SKILL_DIR/kit/tools/check_setup.py"` prints a ✅/❌ table (node 22.6+, python3, numpy, Pillow, ffmpeg, bash, playwright, chromium). Skip anything installed. **Ask before installing** what's missing (the tool prints Windows, macOS and Linux commands). If the user declines, deliver Stages 1–6 and 8 and explain how to render later.
2. **Project:** `bash "$SKILL_DIR/kit/tools/setup.sh" bible-videos/<slug>`, then copy `voice.mp3` and `script.txt` into it.
3. **Timing:** `$PY timing.py voice.mp3 script.txt --out work` → check `work/phrases.json`.
4. **Code the shots:** `work/PLAN.md` (frames per shot) → `web/story.js` (shots, cameras with `camFromKeys`, `fovBy` for BEST framing, lights incl. a solemn preset, `actorsAt` with `T.bibleFront`, `fxAt` with `T.fxLion`/`T.fxGlory`...) → the world section of `web/main.js`. Run `node cast.mjs stills/cast.png` after any cast change.
5. **Look check:** `FMT=<fmt> node render.mjs stills/a "<frames>"` + `$PY sheet.py stills/a stills/sheet_a.jpg --safe <fmt>` (FAST: `SIZE=<master>` + `--centre <box> --crops <list>`). Check against the reverence rules too. Send the sheet, then render.
6. **Sound:** rewrite `audio.py` (reverent bed, no comic SFX) → `$PY audio.py` → `$PY mix.py voice.mp3 music.wav sfx.wav --music-db -9`.
7. **Render + finish:** BEST: `FMT=<fmt> node render.mjs frames_<fmt> "0-<N-1>"` → `bash finish.sh "<Title>" frames_<fmt> <fmt>` for each format. FAST: `SIZE=<master> node render.mjs frames_master ...` → `bash finish.sh "<Title>" frames_master master` → `$PY formats.py crop out/<Title>_master.mp4 <formats>` (spaces in the title become hyphens in file names). Run long renders in the background and watch the progress lines. Check `out/qa_sheet_*.jpg`.
8. Deliver the MP4(s) with one line per shot describing what it shows.

## Stage 8: Extras (offer at the end; produce only what the user picks)
Ask once (multiSelect): **Discussion questions · Sabbath School lesson · Thumbnail · Captions (.srt)**.
- **Discussion questions** (`questions.md`): 3–5, matched to the audience. Each has a verse answer (fetched) and one application question.
- **Sabbath School lesson** (`lesson.md`): title, memory verse (verbatim), the passage, 3 key points each with a verse, an EGW thought (verified quote + code, or none), application, a short activity for the age group, and a closing prayer idea.
- **Thumbnail:** render a key still per format, then `$PY thumb.py <still> "<2–5 word title>" out/thumb_<fmt>.jpg [--size 1280x720]`. No image of God the Father; keep text inside the safe zone.
- **Captions:** `$PY srt.py work out/<Title>.srt` (word for word from the script). Burn them in only if asked.

## Stage 9: References (end of every output)
- **Scripture:** BibleGateway links, e.g. [Daniel 6 (KJV)](https://www.biblegateway.com/passage/?search=Daniel+6&version=KJV)
- **Further reading (EGW):** book, chapter and codes, linked only to text.egwwritings.org pages the tool actually loaded (or marked UNVERIFIED)
- **Discussion questions** (3–5) for lesson and read-aloud formats, or if picked in Stage 8

## Common myths: never put these in a script as fact
| Myth | What the Bible says |
|---|---|
| Adam and Eve ate an apple | "The fruit": no species named (Gen 3:6) |
| Three wise men | Three gifts; the number of men isn't given (Matt 2:1-11) |
| Wise men at the manger | They came into "the house" and saw "the young child" (Matt 2:11) |
| Jonah swallowed by a whale | "A great fish" (Jonah 1:17) |
| Two of every animal on the ark | Clean beasts "by sevens", unclean "by two" (Gen 7:2-3) |
| Mary Magdalene was a prostitute | Not stated; "seven devils" went out of her (Luke 8:2) |
| Moses had horns | A mistranslation; "the skin of his face shone" (Ex 34:29-30) |
| The innkeeper turned them away | No innkeeper is mentioned; "no room for them in the inn" (Luke 2:7) |
| The wise men were kings | Called "wise men from the east" (Matt 2:1) |
| All angels have wings and halos | Seraphim have six wings (Isa 6:2); angels often appear as men (Gen 18:2; 19:1) |
| Daniel was a young man in the lions' den | Taken captive in Jehoiakim's reign (Dan 1:1-6); the den is under Darius (Dan 5:31; 6), many decades later, so he was an older man. A timeline inference 🔎: draw him older, and don't state an age as fact |
| Goliath was ten feet tall (as a fact) | "Six cubits and a span" (1 Sam 17:4); converting to feet is an estimate, so say "about nine feet" and tag it 🔎 |
| David killed Goliath with the stone alone | The stone felled him (1 Sam 17:49); v. 50-51 add that David then used Goliath's sword. Keep the summary honest (implied, not shown) |

## Final self-check (before sending anything)
- [ ] `check_quotes.py` printed "all quotes verified" for the script (and every quote in notes, lessons and questions was copied from fetched text)
- [ ] Every 📖 line was checked against text printed by `bible_fetch.py` (or marked UNVERIFIED)
- [ ] No invented dialogue is presented as a biblical quote
- [ ] Every 📚 quote was printed by `egw_fetch.py`, with the exact code. None appear in the video narration
- [ ] Every 🎨 detail is consistent with Scripture
- [ ] Nothing from the Common Myths table appears as fact
- [ ] Reverence rules followed (no figure for the Father, dignified Jesus, majestic angels), and violence is implied rather than graphic
- [ ] Wording suits the chosen audience, and the length matches the word budget (±10 %)
- [ ] Links are real and were loaded (BibleGateway URLs in the standard format are fine)
- [ ] Shot list matches the chosen format(s) and mode (safe zones, centre-safe box for FAST)
- [ ] Deliverables are written to `bible-videos/<slug>/`, and the user knows what to do next (record the voiceover / pick extras)
