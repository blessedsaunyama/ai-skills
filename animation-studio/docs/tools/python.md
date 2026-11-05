# Python 3.10+

Runs every tool of the skill.

- **Kind:** engine · **Free:** yes (PSF) · **Systems:** Windows, macOS, Linux
- **Official download:** https://www.python.org/downloads/

## How animation-studio uses it
All shared/ tools and engine A; engines get their packages in the skill's own .venv.

## Check whether it is installed
```
python shared/tools.py status --kind engine
```

## Install
The skill shows the right command for the detected system (`python shared/tools.py cmd python`) and asks before running anything.

### Windows (winget, else Chocolatey or Scoop)
```
winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
```

### macOS (Homebrew; Apple Silicon and Intel)
```
brew install python@3.12
```

### Ubuntu / Debian / Linux Mint / Pop!_OS
```
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

### Fedora / RHEL family
```
sudo dnf install -y python3
```

### Arch / Manjaro / EndeavourOS
```
sudo pacman -S --needed python
```

### openSUSE
```
zypper search python3
sudo zypper install python3
```
_The package name could not be verified automatically for this system: the first line searches for it; install only what it finds._

### Any Linux (Flatpak / Snap)
No Flatpak or Snap package.

## Troubleshooting
- Several Pythons installed: use the one setup_check.py prints; engines use the skill's .venv.

_Generated from shared/tools.yaml by shared/make_docs.py. Package names verified on 2026-11-05 (see tools.yaml)._
