// node make_assets.mjs -> assets/og.png (1200x630 share card). icon.png / logo-*.png come from 4 Business Census/Branding/final/business-study-avatar.png
import { createRequire } from 'module';
import fs from 'fs';
const b64 = f => fs.readFileSync(f).toString('base64');
const FD = 'C:/Users/elift/Desktop/Eliftforlife youtube/1 Elijah Westbrook/Stream/overlay/fonts/';
const require = createRequire(import.meta.url);
const pw = require('C:/Users/elift/Desktop/Eliftforlife youtube/14 failed businesses video/editor/main/node_modules/playwright');
const F = `@font-face{font-family:I;font-weight:900;src:url(data:font/woff2;base64,${b64(FD + 'inter-latin-900-normal.woff2')})}@font-face{font-family:I;font-weight:700;src:url(data:font/woff2;base64,${b64(FD + 'inter-latin-700-normal.woff2')})}`;
const b = await pw.chromium.launch({ args: ['--allow-file-access-from-files'] });
const p = await b.newPage({ viewport: { width: 1200, height: 630 } });
await p.setContent(`<style>${F}html,body{margin:0;width:1200px;height:630px;background:#fff;font-family:I;color:#111}
.w{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;padding:0 90px}
h1{font-weight:900;font-size:88px;letter-spacing:-.045em;line-height:1;margin:0}
mark{background:#2456e8;color:#fff;border-radius:16px;padding:0 18px 8px}
p{font-weight:700;font-size:34px;color:#5f6368;margin:34px 0 0}
.n{position:absolute;left:90px;bottom:60px;display:flex;align-items:center;gap:16px;font-weight:900;font-size:32px}
.n img{width:56px;height:56px;border-radius:12px}</style>
<div class="w"><h1>Real data on every <mark>business</mark> question.</h1><p>Free studies on creators, sales, ads and money.</p></div><div class="n"><img src="data:image/png;base64,${b64('assets/logo-128.png')}">thebusinessstudy.com</div>`);
await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(300);
await p.screenshot({ path: 'assets/og.png' });
await b.close(); console.log('assets done');
