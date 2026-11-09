// node _shots.mjs [paths] -> _shots/*.png (desktop 1440 + phone 390, full page) from the local preview on :8847. Scrolls first so reveal
// animations finish. Also prints console errors (CSP blocks show up here) and any horizontal overflow on phones.
// From Git Bash, run with MSYS_NO_PATHCONV=1 so "/" isn't turned into a Windows path.
import { createRequire } from 'module'; import fs from 'fs';
const require = createRequire(import.meta.url);
const pw = require('C:/Users/elift/Desktop/Eliftforlife youtube/14 failed businesses video/editor/main/node_modules/playwright');
fs.mkdirSync('_shots', { recursive: true });
const pages = process.argv.slice(2).length ? process.argv.slice(2) : ['/', '/companies/amazon/'];
const only = process.env.ONLY;   // 'desk' or 'phone'
const b = await pw.chromium.launch();
for (const [name, vp] of [['desk', { width: 1440, height: 900 }], ['phone', { width: 390, height: 844 }]]) {
  if (only && only !== name) continue;
  const p = await b.newPage({ viewport: vp });
  p.on('console', m => { if (m.type() === 'error') console.log(name, 'console:', m.text().slice(0, 200)); });
  p.on('pageerror', e => console.log(name, 'pageerror:', String(e).slice(0, 200)));
  for (const u of pages) {
    await p.goto('http://localhost:8847' + u, { waitUntil: 'networkidle' });
    const h = await p.evaluate(() => document.body.scrollHeight);
    for (let y = 0; y < h; y += 600) { await p.evaluate(y => scrollTo(0, y), y); await p.waitForTimeout(90); }
    await p.waitForTimeout(1200); await p.evaluate(() => scrollTo(0, 0)); await p.waitForTimeout(300);
    const over = await p.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    if (over > 1) console.log(name, u, 'OVERFLOW', over);
    const f = `_shots/${name}${u.replace(/[\/?=&]/g, '_')}.png`;
    await p.screenshot({ path: f, fullPage: true });
    console.log('saved', f);
  }
  await p.close();
}
await b.close(); console.log('shots done');
