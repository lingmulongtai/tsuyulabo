import { CanvasTexture, RepeatWrapping, SRGBColorSpace } from "three";
import { randomSource } from "./random";

/** Locally generated texture: no remote assets or cross-origin image requests. */
export function surfaceTexture(kind: "glass" | "food" | "cotton" | "body", color = "#c7a24f") {
  const canvas = document.createElement("canvas"); canvas.width = canvas.height = 512;
  const ctx = canvas.getContext("2d")!;
  const random = randomSource(kind);
  ctx.fillStyle = kind === "glass" ? "#555555" : kind === "cotton" ? "#e9e5d8" : color;
  ctx.fillRect(0, 0, 512, 512);
  for (let i = 0; i < (kind === "glass" ? 650 : 16000); i++) {
    const x = random() * 512, y = random() * 512;
    ctx.globalAlpha = kind === "glass" ? 0.07 : 0.05 + random() * 0.17;
    ctx.strokeStyle = ctx.fillStyle = random() > 0.5 ? "#ffffff" : "#251c0b";
    if (kind === "glass") {
      ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + random() * 22, y + random() * 3); ctx.stroke();
    } else { ctx.beginPath(); ctx.ellipse(x, y, 0.5 + random() * 3, 0.4 + random(), random() * 6, 0, Math.PI * 2); ctx.fill(); }
  }
  if (kind === "glass") {
    ctx.globalAlpha = 0.06; ctx.strokeStyle = "#ffffff";
    for (let i = 0; i < 20; i++) { ctx.beginPath(); ctx.ellipse(150, 250, 25 + i * 2, 40 + i * 2, 0.4, 0, Math.PI * 1.5); ctx.stroke(); }
  }
  if (kind === "food") {
    // Depressions live in the bump map: raised tubes read as wires at macro scale.
    ctx.globalAlpha = 0.13; ctx.strokeStyle = "#594b31"; ctx.lineWidth = 2; ctx.shadowColor = "#594b31"; ctx.shadowBlur = 4;
    for (let i = 0; i < 5; i++) {
      ctx.beginPath(); ctx.moveTo(40 + i * 80, 50);
      ctx.bezierCurveTo(160 + i * 35, 150, 30 + i * 80, 300, 120 + i * 65, 470); ctx.stroke();
    }
  }
  const texture = new CanvasTexture(canvas);
  texture.wrapS = texture.wrapT = RepeatWrapping;
  if (kind !== "glass") texture.colorSpace = SRGBColorSpace;
  return texture;
}
