import { spawn, spawnSync } from "node:child_process";
import { createRequire } from "node:module";
import { once } from "node:events";
import { readFile, readdir, rename, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

const root = fileURLToPath(new URL("../../../../", import.meta.url));
const raw = path.join(root, "eval-results/media/playthrough-raw.webm");
const output = path.join(root, "docs/media/playthrough.webm");
const screens = path.join(root, "docs/media/screens");
const sizes = await Promise.all((await readdir(screens)).filter(name => name.endsWith(".webp"))
  .map(async name => ({ name, size: (await stat(path.join(screens, name))).size })));
if (sizes.length !== 26 || sizes.some(file => file.size >= 150_000) || sizes.reduce((sum, file) => sum + file.size, 0) >= 3_000_000) {
  throw new Error("Expected 26 WebP images, each <150 KB and total <3 MB");
}

// Reuse Playwright's installed recorder; no new codec dependency or system install.
const require = createRequire(import.meta.url);
const { registry } = require("playwright-core/lib/coreBundle").registry;
const ffmpeg = process.env.FFMPEG_PATH || registry.findExecutable("ffmpeg").executablePath();
const probe = spawnSync(ffmpeg, ["-hide_banner", "-i", raw], { encoding: "utf8", windowsHide: true });
const match = probe.stderr?.match(/Duration: (\d+):(\d+):([\d.]+)/);
if (probe.error || !match) {
  console.warn(`Video conversion unavailable; keep the raw recording outside git: ${raw}`);
  process.exit(0);
}
const duration = Number(match[1]) * 3600 + Number(match[2]) * 60 + Number(match[3]);
const { chapters } = JSON.parse(await readFile(path.join(root, "eval-results/media/capture.json"), "utf8"));

// A 75s highlight edit: retain real moving frames around each capture, omit repeated meal waits.
// [scene, seconds before screenshot, seconds after screenshot, output seconds]
const edit = [
  ["home", 0.2, 0.6, 4], ["meal", 1.5, 0.6, 8],
  ["training", 0.6, 0.6, 5], ["training-result", 1.4, 0.6, 4],
  ["cleaning", 1, 0.6, 5], ["temperature", 1, 0.6, 5],
  ["presentation", 5, 0.6, 8], ["eclosion", 4, 0.6, 8],
  ["adult", 4, 0.6, 6], ["brain", 2, 0.6, 7],
  ["team", 0.2, 0.6, 5], ["zukan", 0.1, 0.6, 5], ["shiori", 0.2, 0.6, 5],
];
const sourceFps = 10;
const outputFps = 24;
const timeline = edit.flatMap(([name, before, after, seconds]) => {
  const chapter = chapters.find(item => item.name === name);
  if (!chapter) throw new Error(`Missing video chapter: ${name}`);
  const start = Math.max(0, chapter.seconds - before);
  const end = Math.min(duration - 0.2, chapter.seconds + after);
  return Array.from({ length: seconds * outputFps }, (_, i) =>
    Math.round((start + (end - start) * i / (seconds * outputFps)) * sourceFps));
});
const wanted = new Set(timeline);
const frames = new Map();

function processVideo(args) {
  const child = spawn(ffmpeg, ["-hide_banner", "-loglevel", "error", ...args], { windowsHide: true });
  let errors = "";
  child.stderr.on("data", chunk => { errors += chunk.toString(); });
  const completed = once(child, "close").then(([code]) => {
    if (code !== 0) throw new Error(`FFmpeg exited ${code}: ${errors}`);
  });
  return { child, completed };
}

// The bundled FFmpeg has no concat/setpts filters and cannot decode PNG. Decode to PNG,
// select actual video frames, then pass JPEG frames back to its supported MJPEG decoder.
const decode = processVideo(["-i", raw, "-an", "-r", String(sourceFps), "-f", "image2pipe", "-c:v", "png", "pipe:1"]);
decode.child.stdin.end();
let pending = Buffer.alloc(0);
let cursor = 8; // PNG signature precedes its length/type/data/CRC chunks.
let index = 0;
for await (const chunk of decode.child.stdout) {
  pending = Buffer.concat([pending, chunk]);
  while (pending.length >= cursor + 8) {
    const length = pending.readUInt32BE(cursor);
    const end = cursor + length + 12;
    if (pending.length < end) break;
    const isEnd = pending.toString("ascii", cursor + 4, cursor + 8) === "IEND";
    cursor = end;
    if (isEnd) {
      if (wanted.has(index)) frames.set(index, await sharp(pending.subarray(0, end)).jpeg({ quality: 90 }).toBuffer());
      index++;
      pending = pending.subarray(end);
      cursor = 8;
    }
  }
}
await decode.completed;
if (timeline.some(frame => !frames.has(frame))) throw new Error("Missing frames in the raw video; keep capture.json with its matching recording");
const temporary = path.join(root, "eval-results/media/playthrough-edited.webm");
const encode = processVideo(["-y", "-f", "image2pipe", "-c:v", "mjpeg", "-r", String(outputFps), "-i", "pipe:0", "-an",
  "-c:v", "libvpx", "-b:v", "650k", "-crf", "12", "-deadline", "realtime", temporary]);
encode.child.stdout.resume();
for (const frame of timeline) {
  if (!encode.child.stdin.write(frames.get(frame))) await once(encode.child.stdin, "drain");
}
encode.child.stdin.end();
await encode.completed;
if ((await stat(temporary)).size >= 8_000_000) throw new Error("Video exceeds 8 MB");
await rename(temporary, output);
console.log(`Saved 26 WebP images and a 75-second highlight video to docs/media (raw duration ${duration.toFixed(1)}s).`);
