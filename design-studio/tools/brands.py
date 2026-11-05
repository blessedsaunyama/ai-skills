"""Saved brands, stored OUTSIDE the skill (so real logos never ship with it):
Windows %LOCALAPPDATA%\\design-studio\\brands\\<slug>\\, macOS/Linux ~/.local/share/design-studio/brands/<slug>/

    python brands.py list
    python brands.py show <slug>
    python brands.py save <slug> --name "MSU SDA Youth" --colors "#1D3C8F,#F2B705" [--host "MSU SDA presents"]
                      [--logo path --logo-pos top-left]... [--contact phone=0772...]... [--style youthful]
Logos are copied into the brand folder. A brand only fills defaults: the user can override anything.
"""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path


def root():
    base = os.environ.get("LOCALAPPDATA") or os.path.join(Path.home(), ".local", "share")
    p = Path(base) / "design-studio" / "brands"
    p.mkdir(parents=True, exist_ok=True)
    return p


def load(slug):
    f = root() / slug / "brand.json"
    if not f.exists():
        sys.exit(f"No brand '{slug}'. Saved brands: {', '.join(list_all()) or 'none'}")
    b = json.loads(f.read_text(encoding="utf-8"))
    for lg in b.get("logos", []):
        lg["file"] = str(root() / slug / lg["file"])
    return b


def list_all():
    return sorted(p.name for p in root().iterdir() if (p / "brand.json").exists())


def save(a):
    d = root() / a.slug
    d.mkdir(parents=True, exist_ok=True)
    f = d / "brand.json"
    b = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    b["name"] = a.name or b.get("name", a.slug)
    if a.colors:
        b["palette"] = [c.strip() for c in a.colors.split(",")]
    if a.host:
        b["host_line"] = a.host
    if a.style:
        b["style"] = a.style
    if a.logo:
        b["logos"] = []
        poss = a.logo_pos or []
        for i, lp in enumerate(a.logo):
            shutil.copy2(lp, d / Path(lp).name)
            b["logos"].append({"file": Path(lp).name, "pos": poss[i] if i < len(poss) else "top-left"})
    if a.contact:
        b["contacts"] = [{"type": c.split("=", 1)[0], "value": c.split("=", 1)[1]} for c in a.contact]
    f.write_text(json.dumps(b, indent=2), encoding="utf-8")
    print(f"Saved brand '{a.slug}' -> {d}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "show", "save"])
    ap.add_argument("slug", nargs="?")
    ap.add_argument("--name")
    ap.add_argument("--colors")
    ap.add_argument("--host")
    ap.add_argument("--style")
    ap.add_argument("--logo", action="append")
    ap.add_argument("--logo-pos", action="append")
    ap.add_argument("--contact", action="append")
    a = ap.parse_args()
    if a.cmd == "list":
        print("\n".join(list_all()) or "(no saved brands)")
    elif a.cmd == "show":
        print(json.dumps(load(a.slug), indent=2))
    else:
        save(a)
