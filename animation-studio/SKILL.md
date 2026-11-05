---
name: animation-studio
description: Turn an idea or script into a finished animated video (Bible story, tech/programming, maths/education or general story/ad) in a chosen style (stickman, whiteboard, flat 2D, modern vector, storybook, toon 3D, cinematic 3D) and format (9:16, 16:9, 1:1, 4:5), after checking that the computer can render it safely. Use for any request to make an animation, animated explainer, cartoon, Bible video or animated short.
---

# animation-studio: idea → script → voice → safe render → MP4

This file is a **router**. Ask the four big questions, check the hardware, then load **only** the files the job needs:
`content/<pack>.md` (writing and accuracy rules) + `styles/<style>.md` (look; its JSON block is the preset the engine reads) + `engines/<engine>/README.md` (how to render). Shared tools live in `shared/`.

**Find the skill folder (`SKILL_DIR`)** = the folder containing this file. Claude Code shows it as the skill's base directory; other agents: the folder of the SKILL.md you were told to read. Always call tools as `"$SKILL_DIR/shared/..."`, quoted (paths often contain spaces). Find a Python 3.10+ (`python3`, `python` or `py -3`) and call it `PY`. After `setup_check.py --install`, use the venv python it prints.

Keep the user informed with a task list. Write every deliverable to `videos/<slug>/` in the user's working folder (slug = short lowercase-hyphen name). Explain in plain language.

## What works in this version
| Part | Status |
|---|---|
| Content packs | ✅ Bible (`content/bible.md`) · ✅ Tech (`content/tech.md`) · ✅ General story/ad (`content/general-story.md`) · ✅ Maths/education (`content/education-math.md`) |
| Styles | engine A: ✅ Stickman · ✅ Flat 2D · ✅ Storybook · ✅ Whiteboard · ✅ Modern vector — engine B: ✅ Manim (+ Whiteboard / Modern vector colours) — engine C: ✅ Toon 3D — engine D: ✅ Cinematic 3D |
| Engines | ✅ A py2d (Python 2D) · ✅ B Manim (LaTeX optional) · ✅ C Toon 3D (slow: tier-limited) · ✅ D Blender (Eevee previews, Cycles finals on POWER) |
| Formats | ✅ 9:16 · ✅ 16:9 · ✅ 1:1 · ✅ 4:5 |
| Captions | ✅ .srt always + styled burn-in with word highlight (`shared/captions.py`) |
| Voice | ✅ user's recording · ✅ Piper TTS (`shared/voice.py`, free, offline) |
| Music/SFX | ✅ synthesized (`shared/sound.py`) · ✅ user's own licensed music file |
| Editor projects | ✅ Kdenlive · ✅ Shotcut · ✅ DaVinci Resolve (FCPXML) · ✅ Blender VSE · 🧪 OpenShot (experimental) · ✅ editor pack (CapCut, any editor) |
| Brand kit | ✅ saved brands (user folder), watermark, lower third, brand end card, brand colours on any style (`shared/brand.py`, [docs/branding.md](docs/branding.md)) |
| Software installs | ✅ one verified registry (`shared/tools.yaml`) with commands for Windows, macOS and each Linux family; never installs without a yes |

If the user picks a 🚧 item, say so plainly, offer the closest ✅ option, and still deliver the script package.

## Stage 1: Intake (AskUserQuestion, max 4 questions per call; skip anything already answered)
**Call 1**
1. **Content:** Bible story · Tech/programming · Maths/education · General story/ad
2. **Style:** offer the default for the content first (Bible → Storybook · Tech → Modern vector · Maths → Manim · General → Flat 2D), then 2–3 others. Mention Stickman for fast, light pieces.
3. **Format(s)** (multiSelect): 9:16 1080x1920 (TikTok/Reels/Shorts) · 16:9 1920x1080 (YouTube/projector) · 1:1 1080x1080 · 4:5 1080x1350. `PY shared/formats.py table` prints the platform table.
4. **Quality:** Preview (fast, 720p) · Final (1080p). Recommend a 5 s Preview first, always.

**Call 2** (only what applies)
0. **Branding?** None · Use saved brand (list from `PY "$SKILL_DIR/shared/brand.py" list`) · Create new brand. *Create new:* ask each field ONE at a time, all optional (name, tagline, website, logo file, phones, WhatsApp, emails, socials, colours, OFL font, CTA) and save each with `brand.py set` (it validates phone/email/URL/colour formats); logo via `brand.py logo`, font via `brand.py font`. **Never invent contact details**: only what the user gives (or confirms from their own website). Then the options, with defaults from [docs/branding.md](docs/branding.md): **watermark** (ad/promo ON; Bible, tech and maths OFF), corner/size/opacity/logo or logo+name · **lower third** (when, how long) · **end card** with CTA + contacts (ad/promo ON) and its length · **recolour the style** to the brand colours (yes/no).
5. Topic/story and **length** (30 s · 60 s · 90 s · 2–3 min; other lengths via "Other"). Content packs add their own (Bible: audience).
6. **Voice:** My own recording (default) · Piper TTS (free, offline; default voice `en_US-ljspeech-medium`, public-domain data). Piper needs a one-time install (`setup_check.py --tts --install`) and voice download (`voice.py --download`, ~60 MB): ask first.
7. **Captions burned in?** Suggest Yes for 9:16 and 1:1 (most people watch muted), No for 16:9. An .srt file is always made.
8. **End card "Made with animation-studio"?** Off by default; opt-in only. Never add a watermark.
9. **Output:** Finished MP4 · Project file for an editor · Both.

**Editor choice** (only if the output includes a project file): run `PY "$SKILL_DIR/shared/tools.py" status --kind editor` and show the WHOLE numbered list (✅ installed + version · ❌ not installed · ⚠️ not supported here, e.g. desktop editors on a headless server). The user picks exactly one (AskUserQuestion: up to 4 options with installed editors first; the rest can be typed under "Other"). If the pick is ❌, show `PY "$SKILL_DIR/shared/tools.py" flow <editor>` word for word (what it is, the install command for THIS OS/distro/shell, the official link) and ask: **Install now (I'll run it) · I'll install it myself, then say "done" · Pick a different editor · Skip, give me MP4 + editor pack**. "Install now" → `tools.py install <editor> --yes` (say first if Windows will show a permission prompt or if a step needs sudo; sudo steps are handed to the user as `! sudo ...`). After any install or "done": run `status` again, confirm ✅, continue where you left off. CapCut and unsupported editors get the editor pack. Details: [docs/editors.md](docs/editors.md).

Record the answers in `videos/<slug>/brief.md`.

## Stage 2: Hardware check (before any render; never skip)
Run `PY "$SKILL_DIR/shared/hwcheck.py"` and show its table and tier in one short message. It also saves the **system profile** (OS + version, WSL, Apple Silicon, Linux distro and family, package managers, shell, display) that every later step reads. **Every install command you show or run comes from `PY "$SKILL_DIR/shared/tools.py" cmd <tool>`** (matched to this OS, distro and shell); never type one from memory. No display (headless) → render-only: no editor apps.
| Tier | Rule | Engines | Limits |
|---|---|---|---|
| LITE | < 12 GB RAM or < 4 CPU threads | A, B | 720p only; Toon 3D and Blender blocked (offer stills) |
| STANDARD | between | A, B full; C ≤ 5 s preview (longer only with confirmation + resume); D Eevee ≤ 5 s at 720p, low samples | 1 render job; workers = threads − 2 |
| POWER | ≥ 32 GB RAM + dedicated GPU ≥ 6 GB VRAM | all, Cycles on the GPU | workers = threads − 1 |
If the laptop is on battery, warn before any render longer than a minute. If free RAM is under 25 %, ask the user to close big apps.

## Stage 3: Pick the engine (style → engine), then load files
| Style | Engine | Load |
|---|---|---|
| Stickman, Flat 2D, Storybook, Whiteboard, Modern vector | A `engines/py2d` | `styles/<style>.md`, `engines/py2d/README.md` |
| Manim (maths, algorithms, diagrams); Whiteboard/Modern vector colours also work here | B `engines/manim` | `styles/manim.md` (or the chosen style), `engines/manim/README.md` |
| Toon 3D | C `engines/toon3d` (a project folder with `story.js` + `world.js`) | `styles/toon-3d.md`, `engines/toon3d/README.md` |
| Cinematic 3D | D `engines/blender` (scene.json, Z up) | `styles/cinematic-3d.md`, `engines/blender/README.md` |
If the tier blocks the engine, say why and offer: the same story in an engine-A style, or a few stills only. The user may override a limit only after a clear warning ("this may freeze or overheat your computer; save your work first").

Then load `content/<pack>.md` and follow its research and writing stages.

## Stage 4: Script package (content pack rules), then STOP
Every pack delivers: the narration in a copyable block (≈ 3.7 words/s unless the pack says otherwise) with word count and length → `script.txt`; a **shot list** → `shotlist.md`; pack extras (Bible: fidelity table, study notes, description); and **sources at the end**. Never invent verses, quotes, APIs, flags, versions or facts: fetch or run them, otherwise mark **UNVERIFIED**.
Then hand off the voiceover (user's recording: mp3/wav, no music) and **wait** for the audio. If the user only wanted the script, stop here.

## Stage 5: Production
1. **Setup:** `PY "$SKILL_DIR/shared/setup_check.py" --engine <engine>` → ✅/❌ table. A missing tool (Blender, Manim, Node, LaTeX, Inkscape...) uses the same flow as editors: show `tools.py flow <tool> --for engine`, then **Install now · I'll install it myself, then say "done" · Choose another style · Skip (script, shot list and references only)**; re-check after. Python packages go only into the skill's own `.venv` (`--install`, after a yes).
2. **Voice + timing.** Piper: `PY "$SKILL_DIR/shared/voice.py" script.txt voice.wav --timing work --speed 0.85` (exact phrase times, no guessing). User's recording: `PY "$SKILL_DIR/shared/timing.py" voice.mp3 script.txt --out work`. Both write `work/words.json` + `work/phrases.json`.
3. **Scene:** engine A: `videos/<slug>/scene.json`; engine B: a Manim `.py` scene that starts with `from studio import *`; engine C: `videos/<slug>/story.js` + `world.js`; engine D: a Blender `scene.json` (formats in the engine READMEs). One shot per phrase; keep faces, text and key props inside the safe zone of every chosen format (`shared/formats.md`).
4. **Look check:** render 3–6 stills per format (`--frames 0,60,...`), make a contact sheet (`PY "$SKILL_DIR/shared/sheet.py" sheet.jpg <dirs> --safe <fmt>`), **show it**, and check it against the content pack's rules (Bible: reverence + violence). Fix before rendering.
5. **Estimate:** `PY "$SKILL_DIR/shared/estimate.py" --engine <engine> scene.json --fmt <fmts> --quality <q>` (Manim: `--engine manim scene.py --name SceneName --timing work/phrases.json`; Toon 3D: `--engine toon3d <project folder>`; Blender: `--engine blender scene.json`) → `DECISION: OK` render · `ASK` tell the user "~X min, Y GB" and ask (offer the 5 s preview) · `REFUSE` not enough disk (needs 2× the estimate): ask the user to free space.
6. **Render** one format at a time (never two jobs at once). Long renders run in the background; the engine runs at low priority, resumes from the last saved frame if re-run, and pauses itself (exit code 4) if free RAM drops below 15 %. Tell the user they can keep working.
7. **Audio:** music `PY "$SKILL_DIR/shared/sound.py" music music.wav --seconds <video length> --mood warm|calm|tense|tech|playful`, SFX `... sfx sfx.wav --seconds <len> --cues cues.json` (pop, whoosh, type, chime, success, swell, rain, soft thunder), then `PY "$SKILL_DIR/shared/mix.py" voice.wav music.wav sfx.wav --music-db -12 --sfx-db -10 --seconds <len>` (music never louder than −6 dB under the voice; −9 to −12 for speech-heavy or reverent videos). A user-supplied music file replaces music.wav: remind them once that they must own the rights.
7b. **Brand** (if chosen): recolour before rendering (`brand.py recolor <brand> --style <style> --out style_<brand>.md`, use it as the scene's style); after rendering, `brand.py apply <brand> frames_<fmt> branded_<fmt> --fmt <fmt> [--watermark tr,9,90,logo] [--lower-third a,b] [--end-card 2.5 --cta "..."] [--captions]` and use `branded_<fmt>` from here on. With an end card, mix the audio with `--seconds <new length>`.
8. **Captions + finish + QA:** `PY "$SKILL_DIR/shared/captions.py" work out/<Title> --style <style> --fmt <fmt> --quality <q>` (→ `.srt` + `_<fmt>.ass`), then `PY "$SKILL_DIR/shared/finish.py" frames_<fmt> out/<Title>_<fmt>.mp4 --audio mix.wav --quality <q> [--ass out/<Title>_<fmt>.ass] --srt out/<Title>.srt [--end-card only if opted in]`. Check the QA lines (black/still spans, about −14 LUFS) and look at the `_qa.jpg` sheet.
9. **Editor project** (if chosen): `PY "$SKILL_DIR/shared/editors.py" prepare --frames frames_<fmt> --shots "<f0>-<f1>:<name>,..." --final out/<Title>_<fmt>.mp4 --voice voice.wav --music music.wav --sfx sfx.wav --srt out/<Title>.srt --out videos/<slug>/editor` then `... export videos/<slug>/editor/timeline.json --editor <kdenlive|shotcut|openshot|resolve|blender-vse|pack>`. Show its check table (timing must match the MP4; Kdenlive/Shotcut also get a 2 s melt render). Tell the user how to open it (docs/tools/<editor>.md).
10. Deliver the MP4(s), the .srt, the editor project if any, and one line per shot describing what it shows. Optional end card only if the user opted in.

## Safety rules (always)
- Never start a render without Stage 2 and step 5 (estimate). Always offer "Preview 5 s first".
- Respect the tier limits; overrides only after a clear warning and a yes.
- One heavy job at a time. Never delete or overwrite the user's files without asking (re-rendering into an existing frames folder resumes; `--force` overwrites, so ask).
- If a tool is missing or the user declines installs, still deliver the script, shot list and references.

## Credits and licences
Code: MIT (see LICENSE). Bundled third-party code is listed in THIRD_PARTY_NOTICES.md. The skill bundles no fonts, music or images: it uses system fonts and synthesized sound. Users' videos are theirs: no forced watermark; the end card is opt-in.
