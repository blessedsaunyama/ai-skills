"""Palettes, font pairings, styles, colour helpers and date formatting."""
import datetime as _dt

# Each palette: bg, bg2 (gradient end), title, accent, text, muted, band (contact bar), on_band
PALETTES = {
    "youthful":  {"bg": "#24084F", "bg2": "#7A1FA2", "title": "#FFFFFF", "accent": "#FFC727", "text": "#F3ECFF", "muted": "#C9B6EA", "band": "#FFC727", "on_band": "#24084F", "pop": "#FF3D8B"},
    "modern":    {"bg": "#0B1F3A", "bg2": "#12355E", "title": "#FFFFFF", "accent": "#18C3B0", "text": "#E6EEF7", "muted": "#9FB3CC", "band": "#18C3B0", "on_band": "#0B1F3A", "pop": "#5EE6D5"},
    "formal":    {"bg": "#14213D", "bg2": "#1F3360", "title": "#F7F1E1", "accent": "#C9A227", "text": "#EDE6D3", "muted": "#B8AE95", "band": "#C9A227", "on_band": "#14213D", "pop": "#E6C65C"},
    "elegant":   {"bg": "#F8F4EE", "bg2": "#EFE6DA", "title": "#2B2B2B", "accent": "#A8636E", "text": "#3A3A3A", "muted": "#7D7368", "band": "#2B2B2B", "on_band": "#F8F4EE", "pop": "#C9A227"},
    "warm":      {"bg": "#3D0C11", "bg2": "#B3261E", "title": "#FFFFFF", "accent": "#FFB000", "text": "#FFEFE3", "muted": "#F2B8A0", "band": "#FFB000", "on_band": "#3D0C11", "pop": "#FF7A00"},
    "fresh":     {"bg": "#0F3D2E", "bg2": "#1F6F50", "title": "#FFFFFF", "accent": "#B6E35C", "text": "#E8F5EC", "muted": "#A9CDB7", "band": "#B6E35C", "on_band": "#0F3D2E", "pop": "#FFE066"},
    "royal":     {"bg": "#0E1E5B", "bg2": "#1D3C8F", "title": "#FFFFFF", "accent": "#F2B705", "text": "#E7ECFA", "muted": "#AAB7E0", "band": "#F2B705", "on_band": "#0E1E5B", "pop": "#FFD84D"},
    "tech":      {"bg": "#0D1117", "bg2": "#161B22", "title": "#FFFFFF", "accent": "#2F81F7", "text": "#E6EDF3", "muted": "#8B949E", "band": "#2F81F7", "on_band": "#FFFFFF", "pop": "#3FB950"},
    "light":     {"bg": "#FFFFFF", "bg2": "#EEF3F8", "title": "#0B1F3A", "accent": "#E4572E", "text": "#1E2A38", "muted": "#5B6B7C", "band": "#0B1F3A", "on_band": "#FFFFFF", "pop": "#FFC914"},
}

# pairing key -> (display family, display weight, body family, body weight, bold body weight, uppercase titles?)
PAIRINGS = {
    "montserrat-opensans": ("Montserrat", 800, "Open Sans", 400, 600, True),
    "playfair-lato":       ("Playfair Display", 700, "Lato", 400, 700, False),
    "bebas-poppins":       ("Bebas Neue", 400, "Poppins", 400, 600, True),
}

STYLES = {
    # style: (default palette, default pairing, decoration)
    "youthful": ("youthful", "bebas-poppins", "orbs"),
    "modern":   ("modern", "montserrat-opensans", "rings"),
    "formal":   ("formal", "playfair-lato", "border"),
    "elegant":  ("elegant", "playfair-lato", "arcs"),
}

MOOD_WORDS = {  # free-text mood -> palette
    "fun": "youthful", "party": "youthful", "music": "youthful", "bright": "warm", "sunset": "warm",
    "church": "royal", "worship": "royal", "classy": "elegant", "wedding": "elegant", "nature": "fresh",
    "green": "fresh", "tech": "tech", "dark": "tech", "clean": "light", "white": "light", "gold": "formal",
}


def hex_rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_hex(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(c))) for c in rgb)


def mix(a, b, t):
    ra, rb = hex_rgb(a), hex_rgb(b)
    return rgb_hex([ra[i] + (rb[i] - ra[i]) * t for i in range(3)])


def luminance(h):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = hex_rgb(h)
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def readable_on(bg, preferred, minimum=4.5):
    """preferred if it reads on bg, else black/white whichever is better."""
    if contrast(bg, preferred) >= minimum:
        return preferred
    return "#FFFFFF" if contrast(bg, "#FFFFFF") >= contrast(bg, "#111111") else "#111111"


def palette_from_brand(colors, dark=True):
    """Build a palette from 1-3 brand colours (first = main)."""
    main = colors[0]
    acc = colors[1] if len(colors) > 1 else ("#FFC727" if luminance(main) < 0.4 else "#14213D")
    pop = colors[2] if len(colors) > 2 else acc
    if luminance(main) < 0.35 or dark:
        bg = main if luminance(main) < 0.35 else mix(main, "#000000", 0.55)
        return {"bg": bg, "bg2": mix(bg, "#FFFFFF", 0.15), "title": "#FFFFFF", "accent": acc, "text": mix("#FFFFFF", bg, 0.08),
                "muted": mix("#FFFFFF", bg, 0.35), "band": acc, "on_band": readable_on(acc, bg), "pop": pop}
    return {"bg": "#FFFFFF", "bg2": mix(main, "#FFFFFF", 0.85), "title": main, "accent": acc, "text": "#1E2A38",
            "muted": "#5B6B7C", "band": main, "on_band": readable_on(main, "#FFFFFF"), "pop": pop}


def resolve(spec):
    """Return (palette dict, pairing tuple, decoration) from a design spec."""
    style = spec.get("style", "modern")
    pal_key, pair_key, deco = STYLES.get(style, STYLES["modern"])
    p = spec.get("palette")
    if isinstance(p, dict):
        pal = dict(PALETTES[pal_key], **p)
    elif isinstance(p, list):
        pal = palette_from_brand(p, dark=spec.get("dark", True))
    elif isinstance(p, str):
        pal = dict(PALETTES[MOOD_WORDS.get(p, p)] if MOOD_WORDS.get(p, p) in PALETTES else PALETTES[pal_key])
    else:
        pal = dict(PALETTES[pal_key])
    for k in ("title", "text"):
        pal[k] = readable_on(pal["bg"], pal[k], 4.5 if k == "text" else 3.0)
    pair = PAIRINGS[spec.get("fonts", pair_key)]
    return pal, pair, spec.get("decoration", deco)


# ---------- dates (English, Shona, Ndebele) ----------
MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    "sn": ["Ndira", "Kukadzi", "Kurume", "Kubvumbi", "Chivabvu", "Chikumi", "Chikunguru", "Nyamavhuvhu", "Gunyana", "Gumiguru", "Mbudzi", "Zvita"],
    "nd": ["uMasingana", "uNhlolanja", "uNdasa", "uMbasa", "uNkwenkwezi", "uNhlangulana", "uNtulikazi", "uNcwabakazi", "uMpandula", "uMfumfu", "uLwezi", "uZibandlela"],
}
DAYS = {  # Monday first (Python weekday())
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "sn": ["Muvhuro", "Chipiri", "Chitatu", "China", "Chishanu", "Mugovera", "Svondo"],
    "nd": ["uMvulo", "uLwesibili", "uLwesithathu", "uLwesine", "uLwesihlanu", "uMgqibelo", "iSonto"],
}


def format_date(iso, lang="en", short=False):
    """ISO date (2026-11-21) -> 'Saturday 21 November 2026'. Any other text is used exactly as written."""
    try:
        d = _dt.date.fromisoformat(str(iso))
    except ValueError:
        return str(iso)
    lang = lang if lang in MONTHS else "en"
    if short:
        day = DAYS[lang][d.weekday()]
        mon = MONTHS[lang][d.month - 1]
        if lang == "en":
            day, mon = day[:3], mon[:3]
        return f"{day} {d.day} {mon} {d.year}"
    return f"{DAYS[lang][d.weekday()]} {d.day} {MONTHS[lang][d.month - 1]} {d.year}"


def format_time(start, end=None, fmt="12h"):
    """'09:00' -> '9 AM'. Any other text (e.g. '9am till late') is used exactly as written."""
    def one(t):
        try:
            h, m = (int(x) for x in str(t).split(":"))
        except ValueError:
            return str(t)
        if fmt == "24h":
            return f"{h:02d}:{m:02d}"
        suf = "AM" if h < 12 else "PM"
        h12 = h % 12 or 12
        return f"{h12}:{m:02d} {suf}" if m else f"{h12} {suf}"
    return one(start) + (f" – {one(end)}" if end else "")
