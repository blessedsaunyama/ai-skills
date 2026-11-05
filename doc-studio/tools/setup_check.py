#!/usr/bin/env python3
"""doc-studio setup check: computer, Python and the document libraries. Standard library only.

  python tools/setup_check.py              report only (changes nothing)
  python tools/setup_check.py --net        also test that BibleGateway and egwwritings.org can be reached
  python tools/setup_check.py --install    install ONLY the missing libraries with pip --user
                                           (run this only after the user said yes)
Exit code 0 = ready, 1 = something required is missing.
"""
import importlib, os, platform, shutil, subprocess, sys, urllib.request

REQUIRED = [  # (import name, pip name, what it is for)
    ("docx", "python-docx", "Word .docx"),
    ("pptx", "python-pptx", "PowerPoint .pptx"),
    ("openpyxl", "openpyxl", "Excel .xlsx"),
    ("reportlab", "reportlab", "PDF"),
    ("PIL", "Pillow", "images (logos, photos, resizing)"),
]
OPTIONAL = [
    ("svglib", "svglib", "AI-drawn SVG pictures (without it, SVG art is skipped)"),
    ("rlPyCairo", "rlPyCairo", "turns SVG into PNG for Word/PowerPoint (without it, SVG works in PDF only)"),
]


def have(mod):
    try:
        importlib.import_module(mod)
        return True
    except Exception:
        return False


def ram_gb():
    try:
        if os.name == "nt":
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [("l", ctypes.c_ulong), ("m", ctypes.c_ulong), ("t", ctypes.c_ulonglong), ("a", ctypes.c_ulonglong),
                            ("tp", ctypes.c_ulonglong), ("ap", ctypes.c_ulonglong), ("tv", ctypes.c_ulonglong),
                            ("av", ctypes.c_ulonglong), ("e", ctypes.c_ulonglong)]
            s = MS(); s.l = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s))
            return s.t / 2**30
        if hasattr(os, "sysconf"):
            return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30
    except Exception:
        pass
    return None


def reach(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 doc-studio-check"})
        urllib.request.urlopen(req, timeout=15).read(200)
        return True
    except Exception:
        return False


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    print("doc-studio setup check")
    print(f"  OS       : {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"  Python   : {sys.version.split()[0]}  ({sys.executable})")
    r = ram_gb()
    print(f"  RAM      : {r:.1f} GB" if r else "  RAM      : unknown")
    free = shutil.disk_usage(os.getcwd()).free / 2**30
    print(f"  Disk free: {free:.1f} GB here")
    ok_py = sys.version_info >= (3, 9)
    if not ok_py:
        print("  !! Python 3.9 or newer is needed")
    if r and r < 2:
        print("  note: under 2 GB RAM. Keep images small and decks under ~40 slides.")

    missing, opt_missing = [], []
    print("\nLibraries")
    for mod, pipn, why in REQUIRED:
        h = have(mod)
        print(f"  [{'OK' if h else 'MISSING'}] {pipn:12} {why}")
        if not h:
            missing.append(pipn)
    for mod, pipn, why in OPTIONAL:
        h = have(mod)
        print(f"  [{'OK' if h else 'optional'}] {pipn:12} {why}")
        if not h:
            opt_missing.append(pipn)

    if "--net" in args:
        print("\nNetwork (for verifying Bible / EGW / sources)")
        for u in ["https://www.biblegateway.com/", "https://text.egwwritings.org/"]:
            print(f"  [{'OK' if reach(u) else 'NO'}] {u}")

    cmd = [sys.executable, "-m", "pip", "install", "--user"]
    if missing or opt_missing:
        print("\nTo install (download is about 20-30 MB):")
        if missing:
            print("  required: " + " ".join(cmd + missing))
        if opt_missing:
            print("  optional: " + " ".join(cmd + opt_missing))

    if "--install" in args and (missing or opt_missing):
        todo = missing + (opt_missing if "--no-optional" not in args else [])
        print("\nInstalling: " + " ".join(todo))
        rc = subprocess.call(cmd + todo)
        if rc != 0:
            print("pip failed. Show the error to the user; do not retry with other flags without asking.")
            sys.exit(1)
        importlib.invalidate_caches()
        still = [p for m, p, _ in REQUIRED if not have(m)]
        print("All required libraries ready." if not still else f"Still missing: {still}")
        sys.exit(1 if still else 0)

    if not missing and ok_py:
        print("\nREADY: all required libraries are installed.")
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
