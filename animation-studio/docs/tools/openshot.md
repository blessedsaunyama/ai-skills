# OpenShot

Free, open-source, beginner-friendly video editor (Windows, macOS, Linux).

- **Kind:** editor · **Free:** yes (GPL) · **Systems:** Windows, macOS, Linux
- **Official download:** https://www.openshot.org/download/

## How animation-studio uses it
Writes a native .osp project (JSON) with the clips on tracks, audio on separate tracks; validates it by parsing.

Project file: `.osp` (opens directly)

## Check whether it is installed
```
python shared/tools.py status --kind editor
```

## Install
The skill shows the right command for the detected system (`python shared/tools.py cmd openshot`) and asks before running anything.

### Windows (winget, else Chocolatey or Scoop)
```
winget install --id OpenShot.OpenShot -e --accept-package-agreements --accept-source-agreements
```

### macOS (Homebrew; Apple Silicon and Intel)
```
brew install --cask openshot-video-editor
```

### Ubuntu / Debian / Linux Mint / Pop!_OS
```
sudo apt update
sudo apt install -y openshot-qt
```

### Fedora / RHEL family
```
sudo dnf install -y openshot
```

### Arch / Manjaro / EndeavourOS
```
flatpak install --user -y flathub org.openshot.OpenShot
```
Note: Not in Arch's official repos, so the Flatpak is used on Arch/Manjaro.

### openSUSE
```
zypper search openshot-qt
sudo zypper install openshot-qt
```
_The package name could not be verified automatically for this system: the first line searches for it; install only what it finds._

### Any Linux (Flatpak / Snap)
```
flatpak install --user -y flathub org.openshot.OpenShot
```

## Troubleshooting
- Experimental export: if a clip is missing, re-import it from media/ and place it at the time shown in EDIT_GUIDE.txt.

_Generated from shared/tools.yaml by shared/make_docs.py. Package names verified on 2026-11-05 (see tools.yaml)._
