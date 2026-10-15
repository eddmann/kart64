// Silverstone through the game's own menus, with a real ROM: Up from the cup
// row opens Custom, a standalone Grand Prix race runs to its own finish menu,
// Change Course goes back to Custom, and a Time Trial saves only to the
// course's own EEPROM.
//
//   ROM_PATH=~/roms/mk64.z64 node course-test.mjs <buildDir>
import path from 'node:path';
import { SCRATCH, check, finish, serve, buildDir, chromium, launchArgs, exec, collect } from './common.mjs';

const PORT = 8101;
const RACING = 4, RACE_IN_PROGRESS = 3, RACE_FINISHED = 5;
// gMenuSelection values (include/defines.h).
const MAIN_MENU = 11, PLAYER_SELECT = 12, COURSE_SELECT = 13;

const server = await serve(buildDir(), PORT);
const ctx = await chromium.launchPersistentContext(path.join(SCRATCH, 'kart64-course-profile'), {
  ...exec(), args: launchArgs, viewport: { width: 640, height: 800 }, hasTouch: true,
});
const page = await ctx.newPage();
for (const old of ctx.pages()) if (old !== page) await old.close();
const logs = collect(page);

const snap = () => page.evaluate(() => {
  if (!runtimeReady || !Module._Kart64_GetState) return null;
  const o = Module._Kart64_GetState() >> 2;
  if (!HEAP32[o + 7]) return null;
  const c = Module._Kart64_GetCourseBrowserState() >> 2;
  const p = Module._Kart64_GetCustomCourseName();
  let e = p; while (HEAPU8[e]) e++;
  return {
    game: HEAP32[o], race: HEAP32[o + 1], menu: HEAP32[o + 2], lap: HEAP32[o + 4], character: HEAP32[o + 10],
    custom: HEAP32[c], count: HEAP32[c + 1], confirm: HEAP32[c + 3], customSave: HEAP32[c + 4], single: HEAP32[c + 5],
    results: HEAP32[c + 6], cursor: HEAP32[c + 7], mode: HEAP32[c + 8], cpus: HEAP32[c + 10],
    silverstone: !!Module._Kart64_IsSilverstone(), name: new TextDecoder().decode(HEAPU8.slice(p, e)),
  };
});
const until = async (what, pred, maxMs = 60000) => {
  const t0 = Date.now();
  let s = null;
  while (Date.now() - t0 < maxMs) {
    s = await snap();
    if (s && pred(s)) return s;
    if (logs.some(l => /PAGEERROR|Aborted|Setup failed/.test(l))) break;
    await page.waitForTimeout(500);
  }
  throw new Error(`gave up waiting for ${what}; last: ${JSON.stringify(s)}`);
};
const tap = async (sel, wait = 1200) => { await page.tap(sel); await page.waitForTimeout(wait); };
// Tap A until the game leaves this menu.
const through = async menu => {
  let s = await snap();
  for (let i = 0; i < 8 && s.menu === menu && s.game !== RACING; i++) { await tap('#m-a'); s = await snap(); }
  return s;
};
const backTo = async menu => {
  let s = await snap();
  for (let i = 0; i < 8 && s.menu !== menu; i++) { await tap('#m-b', 2000); s = await snap(); }
  return until(`menu ${menu}`, x => x.game === 0 && x.menu === menu);
};
const readSave = file => page.evaluate(file => Array.from(FS.readFile('/data/' + file)), file);

try {
  await page.addInitScript(() => { localStorage.removeItem('k64.ctrl'); localStorage.setItem('k64.full', '0'); });
  await page.goto(`http://127.0.0.1:${PORT}/index.html`);
  await page.click('#start');
  const outcome = await Promise.race([
    page.waitForSelector('#drop:not(.hidden)', { timeout: 120000 }).then(() => 'drop'),
    page.waitForFunction(() => document.getElementById('overlay').classList.contains('hidden'), null, { timeout: 120000 }).then(() => 'booted'),
  ]);
  if (outcome === 'drop') {
    if (!process.env.ROM_PATH) { console.error('ROM_PATH must point at a US Mario Kart 64 ROM — it stays on this machine'); process.exit(2); }
    await page.setInputFiles('#file', process.env.ROM_PATH);
  }

  // --- Grand Prix: Up from the cup row opens Custom ---------------------------
  let s = await until('the engine', () => true, 8 * 60 * 1000);
  await page.waitForTimeout(3000);
  for (let i = 0; i < 15 && s.menu !== MAIN_MENU; i++) { await tap('#t-start', 2500); s = await snap(); }
  await page.waitForFunction(() => FS.analyzePath('/data/default.sav').exists);
  const original = await readSave('default.sav');
  await tap('#m-a');                                     // one player
  await tap('#m-a');                                     // Grand Prix
  await tap('#d-down', 500); await tap('#d-down', 500);  // 150cc
  s = await through(MAIN_MENU);
  await tap('#d-right', 700);                            // Luigi
  s = await through(PLAYER_SELECT);
  check('the cup row starts on the original courses', s.menu === COURSE_SELECT && !s.custom);
  await tap('#d-up');
  s = await snap();
  check('Up opens Custom, listing Silverstone', s.custom && s.count === 1 && s.name === 'Silverstone');

  // --- a standalone race to its own finish menu --------------------------------
  await tap('#m-a'); await tap('#m-a');
  s = await until('the Silverstone race', x => x.game === RACING && x.race === RACE_IN_PROGRESS && x.silverstone);
  check('Silverstone runs as one race against seven CPU rivals', s.single && s.character === 1 && s.cpus === 7);
  await page.evaluate(() => Module._Kart64_SetAutopilot(1));
  s = await until('the finish menu', x => x.results, 30 * 60 * 1000);
  check('three laps end in the course\'s own finish menu', s.lap >= 3 && s.cursor === 0);
  await tap('#d-down');
  check('Down moves to Change Course', (await snap()).cursor === 1);
  await tap('#m-a');
  s = await until('Change Course', x => x.game === 0 && x.menu === COURSE_SELECT);
  check('Change Course returns to Custom', s.custom && !s.single);

  // --- Time Trials save only to the course's own EEPROM ------------------------
  await tap('#m-b');                                     // Original
  await backTo(PLAYER_SELECT);
  await backTo(MAIN_MENU);
  await tap('#m-b'); await tap('#m-b');                  // back through class to mode
  await tap('#d-down');                                  // Time Trials
  s = await through(MAIN_MENU);
  if (s.character === 0) await tap('#d-right', 700);
  s = await through(PLAYER_SELECT);
  await tap('#d-up'); await tap('#m-a'); await tap('#m-a');
  s = await until('the Silverstone time trial', x => x.game === RACING && x.race === RACE_IN_PROGRESS && x.silverstone);
  check('Time Trials run Silverstone without CPU rivals', !s.single && s.mode === 1 && s.cpus === 0);
  const before = await readSave('silverstone-default.sav');
  await until('the time trial finish', x => x.race >= RACE_FINISHED && x.lap >= 3, 30 * 60 * 1000);
  // The record is written once the results are up; wait for it rather than a fixed time.
  const courseSaved = await page.waitForFunction(before => FS.readFile('/data/silverstone-default.sav').join() !== before,
    before.join(), { timeout: 30000 }).then(() => true, () => false);
  const originalKept = JSON.stringify(await readSave('default.sav')) === JSON.stringify(original);
  check('the time trial saves to Silverstone\'s EEPROM, not the original', courseSaved && originalKept, `course saved: ${courseSaved}, original kept: ${originalKept}`);
  check('no page errors, aborts or WebGL errors', !logs.some(l => /PAGEERROR|Aborted|WebGL: INVALID|Setup failed/.test(l)));
} catch (e) {
  check('harness ran to the end', false, e.message);
} finally {
  await page.screenshot({ path: SCRATCH + '/course-test-last.png' }).catch(() => {});
  await ctx.close();
  server.kill();
}
finish();
