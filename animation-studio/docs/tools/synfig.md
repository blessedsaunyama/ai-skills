# Synfig Studio

Free 2D vector animation program.

- **Kind:** helper · **Free:** yes (GPL) · **Systems:** Windows, macOS, Linux
- **Official download:** https://www.synfig.org/download-stable/

## How animation-studio uses it
Optional. Renders the user's own Synfig (.sifz) animations to frames so they can be placed into a video; not needed by the built-in styles.

## Check whether it is installed
```
python shared/tools.py status --kind helper
```

## Install
The skill shows the right command for the detected system (`python shared/tools.py cmd synfig`) and asks before running anything.

### Windows (winget, else Chocolatey or Scoop)
```
winget install --id Synfig.SynfigStudio -e --accept-package-agreements --accept-source-agreements
```

### macOS (Homebrew; Apple Silicon and Intel)
```
brew install --cask synfigstudio
```

### Ubuntu / Debian / Linux Mint / Pop!_OS
```
sudo apt install -y flatpak
flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install --user -y flathub org.synfig.SynfigStudio
```
Note: Not in Ubuntu 24.04's repos (checked), so the Flatpak is used.

### Fedora / RHEL family
```
flatpak install --user -y flathub org.synfig.SynfigStudio
```
Note: Not in Fedora's repos (checked), so the Flatpak is used.

### Arch / Manjaro / EndeavourOS
```
sudo pacman -S --needed synfig
```

### openSUSE
```
flatpak install --user -y flathub org.synfig.SynfigStudio
```

### Any Linux (Flatpak / Snap)
```
flatpak install --user -y flathub org.synfig.SynfigStudio
```

## Troubleshooting
- Render a file from the command line: synfig file.sifz -t png -o frames/f.png

_Generated from shared/tools.yaml by shared/make_docs.py. Package names verified on 2026-11-05 (see tools.yaml)._
