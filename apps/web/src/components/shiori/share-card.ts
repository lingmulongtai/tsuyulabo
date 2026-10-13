/** A readable PNG card; original evidence remains available in the diary disclosure. */
export function shareText(text: string): string {
  return text.replace(/#[A-Za-z0-9][A-Za-z0-9_-]*/g, "").replace(/ +。/g, "。").trim();
}
export function wrapCardText(text: string, width: number, measure: (text: string) => number): string[] {
  const lines: string[] = [];
  let line = "";
  for (const char of Array.from(text)) {
    if (char === "\n") { lines.push(line); line = ""; continue; }
    if (line && measure(line + char) > width) { lines.push(line); line = ""; }
    line += char;
  }
  if (line) lines.push(line);
  return lines;
}
export async function diaryImage(text: string, name: string, day: string): Promise<Blob> {
  await document.fonts.ready;
  const canvas = document.createElement("canvas");
  canvas.width = 1080; canvas.height = 1350;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("画像を作れませんでした。");
  ctx.fillStyle = "#f5f1e7"; ctx.fillRect(0, 0, 1080, 1350);
  ctx.strokeStyle = "#c3b599"; ctx.lineWidth = 2; ctx.strokeRect(48, 48, 984, 1254);
  ctx.fillStyle = "#756444"; ctx.font = "30px sans-serif"; ctx.fillText("ツユラボ ・ 観察日記", 88, 136);
  ctx.fillStyle = "#312d27"; ctx.font = "44px sans-serif";
  let y = 244;
  for (const line of wrapCardText(name, 904, value => ctx.measureText(value).width)) {
    ctx.fillText(line, 88, y); y += 62;
  }
  ctx.font = "30px sans-serif"; ctx.fillText(day, 88, y + 30);
  ctx.font = "40px sans-serif";
  const lines = wrapCardText(shareText(text), 904, value => ctx.measureText(value).width);
  y += 144;
  for (const line of lines) { ctx.fillText(line, 88, y); y += 68; }
  ctx.fillStyle = "#756444"; ctx.font = "25px sans-serif";
  ctx.fillText("シオリ AI ・ ゲーム内の記録から", 88, 1224);
  return await new Promise<Blob>((resolve, reject) => canvas.toBlob(
    blob => blob ? resolve(blob) : reject(new Error("画像を保存できませんでした。")), "image/png"));
}
