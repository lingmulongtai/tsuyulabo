/** Translate legacy generated copy at the display boundary; stored answers remain intact. */
export function raisingText(text: string): string {
  const terms: Array<[string, string]> = [
    ["研究員シオリ", "シオリ"], ["研究員さん", "飼い主さん"], ["研究員", "飼い主"],
    ["研究発表会", "羽化の日"], ["発表会", "羽化の日"],
    ["研究チーム", "コロニー"], ["研究ポイント", "飼育の経験"],
    ["研究ランク", "育ちの評価"], ["研究室", "飼育棚"], ["研究所", "飼育棚"],
    ["研究週", "この子の一週間"], ["実験し", "コピーを試し"], ["実験", "ためし"], ["論文", "図鑑の豆知識"],
  ];
  let result = text.replace(/研究(?=\d+日目)/g, "");
  for (const [old, next] of terms) result = result.replaceAll(old, next);
  return result.replaceAll("研究", "飼育");
}

/** Evidence stays in its own disclosure rather than interrupting the companion's sentences. */
export function companionText(text: string, evidence: readonly string[]): string {
  let result = raisingText(text);
  for (const id of [...evidence].sort((a, b) => b.length - a.length)) {
    const escaped = id.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    result = result.replace(new RegExp(`(?:記録\\s*)?${escaped}(?![\\w-])`, "g"), "");
  }
  return result.replace(/記録\s*#\d+/g, "").replace(/[（(【\[]\s*[）)】\]]/g, "").replace(/\s+([。！？])/g, "$1").replace(/ {2,}/g, " ").trim();
}

/** Put quantitative reports in the disclosure, with a faithful plain-language reading first. */
export function companionDisplay(text: string, evidence: readonly string[]): {
  text: string;
  detail?: string;
} {
  const original = companionText(text, evidence);
  let plain = original.replace(/([^。]+?)のしつけは、ごほうび(\d+)回、罰(\d+)回の記録です。/g,
    (_, cue: string, reward: string, punish: string) => {
      if (Number(reward) > 0 && Number(punish) === 0) return `${cue}とごほうびを結びつける練習をしてきました。`;
      if (Number(punish) > 0 && Number(reward) === 0) return `${cue}と苦いものを結びつける練習をしてきました。`;
      return Number(reward) + Number(punish) > 0 ? `${cue}で、いろいろな練習をしてきました。` : `${cue}のしつけは、まだこれからです。`;
    });
  plain = plain.replace(/([^。]+?)の直近の好みの値は([+-]?\d+(?:\.\d+)?)です。/g,
    (sentence: string, cue: string, value: string) => {
      const preference = Number(value);
      if (!Number.isFinite(preference) || Math.abs(preference) > 1) return sentence;
      return preferenceState(cue.includes("匂い") || cue.includes("光") ? cue : `${cue}の匂い`, preference);
    });
  plain = plain.replace(/コピーで\d+回試すと、接近(\d+)回、回避(\d+)回でした。/g,
    (_, approach: string, avoid: string) => {
      if (Number(approach) > Number(avoid)) return "コピーで試すと、近づく反応が多く見られました。";
      if (Number(avoid) > Number(approach)) return "コピーで試すと、離れる反応が多く見られました。";
      return "コピーで試すと、近づく反応と離れる反応が同じくらい見られました。";
    });
  const quantitative = /\d+(?:\.\d+)?\s*(?:回|Hz|ms|%|％)|[+-]\d+\.\d+/;
  if (quantitative.test(plain)) {
    plain = plain.split(/(?<=。)/).filter(sentence => !quantitative.test(sentence)).join("").trim();
    if (!plain) plain = "細かな数字を含む説明は「根拠」にまとめました。";
  }
  return plain === original ? { text: plain } : { text: plain, detail: original };
}

export function hungerState(value: number): string {
  return value < 30 ? "おなかが空いています。ごはんを作りましょう。" : value < 70 ? "ごはんを食べて過ごしています。" : "おなかが満たされています。";
}

export function cleanlinessState(value: number): string {
  return value < 30 ? "びんが汚れてきました。そうじをしましょう。" : value < 70 ? "びんをそろそろそうじしましょう。" : "びんはきれいです。";
}

export function preferenceState(name: string, value: number): string {
  return value > 0.1 ? `${name}に寄っていくのが好き。` : value < -0.1 ? `${name}から離れたがります。` : `${name}はまだ好きでも苦手でもありません。`;
}
