// World for "Thy servant kept his father's sheep" (1 Sam 17:34): a hillside pasture at golden hour.
// buildWorld(ctx) builds the 3D set once; update(state, f) animates it per frame. Everything here is 🎨 (artistic):
// the text gives no landscape details. Ancient Near East look: flat-roofed houses, olive trees, a stone sheepfold.
export function buildWorld(ctx) {
  const { THREE, M, P, world, add, tbox, toon } = ctx;
  const W = world;
  // ground: a big gently rolling field (one plane, grass texture), and a dirt path
  const field = add(new THREE.PlaneGeometry(400, 400, 1, 1), M.grass, 0, 0, 0, W, { cast: false }); field.rotation.x = -Math.PI / 2;
  const path = add(new THREE.PlaneGeometry(2.2, 60), M.dirt, 3.2, 0.01, -18, W, { cast: false }); path.rotation.x = -Math.PI / 2; path.rotation.z = 0.35;
  // stone sheepfold behind the flock (low dry-stone wall, a gap for the gate)
  const r = P.rng(7), stoneM = M.stone;
  for (let i = 0; i < 26; i++) {
    const a = Math.PI * (0.15 + 1.7 * i / 25); if (i === 12 || i === 13) continue;
    const x = -2.5 + Math.cos(a) * 4.2, z = -5.2 + Math.sin(a) * 2.6;
    const s = add(tbox(0.9 + r() * 0.4, 0.75 + r() * 0.2, 0.6, 1.2), stoneM, x, 0.4, z, W); s.rotation.y = -a + Math.PI / 2;
  }
  // olive trees: twisted trunk + soft canopy blobs
  const olive = (x, z, h = 3) => {
    const g = new THREE.Group(); g.position.set(x, 0, z); W.add(g);
    const t = add(new THREE.CylinderGeometry(0.16, 0.28, h * 0.55, 7), M.trunk, 0, h * 0.27, 0, g); t.rotation.z = 0.15;
    for (let k = 0; k < 4; k++) { const c = add(new THREE.SphereGeometry(h * (0.28 + 0.06 * k % 2), 10, 8), toon({ color: k % 2 ? '#7d9a5a' : '#6e8c4e' }), (k - 1.5) * h * 0.22, h * (0.62 + 0.08 * (k % 2)), (k % 2 - 0.5) * h * 0.25, g); c.scale.y = 0.7; }
    return g;
  };
  [[-6.5, -3, 3.2], [5.5, -6, 3.6], [-11, -14, 4], [10, -15, 3.4], [-17, -6, 3.8], [16, -4, 3.3], [2, -22, 4.2]].forEach(([x, z, h]) => olive(x, z, h));
  // village on the far hill: flat roofs with a low parapet (Deut 22:8 style), plaster walls
  const hill = add(new THREE.SphereGeometry(40, 32, 16), M.hill, -10, -26, -95, W, { cast: false }); hill.scale.set(1.6, 1, 0.8);
  const house = (x, y, z, w, d, h, rot) => {
    const g = new THREE.Group(); g.position.set(x, y, z); g.rotation.y = rot; W.add(g);
    add(tbox(w, h, d, 2), r() < 0.5 ? M.plaster : M.plaster2, 0, h / 2, 0, g);
    add(tbox(w + 0.2, 0.35, d + 0.2, 2), M.plaster2, 0, h + 0.17, 0, g);
    add(new THREE.BoxGeometry(0.8, 1.6, 0.1), M.door, 0, 0.8, d / 2 + 0.03, g, { cast: false });
    return g;
  };
  for (let i = 0; i < 11; i++) house(-26 + i * 5 + r() * 2, 9 + r() * 3.5, -70 - r() * 12, 3 + r() * 2.5, 3 + r() * 2, 2.6 + r() * 1.6, r() * 0.6 - 0.3);
  // rolling hills
  for (let i = 0; i < 14; i++) { const a = r() * Math.PI * 2, d = 140 + r() * 140; const h = add(new THREE.SphereGeometry(40 + r() * 40, 20, 10), i % 2 ? M.hill : M.hillFar, Math.cos(a) * d, -14, Math.sin(a) * d, W, { cast: false }); h.scale.y = 0.45 + r() * 0.3; }
  return { ground: 0, update: () => {} };
}
