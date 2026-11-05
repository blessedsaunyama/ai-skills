"""Shared core for doc-studio: spec loading, themes, brands, inline formatting and checks. Standard library only."""
import json, os, re, sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2]

PAGES_MM = {"A4": (210, 297), "A5": (148, 210), "LETTER": (215.9, 279.4), "LEGAL": (215.9, 355.6)}

# Each theme has a print palette (ink-saving, readable in black and white) and a screen palette (more colour).
THEMES = {
    "classic": {"heading_font": "Georgia", "body_font": "Calibri", "pdf_heading": "Times-Bold", "pdf_body": "Helvetica",
                "print": {"primary": "1F3A5F", "accent": "8A6D3B", "soft": "F2F2F2", "text": "1A1A1A", "muted": "666666"},
                "screen": {"primary": "1F4E8C", "accent": "C9822B", "soft": "EAF1FB", "text": "1A1A1A", "muted": "5A6270"}},
    "modern": {"heading_font": "Segoe UI Semibold", "body_font": "Segoe UI", "pdf_heading": "Helvetica-Bold", "pdf_body": "Helvetica",
               "print": {"primary": "222222", "accent": "0F6E6E", "soft": "F3F3F3", "text": "1A1A1A", "muted": "666666"},
               "screen": {"primary": "0B5CAD", "accent": "11A39B", "soft": "E8F4FF", "text": "17202A", "muted": "5A6270"}},
    "church": {"heading_font": "Georgia", "body_font": "Calibri", "pdf_heading": "Times-Bold", "pdf_body": "Helvetica",
               "print": {"primary": "3B2F5C", "accent": "8C6A1E", "soft": "F4F1EA", "text": "1A1A1A", "muted": "666666"},
               "screen": {"primary": "4B2E83", "accent": "C79A2E", "soft": "F6F0FF", "text": "1A1A1A", "muted": "5E5670"}},
    "school": {"heading_font": "Calibri", "body_font": "Calibri", "pdf_heading": "Helvetica-Bold", "pdf_body": "Helvetica",
               "print": {"primary": "1E4D2B", "accent": "7A4A00", "soft": "F2F5F2", "text": "1A1A1A", "muted": "666666"},
               "screen": {"primary": "1D7A3A", "accent": "E08A00", "soft": "EAF7EE", "text": "1A1A1A", "muted": "56635A"}},
    "minimal": {"heading_font": "Calibri Light", "body_font": "Calibri", "pdf_heading": "Helvetica-Bold", "pdf_body": "Helvetica",
                "print": {"primary": "111111", "accent": "555555", "soft": "F5F5F5", "text": "111111", "muted": "777777"},
                "screen": {"primary": "111111", "accent": "2F6FDE", "soft": "F4F6F8", "text": "111111", "muted": "6B7280"}},
}
PACK_THEME = {"sda": "church", "education": "school", "health": "modern", "tech": "modern", "business": "classic", "general": "classic"}
PACKS = ["general", "sda", "education", "health", "tech", "business"]
BLOCK_TYPES = {"heading", "paragraph", "bullets", "numbered", "verse", "egw", "quote", "callout", "table", "image",
               "question", "pagebreak", "summary", "toc"}


def utf8():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass


def user_dir():
    """Per-user data folder (brands live here, never inside the skill)."""
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "doc-studio"


# ---------------- brands ----------------
def brand_path(bid):
    for d in (user_dir() / "brands", SKILL_DIR / "examples" / "brands"):
        p = d / bid / "brand.json"
        if p.exists():
            return p
    return None


def load_brand(bid):
    if not bid:
        return None
    p = brand_path(bid)
    if not p:
        sys.exit(f"brand '{bid}' not found (python tools/brand.py list)")
    b = json.loads(p.read_text(encoding="utf-8"))
    if b.get("logo"):
        lp = p.parent / b["logo"]
        b["logo"] = str(lp) if lp.exists() else None
    return b


# ---------------- spec ----------------
def load_spec(path):
    path = Path(path)
    spec = json.loads(path.read_text(encoding="utf-8"))
    spec["_base"] = str(path.parent.resolve())
    spec.setdefault("pack", "general")
    spec.setdefault("language", "en")
    spec.setdefault("page", "A4")
    spec.setdefault("orientation", "portrait")
    spec.setdefault("style", "print")
    spec.setdefault("theme", PACK_THEME.get(spec["pack"], "classic"))
    spec.setdefault("blocks", [])
    spec.setdefault("references", [])
    spec.setdefault("credits", [])
    spec["_brand"] = load_brand(spec.get("brand"))
    return spec


def resolve(spec, p):
    """Image/file paths in a spec are relative to the spec file."""
    if not p:
        return None
    q = Path(p)
    return str(q if q.is_absolute() else Path(spec["_base"]) / q)


def palette(spec):
    t = THEMES.get(spec.get("theme"), THEMES["classic"])
    pal = dict(t["screen" if spec.get("style") == "screen" else "print"])
    b = spec.get("_brand") or {}
    for k in ("primary", "accent"):
        v = (b.get("colours") or {}).get(k)
        if v:
            pal[k] = v.lstrip("#").upper()
    fonts = {"heading": b.get("font") or t["heading_font"], "body": b.get("body_font") or t["body_font"],
             "pdf_heading": t["pdf_heading"], "pdf_body": t["pdf_body"]}
    return pal, fonts


def rgb(hexs):
    h = hexs.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def page_mm(spec):
    w, h = PAGES_MM.get(str(spec.get("page", "A4")).upper(), PAGES_MM["A4"])
    return (h, w) if spec.get("orientation") == "landscape" else (w, h)


# ---------------- inline formatting: **bold**, *italic*, [text](url) ----------------
_TOK = re.compile(r"(`[^`]+`|\*\*.+?\*\*|\*[^*\s][^*]*?\*|\[[^\]]+\]\([^)]+\))")
CODE = "\x00code"  # url value that marks an inline `code` run (renderers use a monospace font)


def runs(text):
    """Split text into (text, bold, italic, url) runs. url == CODE marks inline `code`."""
    out = []
    for part in _TOK.split(str(text or "")):
        if not part:
            continue
        if part.startswith("`") and part.endswith("`") and len(part) > 2:
            out.append((part[1:-1], False, False, CODE))
        elif part.startswith("**") and part.endswith("**") and len(part) > 4:
            out.append((part[2:-2], True, False, None))
        elif part.startswith("[") and "](" in part and part.endswith(")"):
            t, u = part[1:].split("](", 1)
            out.append((t, False, False, u[:-1]))
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            out.append((part[1:-1], False, True, None))
        else:
            out.append((part, False, False, None))
    return out


def plain(text):
    return "".join(r[0] for r in runs(text))


# ---------------- quiz helpers ----------------
LETTERS = "ABCDEFGH"


def questions(spec):
    return [b for b in spec["blocks"] if b.get("type") == "question"]


# ---------------- checks ----------------
def lint(spec):
    """Return (errors, warnings). Errors stop the build; warnings are shown to the user."""
    err, warn = [], []
    s = spec.get("summary") or {}
    if not (s.get("topic") and s.get("key_points") and s.get("takeaway")):
        err.append("summary needs topic, key_points and takeaway (every document opens with a SUMMARY block)")
    if not spec.get("references"):
        warn.append("no references: every document should end with its sources (or say 'No external sources used')")
    if spec["pack"] not in PACKS:
        err.append(f"pack must be one of {PACKS}")
    for i, b in enumerate(spec["blocks"]):
        t = b.get("type")
        if t not in BLOCK_TYPES:
            err.append(f"block {i}: unknown type '{t}'")
        if t == "image":
            p = resolve(spec, b.get("path"))
            if not p or not Path(p).exists():
                err.append(f"block {i}: image not found: {b.get('path')}")
            if not b.get("own") and not b.get("credit") and not any(c.get("image") == b.get("path") for c in spec["credits"]):
                warn.append(f"block {i}: image {b.get('path')} has no credit (add one, or set \"own\": true for the user's or AI-drawn images)")
        if t == "verse" and not (b.get("ref") and b.get("text")):
            err.append(f"block {i}: verse needs ref and text (fetched with bible_fetch.py)")
        if t == "egw" and not b.get("ref"):
            err.append(f"block {i}: egw quote needs its reference code")
        if t == "egw" and not b.get("verified"):
            warn.append(f"block {i}: EGW quote not verified, it will be printed as UNVERIFIED")
        if t == "question" and b.get("choices") and str(b.get("answer", "")).upper()[:1] not in LETTERS[:len(b["choices"])]:
            err.append(f"block {i}: question answer must be a letter A-{LETTERS[len(b['choices'])-1]}")
    txt = json.dumps(spec, ensure_ascii=False)
    n = txt.count("UNVERIFIED")
    if n:
        warn.append(f"{n} item(s) marked UNVERIFIED: tell the user")
    if spec["pack"] == "health" and not spec.get("disclaimer"):
        err.append("health pack: add a one-line 'disclaimer' (general information, not medical advice)")
    if spec["pack"] == "education" and "ADD YOUR" not in txt.upper():
        warn.append("education pack: no 'ADD YOUR ...' prompts found; flag where the student must add their own analysis")
    no_src = any("no external sources" in str(r.get("text", "")).lower() for r in spec["references"])
    if spec["pack"] in ("health", "education", "tech", "business") and not no_src and not any(r.get("url") or r.get("verified") for r in spec["references"]):
        warn.append("no reference has a url: references must be real and checkable")
    return err, warn


def _norm(s):
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", re.sub(r"\[\d+\]", "", s)).strip().lower()


def verify_quotes(spec, source_files):
    """Every verse/egw text must appear (word for word, ignoring case/spacing/punctuation at the ends) in the fetched sources.
    '...' may shorten a quote. Returns a list of (ref, ok)."""
    lines = []
    for f in source_files:
        for ln in Path(f).read_text(encoding="utf-8").splitlines():
            # drop bible_fetch.py verse labels ("John 3:16 (KJV)  ...") so multi-verse quotes match across verses
            lines.append(re.sub(r"^\s*(?:[1-3] )?[A-Za-z][A-Za-z ]*? \d+:\d+(?:-\d+)? \([A-Z0-9]+\)\s+", "", ln))
    src = _norm(" ".join(lines))
    src_flat = re.sub(r"[^a-z0-9' ]+", " ", src)
    src_flat = re.sub(r"\s+", " ", src_flat)
    res = []
    for b in spec["blocks"]:
        if b.get("type") not in ("verse", "egw"):
            continue
        q = _norm(plain(b.get("text", "")))
        ok = True
        for part in re.split(r"\.\.\.|…", q):
            part = re.sub(r"\s+", " ", re.sub(r"[^a-z0-9' ]+", " ", part)).strip()
            if part and part not in src_flat:
                ok = False
        res.append((b.get("ref"), ok))
    return res
