#!/usr/bin/env python3
"""Software status and installs, matched to THIS computer's OS, distro, package manager and shell (from shared/tools.yaml).

  python shared/tools.py status [--kind editor|engine|helper|all] [--simulate NAME]   ✅ installed (version) | ❌ not installed | ⚠️ not on this OS
  python shared/tools.py cmd TOOL [--simulate NAME]          the install command(s) for this computer
  python shared/tools.py flow TOOL [--for editor|engine] [--simulate NAME]
                                                             the exact message + choices to show when TOOL is missing
  python shared/tools.py install TOOL --yes                  run the install (ONLY after the user chose "Install now"), then re-check
NAME (testing only): macos-arm, macos-intel, ubuntu, ubuntu-server, fedora, arch, opensuse, wsl-ubuntu.
Never installs without --yes. Steps that need admin rights are announced first; Linux sudo steps are handed to the user
(they need the user's password), e.g. type:  ! sudo apt install -y shotcut
Standard library only.
"""
import glob, json, os, re, shutil, subprocess, sys, urllib.request, zipfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import OS, SKILL_DIR, find_tool, run, utf8, venv_python  # noqa: E402
from registry import load  # noqa: E402
from sysprofile import load_profile, user_dir  # noqa: E402

REG = load()["tools"]
GUI_NAMES = {"kdenlive": "Kdenlive", "shotcut": "Shotcut", "openshot": "OpenShot", "davinci-resolve": "DaVinci Resolve",
             "capcut": "CapCut", "blender": "Blender", "inkscape": "Inkscape", "synfig": "Synfig", "latex": "MiKTeX"}
_WINVER = None


def expand(p):
    env = {"%ProgramFiles%": os.environ.get("ProgramFiles", "C:/Program Files"), "%LOCALAPPDATA%": os.environ.get("LOCALAPPDATA", ""),
           "{userdir}": str(user_dir())}
    for k, v in env.items():
        p = p.replace(k, v)
    return os.path.expanduser(p)


def win_versions():
    """DisplayName -> DisplayVersion from the Windows uninstall registry (one PowerShell call, cached)."""
    global _WINVER
    if _WINVER is None:
        ps = ("$k='HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*','HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',"
              "'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*'; Get-ItemProperty $k -ErrorAction SilentlyContinue | "
              "Where-Object DisplayName | ForEach-Object { $_.DisplayName + '|' + $_.DisplayVersion }")
        _WINVER = dict(l.split("|", 1) for l in run(["powershell", "-NoProfile", "-Command", ps], timeout=60).splitlines() if "|" in l)
    return _WINVER


def version_of(key, t, exe):
    det = t.get("detect", {})
    if OS == "win" and key in GUI_NAMES:
        for name, v in win_versions().items():
            if GUI_NAMES[key].lower() in name.lower() and v:
                return v
    if det.get("version_arg") and exe and not t.get("gui"):
        m = re.search(r"(\d+\.\d+(?:\.\d+)?)", run([exe, det["version_arg"]], timeout=60))
        return m.group(1) if m else ""
    return ""


def detect(key, prof):
    """('ok', version/where) | ('missing', '') | ('unsupported', reason) | ('unknown', reason for simulations)."""
    t = REG[key]
    if t.get("detect", {}).get("same_as"):
        st, d = detect(t["detect"]["same_as"], prof)
        return st, d
    if prof["os"] not in t.get("os", []):
        return "unsupported", f"not available on {prof['os_name']}"
    if t.get("gui") and not prof.get("display", True):
        return "unsupported", "needs a desktop; this computer has no display (render-only)"
    if t.get("install", {}).get("manual") and prof["os"] == "linux" and key == "davinci-resolve" and prof.get("family") not in ("fedora",):
        note = "official installer supports Rocky Linux; other distros need community scripts"
    else:
        note = ""
    if prof.get("simulated"):
        return "unknown", "simulated computer: not checked" + (f" ({note})" if note else "")
    det = t.get("detect", {})
    exe = None
    for c in det.get("commands", []):
        exe = exe or find_tool(c)
    for p in det.get(OS, []):
        hits = sorted(glob.glob(expand(p)), reverse=True)
        exe = exe or (hits[0] if hits else None)
    if not exe and det.get("flatpak") and shutil.which("flatpak"):
        if subprocess.run(["flatpak", "info", det["flatpak"]], capture_output=True).returncode == 0:
            return "ok", f"flatpak {det['flatpak']}"
    if not exe and det.get("snap") and os.path.exists(f"/snap/bin/{det['snap']}"):
        exe = f"/snap/bin/{det['snap']}"
    if det.get("pip"):
        v = run([venv_python(), "-c", f"import importlib.metadata as m; print(m.version('{det['pip'] if det['pip'] != 'piper' else 'piper-tts'}'))"]).strip()
        return ("ok", v.splitlines()[-1]) if v and "Error" not in v else ("missing", "")
    if det.get("npm_global"):
        groot = run("npm root -g").strip() if find_tool("npm") else ""
        p = Path(groot) / det["npm_global"] / "package.json" if groot else None
        if p and p.exists():
            return "ok", json.loads(p.read_text(encoding="utf-8")).get("version", "")
        return "missing", ""
    if not exe:
        return "missing", ""
    v = version_of(key, t, exe)
    mv = t.get("min_version")
    if mv and v and tuple(int(x) for x in v.split(".")[:2]) < tuple(int(x) for x in str(mv).split(".")[:2]):
        return "missing", f"{v} found, need {mv}+"
    return "ok", v or "installed"


# ------------------------------------------------------------------ install plans
def _cmd_for(manager, name, t):
    if manager == "winget":
        return f"winget install --id {name} -e --accept-package-agreements --accept-source-agreements", False
    if manager == "choco":
        return f"choco install {name} -y", True
    if manager == "scoop":
        bucket, _, pkg = name.partition("/")
        return (f"scoop bucket add {bucket}\nscoop install {name}" if bucket != "main" else f"scoop install {pkg}"), False
    if manager == "brew":
        return f"brew install {name}", False
    if manager == "apt":
        return f"sudo apt update\nsudo apt install -y {name}", True
    if manager == "dnf":
        return f"sudo dnf install -y {name}", True
    if manager == "pacman":
        return f"sudo pacman -S --needed {name}", True
    if manager == "zypper":
        return f"zypper search {name.split()[0]}\nsudo zypper install {name}", True
    if manager == "flatpak":
        return f"flatpak install --user -y flathub {name}", False
    if manager == "snap":
        return f"sudo snap install {name}", True
    return "", False


def plan(key, prof):
    """Ordered install steps for this computer: {'manager', 'steps': [(command, needs_admin)], 'note', 'link', 'manual'}."""
    t = REG[key]
    inst = t.get("install", {})
    if inst.get("same_as"):
        return plan(inst["same_as"], prof)
    notes = [t.get("notes"), t.get(f"notes_{prof['os']}"), t.get(f"notes_{prof.get('family')}") if prof.get("family") else None]
    out = {"manager": None, "steps": [], "note": " ".join(n for n in notes if n), "link": t.get("download", ""), "manual": inst.get("manual")}
    if inst.get("pip"):
        eng = {"manim": "manim", "piper": "py2d --tts"}.get(key, "py2d")
        out.update(manager="pip (skill .venv)", steps=[(f"python shared/setup_check.py --engine {eng} --install", False)])
        if prof["os"] == "linux" and inst.get(f"{prof.get('native_manager')}_deps"):
            out["note"] = f"If pip has to build from source: {_cmd_for(prof['native_manager'], inst[prof['native_manager'] + '_deps'], t)[0]}"
        return out
    if inst.get("npm"):
        after = inst.get("after_linux") if prof["os"] == "linux" else inst.get("after")
        out.update(manager="npm", steps=[(f"npm install {inst['npm']}", prof["os"] == "linux" and not prof.get("wsl") and False), (after, prof["os"] == "linux")])
        return out
    if inst.get("github"):
        out.update(manager="github", steps=[("python shared/tools.py install rhubarb --yes   (downloads the official release zip)", False)])
        return out
    mgrs = prof.get("managers", [])
    if prof["os"] == "win":
        order = ["winget", "choco", "scoop"]
    elif prof["os"] == "mac":
        order = ["brew"]
        if "brew" not in mgrs and "brew" in inst:
            out["steps"].append(('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"   (installs Homebrew first: https://brew.sh)', False))
            mgrs = mgrs + ["brew"]
    else:
        fam, native = prof.get("family"), prof.get("native_manager")
        prefer_flatpak = (key == "synfig" and fam in ("debian", "fedora")) or (key == "openshot" and fam == "arch") or \
                         (key == "blender" and fam == "debian")
        if key == "node" and fam == "debian":
            order = ["snap"]                              # Ubuntu/Debian apt nodejs is too old (18.x)
        elif prefer_flatpak:
            order = ["flatpak", "snap", native]
        else:
            order = [native, "flatpak", "snap"]
        if "flatpak" in order and "flatpak" in inst and "flatpak" not in mgrs and order[0] == "flatpak":
            setup = {"apt": "sudo apt install -y flatpak", "dnf": "sudo dnf install -y flatpak", "pacman": "sudo pacman -S --needed flatpak",
                     "zypper": "sudo zypper install flatpak"}.get(native)
            if setup:
                out["steps"] += [(setup, True), ("flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo", False)]
                mgrs = mgrs + ["flatpak"]
        if order[0] == "snap" and "snap" not in mgrs and native == "apt":
            out["steps"].append(("sudo apt install -y snapd", True)); mgrs = mgrs + ["snap"]
    for m in order:
        if m and m in inst and (m in mgrs or (prof["os"] == "win" and m == "winget")):
            name = inst[m]
            if m == "brew" and not name.startswith("--cask") and t.get("gui"):
                name = "--cask " + name
            cmd, admin = _cmd_for(m, name, t)
            for i, line in enumerate(cmd.split("\n")):
                out["steps"].append((line, admin and line.startswith(("sudo", "choco"))))
            out["manager"] = m + (" (name not verifiable: search first)" if m in t.get("unverified", []) else "")
            after = t.get(f"after_{prof['os']}")
            if after:
                out["steps"].append((after, False))
            break
    else:
        if not out["manual"]:
            out["manual"] = f"No package for this system: download it from the official page: {t.get('download')}"
    return out


def describe(key, prof):
    t = REG[key]
    if prof["os"] not in t.get("os", []):
        return f"⚠️ {t['name']} is not available on {prof['os_name']}." + (" Use the editor pack instead." if t.get("kind") == "editor" else "")
    p = plan(key, prof)
    lines = []
    if p["steps"]:
        where = f"{prof['os_name']}" + (f", {p['manager']}" if p["manager"] else "")
        lines.append(f"Install it on this computer ({where}):")
        for c, admin in p["steps"]:
            lines.append(f"  {c}")
        if any(a for _, a in p["steps"]):
            lines.append("  (lines starting with sudo need administrator rights: you'll be asked for your password)" if prof["os"] != "win"
                         else "  (choco needs an Administrator terminal: right-click PowerShell > Run as administrator)")
        elif prof["os"] == "win" and p["manager"] == "winget":
            lines.append("  (Windows may show a permission prompt once: click Yes.)")
    if p["manual"]:
        lines.append(p["manual"])
    if p["link"]:
        lines.append(f"Official download page (if the command doesn't work): {p['link']}")
    if p["note"]:
        lines.append(f"Note: {p['note']}")
    if prof.get("wsl") and REG[key].get("gui"):
        lines.append("You're in WSL: the Linux app opens through WSLg; you can also install the Windows version with winget from Windows.")
    return "\n".join(lines)


def status_rows(kind, prof):
    rows = []
    for key, t in REG.items():
        if kind != "all" and t.get("kind") != kind:
            continue
        st, d = detect(key, prof)
        icon = {"ok": "✅", "missing": "❌", "unsupported": "⚠️", "unknown": "❔"}[st]
        rows.append((key, t["name"], icon, d, t.get("project", ""), t.get("opens_automatically")))
    return rows


def flow(key, prof, role):
    t = REG[key]
    st, d = detect(key, prof)
    if st == "ok":
        return f"✅ {t['name']} is installed ({d}). Continuing."
    if st == "unsupported":
        alt = "Pick a different editor, or get the MP4 + editor pack." if role == "editor" else "Choose another style, or skip this engine."
        return f"⚠️ {t['name']} is not supported here: {d}.\n{alt}"
    msg = [f"{t['name']} is not installed{(' (' + d + ')') if d else ''}.", f"{t['name']}: {t['purpose']}", describe(key, prof), "", "What would you like to do?"]
    if role == "editor":
        msg += ["  1. Install now (I'll run the command above)", "  2. I'll install it myself, then say \"done\"", "  3. Pick a different editor",
                "  4. Skip: give me the MP4 + editor pack"]
    else:
        msg += ["  1. Install now (I'll run the command above)", "  2. I'll install it myself, then say \"done\"", "  3. Choose another style",
                "  4. Skip: give me the script, shot list and references only"]
    return "\n".join(msg)


def install(key, prof):
    p = plan(key, prof)
    if key == "rhubarb":
        return install_rhubarb()
    if p["manual"] and not p["steps"]:
        print(p["manual"]); return 2
    for cmd, admin in p["steps"]:
        if admin and prof["os"] != "win":
            print(f"This step needs your password, so please run it yourself (in Claude Code type: ! {cmd})\nThen say \"done\".")
            return 5
        cmd = cmd.split("   (")[0]
        if cmd.startswith("python shared/"):
            cmd = cmd.replace("python shared/", f'"{sys.executable}" "{SKILL_DIR / "shared"}/', 1).replace(".py ", '.py" ', 1)
        print(f"$ {cmd}", flush=True)
        r = subprocess.run(cmd, shell=True)
        if r.returncode not in (0,):
            print(f"Step failed (exit {r.returncode}). Try the official page: {p['link']}"); return r.returncode or 1
    st, d = detect(key, load_profile())
    print(f"{'✅' if st == 'ok' else '❌'} {REG[key]['name']}: {d or st}" + ("" if st == "ok" else "  (open a NEW terminal if it was just installed; PATH updates need one)"))
    return 0 if st == "ok" else 3


def install_rhubarb():
    tag = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.github.com/repos/DanielSWolf/rhubarb-lip-sync/releases/latest",
                                                                   headers={"User-Agent": "animation-studio"}), timeout=30).read())
    want = {"win": "Windows", "mac": "macOS", "linux": "Linux"}[OS]
    asset = next(a for a in tag["assets"] if want in a["name"] and a["name"].endswith(".zip"))
    dst = user_dir() / "tools"; dst.mkdir(parents=True, exist_ok=True)
    z = dst / asset["name"]
    print(f"downloading {asset['name']} ({asset['size'] / 1e6:.1f} MB) from the official GitHub release {tag['tag_name']}")
    urllib.request.urlretrieve(asset["browser_download_url"], z)
    with zipfile.ZipFile(z) as f:
        f.extractall(dst)
    z.unlink()
    exe = next(iter(dst.rglob("rhubarb.exe" if OS == "win" else "rhubarb")), None)
    if exe and OS != "win":
        exe.chmod(0o755)
    (dst / "rhubarb").mkdir(exist_ok=True)
    print(f"✅ Rhubarb Lip Sync: {exe}")
    return 0


def main():
    utf8()
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); return
    sim = a[a.index("--simulate") + 1] if "--simulate" in a else None
    prof = load_profile(sim)
    if sim:
        print(f"(SIMULATED computer: {prof['os_name']}, package managers: {', '.join(prof['managers'])}, shell: {prof['shell']})\n")
    if a[0] == "status":
        kind = a[a.index("--kind") + 1] if "--kind" in a else "all"
        print("| # | Tool | Status | Version / note | Project file |\n|---|---|---|---|---|")
        for i, (key, name, icon, d, proj, auto) in enumerate(status_rows(kind, prof), 1):
            pf = "" if not proj else (f"{proj}" + (" (opens automatically)" if auto else (" (import)" if proj != "none" else " editor pack only")))
            print(f"| {i} | {name} (`{key}`) | {icon} | {d} | {pf} |")
    elif a[0] == "cmd":
        print(describe(a[1], prof))
    elif a[0] == "flow":
        role = a[a.index("--for") + 1] if "--for" in a else ("editor" if REG[a[1]].get("kind") == "editor" else "engine")
        print(flow(a[1], prof, role))
    elif a[0] == "install":
        if "--yes" not in a:
            sys.exit("Refusing to install without --yes (the user must choose 'Install now' first).")
        if sim:
            sys.exit("Can't install on a simulated computer.")
        sys.exit(install(a[1], prof))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
