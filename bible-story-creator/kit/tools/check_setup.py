#!/usr/bin/env python3
"""Setup check for the video stage. Prints a ✅/❌ table and the install commands for anything missing.
Never installs anything itself.

  python3 check_setup.py            (or: python check_setup.py / py check_setup.py on Windows)
Exit code 0 = everything present, 1 = something missing.
Standard library only, so it runs before numpy/Pillow exist.
"""
import importlib.util, json, os, platform, re, shutil, subprocess, sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
OS = {"Windows": "win", "Darwin": "mac"}.get(platform.system(), "linux")
PY = os.path.basename(sys.executable)
INSTALL = {
    "node": {"win": "winget install OpenJS.NodeJS.LTS", "mac": "brew install node", "linux": "curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt-get install -y nodejs"},
    "python3": {"win": "winget install Python.Python.3.12", "mac": "brew install python", "linux": "sudo apt-get install -y python3 python3-pip"},
    "numpy": {k: f'"{sys.executable}" -m pip install --user numpy' for k in ("win", "mac", "linux")},
    "Pillow": {k: f'"{sys.executable}" -m pip install --user pillow' for k in ("win", "mac", "linux")},
    "ffmpeg": {"win": "winget install Gyan.FFmpeg   (then open a new terminal)", "mac": "brew install ffmpeg", "linux": "sudo apt-get install -y ffmpeg"},
    "playwright": {k: "npm i -g playwright" for k in ("win", "mac", "linux")},
    "chromium": {"win": "npx playwright install chromium", "mac": "npx playwright install chromium", "linux": "npx playwright install --with-deps chromium"},
    "bash": {"win": "winget install Git.Git   (Git Bash provides bash)", "mac": "(built in)", "linux": "(built in)"},
}


def run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60, shell=isinstance(cmd, str))
        return (r.stdout + r.stderr).strip()
    except Exception:
        return ""


def ver(s):
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", s or "")
    return tuple(int(x or 0) for x in m.groups()) if m else None


rows = []
def row(name, ok, detail):
    rows.append((name, ok, detail))

nv = ver(run(["node", "-v"])) if shutil.which("node") else None
row("node", bool(nv and nv >= (22, 6, 0)), f"v{'.'.join(map(str, nv))}" + ("" if nv and nv >= (22, 6, 0) else " (need 22.6+)") if nv else "not found")
row("python3", sys.version_info >= (3, 8), f"{platform.python_version()} at {sys.executable}")
for mod, label in (("numpy", "numpy"), ("PIL", "Pillow")):
    spec = importlib.util.find_spec(mod)
    v = ""
    if spec:
        try:
            v = __import__(mod).__version__
        except Exception:
            v = "installed"
    row(label, bool(spec), v or "missing (for this python)")
ff = shutil.which("ffmpeg"); fp = shutil.which("ffprobe")
row("ffmpeg", bool(ff and fp), (run(["ffmpeg", "-version"]).splitlines() or [""])[0][:40] if ff else "not on PATH")
row("bash", bool(shutil.which("bash")), shutil.which("bash") or "not found")
groot = run("npm root -g") if shutil.which("npm") else ""
pw_dir = os.path.join(groot, "playwright") if groot else ""
pw = bool(pw_dir and os.path.isdir(pw_dir)) or os.path.isdir(os.path.join("node_modules", "playwright"))
pwv = ""
if pw:
    try:
        pwv = json.load(open(os.path.join(pw_dir, "package.json")))["version"]
    except Exception:
        pwv = "installed"
row("playwright", pw, pwv or "not installed (global or local)")
cache = {"win": os.path.join(os.environ.get("LOCALAPPDATA", ""), "ms-playwright"),
         "mac": os.path.expanduser("~/Library/Caches/ms-playwright"),
         "linux": os.path.expanduser("~/.cache/ms-playwright")}[OS]
cache = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", cache)
chrom = os.path.isdir(cache) and any(n.startswith(("chromium", "chromium_headless_shell")) for n in os.listdir(cache))
row("chromium", chrom, cache if chrom else "Playwright Chromium not downloaded")

print("| Requirement | Status | Detail |\n|---|---|---|")
for n, ok, d in rows:
    print(f"| {n} | {'✅' if ok else '❌'} | {d} |")
missing = [n for n, ok, _ in rows if not ok]
if missing:
    print(f"\nMissing on {OS}: " + ", ".join(missing) + "\nInstall commands (ask the user first):")
    for n in missing:
        print(f"  {n}:  " + INSTALL[n][OS])
    print("\nAll platforms:")
    for n in missing:
        print(f"  {n}:  Windows: {INSTALL[n]['win']} | macOS: {INSTALL[n]['mac']} | Linux: {INSTALL[n]['linux']}")
    sys.exit(1)
print(f"\nAll set. Use this python for the kit tools: {sys.executable}")
