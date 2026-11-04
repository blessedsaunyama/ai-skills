# Video editors

Ask for **Output: Project file for an editor** (or **Both**) and animation-studio builds a project for ONE editor: every shot on the video track in order, voice / music / SFX on separate audio tracks, captions as a subtitle track or .srt, same fps and size as the MP4. Each project is checked before it is handed over.

| Editor | Free? | Windows | macOS | Linux | Project file | Opens automatically? | Check done by the skill |
|---|---|---|---|---|---|---|---|
| [Kdenlive](tools/kdenlive.md) | yes (GPL) | ✅ | ✅ | ✅ | `.kdenlive` | yes | Kdenlive renders it itself (--render): size, fps, length, picture vs MP4, audio |
| [Shotcut](tools/shotcut.md) | yes (GPL) | ✅ | ✅ | ✅ | `.mlt` | yes | full render with MLT (Shotcut's engine): size, fps, length, picture vs MP4, audio |
| [OpenShot](tools/openshot.md) | yes (GPL) | ✅ | ✅ | ✅ | `.osp` | yes | parse + timing (experimental) |
| [DaVinci Resolve](tools/davinci-resolve.md) | free edition (Studio is paid) | ✅ | ✅ | ✅ | `.fcpxml` | import: File > Import > Timeline | parse + timing |
| [Blender Video Sequencer](tools/blender-vse.md) | yes (GPL) | ✅ | ✅ | ✅ | `.blend` | yes | re-opened in Blender + strip count + timing |
| [CapCut](tools/capcut.md) | free with paid extras | ✅ | ✅ | — | `none` | no: editor pack | editor pack files present |

**Editor pack** (CapCut, or any editor without a supported project format): numbered shot clips, audio stems, the .srt, the finished MP4 and `EDIT_GUIDE.txt` with drag-in steps.

Commands:
```
python shared/tools.py status --kind editor          # what's installed here
python shared/editors.py prepare --frames ... --shots ... --final ... --out editor/<Title>
python shared/editors.py export editor/<Title>/timeline.json --editor kdenlive
```
