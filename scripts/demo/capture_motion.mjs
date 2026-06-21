// Capture REAL motion from the live UI (not static screenshots):
//   hero.webm    - the Three.js "circle of takes" constellation rotating
//   montage.webm - the autonomous roll, clips auto-playing, smooth scroll top->bottom
//   gate.webm    - the Anchor Gate scene animating in (the QUARANTINE stamp lands)
//   cut.webm     - the CUT clapper animating in
// These give genuine on-screen movement for the demo cut.
//
// Usage: node scripts/demo/capture_motion.mjs [baseUrl] [outDir]
import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';

const BASE = process.argv[2] || 'http://localhost:8000/ui/';
const OUT = process.argv[3] || 'scripts/demo/build/motion';
mkdirSync(OUT, { recursive: true });
const SIZE = { width: 1920, height: 1080 };

const FALLBACK = '/Users/kimsejun/Library/Caches/ms-playwright/chromium-1169/chrome-mac/Chromium.app/Contents/MacOS/Chromium';
let browser;
try { browser = await chromium.launch({ headless: true, channel: 'chrome' }); }
catch { browser = await chromium.launch({ headless: true, executablePath: FALLBACK }); }

// Force any <video> to play muted+looping so the Wan clips move on camera.
const AUTOPLAY = `
  (function(){
    setInterval(function(){
      document.querySelectorAll('video').forEach(function(v){
        v.muted = true; v.loop = true; v.playsInline = true;
        if (v.paused) v.play().catch(function(){});
      });
    }, 150);
  })();`;

async function newPage() {
  const ctx = await browser.newContext({ viewport: SIZE, recordVideo: { dir: OUT, size: SIZE } });
  const page = await ctx.newPage();
  page.setDefaultTimeout(90000);
  await page.addInitScript(AUTOPLAY);
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

// 1) HERO — 3D constellation rotating + gentle parallax sweep
{
  const { ctx, page } = await newPage();
  await page.goto(BASE, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2200);
  for (let i = 0; i < 36; i++) {
    await page.mouse.move(560 + i * 22, 420 + Math.sin(i / 5) * 90);
    await page.waitForTimeout(160);
  }
  await save(ctx, page, 'hero.webm');
}

// 2) MONTAGE — run the real roll, clips playing, then smooth-scroll the whole reel
{
  const { ctx, page } = await newPage();
  await page.goto(BASE, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  await page.click('#roll');
  await page.waitForFunction(() => { const b = document.querySelector('#roll'); return b && !b.disabled; }, { timeout: 90000 });
  await page.waitForTimeout(600);
  // smooth scroll from top of reel to the bottom over ~10s
  await page.evaluate(() => window.scrollTo({ top: document.querySelector('#reel').offsetTop - 40, behavior: 'instant' }));
  await page.waitForTimeout(700);
  const steps = 60;
  const maxY = await page.evaluate(() => document.body.scrollHeight - window.innerHeight);
  const startY = await page.evaluate(() => window.scrollY);
  for (let i = 1; i <= steps; i++) {
    const y = startY + ((maxY - startY) * i) / steps;
    await page.evaluate((yy) => window.scrollTo({ top: yy, behavior: 'instant' }), y);
    await page.waitForTimeout(150);
  }
  await page.waitForTimeout(500);
  await save(ctx, page, 'montage.webm');
}

// (Per-scene reveal clips were dropped: a single recording spans the whole roll,
//  so the build uses Ken Burns on the exact stills for CUT / Anchor Gate instead.)

await browser.close();
console.log('DONE — motion clips in', OUT);
