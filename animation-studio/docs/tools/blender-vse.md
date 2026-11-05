# Blender Video Sequencer

The video editor built into Blender (free, all OSes).

- **Kind:** editor · **Free:** yes (GPL) · **Systems:** Windows, macOS, Linux
- **Official download:** https://www.blender.org/download/

## How animation-studio uses it
Builds a .blend with every shot as a movie strip in order, voice/music/SFX on their own audio channels, the captions as text strips, matching fps and size (made with Blender's Python API in background mode).

Project file: `.blend` (opens directly)

## Check whether it is installed
```
python shared/tools.py status --kind editor
```

## Install
Installed together with [Blender](blender.md).

## Troubleshooting
- Open the .blend and switch to the Video Editing workspace.
- Media paths are absolute; File > External Data > Find Missing Files if the folder moved.

_Generated from shared/tools.yaml by shared/make_docs.py. Package names verified on 2026-11-05 (see tools.yaml)._
