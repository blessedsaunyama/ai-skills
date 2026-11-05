
// ---------------- Bible-era cast (our own designs), appended after roman.js in toon.js ----------------
// Rebuild after edits:  cat web/toonbase.js web/roman.js web/biblical.js > web/toon.js
// Uses the Pen / blob / face helpers from toon.ts and romanFront() from roman.js (same module scope).
// Reverence rules baked in: no outfit for God the Father (use fxGlory + light only); Jesus is drawn with the
// same care as everyone else and never with comic expressions; angels are tall men in shining white with a soft
// glow (no baby cherubs, wings only if a story's text describes them: opts.wings).

const OLIVE = "#c58c5c", BROWN = "#a8754c", TAN = "#d6a679", DEEP = "#8a5a3a", GOLD = "#e3b341";
export const BIBLE = {
  // name: robe = long garment colour, tunic = upper body, mantle = cloak behind, headcloth/cord, crown, staff, glow ...
  shepherdBoy: { tunic: "#c98a4a", robe: "#b5783e", skin: TAN, hair: "#3a2416", staff: true },  // draw at card s ~0.9 (a youth)          // e.g. young David (1 Sam 17:42 "ruddy")
  shepherd:    { tunic: "#9a7a52", robe: "#7d6243", skin: OLIVE, headcloth: "#e8dcc0", cord: "#5a3b2a", beard: "#3a2a20", staff: true },
  prophet:     { tunic: "#6e5a8a", robe: "#5a4a72", skin: OLIVE, headcloth: "#efe6d2", cord: "#8a6a3a", beard: "#d9d4c8", brows: "#d9d4c8" }, // older Daniel, Elijah...
  youngProphet:{ tunic: "#4f6f9a", robe: "#3f5a80", skin: OLIVE, headcloth: "#efe6d2", cord: "#8a6a3a", beard: "#2b1d14" },
  jesus:       { tunic: "#efe7d6", robe: "#e6dcc6", mantle: "#8c4a3a", skin: BROWN, hair: "#2b1a12", beard: "#2b1a12" },
  disciple:    { tunic: "#8a6a4a", robe: "#6f5236", mantle: "#4f6a5a", skin: OLIVE, hair: "#1e1410", beard: "#1e1410" },
  woman:       { tunic: "#3f6a8a", dress: "#3f6a8a", skin: OLIVE, headcloth: "#d9c9a6", veil: true },
  womanB:      { tunic: "#a24a4a", dress: "#a24a4a", skin: TAN, headcloth: "#efe0c0", veil: true },
  child:       { tunic: "#d9a441", robe: "#c4903a", skin: TAN, hair: "#2b1d14" },  // draw at card s ~0.7
  villager:    { tunic: "#7a8a4a", robe: "#66733e", skin: DEEP, headcloth: "#d8ccb0", cord: "#4a3020", beard: "#1e1410" },
  king:        { tunic: "#6a2f7a", robe: "#5a2668", mantle: "#a8282b", skin: OLIVE, hair: "#2b1d14", beard: "#2b1d14", crown: GOLD, stout: true }, // Saul, Darius...
  official:    { tunic: "#2f6a6a", robe: "#2a5a5a", mantle: "#b8862a", skin: OLIVE, headcloth: "#c9a35a", cord: "#6a4a1a", beard: "#1e1410" },     // princes, presidents
  soldierIsr:  { tunic: "#8a6a3a", skin: OLIVE, headcloth: "#8a7a5a", cord: "#4a3020", beard: "#1e1410", spear: true },
  giant:       { tunic: "#6a5a3a", skin: "#c99067", armor: "bronze", bronzeHelm: true, beard: "#2b1d14", spear: true, stout: true },     // Goliath: draw with card s ~1.3 (6 cubits and a span)
  angel:       { tunic: "#fbf8f0", robe: "#f6f2e6", skin: "#f1d2b0", hair: "#e8c98a", glow: "#fff6d8" },
};

/** Draw a Bible-era character on the 600x1000 card. Same opts as romanFront (expr, L, R, facing, look, blink, tilt,
 *  headTilt, bob, step, seed) plus: wings (angel, only when the text supports it), glowK (0..1 glow strength). */
export const bibleFront = (p, key, opts = {}) => {
  const O = typeof key === "string" ? BIBLE[key] : key;
  const { seed = 3, facing = 0, tilt = 0, headTilt = 0, bob = 0 } = opts;
  const H = headBlob(seed, 118, facing), W = 2 * H.a, HH = 2 * H.b, u = W / 100;
  const torsoL = O.stout ? 1.12 : 1.08, legsL = 1.38, sole = 975, cx = 300;
  const torsoBot = sole - legsL * HH - bob * HH, chin = torsoBot - torsoL * HH, hc = chin - H.b, hipY = torsoBot - 0.12 * HH;
  const light = rad(-120), thick = thickAngle(light), ow = 5 * u;
  // --- behind everything: glow, wings, staff ---
  if (O.glow) {
    const g = p.g, k = opts.glowK ?? 1, gr = g.createRadialGradient(cx, hc + 0.9 * HH, 20, cx, hc + 0.9 * HH, 295);
    gr.addColorStop(0, `rgba(255,248,220,${0.85 * k})`); gr.addColorStop(0.45, `rgba(255,240,190,${0.35 * k})`); gr.addColorStop(1, "rgba(255,240,190,0)");
    g.save(); g.fillStyle = gr; g.fillRect(0, 0, 600, 1000); g.restore();
  }
  if (opts.wings) for (const s of [-1, 1]) {
    const base = [cx + s * 0.3 * W, chin + 0.35 * HH], pts = [base, [cx + s * 1.25 * W, chin - 0.9 * HH], [cx + s * 1.45 * W, chin + 0.2 * HH], [cx + s * 1.15 * W, chin + 1.3 * HH], [cx + s * 0.45 * W, chin + 0.9 * HH]];
    p.gradFill(pts, "#fffdf6", "#d9d2c0", light); p.inkRing(pts, ow * 0.8, thick);
    for (let i = 1; i < 4; i++) p.stroke(curve([cx + s * (0.45 + 0.2 * i) * W, chin + (0.9 - 0.1 * i) * HH], [cx + s * (0.7 + 0.18 * i) * W, chin + 0.3 * HH], [cx + s * (0.95 + 0.12 * i) * W, chin - 0.2 * i * HH]), 1.6 * u, "#cfc7b4");
  }
  if (O.staff) {
    const sx = cx + 0.52 * W, top = hc - 0.95 * HH;
    p.band([[sx, sole - 2 * u], [sx, top + 0.12 * HH]], "#7a5434", 4.2 * u, 1.4 * u, "round");
    p.stroke(ellPts(sx - 0.09 * HH, top + 0.12 * HH, 0.09 * HH, 0.11 * HH, 180, 360, 0, 16), 4.2 * u + 3, INK);
    p.stroke(ellPts(sx - 0.09 * HH, top + 0.12 * HH, 0.09 * HH, 0.11 * HH, 180, 360, 0, 16), 4.2 * u, "#7a5434");
  }
  // --- the body via romanFront (robe -> long dress shape; no hair under a headcloth or bronze helmet) ---
  const base = {
    tunic: O.tunic, skin: O.skin, cape: O.mantle || undefined, stout: !!O.stout, moustache: O.beard, brows: O.brows,
    dress: O.dress || O.robe || undefined, hair: (O.headcloth || O.bronzeHelm) ? undefined : O.hair, cap: O.cap,
    spear: !!O.spear, armor: O.armor === true, shield: false, helmet: false,
  };
  romanFront(p, base, { ...opts, R: opts.R || (O.staff || O.spear ? "spear" : "hang") });
  // bronze scale armour for the giant (drawn over the torso, inside its outline)
  if (O.armor === "bronze") {
    const ty0 = chin + 0.05 * HH, ty1 = torsoBot - 0.05 * HH, a = 0.4 * W / 1.06 * 1.12;
    for (let r = 0; r < 6; r++) for (let i = -3; i <= 3; i++) {
      const y = ty0 + (ty1 - ty0) * r / 6, x = cx + i * 0.26 * a + (r % 2) * 0.13 * a;
      if (Math.abs(x - cx) < a * 0.92) p.ell(x, y + 6 * u, 7 * u, 8 * u, r % 2 ? "#b58a3e" : "#c99a48", 1.2 * u, 0, 180);
    }
    for (const s of [-1, 1]) p.poly(rrect(cx + s * 16 * u - 6 * u, sole - 0.55 * HH, cx + s * 16 * u + 6 * u, sole - 0.12 * HH, 3 * u), "#c99a48", 1.6 * u); // greaves of brass
  }
  // --- head layers (follow the head rotation used inside romanFront) ---
  const [cpx, cpy] = rotAbout([cx, chin], rad(tilt), [cx, hipY]), Ah = tilt + headTilt;
  p.rot = Ah ? [rad(Ah), cx, chin, cpx - cx, cpy - chin] : null;
  if (O.beard) { // short jaw beard that leaves the mouth visible (dignified, readable faces)
    const outer = ellPts(cx + 4 * u * facing, hc + 0.05 * H.b, H.a * 1.02, H.b * 1.08, 15, 165, 0, 28);
    const inner = ellPts(cx + 7 * u * facing, hc + 0.2 * H.b, H.a * 0.62, H.b * 0.52, 165, 15, 0, 20).reverse();
    const bd = [...outer, ...inner.reverse()];
    p.shadedFill(bd, O.beard, mul(O.beard, [0.82, 0.82, 0.88]), light, H.a, 0.3); p.inkRing(bd, ow * 0.7, thick);
  }
  if (O.headcloth) {
    const top = ellPts(cx, hc - 0.12 * H.b, H.a * 1.1, H.b * 0.98, 180, 360, 0, 40);
    top.push([cx + H.a * 1.1, hc - 0.05 * H.b], [cx - H.a * 1.1, hc - 0.05 * H.b]);
    for (const s of [-1, 1]) {   // drapes falling beside the face to the shoulders
      const dr = [[cx + s * 0.98 * H.a, hc - 0.3 * H.b], [cx + s * 1.14 * H.a, hc - 0.2 * H.b], [cx + s * 1.22 * H.a, chin + (O.veil ? 0.55 : 0.32) * HH], [cx + s * 0.78 * H.a, chin + (O.veil ? 0.45 : 0.2) * HH], [cx + s * 0.9 * H.a, hc + 0.4 * H.b]];
      p.gradFill(dr, O.headcloth, mul(O.headcloth, SH_CLOTH), light); p.inkRing(dr, ow * 0.8, thick);
    }
    p.shadedFill(top, O.headcloth, mul(O.headcloth, SH_CLOTH), light, H.a, 0.4); p.inkRing(top, ow * 0.9, thick);
    if (O.cord) p.band([[cx - H.a * 1.08, hc - 0.42 * H.b], [cx + H.a * 1.08, hc - 0.42 * H.b]], O.cord, 6 * u, 1.6 * u, "round");
    for (let i = -2; i <= 2; i++) p.stroke([[cx + i * 0.3 * H.a, hc - 0.95 * H.b], [cx + i * 0.38 * H.a, hc - 0.5 * H.b]], 1.1 * u, mul(O.headcloth, [0.8, 0.8, 0.85]));
  }
  if (O.bronzeHelm) {
    const hp = ellPts(cx, hc - 0.3 * H.b, H.a * 1.08, H.b * 0.82, 180, 360, 0, 40); hp.push([cx + H.a * 1.08, hc - 0.2 * H.b], [cx - H.a * 1.08, hc - 0.2 * H.b]);
    p.shadedFill(hp, "#c99a48", "#8a6428", light, H.a, 0.4); p.inkRing(hp, ow * 0.9, thick);
    p.band([[cx - H.a * 1.08, hc - 0.28 * H.b], [cx + H.a * 1.08, hc - 0.28 * H.b]], "#a87a32", 7 * u, 1.6 * u, "round");
    p.poly([[cx - 4 * u, hc - 0.3 * H.b], [cx + 4 * u, hc - 0.3 * H.b], [cx + 3 * u, hc + 0.12 * H.b], [cx - 3 * u, hc + 0.12 * H.b]], "#a87a32", 1.4 * u); // nose guard
  }
  if (O.crown) {
    const y0 = hc - 0.72 * H.b, w = 0.7 * H.a, pts = [[cx - w, y0]];
    for (let i = 0; i <= 4; i++) { const x = cx - w + (2 * w) * i / 4; pts.push([x, y0 - (i % 2 ? 0.18 : 0.42) * H.b]); }
    pts.push([cx + w, y0]);
    p.poly(pts, O.crown, 2.2 * u); for (let i = 0; i <= 4; i += 2) p.dot(cx - w + (2 * w) * i / 4, y0 - 0.42 * H.b, 3 * u, "#fff2b0");
    p.band([[cx - w, y0], [cx + w, y0]], mul(O.crown, [0.8, 0.75, 0.6]), 6 * u, 1.4 * u);
  }
  p.rot = null;
};

/** Lion on the 600x1000 card, feet at y=975. pose 'lie' | 'sit'; mouth 'shut' (Dan 6:22) | 'open'. Use card s ~1.4-1.7. */
export const fxLion = (p, opts = {}) => {
  const { pose = "lie", mouth = "shut", look = 0, blink = 0, seed = 1 } = opts;
  const body = "#d9a654", dark = "#a8732e", mane = "#8a5a24", light = rad(-120), th = thickAngle(light), ow = 7;
  const sitting = pose === "sit", by = sitting ? 800 : 880, hx = sitting ? 300 : 190, hy = sitting ? 560 : 760;
  // tail
  p.stroke(curve([sitting ? 380 : 470, by + 20], [560, by - 20 + 10 * Math.sin(seed)], [585, by - 90]), 10, dark);
  p.ell(585, by - 95, 16, 20, mane, 4);
  // body + legs
  const bp = sitting ? ellPts(320, 790, 120, 170, 0, 360, -8, 48) : ellPts(350, 880, 200, 85, 0, 360, 0, 48);
  p.gradFill(bp, body, mul(body, SH_CLOTH), light); p.inkRing(bp, ow, th);
  const paws = sitting ? [[250, 960], [350, 960]] : [[170, 955], [260, 960], [430, 960], [520, 955]];
  for (const [x, y] of paws) p.ell(x, y, 34, 18, body, 6);
  // mane + head
  const mp = blobPts(hx, hy, { a: 120, b: 125, nTop: 2.2, nBot: 2.2, egg: 0, asym: 0, rot: 0, noise: 0.06, seed: seed + 3 });
  p.shadedFill(mp, mane, mul(mane, [0.7, 0.7, 0.75]), light, 120, 0.35); p.inkRing(mp, ow, th);
  const fp = ellPts(hx, hy + 8, 78, 84, 0, 360, 0, 40);
  p.shadedFill(fp, body, mul(body, SH_SKIN), light, 78); p.inkRing(fp, ow * 0.8, th);
  for (const s of [-1, 1]) p.ell(hx + s * 62, hy - 66, 18, 16, body, 5);
  // face
  const ex = hx + look * 10;
  for (const s of [-1, 1]) blink > 0.5 ? p.stroke([[ex + s * 30 - 10, hy - 12], [ex + s * 30 + 10, hy - 12]], 5) : (p.ell(ex + s * 30, hy - 12, 9, 11, INK, 0), p.dot(ex + s * 30 + 3, hy - 16, 3, "#ffffff"));
  p.poly([[hx - 16, hy + 18], [hx + 16, hy + 18], [hx, hy + 34]], "#5a3020", 3);
  if (mouth === "open") p.ell(hx, hy + 56, 24, 18, "#5a1e28", 4);
  else p.stroke(curve([hx - 26, hy + 50], [hx, hy + 44], [hx + 26, hy + 50]), 4); // shut, calm (Dan 6:22)
  p.stroke([[hx, hy + 34], [hx, hy + 46]], 4);
};
/** Sheep, feet at y=975 (use card s ~0.6). */
export const fxSheep = (p, opts = {}) => {
  const { seed = 1, look = 0 } = opts, light = rad(-120), th = thickAngle(light);
  for (const x of [230, 280, 360, 410]) p.stroke([[x, 880], [x, 968]], 12, "#3a2e2a");
  const wp = blobPts(320, 820, { a: 150, b: 95, nTop: 2.0, nBot: 2.0, egg: 0, asym: 0, rot: 0, noise: 0.08, seed: seed + 11 });
  p.shadedFill(wp, "#f4efe4", "#cfc6b6", light, 150, 0.35); p.inkRing(wp, 7, th);
  p.ell(175 + look * 6, 790, 46, 56, "#4a3a34", 6); for (const s of [-1, 1]) p.ell(175 + s * 40, 770, 18, 9, "#4a3a34", 4);
  p.dot(165 + look * 8, 780, 5, "#ffffff");
};
/** Glory light: God's presence / heavenly light. NEVER a figure. Soft glow + slow rays centred at (300,500); t animates.
 *  Use as an fx card with blob:false, shadow:false, large s (3-10) and order 1 behind or 6 in front. */
export const fxGlory = (p, t = 0, col = "255,244,205") => {
  const cv = document.createElement("canvas"); cv.width = 600; cv.height = 1000; const g = cv.getContext("2d"), cx = 300, cy = 500;
  for (let i = 0; i < 14; i++) {
    const a = (i / 14) * Math.PI * 2 + t * 0.6, w = 0.07 + 0.03 * (i % 3);
    g.fillStyle = `rgba(${col},${0.35 + 0.15 * (i % 2)})`; g.beginPath(); g.moveTo(cx, cy);
    g.lineTo(cx + Math.cos(a - w) * 700, cy + Math.sin(a - w) * 700); g.lineTo(cx + Math.cos(a + w) * 700, cy + Math.sin(a + w) * 700); g.closePath(); g.fill();
  }
  const core = g.createRadialGradient(cx, cy, 5, cx, cy, 300);
  core.addColorStop(0, `rgba(${col},1)`); core.addColorStop(0.3, `rgba(${col},0.75)`); core.addColorStop(1, `rgba(${col},0)`);
  g.fillStyle = core; g.fillRect(0, 0, 600, 1000);
  const mask = g.createRadialGradient(cx, cy, 0, cx, cy, 298);           // fade everything out before the card edge
  mask.addColorStop(0, "rgba(0,0,0,1)"); mask.addColorStop(0.6, "rgba(0,0,0,.7)"); mask.addColorStop(1, "rgba(0,0,0,0)");
  g.globalCompositeOperation = "destination-in"; g.fillStyle = mask; g.fillRect(0, 0, 600, 1000);
  p.g.drawImage(cv, 0, 0);
};
/** Sling stone in flight / smooth brook stone. */
export const fxStone = (p) => { p.ell(300, 500, 46, 38, "#9a948a", 8); p.stroke(ellPts(288, 488, 20, 12, 200, 300, 0, 10), 5, "#ffffff88"); };
/** Whirling sling (t 0..1 = one turn), drawn around the hand position (300, 300). */
export const fxSling = (p, t) => {
  const a = t * Math.PI * 2, r = 170, x = 300 + Math.cos(a) * r, y = 300 + Math.sin(a) * r * 0.45;
  p.stroke(curve([300, 300], [(300 + x) / 2, (300 + y) / 2 - 20], [x, y]), 6, "#6a4a2a");
  p.ell(x, y, 26, 20, "#9a948a", 6);
  const g = p.g; g.save(); g.globalAlpha = 0.35; p.stroke(ellPts(300, 300, r, r * 0.45, deg0(a) - 70, deg0(a) - 10, 0, 16), 8, "#ffffff"); g.restore();
};
const deg0 = (r) => r * 180 / Math.PI;
