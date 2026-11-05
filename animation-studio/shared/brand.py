#!/usr/bin/env python3
"""Brand kit: saved brands, validation, logo prep, OFL fonts, style recolouring and brand overlays on any engine's frames.

Brands live in the USER folder (never inside the public skill):  <user folder>/brands/<id>/brand.yaml (+ logo, fonts).
The skill only ships brands/_template.yaml and a fictional sample (brands/sample/).

  python shared/brand.py list
  python shared/brand.py new ID                         create <user folder>/brands/ID/brand.yaml from the template
  python shared/brand.py set ID FIELD VALUE              e.g. set mybrand phones+ "+1 202 555 0143 | Orders"
                                                         (FIELD+ appends to a list; colours.primary etc. for nested; validated)
  python shared/brand.py logo ID PATH                    copy the user's logo, make the background transparent, trim it
  python shared/brand.py font ID "Space Grotesk"         download an OFL font from the official google/fonts repo (checks OFL.txt)
  python shared/brand.py validate ID                     check every field (phones, emails, URLs, colours, logo, font licence)
  python shared/brand.py recolor ID --style flat-2d --out style_brand.md   style preset in the brand colours
  python shared/brand.py apply ID FRAMES_IN FRAMES_OUT --fmt 9x16 [--fps 30] [--watermark tr,10,85,logo]
         [--lower-third 1.0,3.0] [--end-card 2.5] [--cta TEXT] [--captions]      brand overlays + end card on rendered frames
Never invents contact details: only what the user typed (or confirmed from their own website) is used.
Needs Pillow (+ numpy) for logo/apply.
"""
import json, os, re, shutil, sys, urllib.request
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import SKILL_DIR, utf8  # noqa: E402
from registry import parse  # noqa: E402
from sysprofile import user_dir  # noqa: E402

FIELDS = ["name", "tagline", "website", "logo", "phones", "whatsapp", "emails", "socials", "colours", "font", "cta"]
LISTS = {"phones", "emails", "socials"}


def brand_dirs():
    return [user_dir() / "brands", SKILL_DIR / "brands"]


def find(bid):
    for d in brand_dirs():
        p = d / bid / "brand.yaml"
        if p.exists():
            return p
    sys.exit(f"no brand '{bid}' (python shared/brand.py list)")


def load(bid):
    p = find(bid)
    b = parse(p.read_text(encoding="utf-8"))
    b["_dir"] = str(p.parent)
    return b


# ---------------- writing the small YAML subset ----------------
def _q(v):
    v = str(v)
    return f'"{v}"' if (v.startswith(("#", "[", "{", "'", '"')) or ": " in v or v.endswith(":")) else v


def dump(b):
    out = ["# animation-studio brand kit. Only real details the owner gave. Lists: one item per line, '- value'."]
    for k in FIELDS + ["defaults"]:
        v = b.get(k)
        if isinstance(v, dict):
            out.append(f"{k}:")
            out += [f"  {kk}: {_q(vv)}" for kk, vv in v.items() if vv not in (None, "")]
        elif isinstance(v, list):
            out.append(f"{k}:")
            out += [f"  - {_q(x)}" for x in v]
        elif v not in (None, ""):
            out.append(f"{k}: {_q(v)}")
    return "\n".join(out) + "\n"


# ---------------- validation ----------------
def clean_phone(s):
    num = s.split("|")[0].strip()
    digits = re.sub(r"[\s\-().]", "", num)
    return digits if re.fullmatch(r"\+\d{8,15}", digits) else None


def check_email(s):
    return bool(re.fullmatch(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", s.strip()))


def check_url(s):
    return bool(re.fullmatch(r"https?://[A-Za-z0-9.\-]+\.[A-Za-z]{2,}(/\S*)?", s.strip()))


def norm_url(s):
    s = s.strip()
    return s if s.startswith(("http://", "https://")) else "https://" + s


def font_is_ofl(path):
    """Read the TTF/OTF 'name' table: licence (ID 13) / licence URL (ID 14) must mention the SIL Open Font License."""
    import struct
    data = Path(path).read_bytes()
    try:
        num = struct.unpack(">H", data[4:6])[0]
        for i in range(num):
            tag, _, off, ln = struct.unpack(">4sLLL", data[12 + 16 * i: 28 + 16 * i])
            if tag == b"name":
                _, count, sto = struct.unpack(">HHH", data[off:off + 6])
                texts = []
                for j in range(count):
                    pid, eid, lid, nid, l, o = struct.unpack(">HHHHHH", data[off + 6 + 12 * j: off + 18 + 12 * j])
                    if nid in (13, 14):
                        raw = data[off + sto + o: off + sto + o + l]
                        texts.append(raw.decode("utf-16-be" if pid in (0, 3) else "latin-1", "ignore"))
                t = " ".join(texts).lower()
                return "open font license" in t or "ofl" in t or "scripts.sil.org/ofl" in t or "openfontlicense" in t
    except Exception:
        return False
    return False


def validate(b):
    rows = []
    rows.append(("name", bool(b.get("name")), b.get("name") or "missing (required)"))
    for p in b.get("phones") or []:
        rows.append(("phone", bool(clean_phone(p)), p.replace("|", "·") if clean_phone(p) else f"{p}: use international format with the country code, e.g. +44 20 7946 0000"))
    if b.get("whatsapp"):
        ok = bool(clean_phone(b["whatsapp"]))
        rows.append(("whatsapp", ok, (b["whatsapp"] + f"  (link: https://wa.me/{clean_phone(b['whatsapp'])[1:]})") if ok else f"{b['whatsapp']}: use international format"))
    for e in b.get("emails") or []:
        rows.append(("email", check_email(e), e if check_email(e) else f"{e}: not a complete email address (name@domain.tld)"))
    for u in ([b["website"]] if b.get("website") else []) + (b.get("socials") or []):
        rows.append(("url", check_url(u), u))
    for k, v in (b.get("colours") or {}).items():
        rows.append((f"colour {k}", bool(re.fullmatch(r"#[0-9a-fA-F]{6}", str(v))), str(v)))
    if b.get("logo"):
        lp = Path(b["_dir"]) / b["logo"]
        ok = lp.exists()
        if ok:
            from PIL import Image
            im = Image.open(lp)
            alpha = im.mode in ("RGBA", "LA") and im.getchannel("A").getextrema()[0] < 250
            rows.append(("logo", alpha, f"{lp.name} {im.size[0]}x{im.size[1]}" + ("" if alpha else ": background not transparent (run: brand.py logo)")))
        else:
            rows.append(("logo", False, f"{lp} not found"))
    f = b.get("font") or {}
    if f.get("file"):
        fp = Path(b["_dir"]) / f["file"]
        rows.append(("font licence", fp.exists() and font_is_ofl(fp), f"{f.get('name')}: " + ("SIL OFL" if fp.exists() and font_is_ofl(fp) else "not OFL (or missing): system font will be used")))
    return rows


# ---------------- commands ----------------
def cmd_new(bid):
    d = user_dir() / "brands" / bid
    if (d / "brand.yaml").exists():
        sys.exit(f"brand '{bid}' already exists: {d / 'brand.yaml'} (ask before overwriting)")
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SKILL_DIR / "brands" / "_template.yaml", d / "brand.yaml")
    print(d / "brand.yaml")


def cmd_set(bid, field, value):
    p = find(bid)
    b = parse(p.read_text(encoding="utf-8"))
    append = field.endswith("+"); field = field.rstrip("+")
    top, _, sub = field.partition(".")
    if top not in FIELDS + ["defaults"]:
        sys.exit(f"unknown field '{top}' (fields: {', '.join(FIELDS)})")
    if top in ("website",) or (top == "socials"):
        value = norm_url(value)
    probe = {"_dir": str(p.parent), top: ([value] if top in LISTS else ({sub: value} if sub else value))}
    bad = [r for r in validate(dict(probe, name="x")) if r[0] != "name" and not r[1]]
    if bad:
        sys.exit(f"not saved: {bad[0][2]}")
    if sub:
        b.setdefault(top, {}) if isinstance(b.get(top), dict) else b.__setitem__(top, {})
        b[top][sub] = value
    elif top in LISTS:
        b[top] = (b.get(top) or []) + [value] if append else [value]
    else:
        b[top] = value
    p.write_text(dump(b), encoding="utf-8")
    print(f"saved {top}{'.' + sub if sub else ''} = {value}")


def cmd_logo(bid, src):
    from PIL import Image
    import numpy as np
    p = find(bid)
    b = parse(p.read_text(encoding="utf-8"))
    if str(src).lower().endswith(".svg"):              # SVG -> PNG with Inkscape (registry tool; install flow if missing)
        import subprocess, tempfile, tools as _tools
        st, _ = _tools.detect("inkscape", _tools.load_profile())
        if st != "ok":
            sys.exit("An SVG logo needs Inkscape to convert it.\n" + _tools.flow("inkscape", _tools.load_profile(), "engine") +
                     "\nOr export the logo as a PNG yourself and run: brand.py logo ID logo.png")
        exe = next(x for x in [_tools.find_tool("inkscape")] + [p_ for p_ in _tools.glob.glob(_tools.expand("%ProgramFiles%/Inkscape/bin/inkscape.exe"))] if x)
        png = Path(tempfile.gettempdir()) / "as_logo.png"
        subprocess.run([exe, str(src), "--export-type=png", f"--export-filename={png}", "--export-width=1024"], check=True)
        src = png
    im = Image.open(src).convert("RGBA")
    a = np.asarray(im).copy()
    if a[..., 3].min() >= 250:                       # opaque: remove a plain background by flood-filling from the corners
        from collections import deque
        h, w = a.shape[:2]
        bg = a[0, 0, :3].astype(int); tol = 28
        seen = np.zeros((h, w), bool); dq = deque([(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)])
        while dq:
            y, x = dq.popleft()
            if seen[y, x] or np.abs(a[y, x, :3].astype(int) - bg).max() > tol:
                continue
            seen[y, x] = True; a[y, x, 3] = 0
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < h and 0 <= xx < w and not seen[yy, xx]:
                    dq.append((yy, xx))
        note = "background removed (flood fill from the corners)"
    else:
        note = "already transparent"
    out = Image.fromarray(a, "RGBA")
    out = out.crop(out.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox())
    if max(out.size) > 1024:
        out.thumbnail((1024, 1024), Image.LANCZOS)
    dst = p.parent / "logo.png"
    out.save(dst)
    b["logo"] = "logo.png"
    p.write_text(dump(b), encoding="utf-8")
    print(f"logo: {dst} {out.size[0]}x{out.size[1]} ({note}, trimmed)")


def cmd_font(bid, family):
    """Download an OFL font family from github.com/google/fonts (ofl/ folder only = SIL Open Font License)."""
    p = find(bid)
    b = parse(p.read_text(encoding="utf-8"))
    folder = re.sub(r"[^a-z0-9]", "", family.lower())
    api = f"https://api.github.com/repos/google/fonts/contents/ofl/{folder}"
    req = urllib.request.Request(api, headers={"User-Agent": "animation-studio"})
    try:
        items = json.loads(urllib.request.urlopen(req, timeout=30).read())
    except Exception:
        sys.exit(f"'{family}' is not in google/fonts/ofl (only OFL fonts are allowed). Use a system font instead.")
    names = [i["name"] for i in items]
    if "OFL.txt" not in names:
        sys.exit(f"'{family}' has no OFL.txt: not accepted")
    ttfs = [i for i in items if i["name"].endswith(".ttf") and "Italic" not in i["name"]]
    fd = p.parent / "fonts"; fd.mkdir(exist_ok=True)
    for i in ttfs[:1] + [x for x in items if x["name"] == "OFL.txt"]:
        urllib.request.urlretrieve(i["download_url"], fd / i["name"])
    f = fd / ttfs[0]["name"]
    if not font_is_ofl(f) and "OFL.txt" not in names:
        sys.exit("downloaded font does not declare the OFL: removed"); f.unlink()
    b["font"] = {"name": family, "file": f"fonts/{f.name}", "licence": "OFL-1.1"}
    p.write_text(dump(b), encoding="utf-8")
    print(f"font: {f} (SIL Open Font License; licence text saved as fonts/OFL.txt)")


def cmd_recolor(bid, style, out):
    """A copy of a style preset in the brand colours (primary = titles/boxes/plates, accent = highlights, secondary = second boxes)."""
    b = load(bid)
    c = b.get("colours") or {}
    src = (SKILL_DIR / "styles" / f"{style}.md").read_text(encoding="utf-8")
    m = re.search(r"```json\s*\n(.*?)\n```", src, re.S)
    st = json.loads(m.group(1))
    pal = st["palette"]
    pri, sec, acc = c.get("primary"), c.get("secondary"), c.get("accent")
    if pri:
        shade = lambda h, k: "#%02x%02x%02x" % tuple(max(0, min(255, int(v * k))) for v in _rgb(h))
        pal.update(text_bg=pri, shirt=[pri, acc or pri, sec or pri, pri], sky=[shade(pri, 1.6), shade(pri, 0.7)],
                   box=[acc or pri, sec or pri, acc or pri, sec or pri], box_text=pri, title="#ffffff", label=sec or "#e6e6e6")
        if "code_bg" in pal:
            pal["code_bg"] = shade(pri, 0.6)
    if acc:
        pal.update(accent=acc, highlight=acc, roof=acc)
        st.setdefault("captions", {})["highlight"] = acc
    if st.get("manim"):
        st["manim"].update({k: v for k, v in (("accent", acc), ("highlight", acc)) if v})
    if pri and st.get("captions", {}).get("box"):
        st["captions"]["box_color"] = pri
    st["name"] = f"{style}+{bid}"
    Path(out).write_text(f"# Style: {style} in the {b['name']} colours (generated by brand.py recolor)\n\n```json\n{json.dumps(st, indent=1)}\n```\n", encoding="utf-8")
    print(out)


# ---------------- overlays ----------------
def _font(b, size, bold=True):
    from PIL import ImageFont
    f = b.get("font") or {}
    if f.get("file"):
        fp = Path(b["_dir"]) / f["file"]
        if fp.exists() and font_is_ofl(fp):
            ft = ImageFont.truetype(str(fp), size)
            try:
                ft.set_variation_by_name("Bold" if bold else "Regular")
            except Exception:
                pass
            return ft
    sys.path.insert(0, str(SKILL_DIR / "engines" / "py2d"))
    from canvas import font
    return font(size, "bold" if bold else "regular")


def _rgb(h, default="#222222"):
    h = (h or default).lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lum(rgb):
    return (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) / 255


def contacts(b):
    """Contact lines, ONLY from the brand file (never invented)."""
    lines = []
    for p in b.get("phones") or []:
        num, _, label = p.partition("|")
        lines.append(("Call", num.strip() + (f"  ({label.strip()})" if label.strip() else "")))
    if b.get("whatsapp"):
        lines.append(("WhatsApp", b["whatsapp"].strip()))
    for e in (b.get("emails") or [])[:2]:
        lines.append(("Email", e))
    if b.get("website"):
        lines.append(("Web", re.sub(r"^https?://", "", b["website"]).rstrip("/")))
    return lines


def watermark_layer(b, W, H, safe, spec, scene_img):
    """Logo (or logo + name) in a corner inside the safe zone, with auto-contrast: a soft plate if the scene behind is too similar."""
    from PIL import Image, ImageDraw, ImageFilter, ImageStat
    corner, size, opacity, mode = spec
    logo = Image.open(Path(b["_dir"]) / b["logo"]).convert("RGBA")
    lh = int(min(W, H) * size / 100)
    logo = logo.resize((max(1, int(logo.width * lh / logo.height)), lh), Image.LANCZOS)
    name_img = None
    if mode == "logo+name":
        f = _font(b, int(lh * 0.42))
        tw = int(f.getlength(b["name"])) + 4
        name_img = Image.new("RGBA", (tw, int(lh * 0.6)), (0, 0, 0, 0))
        ImageDraw.Draw(name_img).text((0, name_img.height // 2), b["name"], font=f, fill=(255, 255, 255, 255), anchor="lm")
    gap = int(lh * 0.18)
    w = logo.width + (gap + name_img.width if name_img else 0)
    top, bottom, left, right = safe
    m = int(min(W, H) * 0.02)
    x = left + m if corner[1] == "l" else W - right - m - w
    y = top + m if corner[0] == "t" else H - bottom - m - lh
    region = scene_img.crop((x, y, x + w, y + lh)).convert("RGB")
    bg_l = sum(_lum(c) for c in [tuple(int(v) for v in ImageStat.Stat(region).mean)]) / 1
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fg_l = _lum(tuple(int(v) for v in ImageStat.Stat(logo.convert("RGB"), mask=logo.getchannel("A")).mean))
    need_plate = abs(fg_l - bg_l) < 0.28 or (name_img is not None and bg_l > 0.62)
    if need_plate:                                   # auto-contrast plate: dark on light scenes, light on dark ones
        pc = (12, 18, 24, 150) if bg_l > 0.45 else (245, 245, 245, 150)
        pad = int(lh * 0.14)
        plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(plate).rounded_rectangle([x - pad, y - pad, x + w + pad, y + lh + pad], radius=int(lh * 0.3), fill=pc)
        lay = Image.alpha_composite(lay, plate.filter(ImageFilter.GaussianBlur(2)))
        if name_img is not None and pc[0] > 128:     # name text must contrast with a light plate
            from PIL import ImageOps
            r, g, bb, a = name_img.split(); name_img = Image.merge("RGBA", (ImageOps.invert(r), ImageOps.invert(g), ImageOps.invert(bb), a))
    lay.alpha_composite(logo, (x, y))
    if name_img:
        lay.alpha_composite(name_img, (x + logo.width + gap, y + (lh - name_img.height) // 2))
    a = lay.getchannel("A").point(lambda v: int(v * opacity / 100))
    lay.putalpha(a)
    return lay, need_plate


def lower_third(b, W, H, safe, t, t0, t1, captions):
    """Brand bar with name + the main contact; slides in/out; sits above the caption band when captions are burned in."""
    from PIL import Image, ImageDraw
    if not (t0 - 0.01 <= t <= t1):
        return None
    k = min(1.0, (t - t0) / 0.35, (t1 - t) / 0.35)
    e = 1 - (1 - max(0.0, k)) ** 3
    top, bottom, left, right = safe
    u = min(W, H) / 1080
    bh = int(118 * u)
    band = int(H * 0.16) if captions else 0
    y = H - bottom - band - bh - int(18 * u)
    x0 = left + int(10 * u); x1 = W - right - int(10 * u)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    pri = _rgb((b.get("colours") or {}).get("primary"), "#1f2340"); acc = _rgb((b.get("colours") or {}).get("accent"), "#ffd166")
    slide = int((1 - e) * (x1 - x0))
    bar = tuple(min(255, int(v * 1.7 + 18)) for v in pri)    # lighter than the brand colour: stands out on brand-coloured scenes
    d.rounded_rectangle([x0 - slide, y, x1 - slide, y + bh], radius=int(16 * u), fill=bar + (240,), outline=acc + (255,), width=max(1, int(2 * u)))
    d.rectangle([x0 - slide, y, x0 - slide + int(10 * u), y + bh], fill=acc + (255,))
    logo = Image.open(Path(b["_dir"]) / b["logo"]).convert("RGBA")
    lh = int(bh * 0.78); logo = logo.resize((int(logo.width * lh / logo.height), lh), Image.LANCZOS)
    lay.alpha_composite(logo, (x0 - slide + int(22 * u), y + (bh - lh) // 2))
    tx = x0 - slide + int(22 * u) + logo.width + int(16 * u)
    cl = contacts(b)
    main = next((v for k_, v in cl if k_ == "WhatsApp"), None) or (cl[0][1] if cl else "")
    label = "WhatsApp " if any(k_ == "WhatsApp" for k_, _ in cl) else ""
    fn, fs = _font(b, int(44 * u)), _font(b, int(32 * u), bold=False)
    maxw = x1 - slide - tx - int(12 * u)
    name = b["name"]
    while fn.getlength(name) > maxw and len(name) > 4:
        name = name[:-2]
    d.text((tx, y + bh * 0.33), name, font=fn, fill=(255, 255, 255, 255), anchor="lm")
    d.text((tx, y + bh * 0.72), f"{label}{main}", font=fs, fill=acc + (255,), anchor="lm")
    return lay


def end_card(b, W, H, safe, cta, t):
    """End card in the brand colours: logo, name, tagline, CTA and contacts, measured first, then centred as one block
    inside the platform safe zone (shrunk if needed, so nothing is ever cut off)."""
    from PIL import Image, ImageDraw
    import numpy as np
    pri = _rgb((b.get("colours") or {}).get("primary"), "#1f2340"); acc = _rgb((b.get("colours") or {}).get("accent"), "#ffd166")
    sec = _rgb((b.get("colours") or {}).get("secondary"), "#cccccc")
    yy = np.linspace(0, 1, H)[:, None, None]
    arr = np.clip(np.array(pri, float) * 1.15 * (1 - yy) + np.array(pri, float) * 0.55 * yy, 0, 255).astype(np.uint8).repeat(W, axis=1)
    img = Image.fromarray(arr, "RGB").convert("RGBA"); d = ImageDraw.Draw(img)
    top, bottom, left, right = safe
    sw, sh = W - left - right, H - top - bottom
    cx = left + sw / 2
    portrait = H > W
    lines = contacts(b)
    e = min(1.0, t / 0.5); pop = 0.88 + 0.12 * (1 - (1 - e) ** 3)

    def layout(k):
        """Sizes for scale k; returns (items, total_height, widest)."""
        u = min(W, H) / 1080 * k
        items = [("logo", (360 if portrait else 230) * u)]
        items += [("name", 84 * u), ("gap", 18 * u)]
        if b.get("tagline"):
            items += [("tagline", 42 * u), ("gap", 30 * u)]
        if cta:
            items += [("cta", 92 * u), ("gap", 40 * u)]
        fl, fv = _font(b, int(34 * u), False), _font(b, int(42 * u))
        lw = max((fl.getlength(k_) for k_, _ in lines), default=0); vw = max((fv.getlength(v) for _, v in lines), default=0)
        items += [("contact", 62 * u)] * len(lines)
        widest = max(lw + 24 * u + vw, _font(b, int(84 * u)).getlength(b["name"]))
        return items, sum(h for _, h in items), widest, u, fl, fv, lw
    k = 1.25 if portrait else 1.0
    while True:
        items, total, widest, u, fl, fv, lw = layout(k)
        if (total <= sh * 0.94 and widest <= sw * 0.94) or k < 0.4:
            break
        k *= 0.94
    y = top + (sh - total) / 2
    block_w = lw + 24 * u + max((fv.getlength(v) for _, v in lines), default=0)
    col = cx - block_w / 2 + lw                               # label/value split, so the contact block is centred as a whole
    ci = 0
    for kind, h in items:
        if kind == "logo":
            logo = Image.open(Path(b["_dir"]) / b["logo"]).convert("RGBA")
            lh = int(h * 0.92 * pop); logo = logo.resize((int(logo.width * lh / logo.height), lh), Image.LANCZOS)
            img.alpha_composite(logo, (int(cx - logo.width / 2), int(y + (h - lh) / 2)))
        elif kind == "name":
            d.text((cx, y + h / 2), b["name"], font=_font(b, int(76 * u)), fill=(255, 255, 255, 255), anchor="mm")
        elif kind == "tagline":
            d.text((cx, y + h / 2), b["tagline"], font=_font(b, int(38 * u), False), fill=sec + (255,), anchor="mm")
        elif kind == "cta":
            f = _font(b, int(50 * u)); tw = f.getlength(cta)
            d.rounded_rectangle([cx - tw / 2 - 34 * u, y, cx + tw / 2 + 34 * u, y + h], radius=int(h / 2), fill=acc + (255,))
            d.text((cx, y + h / 2), cta, font=f, fill=pri + (255,), anchor="mm")
        elif kind == "contact":
            lab, val = lines[ci]; ci += 1
            a = min(1.0, max(0.0, (t - 0.25 - 0.08 * ci) / 0.3))
            d.text((col, y + h / 2), lab, font=fl, fill=acc + (int(255 * a),), anchor="rm")
            d.text((col + 24 * u, y + h / 2), val, font=fv, fill=(255, 255, 255, int(255 * a)), anchor="lm")
        y += h
    return img.convert("RGB")


def cmd_apply(bid, fin, fout, a):
    from PIL import Image
    b = load(bid)
    sys.path.insert(0, str(SKILL_DIR / "shared"))
    from formats import safe as fmt_safe
    fin, fout = Path(fin), Path(fout); fout.mkdir(parents=True, exist_ok=True)
    frames = sorted(fin.glob("f[0-9][0-9][0-9][0-9].jpg"))
    if not frames:
        sys.exit(f"no frames in {fin}")
    W, H = Image.open(frames[0]).size
    q = "preview" if min(W, H) < 1000 else "final"
    safe = fmt_safe(a.fmt, q)
    wm = None
    if a.watermark and a.watermark != "off":
        c, s_, o, m = (a.watermark.split(",") + ["tr", "10", "85", "logo"])[:4] if "," in a.watermark else ("tr", "10", "85", "logo")
        wm = (c, float(s_), float(o), m)
    lt = tuple(float(x) for x in a.lower_third.split(",")) if a.lower_third else None
    plates = 0; wm_cache = {}
    for i, f in enumerate(frames):
        t = i / a.fps
        img = Image.open(f).convert("RGBA")
        if wm:
            key = i // 15                             # re-check contrast twice a second (scenes change)
            if key not in wm_cache:
                wm_cache = {key: watermark_layer(b, W, H, safe, wm, img)}
                plates += wm_cache[key][1]; checks = locals().get("checks", 0) + 1
            layer, plated = wm_cache[key]
            img.alpha_composite(layer)
        if lt:
            l3 = lower_third(b, W, H, safe, t, lt[0], lt[1], a.captions)
            if l3 is not None:
                img.alpha_composite(l3)
        img.convert("RGB").save(fout / f.name, quality=92)
    n = len(frames)
    if a.end_card:
        for j in range(int(round(a.end_card * a.fps))):
            end_card(b, W, H, safe, a.cta or b.get("cta"), j / a.fps).save(fout / f"f{n + j:04d}.jpg", quality=92)
        n += int(round(a.end_card * a.fps))
    print(f"branded {len(frames)} frames" + (f" + {int(round(a.end_card * a.fps))} end-card frames" if a.end_card else "") +
          f" -> {fout} ({n / a.fps:.2f} s)." + (f" Watermark contrast plate needed on {plates} of {locals().get('checks', 0)} checks." if wm else "") +
          ("\nNOTE: the video is now longer: mix the audio with --seconds " + f"{n / a.fps:.2f}" if a.end_card else ""))


def main():
    utf8()
    import argparse
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); return
    c = a[0]
    if c == "list":
        print("| Brand | Where | Name | Contacts |\n|---|---|---|---|")
        for d in brand_dirs():
            for p in sorted(d.glob("*/brand.yaml")):
                b = parse(p.read_text(encoding="utf-8"))
                print(f"| {p.parent.name} | {'your brands' if d == brand_dirs()[0] else 'skill (sample)'} | {b.get('name')} | {len(contacts(dict(b, _dir=str(p.parent))))} |")
    elif c == "new":
        cmd_new(a[1])
    elif c == "set":
        cmd_set(a[1], a[2], a[3])
    elif c == "logo":
        cmd_logo(a[1], a[2])
    elif c == "font":
        cmd_font(a[1], a[2])
    elif c == "validate":
        rows = validate(load(a[1]))
        print("| Field | OK | Value |\n|---|---|---|")
        for k, ok, v in rows:
            print(f"| {k} | {'✅' if ok else '❌'} | {v} |")
        sys.exit(0 if all(r[1] for r in rows) else 1)
    elif c == "recolor":
        ap = argparse.ArgumentParser(); ap.add_argument("bid"); ap.add_argument("--style", required=True); ap.add_argument("--out", required=True)
        x = ap.parse_args(a[1:]); cmd_recolor(x.bid, x.style, x.out)
    elif c == "apply":
        ap = argparse.ArgumentParser()
        ap.add_argument("bid"); ap.add_argument("fin"); ap.add_argument("fout"); ap.add_argument("--fmt", default="9x16"); ap.add_argument("--fps", type=int, default=30)
        ap.add_argument("--watermark"); ap.add_argument("--lower-third"); ap.add_argument("--end-card", type=float); ap.add_argument("--cta")
        ap.add_argument("--captions", action="store_true")
        x = ap.parse_args(a[1:]); cmd_apply(x.bid, x.fin, x.fout, x)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
