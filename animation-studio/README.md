# animation-studio

An open-source **Agent Skill** that turns an idea or a script into a finished animated video, safely, on your own computer.

- **Content packs** with accuracy rules: Bible stories (KJV quotes fetched and verified, never invented), tech/programming (every snippet is run, versions from official docs), maths/education (every calculation verified in Python), general stories and ads (facts sourced, legends labelled, honest ad claims).
- **Styles:** Stickman · Whiteboard (marker draw-on) · Flat 2D · Modern vector · Storybook · Manim (maths) · Toon 3D · Cinematic 3D.
- **Formats:** 9:16 (TikTok/Reels/Shorts) · 16:9 (YouTube, projector) · 1:1 · 4:5, each with its own layout and platform-safe zones.
- **Voice:** your own recording, or free offline Piper TTS (licence-checked voices). **Music and SFX** synthesized in code (no copyright claims). **Captions:** .srt always, burned-in with word highlight on request.
- **Editor projects:** Kdenlive, Shotcut, DaVinci Resolve (FCPXML), Blender Video Sequencer, OpenShot (experimental), or an editor pack for CapCut and any other editor. Projects are checked with the editors' own engines.
- **Brand kit:** your logo, colours, OFL font and contacts as watermark, lower third and end card, in every format. Contact details are never invented.
- **Hardware safety:** checks your computer first (LITE / STANDARD / POWER tiers), estimates time and disk before rendering, renders at low priority in resumable chunks, pauses if RAM runs low, one heavy job at a time. Never installs anything without asking.
- **Works everywhere:** Windows, macOS and Linux (Ubuntu/Debian/Mint, Fedora, Arch/Manjaro, openSUSE), with install commands matched to your system from a verified registry. Free software only.

## Install

This skill lives in the [ai-skills](https://github.com/blessedsaunyama/ai-skills) repository, in the `animation-studio/` folder.

### Claude Code
```
git clone https://github.com/blessedsaunyama/ai-skills
cp -r ai-skills/animation-studio ~/.claude/skills/animation-studio
```
Then ask Claude Code: *"Make a 30-second animated Bible story about Daniel in the lions' den"* (or type `/animation-studio`).

### claude.ai
Zip the `animation-studio` folder (the folder itself at the top of the zip), then **Settings > Capabilities > Skills > Upload**. Note: rendering needs the programs below on the machine that runs the code; on claude.ai the skill can still write scripts, shot lists, captions and brand kits.

### Codex, OpenCode, Gemini CLI and other agents
Copy the `animation-studio` folder anywhere and tell the agent: *"Read AGENTS.md in this folder and follow SKILL.md."*

## Requirements
Only Python 3.10+ is needed to start: the skill checks everything else and shows the exact install command for your system, then asks.
| Needed for | Software (all free) |
|---|---|
| everything | Python 3.10+, FFmpeg |
| 2D styles | numpy, Pillow (installed into the skill's own `.venv`) |
| Manim style | Manim Community (+ LaTeX optional) |
| Toon 3D | Node 22.6+, Playwright + Chromium |
| Cinematic 3D | Blender 4.x/5.x |
| Free voice | Piper TTS (optional) |
Check your computer: `python shared/hwcheck.py` · what's installed: `python shared/tools.py status` · per engine: `python shared/setup_check.py --engine py2d`.

## Examples
| Folder | What it shows |
|---|---|
| `examples/bible-noah-preview/` | 5 s Noah's ark in Stickman, Flat 2D and Storybook (engine A), with its fidelity table |
| `examples/bible-shepherd-toon3d/` | 1 Sam 17:34 in Toon 3D (engine C) |
| `examples/bible-tomb-blender/` | Mark 16:2-4 dawn at the tomb in Cinematic 3D (engine D) |
| `examples/tech-python-lists/` | Python lists explainer, code that really ran (Modern vector / Whiteboard) |
| `examples/maths-binary-search/` | Binary search, computed and checked in the scene (Manim) |
| `examples/general-wave-back/` | A tiny original story (Flat 2D) |
| `brands/sample/` | Fictional sample brand for the brand kit |
Each engine has a one-command smoke test in its README (`engines/*/README.md`).

## How it works
`SKILL.md` is a short router: intake questions → hardware check → engine choice → it loads only the files the job needs (`content/`, `styles/`, `engines/`). Shared tools live in `shared/`; docs for every supported program are in `docs/tools/`, editors in `docs/editors.md`, branding in `docs/branding.md`.

## Credits and licence
MIT © 2026 Blessed Tanaka Saunyama ([Arcetel Solutions](https://www.arcetel.com)). Bundled third-party code (three.js, toon.ts) and the programs it calls are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The Toon 3D engine builds on [mromidev/claude-animated-shorts](https://github.com/mromidev/claude-animated-shorts) (MIT).
Videos you make are yours: no watermark is added unless you choose your own brand watermark; the "Made with animation-studio" end card is opt-in.
