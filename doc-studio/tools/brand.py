#!/usr/bin/env python3
"""Saved brands (logo, colours, font, contacts) for doc-studio. Stored in the USER folder, never inside the skill:
  Windows %LOCALAPPDATA%\\doc-studio\\brands\\<id>\\   macOS ~/Library/Application Support/doc-studio/brands/   Linux ~/.local/share/doc-studio/brands/

  python tools/brand.py list
  python tools/brand.py show ID
  python tools/brand.py new ID "Display Name"
  python tools/brand.py set ID FIELD VALUE        FIELD: name tagline website whatsapp address font body_font
                                                  phones+ emails+ socials+ (append)   phones- (clear)
                                                  colours.primary colours.accent (#RRGGBB)
  python tools/brand.py logo ID PATH              copy the user's logo into the brand folder (PNG or JPG)
  python tools/brand.py validate ID
  python tools/brand.py where                     print the brands folder
Only details the user typed are stored. Never invent phone numbers, emails or addresses.
"""
import json, re, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from docstudio.common import SKILL_DIR, brand_path, user_dir, utf8  # noqa: E402

ROOT = user_dir() / "brands"
LISTS = {"phones", "emails", "socials"}
SCALARS = {"name", "tagline", "website", "whatsapp", "address", "font", "body_font"}


def path_for(bid, must=True):
    p = brand_path(bid)
    if must and not p:
        sys.exit(f"no brand '{bid}' (python tools/brand.py list)")
    return p


def load(bid):
    return json.loads(path_for(bid).read_text(encoding="utf-8"))


def save(bid, b):
    p = ROOT / bid / "brand.json"
    existing = path_for(bid, must=False)
    if existing and (SKILL_DIR / "examples" / "brands") in existing.parents:
        sys.exit("the sample brand is read-only; make your own with: brand.py new ID \"Name\"")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(b, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate(b):
    problems = []
    for e in b.get("emails", []):
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}", e):
            problems.append(f"email looks wrong: {e}")
    for ph in b.get("phones", []) + ([b["whatsapp"]] if b.get("whatsapp") else []):
        if len(re.sub(r"\D", "", ph.split("|")[0])) < 7:
            problems.append(f"phone looks too short: {ph}")
    for k, v in (b.get("colours") or {}).items():
        if not re.fullmatch(r"#?[0-9A-Fa-f]{6}", v):
            problems.append(f"colour {k} must be #RRGGBB: {v}")
    if b.get("website") and not re.match(r"^(https?://)?[\w.-]+\.[a-z]{2,}", b["website"], re.I):
        problems.append(f"website looks wrong: {b['website']}")
    if b.get("logo"):
        lp = path_for(b["_id"]).parent / b["logo"] if b.get("_id") else None
        if lp and not lp.exists():
            problems.append(f"logo file missing: {lp}")
    if not b.get("name"):
        problems.append("name is empty")
    return problems


def main():
    utf8()
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(1)
    cmd = a[0]
    if cmd == "where":
        print(ROOT); return
    if cmd == "list":
        found = []
        for d in (ROOT, SKILL_DIR / "examples" / "brands"):
            if d.exists():
                for p in sorted(d.glob("*/brand.json")):
                    b = json.loads(p.read_text(encoding="utf-8"))
                    found.append(f"  {p.parent.name:16} {b.get('name', '')}" + ("   (sample, read-only)" if d != ROOT else ""))
        print("Brands:\n" + ("\n".join(found) if found else "  (none yet: brand.py new ID \"Name\")"))
        return
    if len(a) < 2:
        print(__doc__); sys.exit(1)
    bid = re.sub(r"[^a-z0-9-]+", "-", a[1].lower()).strip("-")
    if cmd == "new":
        if (ROOT / bid / "brand.json").exists():
            sys.exit(f"brand '{bid}' already exists (use set, or ask before replacing it)")
        save(bid, {"name": a[2] if len(a) > 2 else bid, "tagline": "", "website": "", "phones": [], "emails": [],
                   "whatsapp": "", "address": "", "socials": [], "colours": {}, "font": "", "logo": ""})
        print(f"created {ROOT / bid / 'brand.json'}"); return
    if cmd == "show":
        print(json.dumps(load(bid), indent=2, ensure_ascii=False)); return
    if cmd == "validate":
        b = load(bid); b["_id"] = bid
        pr = validate(b)
        print("OK" if not pr else "\n".join("  ! " + x for x in pr)); sys.exit(1 if pr else 0)
    if cmd == "set" and len(a) >= 4:
        b = load(bid); field, val = a[2], a[3]
        if field.rstrip("+-") in LISTS:
            f = field.rstrip("+-")
            if field.endswith("-"):
                b[f] = []
            else:
                b.setdefault(f, []).append(val)
        elif field.startswith("colours."):
            if not re.fullmatch(r"#?[0-9A-Fa-f]{6}", val):
                sys.exit("colour must be #RRGGBB")
            b.setdefault("colours", {})[field.split(".", 1)[1]] = "#" + val.lstrip("#").upper()
        elif field in SCALARS:
            b[field] = val
        else:
            sys.exit(f"unknown field {field}")
        save(bid, b); print(f"{bid}.{field} = {val}"); return
    if cmd == "logo" and len(a) >= 3:
        src = Path(a[2])
        if not src.exists() or src.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            sys.exit("logo must be an existing .png or .jpg")
        b = load(bid)
        dest = ROOT / bid / ("logo" + src.suffix.lower())
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        b["logo"] = dest.name
        save(bid, b); print(f"logo saved: {dest}"); return
    print(__doc__); sys.exit(1)


if __name__ == "__main__":
    main()
