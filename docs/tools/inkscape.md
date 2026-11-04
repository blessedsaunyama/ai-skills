# Inkscape

Free vector editor (SVG).

- **Kind:** helper · **Free:** yes (GPL) · **Systems:** Windows, macOS, Linux
- **Official download:** https://inkscape.org/release/

## How animation-studio uses it
Optional. Converts or cleans the user's own SVG artwork (logos they own, drawings) to PNG layers that the 2D engine can place; exports titles as vectors.

## Check whether it is installed
```
python shared/tools.py status --kind helper
```

## Install
The skill shows the right command for the detected system (`python shared/tools.py cmd inkscape`) and asks before running anything.

### Windows (winget, else Chocolatey or Scoop)
```
winget install --id Inkscape.Inkscape -e --accept-package-agreements --accept-source-agreements
```

### macOS (Homebrew; Apple Silicon and Intel)
```
brew install --cask inkscape
```

### Ubuntu / Debian / Linux Mint / Pop!_OS
```
sudo apt update
sudo apt install -y inkscape
```

### Fedora / RHEL family
```
sudo dnf install -y inkscape
```

### Arch / Manjaro / EndeavourOS
```
sudo pacman -S --needed inkscape
```

### openSUSE
```
zypper search inkscape
sudo zypper install inkscape
```
_The package name could not be verified automatically for this system: the first line searches for it; install only what it finds._

### Any Linux (Flatpak / Snap)
```
flatpak install --user -y flathub org.inkscape.Inkscape
```
```
sudo snap install inkscape
```

## Troubleshooting
- Command line export: inkscape file.svg --export-type=png --export-filename=out.png

_Generated from shared/tools.yaml by shared/make_docs.py. Package names verified on 2026-11-05 (see tools.yaml)._
