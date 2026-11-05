# CapCut

Popular free editor by ByteDance (Windows, macOS, phones). Its project format is closed.

- **Kind:** editor · **Free:** free with paid extras · **Systems:** Windows, macOS
- **Official download:** https://www.capcut.com/

## How animation-studio uses it
No project file (closed format). The skill gives an editor pack (numbered shot clips, audio stems, captions .srt, EDIT_GUIDE.txt with drag-in steps).

Project file: `none` (none: editor pack)

## Check whether it is installed
```
python shared/tools.py status --kind editor
```

## Install
The skill shows the right command for the detected system (`python shared/tools.py cmd capcut`) and asks before running anything.

### Windows (winget, else Chocolatey or Scoop)
```
winget install --id ByteDance.CapCut -e --accept-package-agreements --accept-source-agreements
```
Note: Not on Chocolatey or Scoop (checked); winget works.

### macOS (Homebrew; Apple Silicon and Intel)
```
brew install --cask capcut
```

### Ubuntu / Debian / Linux Mint / Pop!_OS
Not available on this system.

### Fedora / RHEL family
Not available on this system.

### Arch / Manjaro / EndeavourOS
Not available on this system.

### openSUSE
Not available on this system.

### Any Linux (Flatpak / Snap)
No Flatpak or Snap package.

## Troubleshooting
- Follow EDIT_GUIDE.txt: import media/, place numbered clips in order, audio stems on their own tracks, import the .srt.

_Generated from shared/tools.yaml by shared/make_docs.py. Package names verified on 2026-11-05 (see tools.yaml)._
