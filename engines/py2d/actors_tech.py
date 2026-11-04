"""Engine A actors for explainers and modern stories: code, terminal, title, box, arrow, bubble, text, house.

Placement: either world units ("x", "y", "w") like other actors, or screen-anchored with
"screen": [fx, fy] (0-1 inside the format's SAFE area) and "w" as a fraction of the safe width.
Screen-anchored items stay put when the camera moves, and adapt to every format.
"""
import math, re

from canvas import ellipse_pts, font, mix, rgb, scale, val

KEYWORDS = set("""False None True and as assert async await break class continue def del elif else except finally for from global if
import in is lambda nonlocal not or pass raise return try while with yield const let var function new this typeof instanceof
switch case default do of export extends static interface type enum public private protected void null undefined fn pub mut
impl struct use match loop""".split())
BUILTINS = set("print len range list dict set str int float input open sum min max sorted enumerate zip map filter console log".split())
TOKEN = re.compile(r"(#.*$|//.*$)|(\"[^\"]*\"|'[^']*'|`[^`]*`)|(\b\d+(?:\.\d+)?\b)|([A-Za-z_]\w*)|(\s+)|(.)")


def fv(cv, el, key, default=None):
    """Per-format override: "screen_16x9" beats "screen" when rendering 16x9."""
    return el.get(f"{key}_{getattr(cv, 'fmt', '')}", el.get(key, default))


def place(cv, el, default_w=0.8):
    """Centre (px, supersampled) and width (px) of a screen- or world-anchored item."""
    ss = cv.ss
    top, bottom, left, right = cv.safe
    if fv(cv, el, "screen") is not None:
        fx, fy = val(fv(cv, el, "screen"), cv.t)
        sw, sh = (cv.W - left - right), (cv.H - top - bottom)
        fl = el.get("float", cv.style.get("fx", {}).get("float", 0)) * cv.u     # gentle idle drift: the frame never sits dead still
        dy = fl * math.sin(cv.t * 1.3 + (fx * 5 + fy * 3)) if fl else 0
        return (left + fx * sw) * ss, (top + fy * sh) * ss + dy, fv(cv, el, "w", default_w) * sw * ss
    x, y = val(el.get("x", 0), cv.t), val(el.get("y", 0), cv.t)
    px, py = cv.P(x, y)
    return px, py, el.get("w", 6) * cv.k


def rrect(cv, box, r, fill, outline=None, lw=0):
    cv.d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=int(lw) if outline else 0)


def tokens(line):
    out = []
    for m in TOKEN.finditer(line):
        com, st, num, word, ws, other = m.groups()
        if com:
            out.append((com, "code_com"))
        elif st:
            out.append((st, "code_str"))
        elif num:
            out.append((num, "code_num"))
        elif word:
            nxt = line[m.end():m.end() + 1]
            kind = "code_kw" if word in KEYWORDS else ("code_fn" if word in BUILTINS or nxt == "(" else "code_text")
            out.append((word, kind))
        else:
            out.append((ws or other, "code_text"))
    return out


def code(cv, el, t, seed):
    lines = el["lines"]
    cx, cy, wpx = place(cv, el)
    maxc = max(24, max(len(l) for l in lines) + 2)
    fpx = wpx / (maxc * 0.6)
    f = font(fpx, "mono")
    lh = fpx * 1.45
    bar = fpx * 1.6
    h = bar + lh * len(lines) + fpx * 1.0
    x0, y0 = cx - wpx / 2, cy - h / 2
    rad = fpx * 0.7
    out = cv.c("ink") if cv.outline else None
    rrect(cv, [x0, y0, x0 + wpx, y0 + h], rad, cv.c("code_bg"), out, cv.lw)
    rrect(cv, [x0, y0, x0 + wpx, y0 + bar], rad, cv.c("code_bar"))
    cv.d.rectangle([x0, y0 + bar - rad, x0 + wpx, y0 + bar], fill=cv.c("code_bar"))
    for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        r = fpx * 0.3
        cx_, cy_ = x0 + fpx * (1.0 + i * 0.95), y0 + bar / 2
        cv.d.ellipse([cx_ - r, cy_ - r, cx_ + r, cy_ + r], fill=rgb(c))
    if el.get("label"):                                    # language + version, always visible (tech pack rule)
        cv.d.text((x0 + wpx - fpx * 0.8, y0 + bar / 2), el["label"], font=font(fpx * 0.8, "regular"), fill=cv.c("code_com"), anchor="rm")
    total = sum(len(l) for l in lines)
    ty = el.get("typing")
    if not ty:
        shown = total
    elif isinstance(ty[0], list):                      # keyframes [[t, chars], ...]: type line by line in sync with the voice
        shown = int(val(ty, t, "linear"))
    else:
        shown = int(total * max(0.0, min(1.0, (t - ty[0]) / max(1e-6, ty[1] - ty[0]))))
    ty_end = ty[-1][0] if ty and isinstance(ty[0], list) else (ty[1] if ty else 0)
    hl = val(el.get("highlight"), t, "linear", None) if el.get("highlight") else None
    if isinstance(el.get("highlight"), list) and el["highlight"] and isinstance(el["highlight"][0], list):
        hl = None
        for tt, idx in el["highlight"]:
            if t >= tt:
                hl = idx
    left = 0
    caret = None
    for i, line in enumerate(lines):
        ly = y0 + bar + fpx * 0.5 + lh * i
        if hl == i:
            cv.d.rectangle([x0 + 2, ly - lh * 0.08, x0 + wpx - 2, ly + lh * 0.92], fill=mix(cv.c("code_bg"), cv.c("highlight"), 0.18))
        xx = x0 + fpx * 1.0
        budget = max(0, shown - left)
        for txt, kind in tokens(line):
            if budget <= 0:
                break
            part = txt[:budget]
            cv.d.text((xx, ly + lh * 0.42), part, font=f, fill=cv.c(kind), anchor="lm")
            xx += f.getlength(part); budget -= len(part)
        if left <= shown <= left + len(line):
            caret = (xx, ly)
        left += len(line)
    if ty and caret and (t < ty_end + 0.8) and int(t * 2.5) % 2 == 0:
        cv.d.rectangle([caret[0] + 2, caret[1] + lh * 0.1, caret[0] + fpx * 0.55, caret[1] + lh * 0.8], fill=cv.c("code_text"))


def terminal(cv, el, t, seed):
    items = el["lines"]                     # [{"t": 2.0, "text": "python lists.py", "prompt": true}, {"t": 2.6, "text": "3"}]
    cx, cy, wpx = place(cv, el, 0.7)
    rows = max(2, len(items))
    maxc = max(28, max(len(i["text"]) + 4 for i in items))
    fpx = wpx / (maxc * 0.6)
    f = font(fpx, "mono")
    lh = fpx * 1.45; bar = fpx * 1.4
    h = bar + lh * rows + fpx * 0.8
    x0, y0 = cx - wpx / 2, cy - h / 2
    out = cv.c("ink") if cv.outline else None
    rrect(cv, [x0, y0, x0 + wpx, y0 + h], fpx * 0.6, cv.c("term_bg"), out, cv.lw)
    cv.d.text((x0 + wpx / 2, y0 + bar / 2), el.get("title", "Terminal"), font=font(fpx * 0.75, "regular"), fill=cv.c("code_com"), anchor="mm")
    for i, it in enumerate(items):
        if t < it["t"]:
            break
        ly = y0 + bar + fpx * 0.3 + lh * i + lh * 0.45
        xx = x0 + fpx * 0.9
        txt = it["text"]
        if it.get("prompt"):
            cv.d.text((xx, ly), "$ ", font=f, fill=cv.c("term_prompt"), anchor="lm"); xx += f.getlength("$ ")
            n = int(len(txt) * min(1.0, (t - it["t"]) / 0.6))
            txt = txt[:n]
        cv.d.text((xx, ly), txt, font=f, fill=cv.c("term_text"), anchor="lm")


def title(cv, el, t, seed):
    cx, cy, wpx = place(cv, el, 0.9)
    size = el.get("size", 78) * cv.u
    col = cv.c(el.get("color", "title"))
    lines = el["text"].split("\n")
    lh = size * 1.15
    y = cy - lh * (len(lines) - 1) / 2
    if el.get("box"):
        f = font(size)
        bw = max(f.getlength(s) for s in lines) + size * 1.2
        rrect(cv, [cx - bw / 2, y - lh * 0.75, cx + bw / 2, y + lh * (len(lines) - 0.25)], size * 0.35, cv.c(el["box"]))
    for s in lines:
        cv.d.text((cx, y), s, font=font(size), fill=col, anchor="mm"); y += lh
    if el.get("sub"):
        cv.d.text((cx, y - lh * 0.2 + size * 0.2), el["sub"], font=font(size * 0.45, "regular"), fill=scale(col, 0.85) if sum(col) > 300 else mix(col, "#888888", 0.4), anchor="mm")


def box(cv, el, t, seed):
    if fv(cv, el, "screen") is not None:
        cx, cy, wpx = place(cv, el, 0.3)
        hpx = fv(cv, el, "h", 0.12) * (cv.H - cv.safe[0] - cv.safe[1]) * cv.ss
    else:
        x, y = val(el["x"], t), val(el["y"], t)
        cx, cy = cv.P(x, y); wpx, hpx = el.get("w", 3) * cv.k, el.get("h", 1.5) * cv.k
    fill = cv.c(el.get("color", "box:0"))
    if val(el.get("glow", 0), t) > 0:
        g = val(el["glow"], t)
        rrect(cv, [cx - wpx / 2 - 10 * cv.u * g, cy - hpx / 2 - 10 * cv.u * g, cx + wpx / 2 + 10 * cv.u * g, cy + hpx / 2 + 10 * cv.u * g],
              hpx * 0.3, cv.c("highlight"))
    rrect(cv, [cx - wpx / 2, cy - hpx / 2, cx + wpx / 2, cy + hpx / 2], min(wpx, hpx) * 0.22, fill, cv.c("ink") if cv.outline else None, cv.lw)
    if el.get("label"):
        size = el.get("size", min(hpx * 0.38, wpx / max(4, len(el["label"])) * 1.6) / cv.u)
        tc = cv.c(el.get("text_color", "box_text"))
        cv.d.text((cx, cy), el["label"], font=font(size * cv.u, el.get("font", "bold")), fill=tc, anchor="mm")


def arrow(cv, el, t, seed):
    (x0, y0), (x1, y1) = el["from"], el["to"]
    gr = el.get("grow")
    u = 1.0 if not gr else max(0.0, min(1.0, (t - gr[0]) / max(1e-6, gr[1] - gr[0])))
    if u <= 0:
        return
    xe, ye = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
    col = el.get("color", "ink")
    w = el.get("width", 5)
    cv.stroke([(x0, y0), (xe, ye)], col, w, seed)
    ang = math.atan2(ye - y0, xe - x0)
    hl = el.get("head", 0.35)
    pts = [(xe, ye), (xe - hl * math.cos(ang - 0.45), ye - hl * math.sin(ang - 0.45)), (xe - hl * math.cos(ang + 0.45), ye - hl * math.sin(ang + 0.45))]
    cv.fill(pts, col, line=False, seed=seed)


def bubble(cv, el, t, seed):
    tip = cv.P(*val(el["at"], t))            # where the tail points (e.g. a speaker's mouth), world units
    size = el.get("size", 40) * cv.u
    f = font(size, "regular")
    lines = el["text"].split("\n")
    tw = max(f.getlength(s) for s in lines) + size * 1.2
    th = size * 1.3 * len(lines) + size * 0.8
    side = el.get("side", 1)
    bx = tip[0] + side * size * 0.6 - (tw if side < 0 else 0)
    by = tip[1] - th - size * 1.4
    fill = cv.c(el.get("color", "paper")) if el.get("color") else (255, 255, 255)
    ol = cv.c("ink")
    lw = max(2, int(cv.lw)) if cv.outline else max(2, int(2 * cv.u))
    tail = [(tip[0], tip[1]), (bx + (tw * 0.25 if side > 0 else tw * 0.75) - size * 0.3, by + th - 1), (bx + (tw * 0.25 if side > 0 else tw * 0.75) + size * 0.3, by + th - 1)]
    cv.d.polygon(tail, fill=fill, outline=ol, width=lw)
    rrect(cv, [bx, by, bx + tw, by + th], size * 0.6, fill, ol, lw)
    cv.d.polygon([(tail[0][0], tail[0][1] - lw * 1.5), (tail[1][0] + lw, tail[1][1] - lw), (tail[2][0] - lw, tail[2][1] - lw)], fill=fill)
    yy = by + size * 0.4 + size * 0.65
    for s in lines:
        cv.d.text((bx + tw / 2, yy), s, font=f, fill=ol, anchor="mm"); yy += size * 1.3


def text(cv, el, t, seed):
    if fv(cv, el, "screen") is not None:
        cx, cy, _ = place(cv, el)
    else:
        cx, cy = cv.P(*val(el["at"], t))
    cv.d.text((cx, cy), el["text"], font=font(el.get("size", 40) * cv.u, el.get("font", "bold")), fill=cv.c(el.get("color", "label")), anchor=el.get("anchor", "mm"))


def house(cv, el, t, seed):
    x, w, h = el.get("x", 0), el.get("w", 4), el.get("h", 3)
    y = el.get("y", 0)
    wall, roof = cv.c(el.get("wall", "wall")), cv.c(el.get("roof", "roof"))
    if el.get("flat_roof"):                                 # Ancient Near East: flat roof with a low parapet
        cv.fill([(x - w / 2, y), (x + w / 2, y), (x + w / 2, y + h), (x - w / 2, y + h)], wall, seed=seed)
        cv.fill([(x - w / 2 - 0.1, y + h), (x + w / 2 + 0.1, y + h), (x + w / 2 + 0.1, y + h + 0.25), (x - w / 2 - 0.1, y + h + 0.25)], scale(wall, 0.85), seed=seed + 1)
    else:
        cv.fill([(x - w / 2, y), (x + w / 2, y), (x + w / 2, y + h), (x - w / 2, y + h)], wall, seed=seed)
        cv.fill([(x - w / 2 - 0.35, y + h), (x + w / 2 + 0.35, y + h), (x, y + h + h * 0.55)], roof, seed=seed + 1)
    dw = min(0.9, w * 0.22)
    cv.fill([(x - dw / 2, y), (x + dw / 2, y), (x + dw / 2, y + 1.7), (x - dw / 2, y + 1.7)], scale(roof, 0.7) if not el.get("flat_roof") else rgb("#6a4a32"), seed=seed + 2)
    for k in (-1, 1):
        wx = x + k * w * 0.3
        cv.fill([(wx - 0.4, y + h * 0.55), (wx + 0.4, y + h * 0.55), (wx + 0.4, y + h * 0.55 + 0.7), (wx - 0.4, y + h * 0.55 + 0.7)], cv.c("window"), seed=seed + 3 + k)


DRAW_TECH = {"code": code, "terminal": terminal, "title": title, "box": box, "arrow": arrow, "bubble": bubble, "text": text, "house": house}
