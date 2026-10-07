// The capability gate, and the page's static behaviour before any wasm loads.
// Needs only web/ (or a build dir): Spaghettify.js is never requested.
//
//   node gate-test.mjs [dir]        (defaults to ../web)
//
// 1. Served WITHOUT COOP/COEP, as GitHub Pages serves, the page isolates
//    itself with its service worker and offers Start after one reload.
// 2. Where the service worker cannot run either, it must refuse with a clear
//    message and no Start button.
// 3. Served WITH the headers, Start is offered straight away, no service
//    worker is registered, and the reset button is not shown (nothing is
//    cached yet).
import { check, finish, serve, chromium, launchArgs, exec, collect, ROOT } from './common.mjs';
import path from 'node:path';

const dir = path.resolve(process.argv[2] || path.join(ROOT, '..', 'web'));
const browser = await chromium.launch({ ...exec(), args: launchArgs });

// A plain server: no isolation headers.
const plain = await serve(dir, 8098, true);
const server = await serve(dir, 8099);
try {
  let page = await browser.newPage();
  let logs = collect(page);
  await page.goto('http://127.0.0.1:8098/index.html');
  await page.waitForFunction(() => self.crossOriginIsolated, null, { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(300);
  check('without COOP/COEP: the service worker isolates the page', await page.evaluate(() => self.crossOriginIsolated));
  check('without COOP/COEP: the page is controlled by coi-sw.js',
    await page.evaluate(() => /coi-sw\.js$/.test(navigator.serviceWorker.controller?.scriptURL || '')));
  check('without COOP/COEP: Start is visible', await page.isVisible('#start'));
  check('without COOP/COEP: no page errors', !logs.some(l => /PAGEERROR/.test(l)));
  await page.close();

  // No headers and no service worker (a private window, say): say so.
  const blocked = await browser.newContext({ serviceWorkers: 'block' });
  page = await blocked.newPage();
  logs = collect(page);
  await page.goto('http://127.0.0.1:8098/index.html');
  await page.waitForFunction(() => /Cross-Origin-Opener-Policy/.test(document.getElementById('status').textContent), null, { timeout: 15000 }).catch(() => {});
  check('no headers, no service worker: Start is hidden', !(await page.isVisible('#start')));
  check('no headers, no service worker: the status names the headers',
    /Cross-Origin-Opener-Policy/.test(await page.textContent('#status')));
  check('no headers, no service worker: no page errors', !logs.some(l => /PAGEERROR/.test(l)));
  await blocked.close();

  page = await browser.newPage();
  logs = collect(page);
  await page.goto('http://127.0.0.1:8099/index.html');
  await page.waitForTimeout(500);
  check('with COOP/COEP: the page is cross-origin isolated', await page.evaluate(() => self.crossOriginIsolated));
  check('with COOP/COEP: no service worker is registered',
    await page.evaluate(async () => (await navigator.serviceWorker.getRegistrations()).length === 0));
  check('with COOP/COEP: Start is visible', await page.isVisible('#start'));
  check('with COOP/COEP: the drop zone is not shown before Start', !(await page.isVisible('#drop')));
  check('with COOP/COEP: no reset button on a clean profile', !(await page.isVisible('#reset')));
  check('with COOP/COEP: no page errors', !logs.some(l => /PAGEERROR/.test(l)));

  // The ROM intake rejects junk without ever reaching the wasm: feed a bogus
  // file through the drop path after Start. Spaghettify.js will 404 when
  // serving web/ directly, so only assert on the intake's own messages.
  await page.click('#start');
  await page.waitForTimeout(1500);
  const status = await page.textContent('#status');
  check('clicking Start without a build reports the missing build, not a blank screen',
    /Spaghettify\.js/.test(status), status);
  await page.close();

  // Touch layout smoke: forced on with ?touch, the deck is hidden until the
  // game is running, and the buttons exist with their N64 bit masks.
  page = await browser.newPage({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
  await page.goto('http://127.0.0.1:8099/index.html?touch');
  await page.waitForTimeout(300);
  check('touch: controls hidden while the overlay is up', !(await page.isVisible('#touch')));
  const bits = await page.$$eval('.tbtn[data-bit]', els => els.map(e => e.id + '=' + e.dataset.bit).sort().join(' '));
  // Racing deck: DRIFT is R, ITEM is Z, BRAKE is B, GO is A. Menu deck: A, B, L, R and the D-pad.
  const want = ['t-r=16', 't-z=8192', 't-b=16384', 't-a=32768', 't-start=4096',
                'm-a=32768', 'm-b=16384', 'm-l=32', 'm-r=16', 'd-up=2048', 'd-down=1024', 'd-left=512', 'd-right=256'].sort().join(' ');
  check('touch: every deck button carries its N64 bit', bits === want, bits);
  await page.evaluate(() => document.getElementById('overlay').classList.add('hidden'));
  await page.waitForTimeout(100);
  check('touch: controls appear once the overlay hides', await page.isVisible('#touch'));
  check('touch: the picture keeps 4:3 in portrait', await page.evaluate(() => {
    const r = document.getElementById('canvas').getBoundingClientRect();
    return Math.abs(r.width / r.height - 4 / 3) < 0.02;
  }));
  await page.close();
} finally {
  await browser.close();
  server.kill();
  plain.kill();
}
finish();
