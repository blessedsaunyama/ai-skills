# Video pipeline: exact commands (Stage 7 of SKILL.md)

All paths are relative. `KIT` = the `kit/` folder next to SKILL.md, `PROJ` = the project folder (default `./bible-videos/<slug>` in the user's current working directory). `PY` = the python that `check_setup.py` reported (often `python3`; on Windows it can be `python` or `py`). Run bash scripts with Git Bash on Windows.

## 7.0 Find the kit (portable, no hard-coded paths)
The kit is always at `<directory containing this SKILL.md>/kit`. Claude Code tells you the skill's base directory when the skill loads. Use it as `SKILL_DIR`. If it isn't known, search from these roots only:
```bash
for d in "./.claude/skills/bible-story-creator" "$HOME/.claude/skills/bible-story-creator" "/mnt/skills/user/bible-story-creator" "/mnt/user-data/uploads/bible-story-creator"; do [ -f "$d/SKILL.md" ] && SKILL_DIR="$d" && break; done
[ -z "$SKILL_DIR" ] && SKILL_DIR="$(dirname "$(find "$HOME" /mnt -maxdepth 6 -name SKILL.md -path '*bible-story-creator*' 2>/dev/null | head -1)")"
KIT="$SKILL_DIR/kit"
```
Treat `KIT` as read-only. All work happens in `PROJ`.

## 7.1 Setup check (always before any rendering)
```bash
$PY "$KIT/tools/check_setup.py"
```
It prints the ✅/❌ table and install commands for Windows, macOS and Linux. Show the table to the user. Skip anything that's ✅. **Ask before installing** anything ❌ (one question listing exactly what will be installed). If the user declines, stop here and deliver the script package (script, fidelity table, shot list, references, extras). After installing ffmpeg on Windows, a new shell may be needed. Add `%LOCALAPPDATA%\Microsoft\WinGet\Links` to PATH for the current session.

## 7.2 New project
```bash
bash "$KIT/tools/setup.sh" "$PROJ" && cd "$PROJ"
cp <voice file> voice.mp3      # or .wav, keep the original untouched
printf '%s\n' "<final narration text exactly as recorded>" > script.txt
```
setup.sh works offline (three.js and toon.ts are vendored in `kit/vendor/`).

## 7.3 Timing
```bash
$PY timing.py voice.mp3 script.txt --out work
```
Check `work/phrases.json`: pauses should fall at sentence ends. Total frames = `frames30`. Claude can't hear audio, so the script text is required (or install faster-whisper).

## 7.4 Shot plan → `work/PLAN.md`, then code
1. Turn the Stage 5 shot list into frame ranges using `phrases.json` (usually one shot per phrase; merge tiny phrases).
2. Edit `web/story.js`. It exports `SHOTS`, `shotAt`, `camAt`, `dofAt`, `LIGHTS`, `lightFor`, `worldAt`, `actorsAt(f,T)`, `fxAt(f,T)`, all pure functions of the frame. Start from the soldier example's structure. Prefer `camFromKeys` and `idle`/`blinkAt` from `motion.js` (`import { M, camFromKeys, idle, blinkAt, q, FMT, fmtPick } from './motion.js'`).
3. Characters: `R = (T, who, o, pos, extra) => ({ key: who + JSON.stringify(o), draw: (p) => T.bibleFront(p, who, o), x, y, z, ...extra })`. Outfits are in `T.BIBLE` (shepherdBoy, shepherd, prophet, youngProphet, jesus, disciple, woman, womanB, child, villager, king, official, soldierIsr, giant, angel). Animals and effects: `T.fxLion(p,{pose:'lie'|'sit', mouth:'shut'|'open'})`, `T.fxSheep`, `T.fxGlory(p,t)`, `T.fxStone`, `T.fxSling(p,t)`. Scale with `s` (child 0.7, youth 0.9, giant ~1.3, lion 1.5).
4. World: in `web/main.js`, replace everything between `// ---------- world ----------` and `// ---------- cards ----------` (the soldier bridge, temple and village), plus the story parts of `worldState()` and the helmet prop. Build from `tbox` + `paint.js` textures (plaster, stone, dirt, grass, planks, roof). See animation-styles.md §6 for an ANE look. **Build the world wide enough for 16:9** (it shows ±2.6 m at 4 m where 9:16 shows ±0.8 m).
5. After any cast edit: `cat web/toonbase.js web/roman.js web/biblical.js > web/toon.js`, then `node cast.mjs stills/cast.png` and look at it.

## 7.5 Look check (before the long render)
Pick stills at each shot's middle, the transitions and the key actions:
```bash
FMT=9x16 node render.mjs stills/a "5,40,95,..."  &&  $PY sheet.py stills/a stills/sheet_a.jpg --safe 9x16
```
- BEST mode: one sheet per chosen format (`FMT=16x9 ... stills/a16`, `--safe 16x9`).
- FAST mode: `SIZE=<master> node render.mjs stills/m "..."` then `$PY sheet.py stills/m stills/sheet_m.jpg --centre <safe box> --crops <list>`. Faces and key props must sit inside the green box.
Check: faces inside the safe zone, nobody cut by the frame edge, no posts or railings across faces, no camera inside walls, text not mirrored, ink present, no glory or angel light looking like a human figure of God. Send the sheet with a one-line summary per shot, then start the render.

## 7.6 Sound
```bash
$PY audio.py                                  # rewritten music + cue table -> music.wav, sfx.wav
$PY mix.py voice.mp3 music.wav sfx.wav --music-db -9    # reverent bed; prints the measured levels
```
Confirm music is at or below the target vs voice and SFX at or below −6 dB. Lock picture timing first: any timing change means re-running audio.py and mix.py.

## 7.7 Render + finish
Run long renders with Bash `run_in_background` and watch the `progress` lines. `RESUME=1` continues after an interruption.
- **Single format / BEST:**
  ```bash
  FMT=9x16 node render.mjs frames_9x16 "0-<N-1>"   &&  bash finish.sh "Title" frames_9x16 9x16
  FMT=16x9 node render.mjs frames_16x9 "0-<N-1>"   &&  bash finish.sh "Title" frames_16x9 16x9
  ```
- **FAST:**
  ```bash
  SIZE=1920x1920 node render.mjs frames_master "0-<N-1>"  &&  bash finish.sh "Title" frames_master master
  $PY formats.py crop out/Title_master.mp4 9x16,16x9
  ```
Spaces in the title become hyphens in the output names (`"Daniel and the Lions"` → `out/Daniel-and-the-Lions_9x16.mp4`). finish.sh prints the duration and size, any freeze/black spans (empty = good) and loudness, and writes `out/qa_sheet_<fmt>.jpg`. Look at it. Frozen spans ≥0.4 s or black frames need a fix.

## 7.8 Extras (only those the user picked)
- Captions: `$PY srt.py work out/Title.srt`. Burn them in only on request (the command is in srt.py's header).
- Thumbnail: `FMT=16x9 node render.mjs stills/thumb "<key frame>"` then `$PY thumb.py stills/thumb/f0420.jpg "Daniel and the Lions" out/thumb_16x9.jpg --size 1280x720`.

## Render-time estimate (show at intake)
`$PY "$KIT/tools/formats.py" plan <formats> --seconds <length> --spf <s/frame>`. Measured on a 4-core Windows laptop with CPU SwiftShader (2026-11-04 test): **4.4 s/frame at 1080x1920 and 5.0 s/frame at 1920x1080** once warm (the first frame takes about 10 s while shaders compile). Rough guide for one vertical render: 30 s ≈ 1.2 h, 45 s ≈ 1.8 h, 60 s ≈ 2.4 h, 3 min ≈ 7 h. 1:1 is about 60 %, 4:5 about 75 %, and a 1920x1920 FAST master about 1.8×. Slower machines can take 2× as long.
