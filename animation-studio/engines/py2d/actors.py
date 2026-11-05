"""Engine A actors. Each draw function takes (cv, el, t, seed) and reads colours/lines from the style preset.

Element types (scene.json "elements", drawn in order):
  sky, sun, clouds, hills, ground, tree, ark, person, animal, bird, rain, caption, clip (children)
Any numeric property may be keyframes: [[t, value], ...]. Positions are world units (y up, ground = 0).
"""
import math, random, textwrap

from canvas import ellipse_pts, mix, rgb, scale, val


def soft(cv):
    return cv.style.get("fill") == "soft"


def lbegin(cv):
    """Actors draw into their own layer when the style shades them (storybook, modern vector) or casts shadows."""
    on = cv.style.get("fill") in ("soft", "gradient") or cv.style["fx"].get("shadow", 0) > 0
    if on:
        cv.begin()
    return on


def lend(cv, on, k=1.0, blur=0.3):
    if on:
        cv.end(shade=cv.style.get("shade", 0) * k, blur=blur if soft(cv) else 0, shadow=cv.style["fx"].get("shadow", 0))


def stick(cv):
    return cv.style.get("body") == "stick"


def fillc(cv, name):
    """In the stickman style every body fill is paper; colour lives in the ink."""
    return cv.c("paper") if stick(cv) else cv.c(name)


def floor_y(floor, x):
    if not floor:
        return 0.0
    if x <= floor[0][0]:
        return floor[0][1]
    for (x0, y0), (x1, y1) in zip(floor, floor[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / max(1e-9, x1 - x0)
    return floor[-1][1]


def walk_state(el, t, size):
    """Position + walk phase from x keyframes (distance travelled drives the legs)."""
    x = val(el.get("x", 0), t, "linear")
    xa, xb = val(el.get("x", 0), t - 0.05, "linear"), val(el.get("x", 0), t + 0.05, "linear")
    moving = abs(xb - xa) > 0.004
    phase = (x / (0.55 * size)) * math.pi + el.get("phase", 0)
    y = floor_y(el.get("floor"), x) + val(el.get("y", 0), t)
    return x, y, phase, moving, (1 if xb >= xa else -1) if moving else el.get("facing", 1)


# ---------------- background ----------------
def sky(cv, el, t, seed):
    p = cv.pal
    s = cv.storm
    cv.sky(mix(p["sky"][0], p["storm_sky"][0], s), mix(p["sky"][1], p["storm_sky"][1], s))


def sun(cv, el, t, seed):
    if cv.storm > 0.9:
        return
    x, y, r, par = el.get("x", 0), el.get("y", 20), el.get("r", 1.6), el.get("par", 0.1)
    skyc = mix(cv.pal["sky"][1], cv.pal["storm_sky"][1], cv.storm)
    fade = 1 - cv.storm / 0.9
    for i, k in enumerate((2.4, 1.8, 1.35)):
        cv.circle(x, y, r * k, mix(skyc, cv.c("sun"), (0.18 + 0.12 * i) * fade), line=False, par=par)
    cv.circle(x, y, r, mix(skyc, cv.c("sun"), fade), line=not stick(cv) and False, par=par)


def clouds(cv, el, t, seed):
    par = el.get("par", 0.45)
    col = mix(cv.pal["cloud"], cv.pal["storm_cloud"], cv.storm)
    for i, c in enumerate(el.get("items", [])):
        r = random.Random(seed * 31 + i)
        x = c["x"] + el.get("drift", 0.3) * t
        y, w = c["y"], c.get("w", 4)
        if c.get("storm"):                                   # storm clouds roll in with the storm value
            if cv.storm < 0.05:
                continue
            x += (1 - cv.storm) * c.get("enter", 12)
        circles = [(x + (j / 5 - 0.5) * w, y + r.uniform(0, 0.35) * w * (0.5 - abs(j / 5 - 0.5)), w * r.uniform(0.17, 0.26)) for j in range(6)]
        circles.append((x, y - 0.02 * w, w * 0.3))
        cv.blob(circles, scale(col, 0.95 if c.get("storm") else 1.0), seed=seed + i, par=par, lw=0.8)


def hills(cv, el, t, seed):
    layers = el.get("layers", [{"par": 0.25, "y": 3.0, "amp": 1.6}, {"par": 0.5, "y": 1.6, "amp": 1.0}, {"par": 0.75, "y": 0.6, "amp": 0.6}])
    storm_c = cv.pal["storm_sky"][1]
    for i, L in enumerate(layers):
        par = L["par"]
        x0, x1 = cv.world_x_range(par)
        y0, _ = cv.world_y_range(par)
        r = random.Random(seed * 13 + i)
        ph = [r.uniform(0, 6.28) for _ in range(3)]
        n = 60
        pts = []
        for j in range(n + 1):
            x = x0 - 1 + (x1 - x0 + 2) * j / n
            y = L["y"] + L["amp"] * (0.6 * math.sin(x * 0.11 + ph[0]) + 0.3 * math.sin(x * 0.27 + ph[1]) + 0.1 * math.sin(x * 0.7 + ph[2]))
            pts.append((x, y))
        pts += [(x1 + 1, y0 - 2), (x0 - 1, y0 - 2)]
        col = mix(cv.pal["hills"][i % len(cv.pal["hills"])], storm_c, 0.35 * cv.storm)
        cv.fill(pts, col, line=cv.pal.get("hill_line", False), lw=0.8, seed=seed + i, par=par)


def ground(cv, el, t, seed):
    x0, x1 = cv.world_x_range()
    y0, _ = cv.world_y_range()
    cv.fill([(x0 - 1, 0), (x1 + 1, 0), (x1 + 1, y0 - 1), (x0 - 1, y0 - 1)], "ground", line=False)
    if not stick(cv):
        cv.fill([(x0 - 1, -0.6), (x1 + 1, -0.6), (x1 + 1, y0 - 1), (x0 - 1, y0 - 1)], scale(cv.c("ground"), 0.9), line=False)
    if cv.outline:
        cv.stroke([(x0 - 1, 0), (x1 + 1, 0)], "ground_line", cv.style["line"]["width"] * (1.0 if stick(cv) else 0.7), seed=seed)
    tuft = mix(cv.pal["ground"], cv.pal["ink"], 0.45 if stick(cv) else 0.25)
    import math as _m
    for i in range(int(_m.floor(x0)), int(_m.ceil(x1)) + 1):
        r = random.Random(i * 977 + seed)
        if r.random() < 0.55:
            gx, gy = i + r.random(), -r.uniform(0.05, 1.6)
            h = r.uniform(0.12, 0.22)
            cv.stroke([(gx - 0.08, gy + h), (gx, gy), (gx + 0.08, gy + h * 1.1)], tuft, 1.6, seed=i)


def tree(cv, el, t, seed):
    x, h, par = el.get("x", 0), el.get("h", 4.0), el.get("par", 1.0)
    y = el.get("y", 0)
    lay = lbegin(cv)
    trunk = cv.c("wood_line") if not stick(cv) else cv.c("ink")
    sway = 0.05 * math.sin(t * 1.3 + seed) + 0.12 * cv.storm * math.sin(t * 4 + seed)
    cv.wstroke([(x, y), (x + 0.1, y + h * 0.45), (x + sway * h, y + h * 0.72)], trunk, 0.09 * h if not stick(cv) else 0.0, seed, par)
    if stick(cv):
        cv.stroke([(x, y), (x + 0.1, y + h * 0.45), (x + sway * h, y + h * 0.72)], "ink", cv.style["line"]["width"], seed, par)
    r = random.Random(seed)
    cx, cy = x + sway * h, y + h * 0.8
    circles = [(cx + r.uniform(-0.3, 0.3) * h, cy + r.uniform(-0.12, 0.18) * h, h * r.uniform(0.15, 0.22)) for _ in range(6)]
    cv.blob(circles, fillc(cv, "foliage"), seed=seed, par=par)
    lend(cv, lay, 1.0, 0.3)


# ---------------- the ark (Gen 6:14-16: box-shaped, pitched, window strip above, door in the side) ----------------
def ark(cv, el, t, seed):
    dx = el["door_x"]
    Hk = el.get("height", 9.0)
    xl, xr = dx - el.get("left", 40), dx + el.get("right", 8)
    base = 0.5
    deck = Hk - 1.6
    lay = lbegin(cv)
    pitch = fillc(cv, "pitch")
    for bx in range(int(xl), int(xr), 3):                    # stone blocks under the hull
        cv.fill([(bx, 0), (bx + 1.2, 0), (bx + 1.2, base + 0.05), (bx, base + 0.05)], fillc(cv, "#8f877b"), seed=seed + bx)
    hull = [(xl, base), (xr - 1.2, base), (xr, base + 1.6), (xr + 0.3, deck), (xl, deck)]
    cv.fill(hull, pitch, seed=seed)
    plank = cv.c("ink") if stick(cv) else mix(cv.c("pitch"), cv.c("wood"), 0.35)
    yy = base + 0.55
    while yy < deck - 0.1:
        f = (yy - base) / 1.6
        right = xr - 1.2 + min(1, f) * 1.2 + max(0, (yy - base - 1.6) / (deck - base - 1.6)) * 0.3
        third = abs(((yy - base) / (deck - base)) * 3 - round(((yy - base) / (deck - base)) * 3)) < 0.06
        cv.stroke([(xl, yy), (right, yy)], plank, (2.6 if third else 1.1) * (1.4 if stick(cv) else 1), seed=seed + int(yy * 10))
        yy += 0.55
    band = [(xl, deck), (xr + 0.3, deck), (xr + 0.3, deck + 0.8), (xl, deck + 0.8)]
    cv.fill(band, cv.c("ink") if stick(cv) else scale(cv.c("pitch"), 0.45), seed=seed + 1)
    px = xl + 0.6
    while px < xr + 0.2:
        cv.fill([(px, deck), (px + 0.25, deck), (px + 0.25, deck + 0.8), (px, deck + 0.8)], fillc(cv, "wood"), lw=0.6, seed=seed + int(px * 3))
        px += 1.6
    roof = [(xl, deck + 0.8), (xr + 0.8, deck + 0.8), (xr + 0.4, Hk), (xl, Hk + 0.15)]
    cv.fill(roof, fillc(cv, "wood"), seed=seed + 2)
    # door opening + ramp
    d0, d1, db, dt = dx - 1.1, dx + 1.1, base + 1.0, base + 4.0
    cv.fill([(d0, db), (d1, db), (d1, dt), (d0, dt)], cv.c("ink") if stick(cv) else rgb("#1b130e"), seed=seed + 3)
    cv.stroke([(d0, db), (d0, dt), (d1, dt), (d1, db)], cv.c("wood_line") if not stick(cv) else cv.c("ink"), 4.5, seed=seed + 4)
    rf = el.get("ramp_to", 8.0)
    ramp = [(d0 + 0.1, db), (dx + rf, 0.0), (dx + rf, -0.22), (d0 + 0.1, db - 0.25)]
    cv.fill(ramp, fillc(cv, "wood"), seed=seed + 5)
    for i in range(1, 9):
        u = i / 9
        rx, ry = d0 + 0.1 + (dx + rf - d0 - 0.1) * u, db * (1 - u)
        cv.stroke([(rx, ry), (rx + 0.05, ry - 0.2)], cv.c("wood_line") if not stick(cv) else cv.c("ink"), 1.6, seed=seed + 10 + i)
    lend(cv, lay, 0.8, 0.25)


# ---------------- people ----------------
ARM_POSES = {"stand": (0.12, 0.25), "gesture": (1.45, 2.35), "pray": (0.55, 2.7), "point": (1.5, 1.6)}


def person(cv, el, t, seed):
    H = el.get("h", 1.75)
    x, y, phase, moving, f = walk_state(el, t, H)
    f = el.get("facing", f) if not moving else f
    pose = val(el.get("pose", "stand"), t)
    body = cv.style.get("body", "bean")
    head_k = cv.style["proportions"]["head"]
    limb = max(cv.style["proportions"]["limb"], 0.04) * H
    bounce = cv.style["motion"].get("bounce", 0.04)
    bob = bounce * H * abs(math.sin(phase)) if moving else 0.006 * H * math.sin(t * 2.1 + seed)
    D = head_k * H
    r = D / 2
    old = el.get("old", False)
    stoop = 0.04 * H * f if old else 0
    skin = cv.c("skin", el.get("skin", 0))
    robe = cv.c(el.get("shirt", "shirt:0")) if el.get("outfit") == "modern" else cv.c(el.get("robe", "cloth:0"))
    hc = (x + stoop + 0.01 * H * f, y + H - r + bob)
    neck_y = y + H - D + bob
    sh_y = neck_y - 0.035 * H
    swing = math.sin(phase) if moving else 0.0
    if moving:
        arms = ((0.5 * swing, 0.5 * swing + 0.35), (-0.5 * swing, -0.5 * swing + 0.35))
    else:
        a1, a2 = ARM_POSES.get(pose, ARM_POSES["stand"])
        wave = 0.32 * math.sin(t * 7) if pose == "gesture" else 0
        arms = ((a1, a2 + wave), ARM_POSES["stand"] if pose != "pray" else (0.6, 2.65))
    lay = lbegin(cv)

    def arm(shoulder, angles, front):
        ua, fa = angles
        L1, L2 = 0.19 * H, 0.18 * H
        el_ = (shoulder[0] + math.sin(ua) * L1 * f, shoulder[1] - math.cos(ua) * L1)
        hand = (el_[0] + math.sin(fa) * L2 * f, el_[1] - math.cos(fa) * L2)
        if body == "stick":
            cv.stroke([shoulder, el_, hand], "ink", cv.style["line"]["width"], seed)
        else:
            sleeve = robe if front else scale(robe, 0.86)
            cv.wstroke([shoulder, el_, hand], sleeve, limb, seed)
            cv.circle(hand[0], hand[1], limb * 0.62, skin if front else scale(skin, 0.9), seed=seed + 3)

    back_sh = (x + stoop * 0.6 - 0.05 * H * f, sh_y)
    front_sh = (x + stoop * 0.6 + 0.06 * H * f, sh_y)

    if body == "stick":
        hip = (x, y + 0.47 * H + bob)
        arm(back_sh, arms[1], False)
        for s in (1, -1):
            sw = math.sin(phase + (0 if s > 0 else math.pi)) if moving else 0
            foot = (x + sw * 0.16 * H * f + (0 if moving else s * 0.05 * H), y + max(0, math.cos(phase + (0 if s > 0 else math.pi))) * 0.05 * H * moving)
            knee = ((hip[0] + foot[0]) / 2 + 0.04 * H * f, (hip[1] + foot[1]) / 2)
            cv.stroke([hip, knee, foot], "ink", cv.style["line"]["width"], seed + s)
        cv.stroke([(x + stoop, neck_y), hip], "ink", cv.style["line"]["width"], seed)
    elif el.get("outfit") == "modern":
        hip = (x, y + 0.46 * H + bob)
        pants = cv.c(el.get("pants", "pants:0"))
        arm(back_sh, arms[1], False)
        for s_ in (-1, 1):
            sw = math.sin(phase + (0 if s_ > 0 else math.pi)) if moving else 0
            foot = (x + sw * 0.15 * H * f + (0 if moving else s_ * 0.05 * H), y + 0.03 * H + max(0, math.cos(phase + (0 if s_ > 0 else math.pi))) * 0.04 * H * moving)
            knee = ((hip[0] + foot[0]) / 2 + 0.03 * H * f, (hip[1] + foot[1]) / 2)
            cv.wstroke([hip, knee, foot], pants if s_ > 0 else scale(pants, 0.85), limb * 1.25, seed + s_)
            cv.fill(ellipse_pts(foot[0] + 0.03 * H * f, foot[1] - 0.01 * H, 0.065 * H, 0.03 * H, n=18), rgb("#2a2a2e"), seed=seed + 8 + s_)
        shirt = cv.c(el.get("shirt", "shirt:0"))
        tw = 0.115 * H
        top = sh_y + 0.035 * H
        torso = ellipse_pts(x + stoop * 0.6, top - 0.03 * H, tw, 0.05 * H, n=14, a0=0, a1=math.pi)
        torso += [(x - tw * 0.95, hip[1] - 0.02 * H), (x - tw * 0.7, hip[1] - 0.06 * H), (x + tw * 0.7, hip[1] - 0.06 * H), (x + tw * 0.95, hip[1] - 0.02 * H)]
        cv.fill(torso, shirt, seed=seed + 1)
        robe = shirt
    else:
        hem_y = y + 0.07 * H + bob * 0.5
        sway = 0.02 * H * swing
        for s in (-1, 1):                                    # feet peek out under the robe
            sw = math.sin(phase + (0 if s > 0 else math.pi)) if moving else 0
            fx = x + sw * 0.11 * H * f + (0 if moving else s * 0.045 * H)
            lift = max(0, math.cos(phase + (0 if s > 0 else math.pi))) * 0.03 * H if moving else 0
            cv.fill(ellipse_pts(fx + 0.03 * H * f, y + 0.025 * H + lift, 0.06 * H, 0.028 * H, n=20), rgb("#4a3022") if s < 0 else rgb("#5a3a28"), seed=seed + 7 + s)
        arm(back_sh, arms[1], False)
        tw, bw = 0.12 * H, 0.19 * H if body == "soft" else 0.17 * H
        top = sh_y + 0.03 * H
        robe_pts = ellipse_pts(x + stoop * 0.6, top - 0.02 * H, tw, 0.06 * H, n=16, a0=0, a1=math.pi)
        robe_pts += [(x - bw + sway, hem_y + 0.02 * H), (x, hem_y - 0.012 * H), (x + bw + sway, hem_y + 0.02 * H)]
        robe_pts = robe_pts[:16] + robe_pts[16:]
        cv.fill(robe_pts, robe, seed=seed + 1)
        sash = cv.c(el.get("sash", "accent")) if el.get("sash", True) else None
        if sash:
            wy = y + 0.52 * H + bob
            cv.fill([(x - 0.14 * H, wy), (x + 0.14 * H + stoop * 0.3, wy), (x + 0.145 * H + stoop * 0.3, wy + 0.035 * H), (x - 0.135 * H, wy + 0.035 * H)], scale(sash, 0.95), lw=0.7, seed=seed + 2)
        if el.get("mantle"):
            m = cv.c(el["mantle"])
            cv.fill([(x - 0.04 * H * f + stoop * 0.6, top), (x + 0.03 * H * f + stoop * 0.6, top), (x + 0.07 * H * f, hem_y + 0.05 * H), (x - 0.05 * H * f, hem_y + 0.05 * H)], m, lw=0.7, seed=seed + 5)

    # head
    modern = el.get("outfit") == "modern"
    hair = el.get("hair", "short" if modern else None)
    if hair == "long" and body != "stick":
        cv.fill([(hc[0] - f * 1.05 * r, hc[1] + 0.4 * r), (hc[0] - f * 1.2 * r, hc[1] - 1.3 * r), (hc[0] - f * 0.1 * r, hc[1] - 1.1 * r), (hc[0] + f * 0.3 * r, hc[1] + 0.5 * r)], cv.c(el.get("hair_color", "hair:0")), seed=seed + 10)
    if el.get("headcloth", not modern) and body != "stick":
        hcl = cv.c(el.get("headcloth_color", "cloth:4"))
        back = [(hc[0] - f * r * 1.1, hc[1] + 0.35 * r), (hc[0] - f * r * 1.2, hc[1] - 1.5 * r), (hc[0] - f * 0.15 * r, hc[1] - 1.3 * r), (hc[0] + f * 0.2 * r, hc[1] + 0.3 * r)]
        cv.fill(back, scale(hcl, 0.9), seed=seed + 11)
    if body == "stick":
        cv.circle(hc[0], hc[1], r, "paper", seed=seed + 12)
    else:
        cv.fill(ellipse_pts(hc[0], hc[1], r, r * (1.05 if body == "soft" else 1.0), n=40), skin, seed=seed + 12)
    beard = el.get("beard")
    if beard:
        bc = cv.c("beard") if beard in ("white", True) else rgb("#3a2a20")
        bpts = [(hc[0] - f * 0.55 * r, hc[1] - 0.22 * r), (hc[0] + f * 0.98 * r, hc[1] - 0.32 * r),
                (hc[0] + f * 0.7 * r, hc[1] - 0.95 * r), (hc[0] + f * 0.25 * r, hc[1] - 1.45 * r), (hc[0] - f * 0.2 * r, hc[1] - 0.9 * r)]
        cv.fill(bpts, cv.c("paper") if stick(cv) else bc, seed=seed + 13)
    # face
    face = cv.style.get("face", {})
    ex = hc[0] + f * 0.32 * r
    ey = hc[1] + 0.02 * r
    if body != "stick":                                          # small nose: reads the facing direction
        cv.fill([(hc[0] + f * 0.82 * r, hc[1] + 0.12 * r), (hc[0] + f * 1.13 * r, hc[1] - 0.14 * r), (hc[0] + f * 0.84 * r, hc[1] - 0.2 * r)], skin, lw=0.8, seed=seed + 19)
    for k, dxx in enumerate((-0.24 * r, 0.24 * r)):
        px = ex + dxx
        if face.get("eyes") == "oval":
            cv.fill(ellipse_pts(px, ey, 0.085 * r, 0.13 * r, n=14), "ink", line=False, seed=seed + 20 + k)
        else:
            cv.fill(ellipse_pts(px, ey, 0.09 * r, 0.09 * r, n=12), "ink", line=False, seed=seed + 20 + k)
        if old and not stick(cv):
            cv.stroke([(px - 0.12 * r, ey + 0.25 * r), (px + 0.12 * r, ey + 0.28 * r)], cv.c("beard"), 2.4, seed=seed + 30 + k)
    if face.get("blush") and not beard:
        for dxx in (-0.35 * r, 0.45 * r):
            cv.fill(ellipse_pts(ex + dxx, ey - 0.3 * r, 0.15 * r, 0.08 * r, n=14), mix(skin, "#e07a6a", 0.45), line=False)
    elif face.get("blush"):
        cv.fill(ellipse_pts(ex + 0.42 * r, ey - 0.22 * r, 0.13 * r, 0.07 * r, n=14), mix(skin, "#e07a6a", 0.4), line=False)
    if face.get("mouth", True):
        my = hc[1] - (0.35 if not beard else 0.5) * r
        smile = 0.06 * r
        cv.stroke([(ex - 0.16 * r, my + smile), (ex, my), (ex + 0.16 * r, my + smile)], "ink" if not beard else rgb("#6a4a3a"), 2.0, seed=seed + 40)
    if hair and body != "stick":
        cap = ellipse_pts(hc[0] - f * 0.08 * r, hc[1] + 0.22 * r, r * 1.06, r * 0.86, n=24, a0=-0.1, a1=math.pi + 0.35)
        cv.fill(cap, cv.c(el.get("hair_color", "hair:0")), seed=seed + 17)
    if el.get("headcloth", not modern):
        if body == "stick":
            cv.stroke(ellipse_pts(hc[0], hc[1], r * 1.08, r * 1.08, n=16, a0=0.15, a1=math.pi - 0.15), "ink", cv.style["line"]["width"] * 0.8, seed + 14)
        else:
            hcl = cv.c(el.get("headcloth_color", "cloth:4"))
            cap = ellipse_pts(hc[0] - f * 0.06 * r, hc[1] + 0.3 * r, r * 1.12, r * 0.88, n=24, a0=0.0, a1=math.pi)
            cv.fill(cap, hcl, seed=seed + 15)
            cv.stroke([(hc[0] - 1.12 * r, hc[1] + 0.32 * r), (hc[0] + 1.06 * r, hc[1] + 0.32 * r)], cv.c(el.get("band", "accent")), 4.0, seed=seed + 16)
    arm(front_sh, arms[0], True)
    lend(cv, lay, 1.0, 0.35)


# ---------------- animals ----------------
KINDS = {
    "sheep": dict(bl=1.0, bh=0.55, leg=0.36, head=0.22, neck=0.12, body="animal", head_c="#3d3029", leg_c="#3d3029", wool=True, horns=False, tail=0.1),
    "goat": dict(bl=0.9, bh=0.42, leg=0.44, head=0.22, neck=0.16, body="#c9b393", head_c="#c9b393", leg_c="#8a7354", wool=False, horns=True, tail=0.12, beard=True),
    "ox": dict(bl=1.7, bh=0.82, leg=0.6, head=0.3, neck=0.14, body="#8a5a3a", head_c="#7a4e32", leg_c="#6e4630", wool=False, horns=True, tail=0.45),
}


def animal(cv, el, t, seed):
    kind = KINDS[el.get("kind", "sheep")]
    sz = el.get("size", 1.0)
    x, y, phase, moving, f = walk_state(el, t, kind["bl"] * sz)
    if "show" in el and not (el["show"][0] <= t <= el["show"][1]):
        return
    bl, bh, leg = kind["bl"] * sz, kind["bh"] * sz, kind["leg"] * sz
    bob = 0.03 * sz * abs(math.sin(phase)) if moving else 0
    by = y + leg + bh / 2 + bob
    slope = 0
    if el.get("floor"):
        slope = math.atan2(floor_y(el["floor"], x + 0.3) - floor_y(el["floor"], x - 0.3), 0.6)
    lc, bc, hcc = fillc(cv, kind["leg_c"]), fillc(cv, kind["body"]), fillc(cv, kind["head_c"])
    lw_units = 0.075 * sz if kind["bl"] < 1.5 else 0.1 * sz
    lay = lbegin(cv)

    def legs(back):
        for i, lx in enumerate((-0.33, 0.33)):
            ph = phase + (math.pi if (i == 0) ^ back else 0)
            sw = math.sin(ph) * 0.18 * leg if moving else 0
            hx = x + lx * bl * f
            hy = by - bh * 0.25 + math.sin(slope) * lx * bl * f
            fy = floor_y(el.get("floor"), hx + sw * f) if el.get("floor") else y
            col = scale(lc, 0.8) if back else lc
            if stick(cv):
                cv.stroke([(hx, hy), (hx + sw * f, fy)], "ink", cv.style["line"]["width"], seed + i)
            else:
                cv.wstroke([(hx, hy), (hx + sw * f * 0.5, (hy + fy) / 2), (hx + sw * f, fy)], col, lw_units, seed + i)

    legs(True)
    # tail
    tx = x - 0.5 * bl * f
    cv.stroke([(tx, by + 0.1 * bh), (tx - 0.12 * f * sz, by - kind["tail"] * sz)], "ink" if stick(cv) else scale(bc if not kind["wool"] else lc, 0.85), 3.0, seed)
    # body
    if kind["wool"]:
        r = random.Random(seed)
        circles = [(x + (j / 6 - 0.5) * bl * 0.9 * f, by + math.sin(slope) * (j / 6 - 0.5) * bl * f + r.uniform(-0.12, 0.15) * bh, bh * r.uniform(0.38, 0.48)) for j in range(7)]
        cv.blob(circles, bc, seed=seed)
    else:
        cv.fill(ellipse_pts(x, by, bl / 2, bh / 2, rot=slope * f if f > 0 else -slope, n=36), bc, seed=seed)
    legs(False)
    # neck + head
    nx, ny = x + 0.45 * bl * f, by + 0.15 * bh + math.sin(slope) * 0.45 * bl
    hx, hy = nx + 0.2 * sz * f, ny + kind["neck"] + 0.1 * sz + 0.03 * math.sin(phase * 0.5) * moving
    if kind["neck"] > 0.15:
        cv.wstroke([(nx, ny), (hx, hy)], bc, 0.16 * sz, seed + 2) if not stick(cv) else cv.stroke([(nx, ny), (hx, hy)], "ink", cv.style["line"]["width"], seed + 2)
    hr = kind["head"]
    if kind["horns"]:
        for k in (0, 1):
            hx0 = hx - 0.05 * f * sz + k * 0.06 * sz * f
            cv.stroke([(hx0, hy + hr * 0.3), (hx0 - 0.1 * f * sz, hy + hr * 1.1), (hx0 - 0.26 * f * sz, hy + hr * 1.25), (hx0 - 0.34 * f * sz, hy + hr * 0.95)], "ink" if stick(cv) else rgb("#5a4a3a"), 4.2, seed + 5 + k)
    cv.fill(ellipse_pts(hx + 0.06 * f * sz, hy, hr * 0.85, hr * 0.5, rot=-0.35 * f, n=24), hcc, seed=seed + 3)
    cv.fill(ellipse_pts(hx - 0.1 * f * sz, hy + 0.12 * sz, 0.1 * sz, 0.05 * sz, rot=0.5 * f, n=12), scale(hcc, 0.9), seed=seed + 4)
    cv.fill(ellipse_pts(hx + 0.08 * f * sz, hy + 0.05 * sz, 0.025 * sz, 0.025 * sz, n=10), "ink" if not kind["wool"] else rgb("#f4efe6"), line=False)
    if kind.get("beard"):
        cv.stroke([(hx + 0.18 * f * sz, hy - 0.08 * sz), (hx + 0.16 * f * sz, hy - 0.22 * sz)], "ink" if stick(cv) else rgb("#7a6548"), 3.0, seed + 9)
    lend(cv, lay, 1.0, 0.3)


def bird(cv, el, t, seed):
    if "show" in el and not (el["show"][0] <= t <= el["show"][1]):
        return
    x, y = val(el["x"], t, "gentle"), val(el["y"], t, "gentle")
    xb = val(el["x"], t + 0.05, "gentle")
    f = 1 if xb >= x else -1
    s = el.get("size", 0.45)
    flap = math.sin(t * 13 + seed)
    body = fillc(cv, el.get("color", "#f7f5ef"))
    cv.fill(ellipse_pts(x, y, s * 0.5, s * 0.22, rot=0.15 * f, n=20), body, seed=seed)
    cv.circle(x + 0.42 * s * f, y + 0.12 * s, s * 0.15, body, seed=seed + 1)
    cv.fill([(x + 0.55 * s * f, y + 0.14 * s), (x + 0.7 * s * f, y + 0.1 * s), (x + 0.55 * s * f, y + 0.07 * s)], rgb("#e09a3a") if not stick(cv) else cv.c("ink"), lw=0.5)
    wing = [(x - 0.1 * s * f, y + 0.05 * s), (x + 0.15 * s * f, y + 0.05 * s), (x - 0.15 * s * f, y + (0.1 + 0.55 * flap) * s)]
    cv.fill(wing, scale(body, 0.92), seed=seed + 2)


# ---------------- weather + text ----------------
def rain(cv, el, t, seed):
    amt = val(el.get("amount", 1.0), t)
    if amt <= 0.01:
        return
    n = int(amt * el.get("density", 240) * (cv.Wp * cv.Hp) / (1440 * 2560))
    col = cv.c("rain")
    cv.begin()
    L, slant = 0.045 * cv.Hp, 0.18
    w = max(1, int(round(1.7 * cv.u)))
    for i in range(n):
        r = random.Random(seed * 1000 + i)
        x0, ph, sp = r.uniform(-0.1, 1.1) * cv.Wp, r.random(), r.uniform(1.6, 2.2)
        yy = ((ph + sp * t) % 1.2 - 0.1) * cv.Hp
        xx = x0 - slant * yy
        cv.d.line([(xx, yy), (xx - slant * L, yy + L)], fill=col + (int(150 * r.uniform(0.6, 1.0)),), width=w)
    cv.end()


def caption(cv, el, t, seed):
    t0, t1 = el.get("show", [0, 1e9])
    if not (t0 <= t <= t1):
        return
    fade = min(1, (t - t0) / 0.4, (t1 - t) / 0.4) if t1 < 1e8 else min(1, (t - t0) / 0.4)
    top, bottom, left, right = cv.safe
    ss = cv.ss
    W, H = cv.W, cv.H
    maxw = (W - left - right) * 0.92 * ss
    size = el.get("size", 44)
    fnt_px = size * cv.u
    chars = max(12, int(maxw / (fnt_px * 0.52)))
    lines = textwrap.wrap(el["text"], chars)
    ref = el.get("ref")
    lh = fnt_px * 1.25
    h = lh * len(lines) + (lh * 0.85 if ref else 0) + fnt_px * 0.9
    wbox = min(maxw, max(len(s) for s in lines + [ref or ""]) * fnt_px * 0.55 + fnt_px * 1.2)
    cx = (left + (W - right)) / 2 * ss
    by = (H - bottom) * ss - h - 20 * cv.u
    cv.begin()
    bg = cv.c("text_bg")
    cv.d.rounded_rectangle([cx - wbox / 2, by, cx + wbox / 2, by + h], radius=fnt_px * 0.45, fill=bg + (215,))
    yy = by + fnt_px * 0.45 + lh / 2
    from canvas import font
    for s in lines:
        cv.d.text((cx, yy), s, font=font(fnt_px), fill=cv.c("text") + (255,), anchor="mm"); yy += lh
    if ref:
        cv.d.text((cx, yy), ref, font=font(fnt_px * 0.62), fill=cv.c("text") + (210,), anchor="mm")
    cv.end(alpha=fade)


def clip(cv, el, t, seed):
    cv.begin()
    for i, ch in enumerate(el.get("children", [])):
        DRAW[ch["type"]](cv, ch, t, seed * 10 + i)
    cv.end(clip_left_x=el.get("left"))


DRAW = {"sky": sky, "sun": sun, "clouds": clouds, "hills": hills, "ground": ground, "tree": tree, "ark": ark,
        "person": person, "animal": animal, "bird": bird, "rain": rain, "caption": caption, "clip": clip}

from actors_tech import DRAW_TECH  # noqa: E402

DRAW.update(DRAW_TECH)
