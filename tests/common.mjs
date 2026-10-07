// Shared bits for the harnesses: a COOP/COEP static server for a build dir,
// a Chromium launcher, and PASS/FAIL bookkeeping. Every harness prints one
// line per check and exits non-zero if any failed.
import { chromium } from '@playwright/test';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import os from 'node:os';

export const SCRATCH = process.env.SCRATCH || os.tmpdir();
export const ROOT = path.dirname(fileURLToPath(import.meta.url));

let fails = 0;
export const check = (name, ok, detail) => {
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? `  (${detail})` : ''}`);
  if (!ok) fails++;
};
export const finish = () => {
  console.log(fails ? `\n❌ ${fails} check(s) FAILED` : '\n✅ all checks passed');
  process.exit(fails ? 1 : 0);
};

// Serve `dir` on `port` with the isolation headers (scripts/serve.py), or
// without them if `plain` (as GitHub Pages does), and resolve once it answers.
export async function serve(dir, port, plain = false) {
  const py = path.join(ROOT, '..', 'scripts', 'serve.py');
  const proc = spawn('python3', [py, dir, String(port), ...(plain ? ['--plain'] : [])], { stdio: ['ignore', 'ignore', process.env.VERBOSE ? 'inherit' : 'ignore'] });
  for (let i = 0; i < 60; i++) {
    try { await fetch(`http://127.0.0.1:${port}/`, { method: 'HEAD' }); return proc; }
    catch { await new Promise(r => setTimeout(r, 250)); }
  }
  proc.kill();
  throw new Error(`serve.py did not come up on :${port}`);
}

// The build dir is the one argument every harness takes; BUILD_DIR env works too.
export function buildDir() {
  const d = process.argv[2] || process.env.BUILD_DIR;
  if (!d) { console.error('usage: node <harness>.mjs <buildDir>'); process.exit(2); }
  return path.resolve(d);
}

export const launchArgs = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'];
export const exec = () => (process.env.PW_CHROMIUM ? { executablePath: process.env.PW_CHROMIUM } : {});
export { chromium };

// Attach a console collector to a page. Returns the array of lines.
export function collect(page) {
  const logs = [];
  page.on('console', m => logs.push(m.text()));
  page.on('pageerror', e => logs.push('PAGEERROR: ' + e.message));
  return logs;
}

// Click Start, then feed the ROM through the real file input — the same path
// a player takes, rather than a server-side shortcut. ROM_PATH is required
// and is never served or copied anywhere.
export async function startAndDropRom(page) {
  const rom = process.env.ROM_PATH;
  if (!rom) { console.error('ROM_PATH must point at a US Mario Kart 64 ROM (.z64/.v64/.n64) — it stays on this machine'); process.exit(2); }
  await page.click('#start');
  // Either the cache boots straight through (drop zone never shows) or the
  // page asks for the ROM. Wait for whichever happens first.
  const outcome = await Promise.race([
    page.waitForSelector('#drop:not(.hidden)', { timeout: 120000 }).then(() => 'drop'),
    page.waitForFunction(() => document.getElementById('overlay').classList.contains('hidden'), null, { timeout: 120000 }).then(() => 'booted'),
  ]);
  if (outcome === 'drop') await page.setInputFiles('#file', rom);
  return outcome;
}

// Wait until the engine has booted or something broke. "Loaded sequence" is
// logged during engine start-up on both paths; a line count is no use, because
// an extraction logs a quarter of a million lines and a cached boot about 100.
export async function waitForBoot(page, logs, maxMs = 6 * 60 * 1000) {
  const t0 = Date.now();
  while (Date.now() - t0 < maxMs) {
    await page.waitForTimeout(5000);
    if (logs.some(l => /PAGEERROR|Aborted|Setup failed/.test(l))) return false;
    if (logs.some(l => /Loaded sequence/.test(l))) return true;
  }
  return false;
}
