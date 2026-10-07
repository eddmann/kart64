//   node layout-test.mjs <buildDir>
//
// Smoke test (no ROM needed): boot the real build headless to the ROM screen and
// prove the bridge exports exist and the page picks the right layout for each
// combination of the full-screen setting and orientation.
import { serve, chromium, launchArgs, exec, collect } from './common.mjs';
import { buildDir } from './common.mjs';
const server = await serve(buildDir(), 8097);
const browser = await chromium.launch({ ...exec(), args: launchArgs });
let fails = 0; const check = (n, ok, d) => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${n}${d ? `  (${d})` : ''}`); if (!ok) fails++; };
const CASES = [
  // A desktop defaults to the 4:3 picture; ?full=1 is what a touch device gets.
  { width: 1280, height: 720, name: 'landscape, full screen off (desktop default)', query: '', full: false, css: [960, 720] },
  // Full screen only takes over while driving, which a ROM-less boot never reaches.
  { width: 1280, height: 720, name: 'landscape, full screen on (not driving)', query: '?full=1', full: false, css: [960, 720] },
  { width: 390, height: 844, name: 'portrait, full screen on (not driving)', query: '?full=1&touch', full: false, css: [390, 293] },
];
for (const vp of CASES) {
  const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: 2 });
  const logs = collect(page);
  await page.goto('http://127.0.0.1:8097/index.html' + vp.query);
  await page.click('#start');
  await page.waitForFunction(() => document.getElementById('status')?.textContent?.includes('Waiting for ROM'), null, { timeout: 120000 });
  await page.waitForTimeout(2500);
  const r = await page.evaluate(() => ({
    exports: ['_Kart64_Resize', '_Kart64_SetResolution', '_Kart64_SetCamera', '_Kart64_SetHudLayout', '_Kart64_SetHudGroup', '_Kart64_GetState', '_Kart64_SetAutoAccel', '_Kart64_SetAutopilot', '_Kart64_SetTouchPad', '_Kart64_SetDriftAssist'].filter(n => typeof Module[n] !== 'function'),
    full: document.body.classList.contains('full'),
    css: (() => { const b = document.getElementById('canvas').getBoundingClientRect(); return [Math.round(b.width), Math.round(b.height)]; })(),
    attr: [document.getElementById('canvas').width, document.getElementById('canvas').height],
    state: (() => { const o = Module._Kart64_GetState() >> 2; return [HEAP32[o], HEAP32[o + 1], HEAP32[o + 7]]; })(),
    dpr: devicePixelRatio,
  }));
  console.log(vp.name, JSON.stringify(r));
  check(`${vp.name}: all bridge exports present`, r.exports.length === 0, r.exports.join(','));
  check(`${vp.name}: the picture ${vp.full ? 'fills the window' : 'is a 4:3 box'}`, r.full === vp.full);
  const expect = vp.css;
  check(`${vp.name}: canvas CSS box is ${expect.join('x')}`, r.css[0] === expect[0] && Math.abs(r.css[1] - expect[1]) <= 1, r.css.join('x'));
  // main() has not run at the ROM screen, so SDL has not sized the canvas yet:
  // the engine-ready word must be 0 and the page must not have touched it.
  check(`${vp.name}: engine reports not-ready before main()`, r.state[2] === 0, 'attr ' + r.attr.join('x'));
  check(`${vp.name}: no page errors`, !logs.some(l => /PAGEERROR|Aborted/.test(l)), logs.filter(l => /PAGEERROR|Aborted/.test(l))[0]);
  if (vp === CASES[0]) {
    // The texture pack picker: nothing installed, then a chosen file shows by
    // name with a way to take it back. (A real pack is a test of its own: it
    // is the player's file, never in this repo.)
    await page.goto('http://127.0.0.1:8097/index.html');
    const pack = () => page.evaluate(() => [document.getElementById('packbtn').textContent, !document.getElementById('packoff').classList.contains('hidden')]);
    const none = await pack();
    await page.setInputFiles('#packfile', { name: 'my-pack.o2r', mimeType: 'application/zip', buffer: Buffer.from('PK') });
    await page.waitForTimeout(200);
    const picked = await pack();
    await page.setInputFiles('#packfile', { name: 'notes.txt', mimeType: 'text/plain', buffer: Buffer.from('hello') });
    await page.waitForTimeout(200);
    const refused = await page.evaluate(() => [document.getElementById('packbtn').textContent, document.getElementById('status').classList.contains('bad')]);
    check(`${vp.name}: anything but a zip-based pack is refused, keeping the chosen one`, refused[0] === 'Texture pack: my-pack' && refused[1], JSON.stringify(refused));
    await page.click('#packoff');
    const removed = await pack();
    check(`${vp.name}: the texture pack picker shows a chosen pack and can take it back`,
      none[0] === 'Texture pack: none' && !none[1] && picked[0] === 'Texture pack: my-pack' && picked[1] && removed[0] === 'Texture pack: none' && !removed[1],
      JSON.stringify([none, picked, removed]));
    await page.click('#start');
    await page.waitForFunction(() => document.getElementById('status')?.textContent?.includes('Waiting for ROM'), null, { timeout: 120000 });
    // On a desktop F toggles the setting (and the browser's full screen, which headless may refuse).
    const label = () => page.evaluate(() => document.getElementById('fullpref').textContent);
    await page.keyboard.press('KeyF'); await page.waitForTimeout(200);
    const on = await label();
    await page.keyboard.press('KeyF'); await page.waitForTimeout(200);
    check(`${vp.name}: F toggles the full-screen setting`, on === 'Full screen: on' && await label() === 'Full screen: off', on);
  }
  if (vp === CASES[2]) {
    // Tour mode, without a race: show the racing deck by hand and record what
    // the page writes to the pad while a mouse plays a thumb. A fast sideways
    // drag must hold R and hand its direction to the game's drift assist, a
    // fast vertical drag must tap Z with the stick up, and lifting lets go of
    // both. race-test checks the game's side: the charge and the boost.
    await page.evaluate(() => {
      window.__pad = []; window.__assist = [];
      const real = Module._Kart64_SetTouchPad, realAssist = Module._Kart64_SetDriftAssist;
      Module._Kart64_SetTouchPad = (a, x, y, m) => { window.__pad.push([x, y, m, Math.round(performance.now())]); real(a, x, y, m); };
      Module._Kart64_SetDriftAssist = d => { window.__assist.push(d); realAssist(d); };
      document.getElementById('overlay').classList.add('hidden');
      window.setDeck(false);
      document.getElementById('t-ctrl').click();
    });
    await page.waitForTimeout(100);
    const shown = await page.evaluate(() => ({ tour: document.body.classList.contains('tour'), surface: !!document.getElementById('tour').offsetParent || getComputedStyle(document.getElementById('tour')).display !== 'none', pads: getComputedStyle(document.getElementById('pads')).display, label: document.getElementById('t-ctrl').textContent }));
    check(`${vp.name}: CTRL switches to Tour and hides the pads`, shown.tour && shown.surface && shown.pads === 'none' && shown.label === 'CTRL: TOUR', JSON.stringify(shown));
    const flick = async (x0, y0, x1, y1) => { await page.mouse.move(x0, y0); await page.mouse.down(); for (let i = 1; i <= 4; i++) { await page.mouse.move(x0 + (x1 - x0) * i / 4, y0 + (y1 - y0) * i / 4); } };
    await flick(150, 500, 220, 500);
    await page.waitForTimeout(1900);
    const held = await page.evaluate(() => window.__pad.slice());
    await flick(220, 500, 220, 420);   // a swipe up while still holding the drift
    await page.waitForTimeout(150);
    await page.mouse.up();
    await page.waitForTimeout(100);
    const pad = await page.evaluate(() => window.__pad.slice());
    const R = held.filter(c => c[2] & 16);
    check(`${vp.name}: a flick holds R with the stick in its direction`, R.length > 0 && R[0][0] > 0 && held.slice(held.indexOf(R[0])).every(c => c[2] & 16), `${R.length} R samples, first stick ${R[0]?.[0]}`);
    const Z = pad.filter(c => c[2] & 8192);
    check(`${vp.name}: a swipe up taps Z with the stick forward, keeping R`, Z.length > 0 && Z.every(c => c[1] > 0 && (c[2] & 16)), `${Z.length} Z samples ${JSON.stringify(Z[0])}`);
    const last = pad[pad.length - 1];
    const assist = await page.evaluate(() => window.__assist.slice());
    check(`${vp.name}: the drift hands its direction to the game's assist, and lifting ends it`, assist.length === 2 && assist[0] === 1 && assist[1] === 0, JSON.stringify(assist));
    check(`${vp.name}: lifting the thumb lets everything go`, last[0] === 0 && last[1] === 0 && last[2] === 0, JSON.stringify(last));
    await page.mouse.move(150, 500); await page.mouse.down();
    for (let i = 1; i <= 10; i++) { await page.mouse.move(150 + 8 * i, 500); await page.waitForTimeout(50); }   // 160 px/s: a steer, not a flick
    const slow = await page.evaluate(() => window.__pad.slice(-3));
    await page.mouse.up();
    check(`${vp.name}: a slow drag steers without drifting`, slow.every(c => c[0] > 0 && !(c[2] & 16)), JSON.stringify(slow));
  }
  await page.close();
}
await browser.close(); server.kill();
console.log(fails ? `\n❌ ${fails} FAILED` : '\n✅ all checks passed'); process.exit(fails ? 1 : 0);
