// Capture every stage of the live Circle Take golden-path UI as high-res stills.
// The roll (#roll "Roll the demo") drives the real API and appends one .scene per
// cue; after it finishes all scenes remain in the DOM, so we screenshot each one.
// Every frame here is a real screenshot of the real product — no mockups.
//
// Usage: node scripts/demo/capture.mjs [baseUrl] [outDir]
//   baseUrl default http://localhost:8000/ui/
//   outDir  default scripts/demo/build/shots
import { chromium } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';

const BASE = process.argv[2] || 'http://localhost:8000/ui/';
const OUT = process.argv[3] || 'scripts/demo/build/shots';
mkdirSync(OUT, { recursive: true });

// Browser-revision in the playwright cache doesn't match this build, so use an
// existing binary instead of downloading: system Chrome first, full Chromium fallback.
const FALLBACK = '/Users/kimsejun/Library/Caches/ms-playwright/chromium-1169/chrome-mac/Chromium.app/Contents/MacOS/Chromium';
let browser;
try {
  browser = await chromium.launch({ headless: true, channel: 'chrome' });
} catch {
  browser = await chromium.launch({ headless: true, executablePath: FALLBACK });
}
const ctx = await browser.newContext({
  viewport: { width: 1920, height: 1080 },
  deviceScaleFactor: 2, // retina-crisp; downscaled later by ffmpeg
});
const page = await ctx.newPage();
page.setDefaultTimeout(60000);

console.log('goto', BASE);
await page.goto(BASE, { waitUntil: 'networkidle' });
await page.waitForTimeout(2500); // let webfonts + three.js hero settle

// 0) Title / hero — full viewport
await page.screenshot({ path: `${OUT}/00_title.png` });
console.log('shot 00_title');

// Drive the real golden path.
await page.click('#roll');
// Roll disables #roll for its duration and re-enables it in finally{} when done.
await page.waitForFunction(
  () => { const b = document.querySelector('#roll'); return b && !b.disabled; },
  { timeout: 90000 },
);
await page.waitForTimeout(800);

// Keep the raw-JSON slate collapsed: the verdict header + per-violation detail
// lines are already on screen and far more legible than a wall of JSON in 3 min.

// Screenshot each appended scene, tightly framed.
const scenes = await page.$$('#reel .scene');
console.log('scenes:', scenes.length);
const index = [];
for (let i = 0; i < scenes.length; i++) {
  const el = scenes[i];
  await el.evaluate((n) => n.scrollIntoView({ block: 'center' }));
  await page.waitForTimeout(450);
  const txt = (await el.evaluate((n) => n.innerText || '')).replace(/\s+/g, ' ').slice(0, 90);
  const name = `${String(i + 1).padStart(2, '0')}_scene.png`;
  await el.screenshot({ path: `${OUT}/${name}` });
  index.push({ i: i + 1, file: name, text: txt });
  console.log('shot', name, '::', txt);
}
writeFileSync(`${OUT}/index.json`, JSON.stringify(index, null, 2));

await browser.close();
console.log('DONE — shots in', OUT);
