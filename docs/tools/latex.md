# LaTeX (optional)

Typesets maths for Manim (MathTex). Without it the skill uses plain-text maths.

- **Kind:** helper · **Free:** yes · **Systems:** Windows, macOS, Linux
- **Official download:** https://www.latex-project.org/get/

## How animation-studio uses it
Found automatically by engines/manim/render.py (also when not on PATH yet).

## Check whether it is installed
```
python shared/tools.py status --kind helper
```

## Install
The skill shows the right command for the detected system (`python shared/tools.py cmd latex`) and asks before running anything.

### Windows (winget, else Chocolatey or Scoop)
```
winget install --id MiKTeX.MiKTeX -e --accept-package-agreements --accept-source-agreements
initexmf --set-config-value=[MPM]AutoInstall=1
```
Note: About 1 GB. The second line makes MiKTeX install missing packages silently; without it renders stop at a dialog.

### macOS (Homebrew; Apple Silicon and Intel)
```
brew install --cask basictex
```
Note: About 1 GB. Full alternative: brew install --cask mactex-no-gui (~5 GB).

### Ubuntu / Debian / Linux Mint / Pop!_OS
```
sudo apt update
sudo apt install -y texlive-latex-extra texlive-fonts-extra
```
Note: About 1 GB.

### Fedora / RHEL family
```
sudo dnf install -y texlive-scheme-medium
```
Note: About 1 GB.

### Arch / Manjaro / EndeavourOS
```
sudo pacman -S --needed texlive-latexextra
```
Note: About 1 GB.

### openSUSE
```
zypper search texlive-latex
sudo zypper install texlive-latex
```
_The package name could not be verified automatically for this system: the first line searches for it; install only what it finds._
Note: About 1 GB.

### Any Linux (Flatpak / Snap)
No Flatpak or Snap package.

## Troubleshooting
- Windows: a MiKTeX dialog asking to install a package stops renders; run initexmf --set-config-value=[MPM]AutoInstall=1 once.
- First maths render is slow (packages download); later renders are fast.

_Generated from shared/tools.yaml by shared/make_docs.py. Package names verified on 2026-11-05 (see tools.yaml)._
