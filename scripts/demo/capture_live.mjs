// Capture two "real operation" clips for the demo:
//   terminal.webm    - the branded terminal replaying the REAL live-run log
//                      (real Qwen3.7-plus + Alibaba OSS output)
//   interactive.webm - a visible cursor pressing "Roll the demo" and the real
//                      golden-path cards rendering live (operating the product)
//
// Usage: node scripts/demo/capture_live.mjs [baseUrl] [outDir]
import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

const BASE = process.argv[2] || 'http://localhost:8000/ui/';
const OUT = process.argv[3] || 'scripts/demo/build/motion';
mkdirSync(OUT, { recursive: true });
const SIZE = { width: 1920, height: 1080 };

const FALLBACK = '/Users/kimsejun/Library/Caches/ms-playwright/chromium-1169/chrome-mac/Chromium.app/Contents/MacOS/Chromium';
let browser;
try { browser = await chromium.launch({ headless: true, channel: 'chrome' }); }
catch { browser = await chromium.launch({ headless: true, executablePath: FALLBACK }); }

async function newPage() {
  const ctx = await browser.newContext({ viewport: SIZE, recordVideo: { dir: OUT, size: SIZE } });
  const page = await ctx.newPage();
  page.setDefaultTimeout(90000);
  return { ctx, page };
}
async function save(ctx, page, name) {
  const v = page.video();
  await page.close();
  await ctx.close();
  await v.saveAs(`${OUT}/${name}`);
  await v.delete();
  console.log('saved', name);
}

// 1) TERMINAL — replay the real live-run log
{
  const { ctx, page } = await newPage();
  const url = pathToFileURL(resolve('scripts/demo/terminal.html')).href;
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForTimeout(9000); // let the typewriter finish + hold
  await save(ctx, page, 'terminal.webm');
}

// 2) INTERACTIVE — synthetic cursor presses "Roll the demo", cards render live
{
  const { ctx, page } = await newPage();
  await page.goto(BASE, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  // inject a visible cursor that follows mouse moves
  await page.evaluate(() => {
    const c = document.createElement('div');
    c.id = '__cursor';
    c.style.cssText = 'position:fixed;z-index:99999;width:26px;height:26px;left:0;top:0;'
      + 'pointer-events:none;transition:transform .04s linear;'
      + 'background:radial-gradient(circle at 35% 35%,#fff,#fff 30%,#e6324b 32%,#e6324b 60%,transparent 62%);'
      + 'filter:drop-shadow(0 2px 6px rgba(0,0,0,.5))';
    document.body.appendChild(c);
    window.__moveCur = (x, y) => { c.style.transform = `translate(${x}px,${y}px)`; };
  });
  const btn = await page.$('#roll');
  const box = await btn.boundingBox();
  const tx = Math.round(box.x + box.width / 2);
  const ty = Math.round(box.y + box.height / 2);
  // glide the cursor toward the button
  for (let i = 0; i <= 24; i++) {
    const x = Math.round(960 + (tx - 960) * (i / 24));
    const y = Math.round(620 + (ty - 620) * (i / 24));
    await page.evaluate(([x, y]) => window.__moveCur(x, y), [x, y]);
    await page.mouse.move(x, y);
    await page.waitForTimeout(28);
  }
  await page.waitForTimeout(350);
  // press: shrink the cursor briefly, then click
  await page.evaluate(() => { document.getElementById('__cursor').style.scale = '0.8'; });
  await page.waitForTimeout(140);
  await page.click('#roll');
  await page.evaluate(() => { document.getElementById('__cursor').style.scale = '1'; });
  // let the first ~3 cards render live, gently scrolling to follow
  await page.waitForTimeout(2600);
  for (let s = 0; s < 5; s++) {
    await page.evaluate(() => window.scrollBy({ top: 360, behavior: 'smooth' }));
    await page.waitForTimeout(900);
  }
  await save(ctx, page, 'interactive.webm');
}

await browser.close();
console.log('DONE — live-operation clips in', OUT);
