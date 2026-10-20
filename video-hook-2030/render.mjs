// Renders index.html frame by frame (deterministic GSAP seek) and pipes the
// frames into ffmpeg.
//
//   node render.mjs                      -> out/video.mp4 (silent; audio/mux.py adds sound)
//   node render.mjs --stills 3,9,20      -> out/still-3.0s.png, ...
//
// Env: CHROMIUM (browser path), FPS (default 30).
import { chromium } from 'playwright-core';
import { spawn } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const FPS = Number(process.env.FPS || 30);
const executablePath = process.env.CHROMIUM || '/opt/pw-browsers/chromium';
const args = process.argv.slice(2);
const stillsArg = args.includes('--stills') ? args[args.indexOf('--stills') + 1] : null;
const out = path.resolve(here, args.find(a => a.endsWith('.mp4')) || 'out/video.mp4');
mkdirSync(path.join(here, 'out'), { recursive: true });

const browser = await chromium.launch({ executablePath, args: ['--force-color-profile=srgb', '--hide-scrollbars'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(path.join(here, 'index.html')).href + '?render=1');
await page.waitForFunction(() => window.__ready === true, null, { timeout: 30000 });
const duration = await page.evaluate(() => window.__duration);
const clip = { x: 0, y: 0, width: 1920, height: 1080 };

if (stillsArg) {
  for (const t of stillsArg.split(',').map(Number)) {
    await page.evaluate(s => window.__seek(s), t);
    const file = path.join(here, 'out', `still-${t.toFixed(1)}s.png`);
    await page.screenshot({ path: file, clip });
    console.log(file);
  }
  await browser.close();
  process.exit(0);
}

const frames = Math.round(duration * FPS);
console.log(`Rendering ${frames} frames (${duration.toFixed(1)}s @ ${FPS}fps) -> ${out}`);
const ff = spawn('ffmpeg', [
  '-y', '-loglevel', 'error',
  '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
  '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-tune', 'film',
  '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
  '-movflags', '+faststart', out,
], { stdio: ['pipe', 'inherit', 'inherit'] });
const done = new Promise((res, rej) => ff.on('close', c => (c === 0 ? res() : rej(new Error('ffmpeg exited ' + c)))));

const t0 = Date.now();
for (let i = 0; i < frames; i++) {
  await page.evaluate(s => window.__seek(s), i / FPS);
  const buf = await page.screenshot({ type: 'jpeg', quality: 95, clip });
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  if (i % (FPS * 5) === 0) console.log(`  ${(i / FPS).toFixed(0)}s / ${duration.toFixed(0)}s  (${((Date.now() - t0) / 1000).toFixed(0)}s elapsed)`);
}
ff.stdin.end();
await done;
await browser.close();
console.log('Done:', out);
