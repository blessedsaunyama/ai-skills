# AI Skills

Agent Skills for Claude (and other AI coding agents) by **Blessed Tanaka Saunyama** · [Arcetel Solutions](https://www.arcetel.com). MIT licence.

Each folder is one self-contained skill: a `SKILL.md` plus the tools and references it needs.

| Skill | What it does |
|---|---|
| [animation-studio](animation-studio/) | Idea or script → finished animated video in 8 styles on 4 engines (py2d, Manim, Toon 3D, Blender), 4 formats, Bible/tech/maths/general packs, Piper voice, captions, brand kit, hardware safety tiers |
| [bible-story-creator](bible-story-creator/) | Scripture-faithful animated Bible story videos: KJV-verified script, fidelity table, shot list, Ellen G. White study notes, then an MP4 from your voiceover in 9:16 / 16:9 / 1:1 / 4:5 |
| [doc-studio](doc-studio/) | Create and edit Word, PowerPoint, Excel, CSV and PDF documents on any topic, with content packs (SDA/Church, Health, Education, Tech, Business), verified sources, English + Shona, saved brands and edit-on-a-copy |
| [design-studio](design-studio/) | Flyers, posters, roll-up banners, social posts and stories, certificates, YouTube thumbnails and simple original logos from your own logos, photos and text (no AI people): 3 variations, print-ready PDF with bleed, PNG and editable SVG; also edits existing SVG/AI/PDF/CDR designs |

## Install a skill

**Claude Code**
```
git clone https://github.com/blessedsaunyama/ai-skills
cp -r ai-skills/<skill-name> ~/.claude/skills/<skill-name>
```
Then start a new session and type `/<skill-name>`, or just ask for what the skill does.

**claude.ai**: zip one skill folder (the folder itself at the top of the zip) and upload it under **Settings > Capabilities > Skills**.

**Other agents** (Codex, Gemini CLI, OpenCode…): copy the skill folder and tell the agent to follow its `SKILL.md`.

Each skill checks your computer and asks before installing anything it needs.

## Principles shared by these skills
- Never invent facts, quotes, Bible verses or citations: verify from the source or mark **UNVERIFIED**.
- Nothing is installed or overwritten without asking.
- No machine-specific paths; personal data (brands, voices) lives in your user folder, never in the skill.

## Licence
MIT © 2026 Blessed Tanaka Saunyama. Bundled third-party code keeps its own licence (see each skill's notices, e.g. `animation-studio/THIRD_PARTY_NOTICES.md`, `bible-story-creator/kit/vendor/`, `design-studio/THIRD_PARTY_NOTICES.md` for its bundled OFL fonts).
