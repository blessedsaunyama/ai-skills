// Shot plan: "Thy servant kept his father's sheep" (1 Sam 17:34, KJV) -- 5 s engine preview, 30 fps.
// Young David (shepherdBoy, a youth: card s 0.9) watches his father's flock at golden hour. No lion or bear on screen:
// the danger in v.34-35 is told, not shown (violence implied only).
import { M as E, camFromKeys, idle, blinkAt, q, ramp, lerp } from './motion.js';
export const FPS = 30, TOTAL = 150;
export const SHOTS = [
  { id: 'wide', a: 0, b: 74, light: 'golden' },
  { id: 'close', a: 75, b: 149, light: 'golden' },
];
export const shotAt = (f) => SHOTS.find((s) => f >= s.a && f <= s.b) || SHOTS[SHOTS.length - 1];

export const LIGHTS = {
  golden: { az: 200, el: 14, sky: '#a9a2d0', ground: '#6a5a40', hemi: 1.05, sun: '#ffc98a', sunI: 2.7, fog: '#f2c79a', fogNear: 40, fogFar: 380,
    skyTop: '#7f86c4', skyHor: '#ffd29a', sunDisc: '#fff2cc', sunSize: 0.004, sat: 1.1, gain: '#fff4e6', vig: 0.24, shadowExt: 14 },
};
export const lightFor = (S, f) => ({ ...LIGHTS[S.light] });

const BOY = [0, 0, 0];
// camera keys: fov = vertical fov of a 1080x1920 frame; fovBy gives each format its own framing (BEST mode)
const CAMS = {
  wide: [
    { f: 0, pos: [2.2, 1.7, 9.5], look: [-0.6, 1.0, -1.5], fov: 44, fovBy: { '16x9': 30, '1x1': 38, '4x5': 40 } },
    { f: 74, pos: [1.6, 1.55, 7.6], look: [-0.4, 0.95, -1.2], fov: 42, fovBy: { '16x9': 28, '1x1': 36, '4x5': 38 } },
  ],
  close: [
    { f: 75, pos: [-2.5, 1.3, 4.0], look: [0.1, 1.15, 0], fov: 38, fovBy: { '16x9': 34, '1x1': 34 } },
    { f: 149, pos: [-2.15, 1.25, 3.4], look: [0.1, 1.15, 0], fov: 36, fovBy: { '16x9': 32, '1x1': 32 } },
  ],
};
export const camAt = (f) => { const c = camFromKeys(CAMS[shotAt(f).id], f); c.shadowAt = [0, 0, -1]; return c; };
const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
export const dofAt = (f) => { const C = camAt(f); return { focus: dist(C.pos, [0, 1.1, 0]), cinf: shotAt(f).id === 'wide' ? 6 : 10 }; };
export const worldAt = (f) => ({});

// flock: [x, z, seed, facing right?, graze phase]
const FLOCK = [[-1.6, -1.2, 1, 1, 0], [1.4, -0.6, 2, 0, 9], [-2.8, -2.6, 3, 1, 21], [0.6, -2.4, 4, 0, 5], [2.6, -2.2, 5, 1, 30],
  [-0.9, -3.6, 6, 0, 14], [-3.9, -1.0, 7, 1, 40], [3.8, -0.4, 8, 0, 3], [1.9, -4.2, 9, 1, 25], [-4.6, -3.2, 10, 0, 11]];
export const actorsAt = (f, T) => {
  const out = [], S = shotAt(f), id = idle(f, 4);
  const look = S.id === 'close' ? q(-0.35 + 0.15 * Math.sin(f * 0.04), 2) : -0.2;
  const o = { seed: 4, expr: S.id === 'close' && f > 110 ? 'smile' : 'neutral', look, blink: blinkAt(f, 4), bob: q(id.bob, 3), tilt: q(id.tilt, 1), headTilt: q(id.headTilt, 1) };
  out.push({ key: 'boy' + JSON.stringify(o), draw: (p) => T.bibleFront(p, 'shepherdBoy', o), x: BOY[0], y: BOY[1], z: BOY[2], s: 0.9 });
  FLOCK.forEach(([x, z, seed, right, ph], i) => {
    const graze = q(Math.sin((f + ph * 3) * 0.08), 1), dx = 0.004 * Math.sin((f + ph * 5) * 0.02) * 30;
    out.push({ key: 'sheep' + seed + graze, draw: (p) => T.fxSheep(p, { seed, look: graze }), x: x + dx, y: 0, z, s: 1.0, flip: !!right, order: 2 });
  });
  return out;
};
export const fxAt = (f, T) => [];
