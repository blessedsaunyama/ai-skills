#!/usr/bin/env python3
"""Captions from the voice timing: an .srt (always) + a styled .ass for burning in (per style and format).

  python shared/captions.py WORK_DIR OUT_BASE --style NAME --fmt 9x16 [--quality final] [--pos bottom|middle|top] [--max-words N]
    WORK_DIR   folder with words.json (from shared/voice.py --timing or shared/timing.py)
    OUT_BASE   e.g. out/My-Video  ->  out/My-Video.srt  and  out/My-Video_9x16.ass
Then burn in: python shared/finish.py FRAMES OUT.mp4 --audio mix.wav --ass out/My-Video_9x16.ass
The look (font size, colours, outline or box, CAPS, words per caption) comes from the style preset's "captions" block.
Words light up in the highlight colour as they are spoken (karaoke). Text stays inside the platform safe zone.
Standard library only.
"""
import json, os, re, sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import OS, SKILL_DIR, utf8  # noqa: E402
from formats import safe, size  # noqa: E402

DEFAULT = {"size": 60, "color": "#ffffff", "highlight": "#ffd25a", "outline": "#000000", "outline_w": 4, "box": False,
           "box_color": "#000000", "upper": False, "max_words": 4}


def style_caps(name):
    p = Path(name) if str(name).endswith(".md") and Path(name).exists() else SKILL_DIR / "styles" / f"{name}.md"
    m = re.search(r"```json\s*\n(.*?)\n```", p.read_text(encoding="utf-8"), re.S)
    return {**DEFAULT, **json.loads(m.group(1)).get("captions", {})}


def cues(words, max_words, max_dur=3.2):
    out, cur = [], []
    for w in words:
        cur.append(w)
        end_here = re.search(r"[.!?;:,][\"”']?$", w["w"]) or len(cur) >= max_words or (cur[-1]["e"] - cur[0]["s"]) > max_dur
        if end_here:
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return out


def ts_srt(t):
    h, r = divmod(max(0.0, t), 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


def ts_ass(t):
    h, r = divmod(max(0.0, t), 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def ass_col(hexc, alpha=0):
    h = hexc.lstrip("#")
    return f"&H{alpha:02X}{h[4:6]}{h[2:4]}{h[0:2]}".upper()


def main():
    utf8()
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__); sys.exit(1)
    opt = lambda n, d=None: a[a.index(n) + 1] if n in a else d
    work, base = Path(a[0]), Path(a[1])
    words = json.loads((work / "words.json").read_text(encoding="utf-8"))
    cap = style_caps(opt("--style", "flat-2d"))
    fmt, q = opt("--fmt", "9x16"), opt("--quality", "final")
    mw = int(opt("--max-words", cap["max_words"]))
    groups = cues(words, mw)
    base.parent.mkdir(parents=True, exist_ok=True)
    clean = lambda s: s.strip()
    # ---- .srt (plain, always) ----
    srt = []
    for i, g in enumerate(groups, 1):
        srt.append(f"{i}\n{ts_srt(g[0]['s'])} --> {ts_srt(g[-1]['e'] + 0.15)}\n{' '.join(clean(w['w']) for w in g)}\n")
    Path(f"{base}.srt").write_text("\n".join(srt), encoding="utf-8")
    # ---- .ass (styled, for burning in) ----
    W, H = size(fmt, q)
    k = min(W, H) / 1080
    top, bottom, left, right = safe(fmt, q)
    pos = opt("--pos", "bottom")
    align = {"bottom": 2, "middle": 5, "top": 8}[pos]
    margin_v = int((bottom if pos == "bottom" else top) + 30 * k)
    font = "Arial" if OS in ("win", "mac") else "DejaVu Sans"
    box = cap["box"]
    border = 3 if box else 1
    outline = int(round((14 if box else cap["outline_w"]) * k))
    oc = cap["box_color"] if box else cap["outline"]
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{font},{int(cap['size'] * k)},{ass_col(cap['highlight'])},{ass_col(cap['color'])},{ass_col(oc, 0x20 if box else 0)},{ass_col('#000000', 0x80)},-1,0,0,0,100,100,0,0,{border},{outline},0,{align},{int(left + 20 * k)},{int(right + 20 * k)},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for g in groups:
        s0, e0 = g[0]["s"], g[-1]["e"] + 0.15
        parts, t = [], s0
        for w in g:
            gap = max(0, w["s"] - t)
            if gap > 0.01:
                parts.append(f"{{\\k{int(round(gap * 100))}}}")
            txt = clean(w["w"]).upper() if cap["upper"] else clean(w["w"])
            parts.append(f"{{\\k{max(1, int(round((w['e'] - w['s']) * 100)))}}}{txt} ")
            t = w["e"]
        ev.append(f"Dialogue: 0,{ts_ass(s0)},{ts_ass(e0)},Cap,,0,0,0,,{''.join(parts).rstrip()}")
    ass = Path(f"{base}_{fmt}.ass")
    ass.write_text(head + "\n".join(ev) + "\n", encoding="utf-8")
    print(f"{base}.srt  ({len(groups)} captions)\n{ass}  (burn in with finish.py --ass)")


if __name__ == "__main__":
    main()
