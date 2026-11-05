# Shotcut

Free, open-source video editor by Meltytech (Windows, macOS, Linux).

- **Kind:** editor · **Free:** yes (GPL) · **Systems:** Windows, macOS, Linux
- **Official download:** https://shotcut.org/download/

## How animation-studio uses it
Writes a native .mlt project (Shotcut's own format) with the shots, separate audio tracks and markers; checks it with Shotcut's bundled melt (2-second render).

Project file: `.mlt` (opens directly)

## Check whether it is installed
```
python shared/tools.py status --kind editor
```

## Install
The skill shows the right command for the detected system (`python shared/tools.py cmd shotcut`) and asks before running anything.

### Windows (winget, else Chocolatey or Scoop)
```
winget install --id Meltytech.Shotcut -e --accept-package-agreements --accept-source-agreements
```

### macOS (Homebrew; Apple Silicon and Intel)
```
brew install --cask shotcut
```

### Ubuntu / Debian / Linux Mint / Pop!_OS
```
sudo apt update
sudo apt install -y shotcut
```

### Fedora / RHEL family
```
sudo dnf install -y shotcut
```

### Arch / Manjaro / EndeavourOS
```
sudo pacman -S --needed shotcut
```

### openSUSE
```
zypper search shotcut
sudo zypper install shotcut
```
_The package name could not be verified automatically for this system: the first line searches for it; install only what it finds._

### Any Linux (Flatpak / Snap)
```
flatpak install --user -y flathub org.shotcut.Shotcut
```
```
sudo snap install shotcut
```

## Troubleshooting
- Clips show as missing: keep the folder in place, or use File > Open Other > relink.
- Captions: Timeline > Subtitles > Import the .srt next to the project.

_Generated from shared/tools.yaml by shared/make_docs.py. Package names verified on 2026-11-05 (see tools.yaml)._
