// Original procedural studio illumination, dedicated to CC0. No source photograph.
// Run from repo root: node apps/web/src/components/vivarium/generate-environment.mjs
import { mkdir, writeFile } from "node:fs/promises";
const width = 256, height = 128;
const pixels = Buffer.alloc(width * height * 4);
for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) {
  const u = x / width, v = y / height;
  const window = (cx, cy, sx, sy) => Math.exp(-(((u-cx)/sx)**8) - ((v-cy)/sy)**8);
  const key = window(0.22, 0.36, 0.042, 0.13) * 7;
  const fill = window(0.73, 0.4, 0.075, 0.18) * 2.2;
  const rim = window(0.47, 0.4, 0.013, 0.2) * 5;
  const rgb = [0.11 + key + fill * 0.73 + rim, 0.13 + key * 0.8 + fill * 0.87 + rim * 0.9, 0.105 + key * 0.55 + fill + rim * 0.7];
  const e = Math.ceil(Math.log2(Math.max(...rgb))), factor = 256 / 2**e, i = (y * width + x) * 4;
  for (let c = 0; c < 3; c++) pixels[i+c] = Math.min(255, Math.round(rgb[c] * factor));
  pixels[i+3] = e + 128;
}
await mkdir("apps/web/public/vivarium", { recursive: true });
await writeFile("apps/web/public/vivarium/studio.hdr", Buffer.concat([Buffer.from(`#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n-Y ${height} +X ${width}\n`), pixels]));
