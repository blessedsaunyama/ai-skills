// Character test sheet (2D only, fast): every Bible-era outfit + lion, sheep, glory, stone.
//   node cast.mjs stills/cast.png [keys,comma,separated] [expr]
// Run inside a project (needs web/toon.js). Look at the PNG before using new or edited designs in shots.
import http from 'http'; import fs from 'fs'; import path from 'path'; import { execSync } from 'child_process'; import { pathToFileURL } from 'url';
let chromium;
try { ({ chromium } = await import('playwright')); }
catch { const root = execSync('npm root -g', { encoding: 'utf8' }).trim(); ({ chromium } = await import(pathToFileURL(path.join(root, 'playwright', 'index.mjs')).href).catch(() => import(pathToFileURL(path.join(root, 'playwright', 'index.js')).href))); }
const [,, out = 'stills/cast.png', keys = '', expr = 'neutral'] = process.argv;
const root = process.env.WEB || path.resolve('web');
const page = `<!doctype html><html><body style="margin:0;background:#d8e4ee"><canvas id="c"></canvas><script type="module">
import * as T from './toon.js';
const keys = ${JSON.stringify(keys)} ? ${JSON.stringify(keys)}.split(',') : [...Object.keys(T.BIBLE), 'lion', 'lionOpen', 'sheep', 'glory', 'stone'];
const cols = 6, cw = 300, ch = 520, c = document.getElementById('c'); c.width = cols * cw; c.height = Math.ceil(keys.length / cols) * ch;
const g = c.getContext('2d'); g.fillStyle = '#d8e4ee'; g.fillRect(0, 0, c.width, c.height);
keys.forEach((k, i) => {
  const x = (i % cols) * cw, y = Math.floor(i / cols) * ch, cv = document.createElement('canvas'); cv.width = 600; cv.height = 1000;
  const p = new T.Pen(cv.getContext('2d'));
  if (k === 'lion') T.fxLion(p, {}); else if (k === 'lionOpen') T.fxLion(p, { mouth: 'open', pose: 'sit' });
  else if (k === 'sheep') T.fxSheep(p, {}); else if (k === 'glory') T.fxGlory(p, 0.2); else if (k === 'stone') T.fxStone(p);
  else T.bibleFront(p, k, { expr: '${expr}', seed: 3 + i, L: 'hang', wings: false });
  g.drawImage(cv, x, y, cw, 500); g.fillStyle = '#222'; g.font = '20px Arial'; g.fillText(k, x + 10, y + 512);
});
window.done = true;
</script></body></html>`;
const srv = http.createServer((q, s) => { const u = decodeURIComponent(q.url.split('?')[0]); if (u === '/cast.html') { s.writeHead(200, { 'Content-Type': 'text/html' }); return s.end(page); } const p = path.join(root, u); if (!fs.existsSync(p)) { s.writeHead(404); return s.end(); } s.writeHead(200, { 'Content-Type': p.endsWith('.js') ? 'text/javascript' : 'text/html' }); fs.createReadStream(p).pipe(s); }).listen(0);
await new Promise(r => srv.on('listening', r));
const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1800, height: 1200 } });
pg.on('pageerror', e => console.log('ERR', e.message)); pg.on('console', m => console.log('PAGE', m.text()));
await pg.goto(`http://localhost:${srv.address().port}/cast.html`); await pg.waitForFunction(() => window.done, null, { timeout: 60000 });
fs.mkdirSync(path.dirname(out), { recursive: true });
await (await pg.$('#c')).screenshot({ path: out }); console.log(out);
await b.close(); srv.close();
