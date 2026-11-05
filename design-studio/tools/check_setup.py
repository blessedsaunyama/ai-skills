"""Check what design-studio needs. Never installs anything: it prints what is missing
and the command to run (ask the user first).

    python check_setup.py
"""
import importlib
import platform
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

REQUIRED = [("PIL", "Pillow", "images"), ("fontTools", "fonttools", "text outlines + font checks")]
OPTIONAL = [("rembg", "\"rembg[cpu]\"", "background removal (speaker cutouts). ~150 MB + ~170 MB model on first use"),
            ("psd_tools", "psd-tools", "reading .psd files"),
            ("numpy", "numpy", "used by rembg / psd-tools")]


def has(mod):
    try:
        importlib.import_module(mod)
        return True
    except Exception:
        return False


def main():
    py = sys.executable
    print(f"Python {platform.python_version()} ({py})  OS: {platform.system()} {platform.release()}")
    missing_req, missing_opt = [], []
    for mod, pkg, why in REQUIRED:
        ok = has(mod)
        print(f"  [{'OK' if ok else 'MISSING'}] {pkg:12} required - {why}")
        if not ok:
            missing_req.append(pkg)
    for mod, pkg, why in OPTIONAL:
        ok = has(mod)
        print(f"  [{'OK' if ok else '--'}] {pkg.strip(chr(34)):12} optional - {why}")
        if not ok:
            missing_opt.append(pkg)
    import render
    ink, cairo, chrome = render.find_inkscape(), render.cairosvg_ok(), render.chromium_ok()
    print("Renderers (need at least one):")
    print(f"  [{'OK' if ink else '--'}] Inkscape")
    print(f"  [{'OK' if cairo else '--'}] cairosvg {'(installed but no Cairo library)' if (not cairo and has('cairosvg')) else ''}")
    print(f"  [{'OK' if chrome else '--'}] Chromium via Playwright (Node)")
    import artcraft
    print("ArtCraft power tools (optional - save back to .ai/.psd/.eps/.idml, CMYK):")
    for app in artcraft.APPS:
        print(f"  [{'OK' if artcraft.find(app) else '--'}] {artcraft.APPS[app].split('/')[0]}")
    fonts = Path(__file__).resolve().parent.parent / "fonts"
    n = len(list(fonts.glob("*.ttf")))
    print(f"Fonts bundled: {n} files in fonts/ {'OK' if n >= 17 else '(some missing!)'}")
    print()
    if missing_req:
        print("REQUIRED - ask the user, then run:\n  " + f'"{py}" -m pip install ' + " ".join(missing_req))
    if not (ink or cairo or chrome):
        print("NO RENDERER - ask the user which to install:")
        print(f'  a) "{py}" -m pip install cairosvg   (Linux/macOS: works directly; Windows: also needs the GTK/Cairo runtime)')
        print("  b) Inkscape from inkscape.org (or: winget install Inkscape.Inkscape)")
        print("  c) npm install -g playwright && npx playwright install chromium")
    if missing_opt:
        print("Optional - offer only when the feature is needed:\n  " + f'"{py}" -m pip install ' + " ".join(missing_opt))
    ready = not missing_req and (ink or cairo or chrome)
    print("\nREADY" if ready else "\nNOT READY")
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()
