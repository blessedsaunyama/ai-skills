#!/usr/bin/env python3
"""Hardware check: what this computer can render safely. Run it before any render.

  python shared/hwcheck.py            table + tier + limits
  python shared/hwcheck.py --json     machine-readable (other tools import detect() / limits())
  python shared/hwcheck.py --simulate macos-arm|macos-intel|ubuntu|ubuntu-server|fedora|arch|opensuse|wsl-ubuntu
                                      show the system part as it would look on that computer (for testing install commands)
Also detects the OS details (Windows build, WSL, macOS + Apple Silicon, Linux distro from /etc/os-release), the package
managers (winget/choco/scoop, brew, apt/dnf/pacman/zypper/flatpak/snap), the shell and whether there is a display, and
SAVES everything to the system profile (sysprofile.profile_path()) that every other step reads.

Detects OS, CPU model and cores, total/free RAM, free disk (current folder), GPU name + VRAM,
battery state, and the tools Blender, ffmpeg, node, python, LaTeX. Assigns a tier:
  LITE      < 12 GB RAM or fewer than 4 CPU threads      -> engines A, B; 720p only; toon3d/Blender blocked (stills)
  STANDARD  everything between                           -> A, B full; toon3d <= 5 s preview; Blender Eevee <= 5 s 720p
  POWER     >= 32 GB RAM and a dedicated GPU >= 6 GB VRAM -> everything, Cycles on the GPU
Standard library only. Never installs or changes anything.
"""
import json, os, platform, re, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import OS, find_tool, gb, memory, on_battery, run, utf8  # noqa: E402
from sysprofile import SIMULATIONS, detect_system, profile_path  # noqa: E402

GB = 1024 ** 3


def cpu_model():
    if OS == "win":
        out = run(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"]).strip()
        return out.splitlines()[0].strip() if out else platform.processor()
    if OS == "mac":
        return run(["sysctl", "-n", "machdep.cpu.brand_string"]).strip() or platform.processor()
    m = re.search(r"model name\s*:\s*(.+)", open("/proc/cpuinfo").read()) if os.path.exists("/proc/cpuinfo") else None
    return m.group(1).strip() if m else platform.processor()


def physical_cores():
    try:
        if OS == "win":
            out = run(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor | Measure-Object NumberOfCores -Sum).Sum"])
            return int(out.strip())
        if OS == "mac":
            return int(run(["sysctl", "-n", "hw.physicalcpu"]).strip())
        ids = set(re.findall(r"physical id\s*:\s*(\d+)[\s\S]*?core id\s*:\s*(\d+)", open("/proc/cpuinfo").read()))
        return len(ids) or None
    except Exception:
        return None


def gpus():
    """List of {name, vram_gb (None if unknown), dedicated}."""
    out = []
    smi = find_tool("nvidia-smi")
    if smi:
        for line in run([smi, "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"]).splitlines():
            if "," in line:
                n, m = line.rsplit(",", 1)
                try:
                    out.append({"name": n.strip(), "vram_gb": round(float(m) / 1024, 1), "dedicated": True})
                except ValueError:
                    pass
    if OS == "win":
        ps = ("$r=@{}; Get-ItemProperty 'HKLM:\\SYSTEM\\ControlSet001\\Control\\Class\\{4d36e968-e325-11ce-bfc1-08002be10318}\\0*' "
              "-ErrorAction SilentlyContinue | ForEach-Object { if ($_.DriverDesc) { $r[$_.DriverDesc]=$_.'HardwareInformation.qwMemorySize' } }; "
              "Get-CimInstance Win32_VideoController | ForEach-Object { $_.Name + '|' + $_.AdapterRAM + '|' + $r[$_.Name] }")
        for line in run(["powershell", "-NoProfile", "-Command", ps]).splitlines():
            parts = line.strip().split("|")
            if len(parts) < 2 or not parts[0] or any(g["name"] == parts[0] for g in out):
                continue
            q = parts[2] if len(parts) > 2 and parts[2].isdigit() else ""
            ram = int(q) if q else (int(parts[1]) if parts[1].isdigit() else 0)   # AdapterRAM caps at 4 GB; registry value is exact
            out.append({"name": parts[0], "vram_gb": round(ram / GB, 1) if ram else None, "dedicated": None})
    elif OS == "mac":
        sp = run(["system_profiler", "SPDisplaysDataType"], timeout=30)
        for block in re.split(r"\n\s{4}(?=\S)", sp):
            n = re.search(r"Chipset Model:\s*(.+)", block)
            if n:
                v = re.search(r"VRAM[^:]*:\s*(\d+)\s*(GB|MB)", block)
                vr = (int(v.group(1)) / (1024 if v.group(2) == "MB" else 1)) if v else None
                out.append({"name": n.group(1).strip(), "vram_gb": vr, "dedicated": None})
    else:
        for line in run(["lspci"]).splitlines():
            if re.search(r"VGA|3D controller|Display controller", line) and not any(g["name"] in line for g in out):
                out.append({"name": line.split(":", 2)[-1].strip(), "vram_gb": None, "dedicated": None})
    for g in out:
        if g["dedicated"] is None:
            n = g["name"].lower()
            integrated = (("intel" in n and "arc" not in n) or re.search(r"radeon\(tm\) graphics|radeon graphics|vega \d+ graphics", n)
                          or "microsoft basic" in n or "llvmpipe" in n)
            apple = "apple m" in n
            g["dedicated"] = bool(not integrated and not apple and (g["vram_gb"] or 0) >= 2) or ("nvidia" in n and not integrated)
            if apple:
                g["unified"] = True
    return out


def tool_version(name, args=("--version",), pat=r"(\d+\.\d+(?:\.\d+)?)"):
    p = find_tool(name)
    if not p:
        return None, None
    m = re.search(pat, run([p, *args], timeout=60))
    return p, (m.group(1) if m else "found")


def tools():
    t = {}
    for name, args in (("ffmpeg", ("-version",)), ("ffprobe", ("-version",)), ("node", ("--version",)),
                       ("blender", ("--version",)), ("latex", ("--version",)), ("piper", ("--help",))):
        p, v = tool_version(name, args)
        t[name] = {"path": p, "version": v}
    t["python"] = {"path": sys.executable, "version": platform.python_version()}
    return t


def detect():
    total, avail = memory()
    du = shutil.disk_usage(os.getcwd())
    threads = os.cpu_count() or 1
    return {"os": f"{platform.system()} {platform.release()}", "os_key": OS, "cpu": cpu_model(), "threads": threads,
            "cores": physical_cores(), "ram_total": total, "ram_free": avail, "disk_free": du.free, "disk_path": os.getcwd(),
            "gpus": gpus(), "on_battery": on_battery(), "tools": tools()}


def tier_of(hw):
    ram = hw["ram_total"] / GB
    ded = [g for g in hw["gpus"] if g.get("dedicated") and (g.get("vram_gb") or 0) >= 6]
    apple_big = any(g.get("unified") for g in hw["gpus"]) and ram >= 31
    if ram < 11.5 or hw["threads"] < 4:
        return "LITE"
    if ram >= 31 and (ded or apple_big):          # 32 GB machines report ~31.x GB usable
        return "POWER"
    return "STANDARD"


def limits(tier, threads):
    if tier == "LITE":
        return {"engines": ["py2d", "manim"], "max_height": 720, "workers": max(1, threads // 2), "ask_over_min": 10,
                "toon3d": "blocked (stills only)", "blender": "blocked (stills only)", "toon3d_max_s": 0, "blender_max_s": 0}
    if tier == "STANDARD":
        return {"engines": ["py2d", "manim", "toon3d", "blender"], "max_height": 1080, "workers": max(1, threads - 2),
                "ask_over_min": 10, "toon3d": "<= 5 s preview; longer only with confirmation + resume",
                "blender": "Eevee only, <= 5 s at 720p, low samples", "toon3d_max_s": 5, "blender_max_s": 5,
                "blender_max_height": 720, "blender_engine": "EEVEE", "blender_samples": 16}
    return {"engines": ["py2d", "manim", "toon3d", "blender"], "max_height": 2160, "workers": max(1, threads - 1),
            "ask_over_min": 30, "toon3d": "full", "blender": "Eevee or Cycles on the GPU", "toon3d_max_s": None,
            "blender_max_s": None, "blender_max_height": 2160, "blender_engine": "CYCLES", "blender_samples": 128}


def print_system(p):
    print("| System | Value |\n|---|---|")
    extra = ""
    if p["os"] == "mac":
        extra = " (Apple Silicon)" if p.get("apple_silicon") else " (Intel)"
    if p["os"] == "linux":
        extra = f" (family: {p.get('family')}, native: {p.get('native_manager') or 'unknown'})" + (" in WSL" if p.get("wsl") else "")
    print(f"| OS | {p['os_name']}{extra} |")
    print(f"| Architecture | {p['arch']} |")
    print(f"| Package managers | {', '.join(p['managers']) or 'none found'} |")
    print(f"| Shell | {p['shell']} (commands are shown in this shell's syntax) |")
    print(f"| Display | {'yes' if p['display'] else 'NO (headless: render-only, no editor apps)'} |")
    print(f"| Admin rights via | {p['admin_tool']} |")


def report():
    hw = detect()
    tier = tier_of(hw)
    lim = limits(tier, hw["threads"])
    return hw, tier, lim


def main():
    utf8()
    if "--simulate" in sys.argv:
        name = sys.argv[sys.argv.index("--simulate") + 1]
        print(f"SIMULATED profile '{name}' (not this computer):")
        print_system(dict(SIMULATIONS[name], simulated=name)); return
    hw, tier, lim = report()
    system = detect_system()
    pp = profile_path(); pp.parent.mkdir(parents=True, exist_ok=True)
    pp.write_text(json.dumps({"system": system, "hw": hw, "tier": tier, "limits": lim}, indent=1), encoding="utf-8")
    if "--json" in sys.argv:
        print(json.dumps({"system": system, "hw": hw, "tier": tier, "limits": lim}, indent=1)); return
    print_system(system)
    print(f"(saved to {pp})\n")
    ok = lambda b: "✅" if b else "❌"
    print("| Item | Value |\n|---|---|")
    print(f"| OS | {hw['os']} |")
    print(f"| CPU | {hw['cpu']} ({hw['cores'] or '?'} cores / {hw['threads']} threads) |")
    print(f"| RAM | {gb(hw['ram_total'])} total, {gb(hw['ram_free'])} free ({100 * hw['ram_free'] / max(1, hw['ram_total']):.0f} %) |")
    print(f"| Free disk | {gb(hw['disk_free'])} (in {hw['disk_path']}) |")
    for g in hw["gpus"] or [{"name": "not detected", "vram_gb": None, "dedicated": False}]:
        kind = "dedicated" if g.get("dedicated") else ("unified (Apple)" if g.get("unified") else "integrated")
        print(f"| GPU | {g['name']} — {kind}, VRAM {str(g['vram_gb']) + ' GB' if g.get('vram_gb') else 'unknown'} |")
    b = hw["on_battery"]
    print(f"| Power | {'⚠️ ON BATTERY: plug in before long renders' if b else ('mains power' if b is False else 'desktop / unknown')} |")
    for n, t in hw["tools"].items():
        print(f"| {n} | {ok(t['path'])} {t['version'] or 'not found'} |")
    print(f"\n**Tier: {tier}**")
    print("| Limit | Value |\n|---|---|")
    print(f"| Engines | {', '.join(lim['engines'])} |\n| Max output height | {lim['max_height']}p |\n| Render workers | {lim['workers']} (one render job at a time) |")
    print(f"| Toon 3D | {lim['toon3d']} |\n| Blender | {lim['blender']} |\n| Ask before renders over | {lim['ask_over_min']} min |")
    if hw["ram_free"] / max(1, hw["ram_total"]) < 0.25:
        print("\n⚠️ Free RAM is low right now. Close big apps (browsers, games) before rendering.")


if __name__ == "__main__":
    main()
