"""Size presets for design-studio.

Every preset has a ratio label (what people understand) and the pixel / mm
equivalent. Screen sizes are in px. Print sizes are in mm, rendered at `dpi`.
Safe insets are fractions of (top, right, bottom, left) of the TRIM size:
keep important text and logos inside them.

    python sizes.py            -> prints the menu (ratio + pixels)
    python sizes.py a4 --landscape
"""
import argparse
import json
import sys

MM_PER_IN = 25.4

# key: (label, kind, w, h, unit, dpi, safe(t,r,b,l), note)
PRESETS = {
    # ---- screen / social (px) ----
    "square":      ("1:1 square post",            "screen", 1080, 1080, "px", 72, (.06, .06, .06, .06), "Instagram / Facebook / WhatsApp post"),
    "portrait":    ("4:5 portrait post",          "screen", 1080, 1350, "px", 72, (.06, .06, .06, .06), "Instagram / Facebook feed (largest in feed)"),
    "3x4":         ("3:4 portrait",               "screen", 1080, 1440, "px", 72, (.06, .06, .06, .06), "Instagram new grid / general portrait"),
    "2x3":         ("2:3 tall portrait",          "screen", 1080, 1620, "px", 72, (.06, .06, .06, .06), "Pinterest / tall poster post"),
    "story":       ("9:16 story / status",        "screen", 1080, 1920, "px", 72, (.13, .06, .18, .06), "IG / FB story, WhatsApp status, TikTok, Reels (top 250 px and bottom 340 px are covered by the app)"),
    "landscape":   ("16:9 landscape",             "screen", 1920, 1080, "px", 72, (.06, .05, .06, .05), "Projector slide, TV screen, YouTube banner art, X post"),
    "4x3":         ("4:3 landscape",              "screen", 1440, 1080, "px", 72, (.06, .06, .06, .06), "Older projectors, tablets"),
    "5x4":         ("5:4 landscape",              "screen", 1350, 1080, "px", 72, (.06, .06, .06, .06), "Near-square landscape"),
    "3x2":         ("3:2 landscape",              "screen", 1620, 1080, "px", 72, (.06, .06, .06, .06), "Photo-style landscape"),
    "youtube":     ("16:9 YouTube thumbnail",     "screen", 1280,  720, "px", 72, (.06, .05, .06, .05), "Keep text away from the bottom-right corner (video length badge). Must be under 2 MB"),
    "link":        ("1.91:1 link preview",        "screen", 1200,  630, "px", 72, (.08, .06, .08, .06), "Website / WhatsApp link preview, FB link post"),
    "fb-cover":    ("2.63:1 Facebook page cover", "screen", 1640,  624, "px", 72, (.08, .17, .10, .17), "Phones crop the sides: keep text in the middle 66 %"),
    "fb-event":    ("1.91:1 Facebook event cover","screen", 1920, 1005, "px", 72, (.08, .06, .08, .06), "Facebook event header"),
    "x-header":    ("3:1 X / Twitter header",     "screen", 1500,  500, "px", 72, (.10, .06, .12, .25), "Profile photo covers bottom-left"),
    "linkedin":    ("4:1 LinkedIn banner",        "screen", 1584,  396, "px", 72, (.10, .06, .10, .25), "Profile photo covers the left"),
    # ---- print (mm) ----
    "a5":          ("A5 flyer (148 x 210 mm)",    "print",  148, 210, "mm", 300, (.05, .06, .05, .06), "Handout flyer"),
    "a4":          ("A4 flyer / poster (210 x 297 mm)", "print", 210, 297, "mm", 300, (.04, .05, .04, .05), "Standard flyer, notice board"),
    "a3":          ("A3 poster (297 x 420 mm)",   "print",  297, 420, "mm", 300, (.035, .04, .035, .04), "Poster"),
    "a2":          ("A2 poster (420 x 594 mm)",   "print",  420, 594, "mm", 200, (.03, .035, .03, .035), "Large poster"),
    "certificate": ("A4 landscape certificate",   "print",  297, 210, "mm", 300, (.07, .06, .07, .06), "Certificate (A4 sideways)"),
    "rollup":      ("Roll-up banner 85 x 200 cm", "print",  850, 2000, "mm", 150, (.03, .05, .12, .05), "Bottom ~20 cm sits low / in the stand: keep key info above it"),
    "rollup-100":  ("Roll-up banner 100 x 200 cm","print", 1000, 2000, "mm", 150, (.03, .05, .12, .05), "Wide roll-up"),
    "banner-3x1":  ("3:1 PVC banner 3 x 1 m",     "print", 3000, 1000, "mm", 100, (.06, .04, .06, .04), "Outdoor banner (eyelets near edges)"),
    "banner-2x1":  ("2:1 PVC banner 2 x 1 m",     "print", 2000, 1000, "mm", 100, (.06, .04, .06, .04), "Outdoor banner"),
}

ALIASES = {
    "1:1": "square", "4:5": "portrait", "3:4": "3x4", "2:3": "2x3", "9:16": "story",
    "16:9": "landscape", "4:3": "4x3", "5:4": "5x4", "3:2": "3x2", "thumbnail": "youtube",
    "yt": "youtube", "whatsapp-status": "story", "ig-story": "story", "ig-post": "square",
    "roll-up": "rollup", "a4-landscape": "a4:landscape", "a3-landscape": "a3:landscape",
}


def get(key, landscape=None, custom=None):
    """Return a dict describing the canvas. key may be 'a4', 'a4:landscape',
    'custom' (with custom=(w, h, unit)), or a ratio alias like '9:16'."""
    key = ALIASES.get(key, key)
    if ":" in key and key.split(":")[1] in ("landscape", "portrait"):
        key, orient = key.split(":")
        landscape = orient == "landscape"
    if key == "custom":
        w, h, unit = custom
        label, kind, dpi, safe, note = f"Custom {w}x{h} {unit}", ("print" if unit == "mm" else "screen"), (300 if unit == "mm" else 72), (.05, .05, .05, .05), "Custom size"
    else:
        if key not in PRESETS:
            raise SystemExit(f"Unknown size '{key}'. Run sizes.py to see the list.")
        label, kind, w, h, unit, dpi, safe, note = PRESETS[key]
    t, r, b, l = safe
    if landscape is not None and (w > h) != landscape and w != h:
        w, h = h, w
        t, r, b, l = l, t, r, b  # rotate insets
        label += " (landscape)" if landscape else " (portrait)"
    px_w, px_h = (w, h) if unit == "px" else (round(w / MM_PER_IN * dpi), round(h / MM_PER_IN * dpi))
    return {"key": key, "label": label, "kind": kind, "w": w, "h": h, "unit": unit, "dpi": dpi,
            "px_w": px_w, "px_h": px_h, "safe": {"top": t, "right": r, "bottom": b, "left": l}, "note": note}


def ratio_text(w, h):
    from math import gcd
    g = gcd(int(w), int(h))
    a, b = int(w) // g, int(h) // g
    return f"{a}:{b}" if a <= 32 and b <= 32 else f"{w / h:.2f}:1"


def menu():
    lines = ["SCREEN (pixels)"]
    for k, (label, kind, w, h, unit, dpi, safe, note) in PRESETS.items():
        if kind == "print" and "PRINT" not in lines[-1] and not any(l.startswith("PRINT") for l in lines):
            lines += ["", "PRINT (mm, rendered at the dpi shown)"]
        if kind == "screen":
            lines.append(f"  {k:12} {label:30} {w} x {h} px   - {note}")
        else:
            pw, ph = round(w / MM_PER_IN * dpi), round(h / MM_PER_IN * dpi)
            lines.append(f"  {k:12} {label:30} {pw} x {ph} px @ {dpi} dpi - {note}")
    lines += ["", "Any rectangle can be flipped: add --landscape / --portrait (e.g. a4:landscape, story -> 16:9)."]
    return "\n".join(lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("size", nargs="?")
    ap.add_argument("--landscape", action="store_true")
    ap.add_argument("--portrait", action="store_true")
    a = ap.parse_args()
    if not a.size:
        print(menu())
        sys.exit()
    orient = True if a.landscape else (False if a.portrait else None)
    print(json.dumps(get(a.size, orient), indent=2))
