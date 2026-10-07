// The whole game on an emulated phone, with a real ROM: the game's own menus
// in the 4:3 letterbox, full screen while driving, a rotation mid-race, the
// results screens back in the letterbox, and on into the next race of the cup.
//
//   ROM_PATH=~/roms/mk64.z64 node race-test.mjs <buildDir>
//
// Everything is driven the way a phone would: taps on the touch deck -- the
// menu deck's A, B and D-pad on the game's screens, START to pause, FULL to
// change the setting. ?autopilot hands the kart to the
// game's own AI so the races actually finish. The profile is kept in SCRATCH,
// so only the first run pays for extraction. RACES=1 stops after one race.
// LAST=1 parks the kart for a while so it finishes below fourth, which is the
// only way to reach the game's RETRY / QUIT screen.
import { SCRATCH, check, finish, serve, buildDir, chromium, launchArgs, exec, collect } from './common.mjs';

const PORT = 8096;
const RACES = +(process.env.RACES || 2);
const W = 390, H = 844, DPR = 2;
const RACING = 4, RACE_IN_PROGRESS = 3, RACE_FINISHED = 5;

const server = await serve(buildDir(), PORT);
const ctx = await chromium.launchPersistentContext(SCRATCH + '/kart64-race-profile', {
  ...exec(), args: launchArgs, viewport: { width: W, height: H }, deviceScaleFactor: DPR, hasTouch: true, isMobile: true,
});
// A restored background tab can throttle rAF and miss touch emulation.
const page = await ctx.newPage();
for (const old of ctx.pages()) if (old !== page) await old.close();
await page.bringToFront();
const logs = collect(page);

// Everything the checks need, in one round trip. null until the engine is up.
const snap = () => page.evaluate(() => {
  if (typeof Module === 'undefined' || !Module._Kart64_GetState || typeof HEAP32 === 'undefined') return null;
  const o = Module._Kart64_GetState() >> 2;
  if (!HEAP32[o + 7]) return null;
  const box = id => { const r = document.getElementById(id).getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom].map(Math.round); };
  const c = document.getElementById('canvas');
  return {
    gamestate: HEAP32[o], race: HEAP32[o + 1], menu: HEAP32[o + 2], rank: HEAP32[o + 3], lap: HEAP32[o + 4], ms: HEAP32[o + 5],
    paused: HEAP32[o + 6] === 1,
    hud: HEAP32[o + 8] === 1,    // the game's HUD is in its portrait layout
    hudUp: HEAP32[o + 9] === 1,  // the track introduction is over
    character: HEAP32[o + 10], players: HEAP32[o + 11],
    drift: HEAP32[o + 12], boost: HEAP32[o + 13],   // player one's mini-turbo charge and boost frames left
    // which deck is showing: the menu deck's A, the racing deck's DRIFT, or Tour's surface
    deck: document.getElementById('m-a').offsetParent ? 'menu' : document.getElementById('t-r').offsetParent ? 'race'
        : getComputedStyle(document.getElementById('tour')).display !== 'none' ? 'tour' : 'none',
    a: box('m-a'), b: box('m-b'), dpad: box('dpadbase'),
    canvas: [c.width, c.height], css: [c.clientWidth, c.clientHeight], full: document.body.classList.contains('full'),
    pads: { drift: box('t-r'), item: box('t-z'), brake: box('t-b') },
    mem: HEAPU8.length >> 20,
  };
});
const until = async (what, pred, maxMs, every = 1000) => {
  const t0 = Date.now();
  let s = null;
  while (Date.now() - t0 < maxMs) {
    s = await snap();
    if (s && pred(s)) return s;
    if (logs.some(l => /PAGEERROR|Aborted|Setup failed/.test(l))) break;
    await page.waitForTimeout(every);
  }
  console.log(`   (gave up waiting for ${what}; last: ${JSON.stringify(s)})`);
  return null;
};
const overlap = (a, b) => a[0] < b[2] && b[0] < a[2] && a[1] < b[3] && b[1] < a[3];
const letterboxed = s => !!s && !s.full && !s.hud && Math.abs(s.css[1] - W * 3 / 4) <= 1;
const is43 = c => Math.abs(c[0] * 3 - c[1] * 4) <= 4 * DPR;   // to within a rounded pixel
const tapStart = () => page.tap('#t-start');
const tap = async (sel, wait = 1500) => { await page.tap(sel); await page.waitForTimeout(wait); };
// gMenuSelection values (include/defines.h).
const MAIN_MENU = 11, PLAYER_SELECT = 12, COURSE_SELECT = 13;
// Tap A until the game leaves this menu (each has two or three confirms).
const through = async (menu, max = 8) => {
  let s = await snap();
  for (let i = 0; i < max && s.menu === menu && s.gamestate !== RACING; i++) { await tap('#m-a'); s = await snap(); }
  return s;
};
const driving = s => s.gamestate === RACING && s.race === RACE_IN_PROGRESS;

try {
  // The profile persists across runs: start on the pads deck whatever the last run left.
  await page.addInitScript(() => { localStorage.removeItem('k64.ctrl'); localStorage.setItem('k64.full', '1'); });
  await page.goto(`http://127.0.0.1:${PORT}/index.html?autopilot`);
  check('Start is offered', await page.isVisible('#start'));
  await page.click('#start');
  const outcome = await Promise.race([
    page.waitForSelector('#drop:not(.hidden)', { timeout: 120000 }).then(() => 'drop'),
    page.waitForFunction(() => document.getElementById('overlay').classList.contains('hidden'), null, { timeout: 120000 }).then(() => 'booted'),
  ]);
  if (outcome === 'drop') {
    if (!process.env.ROM_PATH) { console.error('ROM_PATH must point at a US Mario Kart 64 ROM — it stays on this machine'); process.exit(2); }
    await page.setInputFiles('#file', process.env.ROM_PATH);
  }

  // --- the game's own menus, by touch ----------------------------------------
  let s = await until('the engine', () => true, 8 * 60 * 1000);
  if (!s) throw new Error('the engine never came up');
  await page.waitForTimeout(3000);
  s = await snap();
  check('the title screen is letterboxed to 4:3 in portrait', letterboxed(s), s && `${s.css.join('x')} full=${s.full}`);
  check('the menu deck is showing: D-pad, A and B', s.deck === 'menu' && s.dpad[2] <= W / 2 + 1 && s.a[0] > W / 2 && !overlap(s.a, s.b), `${s.deck} a=${s.a} b=${s.b} dpad=${s.dpad}`);
  await page.screenshot({ path: SCRATCH + '/race-test-menudeck.png' }).catch(() => {});
  // The logos, then the title: the game asks for START. (A saved setting can
  // skip straight to the main menu.) Then A through game select, mode, class and OK.
  for (let i = 0; i < 15 && s.menu !== MAIN_MENU; i++) { await tapStart(); await page.waitForTimeout(2200); s = await snap(); }
  check('START gets past the logos and the title screen', s.menu === MAIN_MENU, `menu ${s.menu}`);
  // Game Select: the 2P-4P columns are dimmed and the cursor cannot reach them.
  await tap('#d-right', 700); await tap('#d-right', 900);
  s = await snap();
  check('the multiplayer columns cannot be selected', s.menu === MAIN_MENU && s.players === 1, `players ${s.players}`);
  await page.screenshot({ path: SCRATCH + '/race-test-gameselect.png' }).catch(() => {});
  s = await through(MAIN_MENU);
  check('A confirms through game select to the driver screen', s.menu === PLAYER_SELECT, `menu ${s.menu}`);
  // B goes back a screen; A returns.
  await tap('#m-b', 2000);
  s = await snap();
  check('B goes back to the previous menu', s.menu === MAIN_MENU, `menu ${s.menu}`);
  s = await through(MAIN_MENU);
  // The D-pad moves the cursor: one step right of Mario is Luigi.
  await tap('#d-right', 800);
  s = await through(PLAYER_SELECT);
  check('D-pad right then A picks the second driver', s.menu === COURSE_SELECT && s.character === 1, `menu ${s.menu} character ${s.character}`);
  s = await through(COURSE_SELECT);
  let intro = null;
  check('A confirms cup and course into a Grand Prix race', s.gamestate === RACING, `gamestate ${s.gamestate}`);
  // The cup and track introduction comes before the grid, with the HUD still down.
  for (let i = 0; i < 40 && !intro; i++) {
    s = await snap();
    if (s.gamestate === RACING && !s.hudUp) { await page.waitForTimeout(700); intro = await snap(); }
    else if (driving(s)) break;
    else await page.waitForTimeout(250);
  }
  check('the track introduction is letterboxed', !!intro && !intro.hudUp && letterboxed(intro), intro && `${intro.css.join('x')} hudUp=${intro.hudUp}`);
  await page.screenshot({ path: SCRATCH + '/race-test-intro.png' }).catch(() => {});
  // CTRL lives on the menu deck, which the introduction still shows: switch
  // to Tour here, so the kart is never touched on the way to the first bend.
  check('CTRL is offered on the menu deck', await page.isVisible('#t-ctrl'));
  await page.tap('#t-ctrl');
  check('CTRL switches to Tour', await page.evaluate(() => document.getElementById('t-ctrl').textContent) === 'CTRL: TOUR');

  // --- race 1: Tour mode -------------------------------------------------------
  s = await until('the race to start', x => driving(x) && x.ms > 3000, 3 * 60 * 1000);
  if (!s) throw new Error('no race');
  check('driving in portrait is full screen', s.full && s.css[0] === W && s.css[1] === H, s.css.join('x'));
  check('Tour mode shows its one-thumb surface, no pads', s.deck === 'tour', s.deck);
  check('SDL sized the canvas to the window x device pixel ratio', s.canvas[0] === W * DPR && s.canvas[1] === H * DPR, s.canvas.join('x'));
  check("the game's HUD is in its portrait layout", s.hud);
  // On Luigi Raceway's first bend (the autopilot has driven the kart there and
  // is already turning right) a fast sideways drag that keeps holding must put
  // the kart into a power slide and, with the stick wiggled for it, charge the
  // game's own mini-turbo (driftState 2); letting go must fire the boost. The
  // harness's mouse moves are ~100ms apart, so the flick is two 30px steps
  // (the page wants 28px inside 150ms), and the thumb keeps a firm lock so
  // the slide follows the bend. A charged slide that ends on its own (the
  // outside wall, say) fires its boost there and then, so the boost is proof
  // of the charge too; the charge itself lasts a frame in that case. The timer
  // also runs through the introduction and restarts at GO, so the start line
  // (only crossed after GO) comes first.
  s = await until('the start line', x => driving(x) && x.lap >= 0, 60000, 100);
  s = await until('the first bend', x => x.ms > 7200 && x.ms < 20000, 20000, 100);
  await page.evaluate(() => Module._Kart64_SetAutopilot(0));
  await page.waitForTimeout(500);   // let the AI's own steering settle out before the thumb takes over
  await page.mouse.move(W / 2, H * 0.7); await page.mouse.down();
  await page.mouse.move(W / 2 + 30, H * 0.7); await page.mouse.move(W / 2 + 60, H * 0.7);
  s = await until('the mini-turbo to charge', x => x.drift >= 2 || x.boost > 0, 3500, 15);
  check('a flick held charges a mini-turbo', !!s, s && `driftState ${s.drift} boost ${s.boost} at ${s.ms}ms`);
  await page.mouse.up();
  s = await until('the boost', x => x.boost > 0, 1500, 15);
  check('letting go fires the boost', !!s);
  await page.screenshot({ path: SCRATCH + '/race-test-tour.png' }).catch(() => {});

  // --- back to the pads, from the pause menu -------------------------------------
  // (A CPU-driven kart cannot pause, so the autopilot stays off until after.)
  await tapStart();
  s = await until('the pause menu', x => x.paused && x.deck === 'menu', 10000, 100);
  await page.tap('#t-ctrl');
  await page.waitForTimeout(300);
  await page.tap('#m-a');   // CONTINUE GAME
  s = await until('the race to resume', x => !x.paused && x.deck !== 'menu', 10000, 100);
  await page.evaluate(() => Module._Kart64_SetAutopilot(1));
  check('CTRL: PADS on the pause menu brings the racing deck back', !!s && s.deck === 'race', s && s.deck);
  const { drift, item, brake } = s.pads;
  check('DRIFT sits in the lower right', drift[0] > W / 2 && drift[1] > H / 2 && drift[2] <= W && drift[3] <= H, drift.join(','));
  check('the touch buttons do not overlap', !overlap(drift, item) && !overlap(drift, brake) && !overlap(item, brake));
  const t1 = s.ms;
  s = await until('the kart to cross the line', x => x.lap >= 0 && x.ms > t1, 60000);
  check('the kart is moving (crossed the start line)', !!s);

  // --- pause -------------------------------------------------------------------
  // (A CPU-driven kart cannot pause, so the autopilot steps aside for this.)
  await page.evaluate(() => Module._Kart64_SetAutopilot(0));
  await page.waitForTimeout(300);
  await tapStart();
  s = await until('the pause menu', x => x.paused, 10000, 250);
  check('START pauses, and the pause menu is letterboxed', !!s && !!(await until('the letterbox', letterboxed, 5000, 250)));
  s = await until('the menu deck', x => x.deck === 'menu', 5000, 250);
  check('the pause menu gets the menu deck', !!s);
  await page.screenshot({ path: SCRATCH + '/race-test-pause.png' }).catch(() => {});
  await page.tap('#m-a');   // CONTINUE GAME is selected
  s = await until('the race to resume', x => !x.paused && x.full && x.hud && x.deck === 'race', 10000, 250);
  check('A on CONTINUE resumes, full screen and racing deck again', !!s);
  await page.evaluate(() => Module._Kart64_SetAutopilot(1));

  // --- rotate mid-race ---------------------------------------------------------
  await page.setViewportSize({ width: H, height: W });
  s = await until('landscape', x => x.canvas[0] === H * DPR && x.canvas[1] === W * DPR, 15000);
  check('rotating to landscape resizes the canvas', !!s, s && s.canvas.join('x'));
  check('landscape puts the HUD back in its own layout', !!s && !s.hud && s.full);
  await page.setViewportSize({ width: W, height: H });
  s = await until('portrait again', x => x.canvas[0] === W * DPR && x.hud, 15000);
  check('rotating back restores the portrait layout', !!s, s && s.canvas.join('x'));

  // --- the full-screen setting, from the deck -----------------------------------
  await page.tap('#t-full');
  s = await until('the 4:3 picture', letterboxed, 10000, 250);
  check('FULL: OFF gives the 4:3 picture while driving, original HUD layout', !!s && is43(s.canvas), s && s.canvas.join('x'));
  await page.screenshot({ path: SCRATCH + '/race-test-43-portrait.png' }).catch(() => {});
  await page.setViewportSize({ width: H, height: W });
  s = await until('the 4:3 picture in landscape', x => !x.full && x.canvas[1] === W * DPR && is43(x.canvas), 15000, 250);
  check('FULL: OFF in landscape is a 4:3 picture with gutters', !!s && s.pads.drift[0] >= s.css[0] + (H - s.css[0]) / 2 - 1, s && `${s.canvas.join('x')} drift at ${s.pads.drift[0]}`);
  await page.screenshot({ path: SCRATCH + '/race-test-43-landscape.png' }).catch(() => {});
  await page.setViewportSize({ width: W, height: H });
  await page.waitForTimeout(1500);
  await page.tap('#t-full');
  s = await until('full screen again', x => x.full && x.hud && x.canvas[0] === W * DPR && x.canvas[1] === H * DPR, 15000, 250);
  check('FULL: ON restores the full-screen portrait layout', !!s, s && s.canvas.join('x'));

  if (process.env.LAST) {
    await page.evaluate(() => { Module._Kart64_SetAutopilot(0); Module._Kart64_SetAutoAccel(0); });
    await page.waitForTimeout(60000);
    await page.evaluate(() => Module._Kart64_SetAutopilot(1));
  }

  // --- finish, the game's results, and on to the next race ---------------------
  let memFirst = 0;
  for (let n = 1; n <= RACES; n++) {
    s = await until(`race ${n} to finish`, x => x.race === RACE_FINISHED, 8 * 60 * 1000);
    check(`race ${n} finished`, !!s, s && `rank ${s.rank + 1}, ${(s.ms / 1000).toFixed(1)}s, mem ${s.mem}MB`);
    if (!s) break;
    if (n === 1) memFirst = s.mem;
    s = await until('the results letterbox', letterboxed, 20000, 250);
    check(`race ${n}: the results screens are letterboxed`, !!s, s && s.css.join('x'));
    const placed = s.rank + 1;
    if (n === 1) { await page.waitForTimeout(6000); await page.screenshot({ path: SCRATCH + '/race-test-results.png' }).catch(() => {}); }
    if (placed > 4) {
      // Below fourth the game moves on to RETRY / QUIT: still its own 4:3 screen.
      s = await until('RETRY / QUIT', x => x.race > RACE_FINISHED, 60000, 500);
      await page.waitForTimeout(1500);
      s = await snap();
      check(`race ${n}: placed ${placed}, and RETRY / QUIT is letterboxed with the menu deck`, letterboxed(s) && s.deck === 'menu', s && `race=${s.race} deck=${s.deck} ${s.css.join('x')}`);
      await page.screenshot({ path: SCRATCH + '/race-test-retry.png' }).catch(() => {});
    }
    if (n === RACES) { check(`memory did not grow across ${RACES} race(s)`, !!s && s.mem <= memFirst + 64, s && `${memFirst}MB -> ${s.mem}MB`); break; }
    // A steps through the results and the points table, on the menu deck.
    // Below fourth place the game offers RETRY / QUIT instead, and A retries.
    let next = null;
    for (let i = 0; i < 40 && !next; i++) {
      s = await snap();
      if (s.gamestate === RACING && s.race < RACE_FINISHED) { next = await until('the next race', x => driving(x) && x.ms > 1000 && x.ms < 60000, 90000); break; }
      if (s.deck === 'menu') await page.tap('#m-a');
      await page.waitForTimeout(2500);
    }
    check(`A carries on to the next race (the next in the cup, or a retry below fourth)`, !!next, next && `full=${next.full} hud=${next.hud}`);
    if (!next) break;
  }
  check('no WebGL errors', !logs.some(l => /WebGL: INVALID/.test(l)), logs.find(l => /WebGL: INVALID/.test(l)));
  check('no page errors or aborts', !logs.some(l => /PAGEERROR|Aborted/.test(l)), logs.find(l => /PAGEERROR|Aborted/.test(l)));
} catch (e) {
  check('harness ran to the end', false, e.message);
} finally {
  await page.screenshot({ path: SCRATCH + '/race-test-last.png' }).catch(() => {});
  await ctx.close();
  server.kill();
}
finish();
