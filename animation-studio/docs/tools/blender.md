# Blender

Free 3D suite; engine D (Cinematic 3D) and the Blender Video Sequencer.

- **Kind:** engine · **Free:** yes (GPL) · **Systems:** Windows, macOS, Linux
- **Official download:** https://www.blender.org/download/

## How animation-studio uses it
Runs in background mode with the skill's scripts (engines/blender) to build scenes and render frames, and to build .blend editor projects.

## Check whether it is installed
```
python shared/tools.py status --kind engine
```

## Install
The skill shows the right command for the detected system (`python shared/tools.py cmd blender`) and asks before running anything.

### Windows (winget, else Chocolatey or Scoop)
```
winget install --id BlenderFoundation.Blender -e --accept-package-agreements --accept-source-agreements
```

### macOS (Homebrew; Apple Silicon and Intel)
```
brew install --cask blender
```

### Ubuntu / Debian / Linux Mint / Pop!_OS
```
sudo apt install -y flatpak
flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install --user -y flathub org.blender.Blender
```
Note: Ubuntu 24.04's apt package is Blender 4.0 (old), so the Flatpak (5.x) is offered first.

### Fedora / RHEL family
```
sudo dnf install -y blender
```

### Arch / Manjaro / EndeavourOS
```
sudo pacman -S --needed blender
```

### openSUSE
```
zypper search blender
sudo zypper install blender
```
_The package name could not be verified automatically for this system: the first line searches for it; install only what it finds._

### Any Linux (Flatpak / Snap)
```
flatpak install --user -y flathub org.blender.Blender
```
```
sudo snap install blender --classic
```

## Troubleshooting
- 'Blender not found': it may be installed but not on PATH; the skill also looks in the usual install folders.
- Black frames in Eevee on integrated graphics: world haze is disabled for Eevee for this reason.
- Render paused (exit code 4): free RAM went under 15 %; close apps and run the same command again (it resumes).

_Generated from shared/tools.yaml by shared/make_docs.py. Package names verified on 2026-11-05 (see tools.yaml)._
