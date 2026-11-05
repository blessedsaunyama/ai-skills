// Render SVG files to PNG / PDF with Playwright Chromium.
// usage: node render_chromium.cjs jobs.json
// jobs: [{"svg": "abs path", "out": "abs path", "type": "png"|"pdf", "w": px or mm, "h": px or mm}]
const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
let chromium;
try { ({ chromium } = require("playwright")); }
catch (e) {
  try { ({ chromium } = require("playwright-core")); }
  catch (e2) { console.error("NO_PLAYWRIGHT"); process.exit(3); }
}

(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
  const browser = await chromium.launch();
  const page = await browser.newPage();
  for (const j of jobs) {
    const url = pathToFileURL(j.svg).href;
    if (j.type === "png") {
      await page.setViewportSize({ width: Math.round(j.w), height: Math.round(j.h) });
      await page.goto(url, { waitUntil: "load" });
      await page.screenshot({ path: j.out, omitBackground: !!j.transparent });
    } else {
      const html = path.join(path.dirname(j.svg), "_print_" + path.basename(j.svg) + ".html");
      // Inline the SVG (an <img> may not load font files referenced by @font-face).
      let svg = fs.readFileSync(j.svg, "utf8").replace(/<\?xml[^>]*\?>/, "").replace(/<!DOCTYPE[^>]*>/i, "");
      fs.writeFileSync(html, `<!doctype html><html><head><meta charset="utf-8"><style>@page{size:${j.w}mm ${j.h}mm;margin:0}html,body{margin:0;padding:0}body>svg{display:block;width:${j.w}mm;height:${j.h}mm}</style></head><body>${svg}</body></html>`);
      await page.goto(pathToFileURL(html).href, { waitUntil: "load" });
      await page.pdf({ path: j.out, width: `${j.w}mm`, height: `${j.h}mm`, printBackground: true, preferCSSPageSize: true });
      fs.unlinkSync(html);
    }
    console.log("OK " + j.out);
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
