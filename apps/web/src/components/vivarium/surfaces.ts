import { CanvasTexture, RepeatWrapping, SRGBColorSpace } from "three";
import { randomSource } from "./random";

/** Locally generated texture: no remote assets or cross-origin image requests. */
export function surfaceTexture(kind: "glass" | "food" | "cotton" | "body" | "roughness", color = "#c7a24f") {
  const canvas = document.createElement("canvas"); canvas.width = canvas.height = 512;
  const ctx = canvas.getContext("2d")!;
  const random = randomSource(kind);
  ctx.fillStyle = kind === "roughness" ? "#dddddd" : kind === "glass" ? "#555555" : kind === "cotton" ? "#e9e5d8" : color;
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
  if (kind === "cotton") {
    ctx.globalAlpha = 0.14; ctx.lineWidth = 0.7;
    for (let i = 0; i < 9000; i++) {
      const x = random() * 512, y = random() * 512;
      ctx.strokeStyle = random() > 0.35 ? "#fffdf4" : "#6e6d62";
      ctx.beginPath(); ctx.moveTo(x, y); ctx.quadraticCurveTo(x + random() * 10 - 5, y + 8, x + random() * 18 - 9, y + 16); ctx.stroke();
    }
  }
  if (kind === "food" || kind === "body") {
    // Broad colour/roughness variation beneath fine grain avoids uniform plastic.
    for (let i = 0; i < 65; i++) {
      const x = random() * 512, y = random() * 512, r = 8 + random() * 48;
      const g = ctx.createRadialGradient(x, y, 0, x, y, r);
      g.addColorStop(0, random() > 0.3 ? "rgba(62,42,18,.32)" : "rgba(239,216,155,.2)"); g.addColorStop(1, "rgba(70,48,20,0)");
      ctx.globalAlpha = kind === "food" ? 0.8 : 0.45; ctx.fillStyle = g; ctx.fillRect(x-r,y-r,r*2,r*2);
    }
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
  if (kind !== "glass" && kind !== "roughness") texture.colorSpace = SRGBColorSpace;
  return texture;
}
