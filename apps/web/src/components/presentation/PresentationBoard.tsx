"use client";

import { useEffect, useRef, useState } from "react";
import { buzz } from "@/game/audio/haptics";
import * as Sound from "@/game/audio/sound";
import type { WeekRank } from "@/game/expectation";
import { Burst, GOLD, RAINBOW } from "../effects/Burst";
import { RANK_LABELS } from "../eclosion/traits";
import { ShioriBubble } from "../home/ShioriBubble";
import { DropIcon, FlaskIcon } from "../ui/icons";
import { Button } from "../ui/primitives";

/** Mirrors GET /v1/weeks/current/presentation. */
export interface PresentationData {
  meal_points: number;
  training_points: number;
  care_points: number;
  care_miss: number;
  penalty: number;
  points: number;
  rank: WeekRank;
  shizuku: number;
  research_points: number;
}

const RANK_STYLE: Record<WeekRank, { ring: string; text: string }> = {
  normal: { ring: "#ffffff", text: "#1e2c29" },
  silver: { ring: "#7fc8ff", text: "#0c3a5c" },
  gold: { ring: "#ffd54a", text: "#5c3d00" },
  rainbow: { ring: "conic-gradient(#ff6b8b,#ffc857,#7ee0a1,#5ec8f2,#a78bfa,#ff6b8b)", text: "#1e2c29" },
};

function useCountUp(target: number, run: boolean, ms = 900) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    if (!run) return;
    let raf = 0;
    const t0 = performance.now();
    const tick = () => {
      const k = Math.min(1, (performance.now() - t0) / ms);
      setValue(Math.round(target * (1 - Math.pow(1 - k, 3))));
      if (k < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, run, ms]);
  return value;
}

/**
 * 研究発表会 — Sunday night. The breakdown lines appear one by one, the total counts up after a drum roll and the
 * rank badge drops in. Shiori hosts.
 */
export function PresentationBoard({ data, week, hostLine, onNext }: { data: PresentationData; week?: number; hostLine?: string; onNext: () => void }) {
  const [step, setStep] = useState(0); // 0..4 rows, 5 total, 6 rank
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  useEffect(() => {
    const at = (ms: number, fn: () => void) => timers.current.push(setTimeout(fn, ms));
    Sound.init();
    [1, 2, 3, 4].forEach((s) =>
      at(500 + s * 520, () => {
        setStep(s);
        Sound.tap();
      }),
    );
    at(3000, () => {
      setStep(5);
      Sound.drumroll();
    });
    at(4400, () => {
      setStep(6);
      Sound.rankReveal(data.rank);
      buzz(data.rank === "rainbow" || data.rank === "gold" ? [30, 40, 60] : 20);
    });
    const list = timers.current;
    return () => list.forEach(clearTimeout);
  }, [data.rank]);

  const total = useCountUp(data.points, step >= 5, 1300);
  const rows: Array<{ label: string; value: number; tone: string }> = [
    { label: "ごはん", value: data.meal_points, tone: "text-[#b98512] dark:text-banana" },
    { label: "しつけ", value: data.training_points, tone: "text-ai" },
    { label: "お世話", value: data.care_points, tone: "text-leaf" },
    { label: `ケアミス ${data.care_miss}`, value: data.penalty > 0 ? -data.penalty : 0, tone: data.penalty > 0 ? "text-eye" : "text-muted" },
  ];
  const style = RANK_STYLE[data.rank];
  const big = data.rank === "gold" || data.rank === "rainbow";

  return (
    <div className="flex flex-col gap-4">
      <div className="relative overflow-hidden rounded-[32px] bg-[radial-gradient(circle_at_50%_0%,#2e5750,#10201d_75%)] px-5 pb-6 pt-5 text-white shadow-[var(--shadow)]">
        <div className="text-center">
          <div className="text-xs tracking-[0.3em] text-white/70">{week ? `第${week}週` : "今週"}</div>
          <div className="font-kiwi text-2xl">研究発表会</div>
        </div>

        <ul className="mt-4 space-y-1.5">
          {rows.map((r, i) => (
            <li
              key={r.label}
              className={`flex items-center justify-between rounded-2xl bg-white/8 px-4 py-2 transition-all duration-300 ${step > i ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"}`}
            >
              <span className="text-sm text-white/80">{r.label}</span>
              <span className="font-mono text-lg tabular">{r.value >= 0 ? r.value.toLocaleString("ja-JP") : `−${Math.abs(r.value).toLocaleString("ja-JP")}`}</span>
            </li>
          ))}
        </ul>

        <div className={`mt-4 text-center transition-opacity duration-300 ${step >= 5 ? "opacity-100" : "opacity-0"}`}>
          <div className="text-xs text-white/70">合計</div>
          <div className="font-mono text-5xl tabular">
            {total.toLocaleString("ja-JP")}
            <span className="ml-1 text-lg">pt</span>
          </div>
        </div>

        <div className="relative mt-4 flex h-28 items-center justify-center">
          {step >= 6 && (
            <>
              {big && <Burst count={data.rank === "rainbow" ? 50 : 30} colors={data.rank === "rainbow" ? RAINBOW : GOLD} spread={180} />}
              <div className="drop-in rounded-full p-[5px] shadow-[0_10px_40px_-10px_rgba(255,213,74,.7)]" style={{ background: style.ring }}>
                <div className="grid size-24 place-items-center rounded-full bg-white text-center" style={{ color: style.text }}>
                  <div>
                    <div className="text-[0.65rem] font-bold tracking-widest opacity-70">RANK</div>
                    <div className={`font-kiwi text-2xl ${data.rank === "rainbow" ? "rainbow-text" : ""}`}>{RANK_LABELS[data.rank]}</div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {step >= 6 && (
        <div className="flex flex-col gap-3 float-up">
          <div className="grid grid-cols-2 gap-2">
            <div className="flex items-center justify-center gap-2 rounded-2xl border border-line-soft bg-surface-2 py-3 font-bold">
              <DropIcon size={22} /> しずく <span className="font-mono tabular">+{Math.max(0, data.shizuku).toLocaleString("ja-JP")}</span>
            </div>
            <div className="flex items-center justify-center gap-2 rounded-2xl border border-line-soft bg-surface-2 py-3 font-bold">
              <FlaskIcon size={22} className="text-leaf" /> 研究pt <span className="font-mono tabular">+{Math.max(0, data.research_points).toLocaleString("ja-JP")}</span>
            </div>
          </div>
          <ShioriBubble
            title="発表会の司会"
            text={
              hostLine ??
              (big
                ? "今週の記録はとても充実していました。ランクが高いほど、羽化で良い素質や突然変異が出やすくなります。"
                : "記録をまとめました。来週はお世話の回数を増やすと、ランクが上がりやすくなります。")
            }
          />
          <Button size="lg" block tone="banana" onClick={onNext}>
            羽化を見る
          </Button>
        </div>
      )}
    </div>
  );
}
