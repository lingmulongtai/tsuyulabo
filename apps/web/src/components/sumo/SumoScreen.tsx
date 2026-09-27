"use client";

import { useEffect, useState } from "react";
import { Tsuyu } from "@/components/art/Tsuyu";
import { CareFrame } from "@/components/games/CareFrame";
import { Button, Card, TruthBadge } from "@/components/ui/primitives";
import { ErrorCard, QueryState } from "@/components/ui/QueryState";
import { useStartSumo, useSumoChallenges, useSumoHistory, useSumoReplay, type BoutReplay } from "@/lib/api/hooks-sumo";

const ACTION: Record<string, string> = {
  approach: "近づく", lunge: "押す！", wing_threat: "翅で威嚇", hold: "こらえる", retreat: "後退",
};

function BoutPlayer({ bout }: { bout: BoutReplay }) {
  const [tick, setTick] = useState(0);
  const [play, setPlay] = useState(0);
  useEffect(() => {
    const timer = window.setInterval(() => setTick(value => {
      if (value >= bout.replay.frames.length) { window.clearInterval(timer); return value; }
      return value + 1;
    }), 550);
    return () => window.clearInterval(timer);
  }, [bout.id, bout.replay.frames.length, play]);
  const frame = bout.replay.frames[Math.max(0, tick - 1)];
  const positions = frame?.positions ?? [-2, 2];
  const finished = tick >= bout.replay.frames.length;
  return <Card className="space-y-3 p-4" aria-label="なわばりずもうの再生">
    <div className="flex items-center justify-between"><h2 className="font-kiwi text-lg">取組の記録</h2><span className="text-xs text-muted">{tick} / {bout.replay.frames.length}</span></div>
    <div className="relative mx-auto aspect-square w-full max-w-sm overflow-hidden rounded-full border-[12px] border-[#a67a55] bg-[radial-gradient(circle,#f9e7a1_0_12%,#dfc791_13%_67%,#c9ac74_68%)]">
      <div className="absolute inset-y-0 left-1/2 w-px bg-[#9b7549]/30" />
      {[0, 1].map(index => <div key={index} className="absolute top-1/2 w-20 -translate-x-1/2 -translate-y-1/2 transition-all duration-500" style={{ left: `${50 + positions[index] * 10}%`, transform: `translate(-50%, -50%) scaleX(${index ? -1 : 1})` }}>
        <Tsuyu sex="m" className="h-20 w-20" />
      </div>)}
      {frame?.push.some(Boolean) && <span className="absolute left-1/2 top-1/4 -translate-x-1/2 text-3xl text-eye motion-safe:animate-bounce" aria-hidden>↔</span>}
      {frame?.actions.includes("wing_threat") && <span className="absolute right-1/4 top-1/4 text-2xl" aria-hidden>✦</span>}
    </div>
    <div className="flex justify-between text-sm"><span>あなた：{ACTION[frame?.actions[0] ?? "hold"]}</span><span>{bout.opponent_name}：{ACTION[frame?.actions[1] ?? "hold"]}</span></div>
    {finished && <p role="status" className="rounded-2xl bg-tint-ai p-3 text-center font-kiwi text-xl">{bout.won ? "勝ち！" : "相手の勝ち！"}　+{bout.reward} しずく</p>}
    <Button tone="plain" size="sm" onClick={() => { setTick(0); setPlay(value => value + 1); }}>もう一度見る</Button>
  </Card>;
}

export function SumoScreen() {
  const choices = useSumoChallenges();
  const history = useSumoHistory();
  const start = useStartSumo();
  const [adultId, setAdultId] = useState("");
  const [opponentId, setOpponentId] = useState("house");
  const [viewId, setViewId] = useState("");
  const replay = useSumoReplay(viewId);
  const submit = () => start.mutate({ adult_id: adultId, opponent_id: opponentId }, {
    onSuccess: bout => setViewId(bout.id),
  });
  return <CareFrame title="なわばりずもう" subtitle="オスどうしの、ちいさな押し合い。">
    <Card className="space-y-2 p-4"><div className="flex items-center justify-between"><b>餌場のまわりで勝負</b><TruthBadge kind="real" /></div>
      <p className="text-sm">本物のオスのショウジョウバエも、餌やなわばりをめぐって突進や翅の威嚇をします。オクトパミンも攻撃行動に関わります。</p>
      <p className="text-xs text-muted">ここでは脳モデルが動きを決めます。買い物は勝敗に影響しません。</p>
    </Card>
    <QueryState query={choices}>{data => <>
      <Card className="p-4 text-sm">きょうはあと <b>{data.remaining} 戦</b> · 連勝 <b>{data.streak}</b></Card>
      {data.males.length ? <Card className="space-y-4 p-4">
        <label className="block text-sm font-bold" htmlFor="sumo-adult">あなたのオス</label>
        <select id="sumo-adult" value={adultId} onChange={event => setAdultId(event.target.value)} className="w-full rounded-xl border border-line bg-surface-2 p-3"><option value="">選んでください</option>{data.males.map(fly => <option key={fly.id} value={fly.id}>{fly.name} · レベル{fly.level}</option>)}</select>
        <label className="block text-sm font-bold" htmlFor="sumo-opponent">対戦相手</label>
        <select id="sumo-opponent" value={opponentId} onChange={event => setOpponentId(event.target.value)} className="w-full rounded-xl border border-line bg-surface-2 p-3">{data.opponents.map(fly => <option key={fly.id} value={fly.id}>{fly.owner_name} · {fly.name}</option>)}</select>
        <Button block tone="ai" disabled={!adultId || data.remaining === 0 || start.isPending} onClick={submit}>{start.isPending ? "取組中…" : "取組をはじめる"}</Button>
        {start.error && <ErrorCard error={start.error} retry={submit} />}
      </Card> : <Card className="p-5 text-center text-sm">オスの成虫を育てると参加できます。</Card>}
    </>}</QueryState>
    {viewId && <QueryState query={replay}>{bout => <BoutPlayer key={bout.id} bout={bout} />}</QueryState>}
    <Card className="space-y-2 p-4"><h2 className="font-kiwi text-lg">これまでの取組</h2><QueryState query={history}>{items => items.length ? items.map(item => <button key={item.id} className="flex w-full justify-between border-t border-line-soft py-3 text-left text-sm" onClick={() => setViewId(item.id)}><span>{item.opponent_name} · {item.won ? "勝ち" : "負け"}</span><span className="text-leaf">再生 →</span></button>) : <p className="text-sm text-muted">まだ取組がありません。</p>}</QueryState></Card>
  </CareFrame>;
}
