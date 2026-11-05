# Manim Community

Maths, algorithm and diagram animation (engine B).

- **Kind:** engine · **Free:** yes (MIT) · **Systems:** Windows, macOS, Linux
- **Official download:** https://docs.manim.community/en/stable/installation.html

## How animation-studio uses it
Installed into the skill's .venv by setup_check.py --engine manim --install; rendered by engines/manim/render.py.

## Check whether it is installed
```
python shared/tools.py status --kind engine
```

## Install
The skill shows the right command for the detected system (`python shared/tools.py cmd manim`) and asks before running anything.

### Windows (winget, else Chocolatey or Scoop)
```
python shared/setup_check.py --engine manim --install
```
Note: The system packages are only needed on Linux/macOS if pip has to build pycairo or ManimPango from source.

### macOS (Homebrew; Apple Silicon and Intel)
```
python shared/setup_check.py --engine manim --install
```
Note: The system packages are only needed on Linux/macOS if pip has to build pycairo or ManimPango from source.

### Ubuntu / Debian / Linux Mint / Pop!_OS
```
python shared/setup_check.py --engine manim --install
```
Note: If pip has to build from source: sudo apt update
sudo apt install -y build-essential python3-dev libcairo2-dev libpango1.0-dev

### Fedora / RHEL family
```
python shared/setup_check.py --engine manim --install
```
Note: If pip has to build from source: sudo dnf install -y cairo-devel pango-devel python3-devel

### Arch / Manjaro / EndeavourOS
```
python shared/setup_check.py --engine manim --install
```
Note: If pip has to build from source: sudo pacman -S --needed cairo pango

### openSUSE
```
python shared/setup_check.py --engine manim --install
```
Note: The system packages are only needed on Linux/macOS if pip has to build pycairo or ManimPango from source.

### Any Linux (Flatpak / Snap)
No Flatpak or Snap package.

## Troubleshooting
- pip tries to build pycairo/ManimPango: install the system libraries listed for your distro, then retry.
- LaTeX errors: maths falls back to plain text when LaTeX is missing; install LaTeX only if you want real typesetting.

_Generated from shared/tools.yaml by shared/make_docs.py. Package names verified on 2026-11-05 (see tools.yaml)._
