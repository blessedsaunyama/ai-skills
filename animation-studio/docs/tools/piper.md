# Piper TTS

Free, offline text-to-speech for narration.

- **Kind:** helper · **Free:** yes (GPL-3.0) · **Systems:** Windows, macOS, Linux
- **Official download:** https://github.com/OHF-Voice/piper1-gpl

## How animation-studio uses it
shared/voice.py; installed into the skill's .venv; voices in the user cache folder (licence-checked list only).

## Check whether it is installed
```
python shared/tools.py status --kind helper
```

## Install
The skill shows the right command for the detected system (`python shared/tools.py cmd piper`) and asks before running anything.

### Windows (winget, else Chocolatey or Scoop)
```
python shared/setup_check.py --engine py2d --tts --install
```

### macOS (Homebrew; Apple Silicon and Intel)
```
python shared/setup_check.py --engine py2d --tts --install
```

### Ubuntu / Debian / Linux Mint / Pop!_OS
```
python shared/setup_check.py --engine py2d --tts --install
```

### Fedora / RHEL family
```
python shared/setup_check.py --engine py2d --tts --install
```

### Arch / Manjaro / EndeavourOS
```
python shared/setup_check.py --engine py2d --tts --install
```

### openSUSE
```
python shared/setup_check.py --engine py2d --tts --install
```

### Any Linux (Flatpak / Snap)
No Flatpak or Snap package.

## Troubleshooting
- 'Voice not downloaded': run shared/voice.py with --download (about 60 MB) after asking the user.
- Only licence-checked voices are allowed by default (published videos need a voice whose data allows it).

_Generated from shared/tools.yaml by shared/make_docs.py. Package names verified on 2026-11-05 (see tools.yaml)._
