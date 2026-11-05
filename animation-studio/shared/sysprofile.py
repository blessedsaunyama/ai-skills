"""System profile: OS, version, distro, WSL, Apple Silicon, package managers, shell, display. Standard library only.

  from sysprofile import detect_system, load_profile, profile_path
Every tool that shows or runs a command reads the saved profile (written by hwcheck.py) so commands match the
user's OS, distro, package manager and shell. `SIMULATIONS` hold test profiles (hwcheck.py --simulate NAME).
"""
import json, os, platform, re, shutil, subprocess, sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import OS, run  # noqa: E402

LINUX_FAMILY = {  # /etc/os-release ID or ID_LIKE -> family + native package manager
    "ubuntu": ("debian", "apt"), "debian": ("debian", "apt"), "linuxmint": ("debian", "apt"), "pop": ("debian", "apt"),
    "elementary": ("debian", "apt"), "zorin": ("debian", "apt"), "kali": ("debian", "apt"),
    "fedora": ("fedora", "dnf"), "rhel": ("fedora", "dnf"), "centos": ("fedora", "dnf"), "rocky": ("fedora", "dnf"), "almalinux": ("fedora", "dnf"),
    "arch": ("arch", "pacman"), "manjaro": ("arch", "pacman"), "endeavouros": ("arch", "pacman"), "garuda": ("arch", "pacman"),
    "opensuse": ("suse", "zypper"), "opensuse-tumbleweed": ("suse", "zypper"), "opensuse-leap": ("suse", "zypper"), "suse": ("suse", "zypper"),
}
MANAGERS = {"win": ["winget", "choco", "scoop"], "mac": ["brew"], "linux": ["apt", "dnf", "pacman", "zypper", "flatpak", "snap"]}


def user_dir():
    """Per-user folder for the profile, voices and downloaded tools (never inside the skill)."""
    if OS == "win":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif OS == "mac":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "animation-studio"


def profile_path():
    return user_dir() / "system.json"


def os_release():
    p = Path("/etc/os-release")
    if not p.exists():
        return {}
    out = {}
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"')
    return out


def detect_shell():
    if OS == "win":
        if os.environ.get("MSYSTEM") or "bash" in os.environ.get("SHELL", ""):
            return "bash"                                    # Git Bash / MSYS
        return "powershell"
    sh = os.path.basename(os.environ.get("SHELL", "/bin/sh"))
    return sh if sh in ("bash", "zsh", "fish", "sh") else "sh"


def detect_display():
    if OS == "win":
        return not os.environ.get("SSH_CONNECTION")
    if OS == "mac":
        return not (os.environ.get("SSH_CONNECTION") and not os.environ.get("DISPLAY"))
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def detect_system():
    p = {"os": OS, "arch": platform.machine().lower(), "shell": detect_shell(), "display": detect_display(), "wsl": False}
    if OS == "win":
        ver = platform.version()                              # 10.0.26100
        build = int(ver.split(".")[-1]) if ver.split(".")[-1].isdigit() else 0
        p["os_name"] = f"Windows {'11' if build >= 22000 else '10'}"
        p["os_version"] = ver
    elif OS == "mac":
        mv = platform.mac_ver()[0]
        p["os_name"] = f"macOS {mv}"
        p["os_version"] = mv
        p["apple_silicon"] = p["arch"] in ("arm64", "aarch64") or "Apple" in run(["sysctl", "-n", "machdep.cpu.brand_string"])
    else:
        rel = os_release()
        ids = [rel.get("ID", "").lower()] + rel.get("ID_LIKE", "").lower().split()
        fam = next((LINUX_FAMILY[i] for i in ids if i in LINUX_FAMILY), ("other", None))
        p.update(os_name=rel.get("PRETTY_NAME", "Linux"), os_version=rel.get("VERSION_ID", ""), distro=rel.get("ID", "linux"),
                 family=fam[0], native_manager=fam[1])
        try:
            p["wsl"] = "microsoft" in Path("/proc/version").read_text().lower()
        except Exception:
            pass
    p["managers"] = [m for m in MANAGERS[OS] if shutil.which(m) or (m == "winget" and _winget())]
    p["admin_tool"] = "sudo" if OS != "win" else "UAC prompt (Windows asks for permission)"
    return p


def _winget():
    la = os.environ.get("LOCALAPPDATA", "")
    return bool(la and (Path(la) / "Microsoft" / "WindowsApps" / "winget.exe").exists())


SIMULATIONS = {
    "macos-arm": {"os": "mac", "arch": "arm64", "shell": "zsh", "display": True, "wsl": False, "os_name": "macOS 15.5", "os_version": "15.5",
                  "apple_silicon": True, "managers": ["brew"], "admin_tool": "sudo"},
    "macos-intel": {"os": "mac", "arch": "x86_64", "shell": "zsh", "display": True, "wsl": False, "os_name": "macOS 13.7", "os_version": "13.7",
                    "apple_silicon": False, "managers": ["brew"], "admin_tool": "sudo"},
    "ubuntu": {"os": "linux", "arch": "x86_64", "shell": "bash", "display": True, "wsl": False, "os_name": "Ubuntu 24.04.3 LTS",
               "os_version": "24.04", "distro": "ubuntu", "family": "debian", "native_manager": "apt", "managers": ["apt", "snap"], "admin_tool": "sudo"},
    "ubuntu-server": {"os": "linux", "arch": "x86_64", "shell": "bash", "display": False, "wsl": False, "os_name": "Ubuntu 24.04.3 LTS (no desktop)",
                      "os_version": "24.04", "distro": "ubuntu", "family": "debian", "native_manager": "apt", "managers": ["apt", "snap"], "admin_tool": "sudo"},
    "fedora": {"os": "linux", "arch": "x86_64", "shell": "bash", "display": True, "wsl": False, "os_name": "Fedora Linux 43 (Workstation Edition)",
               "os_version": "43", "distro": "fedora", "family": "fedora", "native_manager": "dnf", "managers": ["dnf", "flatpak"], "admin_tool": "sudo"},
    "arch": {"os": "linux", "arch": "x86_64", "shell": "zsh", "display": True, "wsl": False, "os_name": "Arch Linux", "os_version": "",
             "distro": "arch", "family": "arch", "native_manager": "pacman", "managers": ["pacman", "flatpak"], "admin_tool": "sudo"},
    "opensuse": {"os": "linux", "arch": "x86_64", "shell": "bash", "display": True, "wsl": False, "os_name": "openSUSE Tumbleweed", "os_version": "20261101",
                 "distro": "opensuse-tumbleweed", "family": "suse", "native_manager": "zypper", "managers": ["zypper", "flatpak"], "admin_tool": "sudo"},
    "wsl-ubuntu": {"os": "linux", "arch": "x86_64", "shell": "bash", "display": True, "wsl": True, "os_name": "Ubuntu 24.04 (WSL2, WSLg)",
                   "os_version": "24.04", "distro": "ubuntu", "family": "debian", "native_manager": "apt", "managers": ["apt"], "admin_tool": "sudo"},
}


def load_profile(simulate=None):
    """The saved profile (hwcheck.py writes it), a simulation, or a fresh detection."""
    if simulate:
        return dict(SIMULATIONS[simulate], simulated=simulate)
    p = profile_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))["system"]
        except Exception:
            pass
    return detect_system()
