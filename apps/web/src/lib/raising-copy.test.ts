import { describe, expect, it } from "vitest";
import { cleanlinessState, companionDisplay, companionText, hungerState, preferenceState, raisingText } from "./raising-copy";

describe("raising display boundary", () => {
  it("translates old generated text without rewriting the stored answer", () => {
    const original = "研究員さん、研究3日目です。研究室で実験し、研究発表会で研究ランクを見よう。";
    const displayed = raisingText(original);
    expect(displayed).toBe("飼い主さん、3日目です。飼育棚でコピーを試し、羽化の日で育ちの評価を見よう。");
    expect(original).toContain("研究員さん");
    expect(raisingText("研究チームの研究ポイント。論文を読む研究員シオリ。")).not.toMatch(/研究|論文|実験/);
  });
  it("moves known references out of the sentence without eating a longer identifier", () => {
    expect(companionText("バナナが好きです（event#12）。記録 #0412", ["event#12"])).toBe("バナナが好きです。");
    expect(companionText("event#123 event#12", ["event#12"])).toBe("event#123");
    expect(companionText("観察しました [copy.1]", ["copy.1"])).toBe("観察しました");
  });
  it("describes care needs and neutral preferences without percentages", () => {
    expect(hungerState(20)).toContain("ごはんを作り");
    expect(cleanlinessState(20)).toContain("そうじ");
    expect(preferenceState("バナナ", 0)).toContain("まだ");
    expect(preferenceState("バナナ", 0.5)).toContain("寄って");
    expect(preferenceState("バナナ", -0.5)).toContain("離れ");
  });
  it("reads verified preference reports plainly and keeps all numbers in the disclosure", () => {
    const answer = "バナナのしつけは、ごほうび18回、罰0回の記録です #0046。バナナの直近の好みの値は+0.57です #0046。コピーで20回試すと、接近18回、回避2回でした #c-19。";
    const display = companionDisplay(answer, ["#0046", "#c-19"]);
    expect(display.text).toContain("ごほうびを結びつける");
    expect(display.text).toContain("バナナの匂いに寄っていくのが好き");
    expect(display.text).toContain("コピーで試すと、近づく反応が多く");
    expect(display.text).not.toMatch(/\d|#c-19/);
    expect(display.detail).toContain("+0.57");
    expect(answer).toContain("#c-19");
  });
  it("keeps unfamiliar quantitative claims as source text instead of inventing a creature state", () => {
    const report = "細胞群の発火率は87 Hzです。";
    expect(companionDisplay(report, [])).toEqual({ text: "細かな数字を含む説明は「根拠」にまとめました。", detail: report });
    expect(companionDisplay("その匂いを避けています。", [])).toEqual({ text: "その匂いを避けています。" });
    expect(companionDisplay("バナナの直近の好みの値は-0.5です。", []).text).toContain("離れたがります");
  });
});
