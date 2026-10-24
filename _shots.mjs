// node _shots.mjs [paths] -> _shots/*.png (desktop + phone, full page) from the local server on :8812. Scrolls first so reveal animations finish.
import { createRequire } from 'module'; import fs from 'fs';
const require = createRequire(import.meta.url);
const pw = require('C:/Users/elift/Desktop/Eliftforlife youtube/14 failed businesses video/editor/main/node_modules/playwright');
fs.mkdirSync('_shots', { recursive: true });
const pages = process.argv.slice(2).length ? process.argv.slice(2) : ['/', '/studies/how-much-youtube-pays/'];
const b = await pw.chromium.launch();
for (const [name, vp] of [['desk', { width: 1280, height: 900 }], ['phone', { width: 390, height: 844 }]]) {
  const p = await b.newPage({ viewport: vp });
  for (const u of pages) {
    await p.goto('http://localhost:8812' + u, { waitUntil: 'networkidle' });
    const h = await p.evaluate(() => document.body.scrollHeight);
    for (let y = 0; y < h; y += 500) { await p.evaluate(y => scrollTo(0, y), y); await p.waitForTimeout(120); }
    await p.waitForTimeout(1600); await p.evaluate(() => scrollTo(0, 0)); await p.waitForTimeout(300);
    await p.screenshot({ path: `_shots/${name}${u.replace(/\//g, '_')}.png`, fullPage: true });
  }
  await p.close();
}
await b.close(); console.log('shots done');
