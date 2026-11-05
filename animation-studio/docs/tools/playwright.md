# Playwright + Chromium

Headless browser that renders the Toon 3D (three.js) frames.

- **Kind:** engine · **Free:** yes (Apache-2.0) · **Systems:** Windows, macOS, Linux
- **Official download:** https://playwright.dev/docs/intro

## How animation-studio uses it
engines/toon3d/tools/render.mjs drives Chromium with CPU WebGL.

## Check whether it is installed
```
python shared/tools.py status --kind engine
```

## Install
The skill shows the right command for the detected system (`python shared/tools.py cmd playwright`) and asks before running anything.

### Windows (winget, else Chocolatey or Scoop)
```
npm install -g playwright
npx playwright install chromium
```

### macOS (Homebrew; Apple Silicon and Intel)
```
npm install -g playwright
npx playwright install chromium
```

### Ubuntu / Debian / Linux Mint / Pop!_OS
```
npm install -g playwright
npx playwright install --with-deps chromium
```

### Fedora / RHEL family
```
npm install -g playwright
npx playwright install --with-deps chromium
```

### Arch / Manjaro / EndeavourOS
```
npm install -g playwright
npx playwright install --with-deps chromium
```

### openSUSE
```
npm install -g playwright
npx playwright install --with-deps chromium
```

### Any Linux (Flatpak / Snap)
No Flatpak or Snap package.

## Troubleshooting
- 'Executable doesn't exist': run npx playwright install chromium.
- Linux missing libraries: npx playwright install --with-deps chromium (needs sudo).

_Generated from shared/tools.yaml by shared/make_docs.py. Package names verified on 2026-11-05 (see tools.yaml)._
