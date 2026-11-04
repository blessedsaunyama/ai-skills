# Rhubarb Lip Sync

Turns a voice recording into mouth shapes over time (free, MIT).

- **Kind:** helper · **Free:** yes (MIT) · **Systems:** Windows, macOS, Linux
- **Official download:** https://github.com/DanielSWolf/rhubarb-lip-sync/releases

## How animation-studio uses it
Optional. Makes talking characters' mouths follow the voice (mouth-shape timeline in work/mouths.json).

## Check whether it is installed
```
python shared/tools.py status --kind helper
```

## Install
The skill shows the right command for the detected system (`python shared/tools.py cmd rhubarb`) and asks before running anything.

### Windows (winget, else Chocolatey or Scoop)
```
python shared/tools.py install rhubarb --yes   (downloads the official release zip)
```
Note: Not on winget, Chocolatey, Scoop or Homebrew (checked). Official release zips only.

### macOS (Homebrew; Apple Silicon and Intel)
```
python shared/tools.py install rhubarb --yes   (downloads the official release zip)
```
Note: Not on winget, Chocolatey, Scoop or Homebrew (checked). Official release zips only.

### Ubuntu / Debian / Linux Mint / Pop!_OS
```
python shared/tools.py install rhubarb --yes   (downloads the official release zip)
```
Note: Not on winget, Chocolatey, Scoop or Homebrew (checked). Official release zips only.

### Fedora / RHEL family
```
python shared/tools.py install rhubarb --yes   (downloads the official release zip)
```
Note: Not on winget, Chocolatey, Scoop or Homebrew (checked). Official release zips only.

### Arch / Manjaro / EndeavourOS
```
python shared/tools.py install rhubarb --yes   (downloads the official release zip)
```
Note: Not on winget, Chocolatey, Scoop or Homebrew (checked). Official release zips only.

### openSUSE
```
python shared/tools.py install rhubarb --yes   (downloads the official release zip)
```
Note: Not on winget, Chocolatey, Scoop or Homebrew (checked). Official release zips only.

### Any Linux (Flatpak / Snap)
No Flatpak or Snap package.

## Troubleshooting
- Not found after install: it lives in the animation-studio user folder (tools/); run tools.py status to see it.

_Generated from shared/tools.yaml by shared/make_docs.py. Package names verified on 2026-11-05 (see tools.yaml)._
