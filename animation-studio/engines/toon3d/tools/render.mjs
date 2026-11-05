// usage: node render.mjs <outdir> <frames: "a-b" or "1,2,3"> [step] [quality]
// Format (env):  FMT=9x16 | 16x9 | 1x1 | 4x5        (default 9x16; BEST mode = one run per format)
//                SIZE=1920x1920                     (FAST master; fit defaults to "focal")
//                FIT=height|focal                   (override how key fovs map to this canvas)
//                SCALE=0.6667  preview size, same framing     RESUME=1  skip frames that exist     HASH=#nd / #e  debug passes     WEB=dir  engine dir
import http from 'http'; import fs from 'fs'; import path from 'path'; import { execSync } from 'child_process'; import { pathToFileURL } from 'url';

// Playwright: local install first, then the global npm root (no symlinks needed, works on Windows/Mac/Linux)
let chromium;
try { ({ chromium } = await import('playwright')); }
catch {
  const root = execSync('npm root -g', { encoding: 'utf8' }).trim();
  ({ chromium } = await import(pathToFileURL(path.join(root, 'playwright', 'index.mjs')).href).catch(() => import(pathToFileURL(path.join(root, 'playwright', 'index.js')).href)));
}

const [,, outdir, spec, step = '1', qual = '0.96'] = process.argv;
if (!outdir || !spec) { console.log('usage: node render.mjs <outdir> <frames "a-b" or "1,2,3"> [step] [quality]'); process.exit(1); }
const FORMATS = { '9x16': [1080, 1920], '16x9': [1920, 1080], '1x1': [1080, 1080], '4x5': [1080, 1350] };
let query, W, H;
if (process.env.SIZE) { [W, H] = process.env.SIZE.toLowerCase().split('x').map(Number); query = `?w=${W}&h=${H}`; }
else { const k = process.env.FMT || '9x16'; if (!FORMATS[k]) { console.log('unknown FMT ' + k + ' (use ' + Object.keys(FORMATS).join(', ') + ')'); process.exit(1); } [W, H] = FORMATS[k]; query = `?fmt=${k}`; const sc = +(process.env.SCALE || 1); if (sc !== 1) { W = Math.round(W * sc / 2) * 2; H = Math.round(H * sc / 2) * 2; query += `&scale=${sc}`; } }
if (process.env.FIT) query += `&fit=${process.env.FIT}`;
fs.mkdirSync(outdir, { recursive: true });
let frames = [];
for (const part of spec.split(',')) { if (part.includes('-')) { const [a, b] = part.split('-').map(Number); for (let f = a; f <= b; f += +step) frames.push(f); } else frames.push(+part); }
const root = process.env.WEB || path.resolve('web');
const srv = http.createServer((q, s) => { const p = path.join(root, decodeURIComponent(q.url.split('?')[0])); if (!fs.existsSync(p)) { s.writeHead(404); return s.end(); } s.writeHead(200, { 'Content-Type': p.endsWith('.js') ? 'text/javascript' : 'text/html' }); fs.createReadStream(p).pipe(s); }).listen(0);
await new Promise(r => srv.on('listening', r));
const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const pg = await b.newPage({ viewport: { width: W, height: H } });
pg.on('console', m => console.log('PAGE', m.text())); pg.on('pageerror', e => console.log('ERR', e.message));
await pg.goto(`http://localhost:${srv.address().port}/index.html${query}${process.env.HASH || ''}`);
await pg.waitForFunction(() => window.ready || window.err, null, { timeout: 180000 });
if (await pg.evaluate(() => window.err)) { console.log('page error'); process.exit(1); }
console.log(`format ${await pg.evaluate(() => JSON.stringify(window.FMT))}`);
const t0 = Date.now(); let n = 0; const times = [];
for (const f of frames) {
  const file = path.join(outdir, `f${String(f).padStart(4, '0')}.jpg`);
  if (process.env.RESUME && fs.existsSync(file)) continue;
  const tf = Date.now();
  const d = await pg.evaluate(([f, q]) => { if (window.location.hash === "#nd") window.DEBUG_ND = 1; if (window.location.hash === "#e") window.DEBUG_E = 1; window.renderFrame(f); return document.getElementById('c').toDataURL('image/jpeg', q); }, [f, +qual]);
  times.push(Date.now() - tf);
  fs.writeFileSync(file + '.tmp', Buffer.from(d.split(',')[1], 'base64')); fs.renameSync(file + '.tmp', file); n++;   // atomic: safe to resume
  if (n % 30 === 0) console.log(`progress ${n}/${frames.length} frames, ${((Date.now() - t0) / n / 1000).toFixed(2)} s/frame`);
}
const steady = times.length > 1 ? times.slice(1).sort((x, y) => x - y)[Math.floor((times.length - 1) / 2)] : (times[0] || 0);
console.log(`steady ${(steady / 1000).toFixed(2)} s/frame (median, without the first-frame warm-up)`);
console.log(`done ${n} frames, ${((Date.now() - t0) / Math.max(1, n) / 1000).toFixed(2)} s/frame, ${W}x${H}`);
await b.close(); srv.close();
