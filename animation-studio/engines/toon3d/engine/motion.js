// Motion helpers: smooth, continuous, "animated" movement for cameras and cards.
// Import in story.js:  import { M } from './motion.js';
export const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const lerp3 = (a, b, t) => a.map((v, i) => lerp(v, b[i], t));
export const ramp = (f, a, b) => clamp((f - a) / (b - a));
export const M = {
  smooth: (t) => { t = clamp(t); return t * t * t * (t * (t * 6 - 15) + 10); },           // smootherstep (glides)
  easeOut: (t) => 1 - Math.pow(1 - clamp(t), 3),                                          // fast start, soft land (reference "burst" moves)
  easeIn: (t) => Math.pow(clamp(t), 3),
  back: (t, s = 1.7) => { t = clamp(t) - 1; return t * t * ((s + 1) * t + s) + 1; },        // overshoot then settle (pops, arrivals)
  anticip: (t, s = 0.12) => { t = clamp(t); return t < 0.25 ? -s * Math.sin(t / 0.25 * Math.PI) : M.back((t - 0.25) / 0.75); }, // wind-up then go
  spring: (t, freq = 3, damp = 5) => { t = Math.max(0, t); return 1 - Math.exp(-damp * t) * Math.cos(freq * 2 * Math.PI * t); },  // settle wobble (t in s)
};
/** Centripetal Catmull-Rom through 3D points; u in [0,1] over the whole path (constant-ish speed). */
export const spline = (pts, u) => {
  const n = pts.length - 1, x = clamp(u) * n, i = Math.min(n - 1, Math.floor(x)), t = x - i;
  const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(n, i + 2)];
  return p1.map((_, k) => 0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t * t + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t * t * t));
};
/** Camera from keys {f,pos,look,fov,roll,ease?}. 3+ keys inside one glide use a spline (no corners).
 *  Every hold creeps (push-in) so nothing ever freezes; add kicks for impacts. */
export const camFromKeys = (K, f, { creep = 0.0012, kicks = [] } = {}) => {
  let c;
  if (f <= K[0].f) c = { ...K[0] };
  else if (f >= K[K.length - 1].f) c = { ...K[K.length - 1] };
  else {
    const i = K.findIndex((k, j) => f >= k.f && f <= K[j + 1].f), a = K[i], b = K[i + 1];
    const ease = M[b.ease || 'smooth'], t = ease((f - a.f) / (b.f - a.f));
    if (b.path) { // optional via-points for curved moves: b.path = [[x,y,z], ...]
      const pts = [a.pos, ...b.path, b.pos]; c = { pos: spline(pts, t), look: lerp3(a.look, b.look, t), fov: lerp(a.fov, b.fov, t), roll: lerp(a.roll || 0, b.roll || 0, t) };
    } else c = { pos: lerp3(a.pos, b.pos, t), look: lerp3(a.look, b.look, t), fov: lerp(a.fov, b.fov, t), roll: lerp(a.roll || 0, b.roll || 0, t) };
    if (a.fovBy || b.fovBy) { c.fovBy = {}; for (const k of new Set([...Object.keys(a.fovBy || {}), ...Object.keys(b.fovBy || {})])) c.fovBy[k] = lerp(a.fovBy?.[k] ?? a.fov, b.fovBy?.[k] ?? b.fov, t); }
  }
  const cr = 1 - creep * Math.max(0, f - K[0].f) * 0.15; c.fov *= cr; // gentle push-in during holds
  if (c.fovBy) { c.fovBy = { ...c.fovBy }; for (const k in c.fovBy) c.fovBy[k] *= cr; }
  for (const k of kicks) { const d = f - k.f; if (d >= 0 && d < 7) { const s = (d % 2 ? -1 : 1) * k.a * (1 - d / 7); c.look = [c.look[0], c.look[1] + s * 3, c.look[2] + s * 2]; c.roll = (c.roll || 0) + s * 20; } }
  return c;
};
/** Idle life for a card: breathing bob + small sway, deterministic per seed. Use on EVERY on-screen character. */
export const idle = (f, seed = 1) => ({
  bob: 0.006 * Math.sin((f + seed * 11) * 0.11),
  tilt: 1.2 * Math.sin((f + seed * 7) * 0.05),
  headTilt: 1.5 * Math.sin((f + seed * 5) * 0.037 + 1),
});
/** Blink: 4-frame lid every 0.5-2.3 s. */
export const blinkAt = (f, seed) => { const per = 38 + (seed * 17) % 31, ph = (f + seed * 13) % per; return ph < 2 ? 0.5 : ph < 4 ? 1 : 0; };
/** Walk: phase for step cycles + planted travel. speed m/s, stride m. */
export const walk = (f, f0, speed = 1.1, stride = 0.8) => { const t = Math.max(0, f - f0) / 30; return { dist: t * speed, phase: (t * speed / (2 * stride)) % 1 }; };
/** Round values used in card keys so canvas redraws happen only when the pose visibly changes. */
export const q = (x, n = 2) => Math.round(x * 10 ** n) / 10 ** n;

// ---------- multi-format framing (see FORMATS.md) ----------
/** Current output format, set by index.html: { key:'9x16'|'16x9'|'1x1'|'4x5'|'WxH', w, h, aspect, fit, master } */
export const FMT = (typeof window !== 'undefined' && window.FMT) || { key: '9x16', w: 1080, h: 1920, aspect: 0.5625, fit: 'height', master: false };
const rad = (d) => d * Math.PI / 180, deg = (r) => r * 180 / Math.PI;
/** vertical fov actually used on this canvas for an authored key fov (mirrors main.js fovFor) */
export const vfovOf = (fov, fmt = FMT) => fmt.fit === 'focal' ? deg(2 * Math.atan(Math.tan(rad(fov) / 2) * fmt.h / 1920)) : fov;
/** horizontal fov for a vertical fov and aspect (w/h) */
export const hfovOf = (vfov, aspect = FMT.aspect) => deg(2 * Math.atan(Math.tan(rad(vfov) / 2) * aspect));
/** visible half-width / half-height (metres) at distance d. 9:16, fov 40, d 4 m -> ±0.82 m wide; 16:9 -> ±2.59 m */
export const halfWidth = (d, fov, fmt = FMT) => d * Math.tan(rad(hfovOf(vfovOf(fov, fmt), fmt.aspect)) / 2);
export const halfHeight = (d, fov, fmt = FMT) => d * Math.tan(rad(vfovOf(fov, fmt)) / 2);
/** distance needed so a subject of half-width hw (m) fits horizontally with margin (e.g. two actors 1.6 m apart -> hw 1.1) */
export const distForWidth = (hw, fov, fmt = FMT, margin = 1.15) => hw * margin / Math.tan(rad(hfovOf(vfovOf(fov, fmt), fmt.aspect)) / 2);
/** pick a value per format: fmtPick({ '9x16': a, '16x9': b, default: c }) */
export const fmtPick = (o, fmt = FMT) => (fmt.key in o ? o[fmt.key] : o.default);
