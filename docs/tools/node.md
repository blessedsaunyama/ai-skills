# Node.js (22.6 or newer)

JavaScript runtime for the Toon 3D engine.

- **Kind:** engine · **Free:** yes (MIT) · **Systems:** Windows, macOS, Linux
- **Official download:** https://nodejs.org/en/download

## How animation-studio uses it
Runs engines/toon3d/tools/render.mjs (Playwright) and strips the TypeScript types of the toon library.

## Check whether it is installed
```
python shared/tools.py status --kind engine
```

## Install
The skill shows the right command for the detected system (`python shared/tools.py cmd node`) and asks before running anything.

### Windows (winget, else Chocolatey or Scoop)
```
winget install --id OpenJS.NodeJS.LTS -e --accept-package-agreements --accept-source-agreements
```

### macOS (Homebrew; Apple Silicon and Intel)
```
brew install node
```

### Ubuntu / Debian / Linux Mint / Pop!_OS
```
sudo snap install node --classic --channel=24
```
Note: Ubuntu 24.04's apt nodejs is 18.19 (too old), so the snap (track 24) is offered instead.

### Fedora / RHEL family
```
sudo dnf install -y nodejs nodejs-npm
```

### Arch / Manjaro / EndeavourOS
```
sudo pacman -S --needed nodejs npm
```

### openSUSE
```
zypper search nodejs22
sudo zypper install nodejs22
```
_The package name could not be verified automatically for this system: the first line searches for it; install only what it finds._

### Any Linux (Flatpak / Snap)
```
sudo snap install node --classic --channel=24
```

## Troubleshooting
- Version too old: Toon 3D needs 22.6+; check with node --version.
- Ubuntu/Debian: use the snap (or nodejs.org), not apt.

_Generated from shared/tools.yaml by shared/make_docs.py. Package names verified on 2026-11-05 (see tools.yaml)._
