# Kdenlive

Free, open-source video editor by KDE (Windows, macOS, Linux).

- **Kind:** editor · **Free:** yes (GPL) · **Systems:** Windows, macOS, Linux
- **Official download:** https://kdenlive.org/download/

## How animation-studio uses it
Writes a native .kdenlive project (MLT XML) with every shot on the video track, voice/music/SFX on separate audio tracks and the captions as a subtitle track; checks it with melt (bundled with Kdenlive).

Project file: `.kdenlive` (opens directly)

## Check whether it is installed
```
python shared/tools.py status --kind editor
```

## Install
The skill shows the right command for the detected system (`python shared/tools.py cmd kdenlive`) and asks before running anything.

### Windows (winget, else Chocolatey or Scoop)
```
winget install --id KDE.Kdenlive -e --accept-package-agreements --accept-source-agreements
```

### macOS (Homebrew; Apple Silicon and Intel)
```
brew install --cask kdenlive
```

### Ubuntu / Debian / Linux Mint / Pop!_OS
```
sudo apt update
sudo apt install -y kdenlive
```

### Fedora / RHEL family
```
sudo dnf install -y kdenlive
```

### Arch / Manjaro / EndeavourOS
```
sudo pacman -S --needed kdenlive
```

### openSUSE
```
zypper search kdenlive
sudo zypper install kdenlive
```
_The package name could not be verified automatically for this system: the first line searches for it; install only what it finds._

### Any Linux (Flatpak / Snap)
```
flatpak install --user -y flathub org.kde.kdenlive
```
```
sudo snap install kdenlive
```

## Troubleshooting
- Clips show as missing: the project uses absolute paths; keep the editor folder where it was made, or use Project > Clean Up / relink.
- A notice says the project was upgraded: normal; Kdenlive converts the file to its current format. Save it once.
- Captions: they are in <project>.kdenlive.srt next to the project (Kdenlive's subtitle file).

_Generated from shared/tools.yaml by shared/make_docs.py. Package names verified on 2026-11-05 (see tools.yaml)._
