import assert from "node:assert/strict";
import sharp from "sharp";

/** Default-fixture guard against native transmission erasing the animal but leaving a valid scene. */
export async function verifyCloseSubject(image, stage) {
  const { data, info } = await sharp(image).removeAlpha().raw().toBuffer({ resolveWithObject: true });
  let visible = 0;
  for (let y = Math.floor(info.height * 0.2); y < info.height * 0.8; y++) {
    for (let x = Math.floor(info.width * 0.15); x < info.width * 0.85; x++) {
      const i = (y * info.width + x) * info.channels, r = data[i], g = data[i + 1], b = data[i + 2];
      if (stage === "egg" || stage === "larva" ? b > 130 && r - b < 95 : stage === "pupa" ? r > 110 && r > g * 1.3 : r > 60 && r > g * 1.6 && r > b * 1.5) visible++;
    }
  }
  const minimum = info.width * info.height * (stage === "adult" ? 0.0001 : 0.002);
  assert(visible > minimum, `${stage}: missing subject colour in macro region (${visible} pixels)`);
  return visible;
}
