# FFmpeg

Encodes video, mixes audio, burns captions, runs QA.

- **Kind:** engine · **Free:** yes (LGPL/GPL) · **Systems:** Windows, macOS, Linux
- **Official download:** https://ffmpeg.org/download.html

## How animation-studio uses it
Required for every engine (shared/finish.py, mix.py, timing.py, captions burn-in).

## Check whether it is installed
```
python shared/tools.py status --kind engine
```

## Install
The skill shows the right command for the detected system (`python shared/tools.py cmd ffmpeg`) and asks before running anything.

### Windows (winget, else Chocolatey or Scoop)
```
winget install --id Gyan.FFmpeg -e --accept-package-agreements --accept-source-agreements
```

### macOS (Homebrew; Apple Silicon and Intel)
```
brew install ffmpeg
```

### Ubuntu / Debian / Linux Mint / Pop!_OS
```
sudo apt update
sudo apt install -y ffmpeg
```

### Fedora / RHEL family
```
sudo dnf install -y ffmpeg-free
```
Note: Fedora's ffmpeg-free lacks some patented codecs; H.264 export needs RPM Fusion's ffmpeg (sudo dnf install ffmpeg --allowerasing after enabling RPM Fusion).

### Arch / Manjaro / EndeavourOS
```
sudo pacman -S --needed ffmpeg
```

### openSUSE
```
zypper search ffmpeg-7
sudo zypper install ffmpeg-7
```
_The package name could not be verified automatically for this system: the first line searches for it; install only what it finds._

### Any Linux (Flatpak / Snap)
No Flatpak or Snap package.

## Troubleshooting
- 'ffmpeg not found' right after installing: open a NEW terminal (PATH changes need one); the skill also checks WinGet's Links folder.
- Fedora: install RPM Fusion's ffmpeg for H.264.

_Generated from shared/tools.yaml by shared/make_docs.py. Package names verified on 2026-11-05 (see tools.yaml)._
