"""Shared helpers for every animation-studio tool. Standard library only.

- SKILL_DIR: the skill folder (found from this file, never hard-coded)
- find_tool(name): ffmpeg, ffprobe, node, blender, latex... on PATH or in the usual install folders
- memory(): (total_bytes, available_bytes)
- on_battery(): True / False / None (unknown or no battery)
- low_priority(): lower this process's CPU priority (children inherit it)
- venv_python(): the python inside SKILL_DIR/.venv if it exists, else the current one
"""
import ctypes, glob, os, platform, re, shutil, subprocess, sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
OS = {"Windows": "win", "Darwin": "mac"}.get(platform.system(), "linux")


def utf8():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass


def _extra_dirs(name):
    home = Path.home()
    la = os.environ.get("LOCALAPPDATA", "")
    pf = [os.environ.get("ProgramFiles", r"C:\Program Files"), os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")]
    d = []
    if OS == "win":
        d += [os.path.join(la, "Microsoft", "WinGet", "Links"), r"C:\ProgramData\chocolatey\bin", str(home / "scoop" / "shims")]
        d += glob.glob(os.path.join(la, "Microsoft", "WinGet", "Packages", "*FFmpeg*", "*", "bin"))
        if name == "blender":
            for p in pf:
                d += sorted(glob.glob(os.path.join(p, "Blender Foundation", "Blender*")), reverse=True)
                d += glob.glob(os.path.join(p, "Steam", "steamapps", "common", "Blender"))
        if name in ("latex", "pdflatex"):
            d += glob.glob(os.path.join(la, "Programs", "MiKTeX", "miktex", "bin", "x64")) + glob.glob(r"C:\texlive\*\bin\windows")
        if name == "piper":
            d += [str(SKILL_DIR / ".tools" / "piper")]
    elif OS == "mac":
        d += ["/opt/homebrew/bin", "/usr/local/bin", "/Library/TeX/texbin"]
        if name == "blender":
            d += ["/Applications/Blender.app/Contents/MacOS"]
    else:
        d += ["/usr/local/bin", "/snap/bin", str(home / ".local" / "bin")]
    return [x for x in d if x and os.path.isdir(x)]


def find_tool(name):
    """Full path of a program, or None. Looks on PATH first, then in common install folders."""
    p = shutil.which(name)
    if p:
        return p
    exe = name + (".exe" if OS == "win" else "")
    for d in _extra_dirs(name):
        for cand in (exe, name.capitalize() + (".exe" if OS == "win" else ""), "Blender" if name == "blender" else exe):
            f = os.path.join(d, cand)
            if os.path.isfile(f):
                return f
    return None


def need_tool(name):
    p = find_tool(name)
    if not p:
        sys.exit(f"{name} not found. Run: python shared/setup_check.py  (it prints the install command for your OS)")
    return p


def run(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=isinstance(cmd, str),
                           encoding="utf-8", errors="replace")
        return (r.stdout or "") + (r.stderr or "")
    except Exception:
        return ""


def memory():
    """(total, available) in bytes; (0, 0) if unknown."""
    try:
        if OS == "win":
            class MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong),
                            ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong),
                            ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            m = MS(); m.dwLength = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return m.ullTotalPhys, m.ullAvailPhys
        if OS == "linux":
            info = dict(re.findall(r"(\w+):\s+(\d+)", open("/proc/meminfo").read()))
            return int(info["MemTotal"]) * 1024, int(info.get("MemAvailable", info["MemFree"])) * 1024
        total = int(run(["sysctl", "-n", "hw.memsize"]).strip() or 0)
        vm = run(["vm_stat"])
        page = int((re.search(r"page size of (\d+)", vm) or [0, 4096])[1])
        pages = sum(int(x) for k, x in re.findall(r"Pages (free|inactive|speculative|purgeable):\s+(\d+)", vm))
        return total, pages * page
    except Exception:
        return 0, 0


def free_ram_fraction():
    t, a = memory()
    return a / t if t else 1.0


def on_battery():
    try:
        if OS == "win":
            class PS(ctypes.Structure):
                _fields_ = [("ACLineStatus", ctypes.c_byte), ("BatteryFlag", ctypes.c_byte), ("BatteryLifePercent", ctypes.c_byte),
                            ("SystemStatusFlag", ctypes.c_byte), ("BatteryLifeTime", ctypes.c_ulong), ("BatteryFullLifeTime", ctypes.c_ulong)]
            s = PS()
            if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(s)):
                return None
            if s.BatteryFlag & 128:            # no system battery (desktop)
                return None
            return s.ACLineStatus == 0
        if OS == "mac":
            out = run(["pmset", "-g", "batt"])
            if "InternalBattery" not in out:
                return None
            return "Battery Power" in out
        sup = glob.glob("/sys/class/power_supply/*")
        bats = [p for p in sup if open(os.path.join(p, "type")).read().strip() == "Battery"] if sup else []
        if not bats:
            return None
        mains = [p for p in sup if open(os.path.join(p, "type")).read().strip() == "Mains"]
        if mains:
            return not any(open(os.path.join(p, "online")).read().strip() == "1" for p in mains)
        return open(os.path.join(bats[0], "status")).read().strip() == "Discharging"
    except Exception:
        return None


def low_priority():
    """Below-normal CPU priority for this process (and the workers it starts), so the PC stays usable."""
    try:
        if OS == "win":
            k = ctypes.windll.kernel32
            k.SetPriorityClass(k.GetCurrentProcess(), 0x00004000)   # BELOW_NORMAL_PRIORITY_CLASS
        else:
            os.nice(10)
    except Exception:
        pass


def venv_python():
    v = SKILL_DIR / ".venv" / ("Scripts/python.exe" if OS == "win" else "bin/python")
    return str(v) if v.exists() else sys.executable


def gb(n):
    return f"{n / 1e9:.1f} GB"


# ---------- one heavy job at a time ----------
import tempfile as _tf

LOCK = Path(_tf.gettempdir()) / "animation-studio-render.lock"


def _alive(pid):
    try:
        if OS == "win":
            h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)      # PROCESS_QUERY_LIMITED_INFORMATION
            if not h:
                return False
            code = ctypes.c_ulong()
            ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
            ctypes.windll.kernel32.CloseHandle(h)
            return code.value == 259                                      # STILL_ACTIVE
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def acquire_lock(what):
    """Refuse to start if another animation-studio render is running. Stale locks are cleared."""
    if LOCK.exists():
        try:
            pid, other = LOCK.read_text(encoding="utf-8").split("\n", 1)
            if int(pid) != os.getpid() and _alive(int(pid)):
                sys.exit(f"Another render is running (pid {pid}: {other.strip()}). Wait for it to finish: "
                         "two heavy jobs at once can freeze the computer.")
        except ValueError:
            pass
    LOCK.write_text(f"{os.getpid()}\n{what}", encoding="utf-8")


def release_lock():
    try:
        if LOCK.exists() and LOCK.read_text(encoding="utf-8").split("\n", 1)[0] == str(os.getpid()):
            LOCK.unlink()
    except Exception:
        pass
