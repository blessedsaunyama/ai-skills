# DaVinci Resolve

Professional editor by Blackmagic Design; the free edition is enough (Windows, macOS, Linux with official installer).

- **Kind:** editor · **Free:** free edition (Studio is paid) · **Systems:** Windows, macOS, Linux
- **Official download:** https://www.blackmagicdesign.com/products/davinciresolve

## How animation-studio uses it
Writes an FCPXML 1.9 timeline (File > Import > Timeline) plus the media; Resolve relinks the clips. Validated by parsing; Resolve has no command line to test-render.

Project file: `.fcpxml` (import it in the editor)

## Check whether it is installed
```
python shared/tools.py status --kind editor
```

## Install
The skill shows the right command for the detected system (`python shared/tools.py cmd davinci-resolve`) and asks before running anything.

### Windows (winget, else Chocolatey or Scoop)
Download the free "DaVinci Resolve" (not Studio) from the official page and run the installer. Registration is optional (click "Download only").
Note: Not on winget, Chocolatey, Scoop, Homebrew or Flathub (checked). Needs a capable GPU.

### macOS (Homebrew; Apple Silicon and Intel)
Download the free "DaVinci Resolve" (not Studio) from the official page and run the installer. Registration is optional (click "Download only").
Note: Not on winget, Chocolatey, Scoop, Homebrew or Flathub (checked). Needs a capable GPU.

### Ubuntu / Debian / Linux Mint / Pop!_OS
Download the free "DaVinci Resolve" (not Studio) from the official page and run the installer. Registration is optional (click "Download only").
Note: Not on winget, Chocolatey, Scoop, Homebrew or Flathub (checked). Needs a capable GPU. Official Linux support is for Rocky Linux; other distros work only with community scripts (not offered by this skill).

### Fedora / RHEL family
Download the free "DaVinci Resolve" (not Studio) from the official page and run the installer. Registration is optional (click "Download only").
Note: Not on winget, Chocolatey, Scoop, Homebrew or Flathub (checked). Needs a capable GPU. Official Linux support is for Rocky Linux; other distros work only with community scripts (not offered by this skill).

### Arch / Manjaro / EndeavourOS
Download the free "DaVinci Resolve" (not Studio) from the official page and run the installer. Registration is optional (click "Download only").
Note: Not on winget, Chocolatey, Scoop, Homebrew or Flathub (checked). Needs a capable GPU. Official Linux support is for Rocky Linux; other distros work only with community scripts (not offered by this skill).

### openSUSE
Download the free "DaVinci Resolve" (not Studio) from the official page and run the installer. Registration is optional (click "Download only").
Note: Not on winget, Chocolatey, Scoop, Homebrew or Flathub (checked). Needs a capable GPU. Official Linux support is for Rocky Linux; other distros work only with community scripts (not offered by this skill).

### Any Linux (Flatpak / Snap)
No Flatpak or Snap package.

## Troubleshooting
- Import with File > Import > Timeline (FCPXML), then relink media if asked (point it at the media/ folder).
- Captions: File > Import > Subtitle, then drag the subtitle onto the timeline.

_Generated from shared/tools.yaml by shared/make_docs.py. Package names verified on 2026-11-05 (see tools.yaml)._
