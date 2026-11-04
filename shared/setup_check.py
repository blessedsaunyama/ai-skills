#!/usr/bin/env python3
"""Dependency check for one engine (or all). Prints a ✅/❌ table and install commands for Windows, macOS and Linux.

  python shared/setup_check.py --engine py2d          check (never changes anything)
  python shared/setup_check.py --engine py2d --install   create SKILL_DIR/.venv and pip-install the missing Python
                                                         packages there (ONLY after the user said yes)
Engines: py2d (A), manim (B), toon3d (C), blender (D), all. Add --tts to also check Piper.
System programs (ffmpeg, node, Blender, LaTeX) are never installed by this script: it prints the command,
the agent asks the user, then runs it. Exit code 0 = ready, 1 = something missing.
Standard library only.
"""
import argparse, os, re, subprocess, sys, venv
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import OS, SKILL_DIR, find_tool, run, utf8, venv_python  # noqa: E402

# Install commands for system programs live in shared/tools.yaml (one verified registry for the whole skill).
PY_PKGS = {  # engine -> [(import name, requirements file)]
    "py2d": [("numpy", "requirements.txt"), ("PIL", "requirements.txt")],
    "manim": [("manim", "requirements-manim.txt")],
    "toon3d": [],
    "blender": [],
}
NEEDS = {"py2d": ["ffmpeg"], "manim": ["ffmpeg"], "toon3d": ["ffmpeg", "node", "playwright", "chromium"], "blender": ["ffmpeg", "blender"]}
OPTIONAL = {"py2d": [("skia", "faster, sharper drawing backend (optional)")], "manim": [("latex", "nicer maths; Text fallback works without it")]}


def ver(s):
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", s or "")
    return tuple(int(x or 0) for x in m.groups()) if m else None


def py_has(mod):
    py = venv_python()
    r = subprocess.run([py, "-c", f"import {mod}; print(getattr({mod}, '__version__', 'ok'))"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def chromium_ok():
    cache = {"win": os.path.join(os.environ.get("LOCALAPPDATA", ""), "ms-playwright"),
             "mac": os.path.expanduser("~/Library/Caches/ms-playwright"), "linux": os.path.expanduser("~/.cache/ms-playwright")}[OS]
    cache = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", cache)
    return os.path.isdir(cache) and any(n.startswith("chromium") for n in os.listdir(cache))


def main():
    utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default="py2d"); ap.add_argument("--install", action="store_true"); ap.add_argument("--tts", action="store_true")
    a = ap.parse_args()
    engines = list(NEEDS) if a.engine == "all" else [a.engine]
    if any(e not in NEEDS for e in engines):
        sys.exit(f"unknown engine; use one of: {', '.join(NEEDS)}, all")
    rows, missing_sys, missing_py = [], [], []
    pyv = sys.version_info
    rows.append(("python", pyv >= (3, 10), f"{pyv.major}.{pyv.minor}.{pyv.micro} (need 3.10+); running engines with {venv_python()}"))
    for tool in sorted({t for e in engines for t in NEEDS[e]}):
        if tool == "playwright":
            groot = run("npm root -g").strip() if find_tool("npm") else ""
            ok = bool(groot and os.path.isdir(os.path.join(groot, "playwright"))) or os.path.isdir(os.path.join("node_modules", "playwright"))
            rows.append(("playwright (node)", ok, "found" if ok else "not installed")); 
            if not ok:
                missing_sys.append(tool)
            continue
        if tool == "chromium":
            ok = chromium_ok(); rows.append(("chromium (Playwright)", ok, "found" if ok else "not downloaded"))
        elif tool == "node":
            p = find_tool("node"); v = ver(run([p, "--version"])) if p else None
            ok = bool(v and v >= (22, 6, 0)); rows.append(("node", ok, f"v{'.'.join(map(str, v))}" if v else "not found"))
        else:
            p = find_tool(tool); rows.append((tool, bool(p), p or "not found"))
            ok = bool(p)
        if not ok:
            missing_sys.append(tool)
    for e in engines:
        for mod, req in PY_PKGS[e]:
            v = py_has(mod)
            rows.append((f"{'Pillow' if mod == 'PIL' else mod} (python)", bool(v), v or "missing"))
            if not v:
                missing_py.append(req)
        for mod, why in OPTIONAL.get(e, []):
            v = find_tool(mod) if mod == "latex" else py_has(mod)
            rows.append((f"{mod} (optional)", "opt" if not v else True, (v or "not installed") + f": {why}"))
    if a.tts:
        v = py_has("piper")
        rows.append(("piper TTS (optional)", "opt" if not v else True, v or "not installed: free local voice"))
    print("| Requirement | Status | Detail |\n|---|---|---|")
    for n, ok, d in rows:
        print(f"| {n} | {'✅' if ok is True else ('➖' if ok == 'opt' else '❌')} | {d} |")
    if pyv < (3, 10):
        print("\nPython 3.10 or newer is needed. Install from https://www.python.org or: " + {"win": "winget install Python.Python.3.12", "mac": "brew install python", "linux": "sudo apt install python3"}[OS])
    if missing_sys:                                       # one registry + planner for every install message (shared/tools.yaml)
        import tools as _tools
        from sysprofile import load_profile
        prof = load_profile()
        for t in dict.fromkeys({"chromium": "playwright"}.get(x, x) for x in missing_sys):
            print("\n" + _tools.flow(t, prof, "engine"))
    reqs = sorted(set(missing_py)) + (["requirements-tts.txt"] if a.tts and not py_has("piper") else [])
    if reqs:
        venv_dir = SKILL_DIR / ".venv"
        if a.install:
            if not venv_dir.exists():
                print(f"\ncreating {venv_dir} ...")
                venv.create(venv_dir, with_pip=True)
                reqs = ["requirements.txt"] + [r for r in reqs if r != "requirements.txt"]   # a new venv needs the core too
            py = venv_python()
            for r in reqs:
                if not (SKILL_DIR / r).exists():
                    print(f"skip {r}: not part of this version yet"); continue
                print(f"pip install -r {r} (into the skill's .venv only)")
                subprocess.run([py, "-m", "pip", "install", "--disable-pip-version-check", "-r", str(SKILL_DIR / r)], check=True)
            print("done. Re-run without --install to confirm.")
        else:
            print(f"\nPython packages missing. With the user's OK run:\n  python shared/setup_check.py --engine {a.engine} --install"
                  f"\n(creates {venv_dir.name}/ inside the skill and installs {', '.join(reqs)} there, nothing global)")
    ready = not missing_sys and (not reqs or a.install) and pyv >= (3, 10)
    print("\nREADY" if ready else "\nNOT READY: the script, shot list and references can still be made; rendering needs the items above.")
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()
