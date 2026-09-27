"use client";
import { AppShell } from "@/components/shell/AppShell";
import { CareFrame, ResultSheet } from "@/components/games/CareFrame";
import { FlyArt } from "@/components/art/FlyArt";
import { MoonIcon, SunIcon } from "@/components/ui/icons";
import { Button, Card } from "@/components/ui/primitives";
import { ErrorCard, QueryState } from "@/components/ui/QueryState";
import { useHome, useSleepEnd, useSleepStart } from "@/lib/api/hooks";
import { CircadianCard } from "@/components/sleep/CircadianCard";

export default function SleepPage() {
  const home = useHome();
  const start = useSleepStart();
  const end = useSleepEnd();
  return <AppShell hideTabs><CareFrame title="ツユとひとやすみ">
    <QueryState query={home}>{data => {
      const night = data.clock.slot === "night";
      const action = night ? "sleep" : "wake";
      const available = data.week ? data.todo.some(item => item.action === action && item.status === "available") : (night || data.clock.slot === "morning");
      return <><CircadianCard circadian={end.data?.circadian ?? data.circadian} /><Card className="overflow-hidden text-center">
        <div className={`relative p-8 ${night ? "bg-[linear-gradient(160deg,#142944,#463b67)] text-white" : "bg-[linear-gradient(160deg,#fff4cc,#d5efe8)] text-[#1e2c29]"}`}>
          {night ? <>
            {[[12, 14, 0], [78, 10, 0.6], [88, 38, 1.2], [20, 44, 0.3], [64, 24, 0.9], [40, 8, 1.5]].map(([x, y, d]) => (
              <span key={`${x}-${y}`} aria-hidden className="absolute size-1.5 rounded-full bg-white motion-safe:animate-pulse" style={{ left: `${x}%`, top: `${y}%`, animationDelay: `${d}s` }} />
            ))}
            <MoonIcon size={56} className="mx-auto drop-shadow-[0_0_18px_rgba(255,224,138,.6)]" />
          </> : <SunIcon size={60} className="mx-auto drop-shadow-[0_0_18px_rgba(255,200,87,.7)]" />}
          <FlyArt stage={data.fly?.stage ?? "egg"} className="mx-auto h-44 w-52" />
          <h2 className="font-kiwi text-2xl">{night ? "おやすみ、ツユ" : "おはよう、ツユ"}</h2>
          <p className="mt-2 text-sm">{night ? "ゆっくり休んで、明日にそなえよう。" : "今日もいっしょに、少しずつ。"}</p>
        </div>
        <div className="space-y-3 p-5">
          <Button block tone={night ? "ai" : "banana"} size="lg" disabled={!available || start.isPending || end.isPending || (night && start.isSuccess) || (!night && end.isSuccess)} onClick={() => night ? start.mutate() : end.mutate()}>{night ? "おやすみ" : "おはよう"}</Button>
          {!available && <p className="text-sm text-muted">おやすみは夜、おはようは朝に、1日1回できます。</p>}
          {start.data && <p role="status" className="text-sm text-ai">おやすみを記録しました。朝になったら会いにきてね。</p>}
        </div>
      </Card>{(start.error || end.error) && <ErrorCard error={start.error ?? end.error} retry={() => night ? start.mutate() : end.mutate()} />}</>;
    }}</QueryState>
    {end.data && <ResultSheet heading="ぐっすり休めたね" lines={[{ label: "睡眠時間", value: `${end.data.hours.toFixed(1)}時間` }, { label: "しずく", value: `+${end.data.bonus}`, tone: "banana" }, { label: "チームのげんき回復", value: `+${Math.round(Object.values(end.data.energy_recovered).reduce((sum, n) => sum + n, 0))}`, tone: "leaf" }]} primary={{ label: "ホームへ", href: "/" }} />}
  </CareFrame></AppShell>;
}
