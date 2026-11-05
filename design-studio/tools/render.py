"""SVG -> PNG / PDF / JPG. Tries cairosvg (fastest), then Inkscape, then Chromium (Playwright).
All three give the same picture because text is already outlined.

    python render.py --which          -> shows which renderer will be used
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_choice = None


def find_inkscape():
    p = shutil.which("inkscape")
    if p:
        return p
    for cand in (r"C:\Program Files\Inkscape\bin\inkscape.exe", r"C:\Program Files (x86)\Inkscape\bin\inkscape.exe",
                 "/Applications/Inkscape.app/Contents/MacOS/inkscape"):
        if os.path.exists(cand):
            return cand
    return None


def _cairo_dlls():
    """Windows: pip's cairosvg needs libcairo-2.dll. Inkscape and the GTK runtime ship one: borrow it."""
    if os.name != "nt":
        return
    ink = find_inkscape()
    cands = [os.path.dirname(ink)] if ink else []
    cands += [r"C:\Program Files\GTK3-Runtime Win64\bin", r"C:\msys64\mingw64\bin"]
    for d in cands:
        if os.path.exists(os.path.join(d, "libcairo-2.dll")):
            if d not in os.environ.get("PATH", ""):
                os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
            try:
                os.add_dll_directory(d)
            except (OSError, AttributeError):
                pass
            return


def cairosvg_ok():
    _cairo_dlls()
    try:
        import cairosvg
        cairosvg.svg2png(bytestring=b'<svg xmlns="http://www.w3.org/2000/svg" width="2" height="2"/>')
        return True
    except Exception:
        return False


def node_env():
    node = shutil.which("node")
    if not node:
        return None, None
    env = dict(os.environ)
    roots = [str(HERE / "node_modules")]
    if os.environ.get("APPDATA"):
        roots.append(os.path.join(os.environ["APPDATA"], "npm", "node_modules"))
    try:
        r = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True, shell=(os.name == "nt"), timeout=60).stdout.strip()
        if r:
            roots.append(r)
    except Exception:
        pass
    roots += [p for p in env.get("NODE_PATH", "").split(os.pathsep) if p]
    env["NODE_PATH"] = os.pathsep.join(p for p in roots if os.path.isdir(p))
    return node, env


def chromium_ok():
    node, env = node_env()
    if not node:
        return False
    r = subprocess.run([node, "-e", "try{require('playwright')}catch(e){require('playwright-core')}"], env=env, capture_output=True, timeout=60)
    return r.returncode == 0


def which(prefer=None):
    global _choice
    if _choice:
        return _choice
    order = [prefer] if prefer else []
    order += ["cairosvg", "inkscape", "chromium"]
    for r in order:
        if r == "inkscape" and find_inkscape():
            _choice = r
        elif r == "cairosvg" and cairosvg_ok():
            _choice = r
        elif r == "chromium" and chromium_ok():
            _choice = r
        if _choice:
            return _choice
    raise SystemExit("No SVG renderer found. Run tools/check_setup.py for install options (Inkscape, cairosvg or Playwright).")


def run(jobs, prefer=None):
    """jobs: dicts with svg, out, type (png|pdf), w, h (px for png, mm for pdf)."""
    r = which(prefer)
    if r == "inkscape":
        ink = find_inkscape()
        for j in jobs:
            args = [ink, j["svg"], f"--export-type={j['type']}", f"--export-filename={j['out']}"]
            if j["type"] == "png":
                args += [f"--export-width={int(j['w'])}", f"--export-height={int(j['h'])}"]
            subprocess.run(args, check=True, capture_output=True)
    elif r == "cairosvg":
        _cairo_dlls()
        import cairosvg
        for j in jobs:
            if j["type"] == "png":
                cairosvg.svg2png(url=j["svg"], write_to=j["out"], output_width=int(j["w"]), output_height=int(j["h"]))
            else:
                cairosvg.svg2pdf(url=j["svg"], write_to=j["out"])
    else:
        node, env = node_env()
        fd, jf = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(jobs, fh)
        try:
            p = subprocess.run([node, str(HERE / "render_chromium.cjs"), jf], env=env, capture_output=True, text=True)
            if p.returncode:
                raise SystemExit("Chromium render failed:\n" + p.stderr[-2000:])
        finally:
            os.unlink(jf)
    return r


def to_jpg(png, jpg, max_bytes=None, quality=92):
    from PIL import Image
    im = Image.open(png).convert("RGB")
    while True:
        im.save(jpg, "JPEG", quality=quality, optimize=True, progressive=True)
        if not max_bytes or os.path.getsize(jpg) <= max_bytes or quality <= 60:
            return quality
        quality -= 6


if __name__ == "__main__":
    if "--which" in sys.argv:
        print("Inkscape :", find_inkscape() or "not found")
        print("cairosvg :", "works" if cairosvg_ok() else "not usable (missing or no Cairo library)")
        print("Chromium :", "works (Playwright)" if chromium_ok() else "not found")
        print("Using    :", which())
