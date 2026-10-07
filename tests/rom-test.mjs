// The ROM's whole journey, headless, through the real drop path:
//
//   ROM_PATH=~/roms/mk64.z64 node rom-test.mjs <buildDir>
//
// Visit 1 starts from a clean profile, feeds the ROM to the file input and
// waits for the in-browser extraction and the engine. Visit 2 has to boot
// straight from the cache. Then "Clear cached game data" has to put the page
// back to asking for a ROM. Takes a couple of minutes: the extraction is the
// slow part and runs on the main thread.
import { SCRATCH, check, finish, serve, buildDir, chromium, launchArgs, exec, collect, startAndDropRom, waitForBoot } from './common.mjs';
import fs from 'node:fs';

const PORT = 8099;
const PROFILE = SCRATCH + '/kart64-profile';
fs.rmSync(PROFILE, { recursive: true, force: true });
const server = await serve(buildDir(), PORT);
const ctx = await chromium.launchPersistentContext(PROFILE, { ...exec(), args: launchArgs, viewport: { width: 960, height: 720 } });
try {
  // --- visit 1: drop the ROM, extract, boot -------------------------------------
  const page = await ctx.newPage();
  const logs = collect(page);
  await page.goto(`http://127.0.0.1:${PORT}/index.html`);
  check('the capability gate passed (Start is visible)', await page.isVisible('#start'));
  const outcome = await startAndDropRom(page);
  check('the page asked for the ROM on a clean profile', outcome === 'drop', outcome);
  // The extraction runs on a worker thread; a timer on the page must keep
  // firing throughout, or the tab is frozen.
  await page.evaluate(() => { window.__gap = 0; let last = performance.now(); setInterval(() => { const n = performance.now(); window.__gap = Math.max(window.__gap, n - last); last = n; }, 250); });
  const booted1 = await waitForBoot(page, logs);
  check('the ROM was accepted and extraction started', logs.some(l => /Extracting the game/.test(l)));
  const gap = await page.evaluate(() => Math.round(window.__gap));
  check('the page stayed responsive during extraction (longest stall under 1s)', gap < 1000, `${gap}ms`);
  check('the engine booted', booted1, `${logs.length} lines`);
  check('no setup failures, page errors or aborts', !logs.some(l => /Setup failed|Wrong ROM|Not an N64 ROM|PAGEERROR|Aborted/.test(l)));
  // A desktop defaults to the 4:3 picture, scaled to the largest box that fits.
  const pic = await page.evaluate(() => { const c = document.getElementById('canvas'), r = c.getBoundingClientRect(); return [c.width, c.height, Math.round(r.width), Math.round(r.height)]; });
  check('the picture is 4:3 and fills the 960x720 window', pic[0] * 3 === pic[1] * 4 && pic[2] === 960 && pic[3] === 720, pic.join(','));
  check('the start page dressing is gone once the game runs', !(await page.isVisible('.road')));
  // The ROM is deleted from browser storage once the archive exists.
  await page.waitForTimeout(25000); // the first sync runs 20s after boot
  const romGone = await page.evaluate(() => !FS.analyzePath('/data/baserom.us.z64').exists && FS.analyzePath('/data/mk64.o2r').exists);
  check('the ROM was removed from storage after extraction', romGone);

  // --- visit 2: boot from the cache ---------------------------------------------
  logs.length = 0;
  await page.goto(`http://127.0.0.1:${PORT}/index.html`);
  check('the reset button is offered once data is cached', await page.isVisible('#reset'));
  await page.click('#start');
  const booted2 = await waitForBoot(page, logs, 90000);
  check('visit 2 booted from cached assets', booted2 && logs.some(l => l.includes('Booting from cached assets')));
  check('visit 2 did not re-extract', !logs.some(l => l.includes('Extracting the game')));
  check('visit 2 had no errors', !logs.some(l => /PAGEERROR|Setup failed/.test(l)));

  // --- reset: the drop zone has to come back -------------------------------------
  await page.goto(`http://127.0.0.1:${PORT}/index.html`);
  page.once('dialog', d => d.accept());
  await page.click('#reset');
  await page.waitForTimeout(3000);
  await page.click('#start');
  const askedAgain = await page.waitForSelector('#drop:not(.hidden)', { timeout: 120000 }).then(() => true).catch(() => false);
  check('after reset the page asks for the ROM again', askedAgain);
} finally {
  await ctx.close();
  server.kill();
}
finish();
