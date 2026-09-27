"use client";

import { useEffect, useState } from "react";
import { CareFrame, ResultSheet } from "@/components/games/CareFrame";
import type { TrainingFinish } from "@/components/games/TrainingGame";
import { Button, Card } from "@/components/ui/primitives";
import { ErrorCard, QueryState } from "@/components/ui/QueryState";
import { dailyTime } from "@/game/daily-circuit";
import { ApiError } from "@/lib/api/client";
import { useDailyCircuit, useDailyRanking, useStartDaily, useSubmitDaily, type DailyCircuit, type DailySubmission } from "@/lib/api/hooks-daily";
import { DailyGame } from "./DailyGame";
import { DailyRankingList } from "./DailyRankingList";

export function DailyScreen() {
  const daily = useDailyCircuit();
  return <CareFrame title="今日の回路" subtitle="7×7の回路をつないで、フレンドとタイムを競おう">
    <QueryState query={daily}>{data => <DailySession key={data.day} daily={data} />}</QueryState>
  </CareFrame>;
}

function DailySession({ daily }: { daily: DailyCircuit }) {
  const start = useStartDaily();
  const submit = useSubmitDaily();
  const ranking = useDailyRanking(daily.day);
  const [active, setActive] = useState<{ daily: DailyCircuit; practice: boolean } | null>(null);
  const [submission, setSubmission] = useState<DailySubmission | null>(null);
  const [practiceTime, setPracticeTime] = useState<number | null>(null);
  const [expired, setExpired] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const result = submit.data ?? daily.my_result;
  const myRank = ranking.data?.day === daily.day ? ranking.data.entries.find(entry => entry.is_me)?.rank : undefined;

  useEffect(() => {
    if (!active || active.practice) return;
    const remaining = Date.parse(active.daily.attempt!.expires_at) - Date.parse(active.daily.server_now);
    const id = setTimeout(() => setExpired(true), Math.max(0, remaining));
    return () => clearTimeout(id);
  }, [active]);

  const finish = (value: TrainingFinish) => {
    if (!active || submission) return;
    if (active.practice) { setPracticeTime(value.elapsedMs); setActive(null); return; }
    const body = { day: active.daily.day, path: [...value.submission.path], elapsed_ms: value.submission.elapsed_ms };
    setSubmission(body);
    setActive(null);
    submit.mutate(body, { onSuccess: () => setShowResult(true) });
  };

  const startScored = () => start.mutate(daily.day, { onSuccess: data => {
    if (data.my_result) return;
    if (!data.attempt || Date.parse(data.attempt.expires_at) <= Date.parse(data.server_now)) {
      setExpired(true); return;
    }
    setExpired(false);
    setPracticeTime(null);
    setActive({ daily: data, practice: false });
  } });
  const practice = () => {
    setPracticeTime(null);
    setSubmission(null);
    setExpired(false);
    setActive({ daily, practice: true });
  };
  const attemptExpired = expired || Boolean(daily.attempt && Date.parse(daily.attempt.expires_at) <= Date.parse(daily.server_now));
  const playing = active && (active.practice || !attemptExpired);
  const retryable = submit.error instanceof ApiError && submit.error.retryable;

  return <>
    <Card className="space-y-2 p-4 text-sm">
      <p className="font-bold text-ai">{daily.day} の問題 · 毎朝4時更新</p>
      <p>数字の順に、全部のマスを一筆書き。本番の記録は1日1回です。</p>
      <p className="text-xs text-muted">20秒未満で60しずく、40秒未満で40しずく、それ以降は20しずく。開始から計測し、やり直し中や画面を閉じている間も進みます（最大10分）。通信時間も記録に含みます。</p>
    </Card>

    {playing ? <>
      <p role="status" className="text-center text-sm font-bold text-ai">{active.practice ? "練習中 · 記録・報酬はありません" : "本番 · 完成したら自動で記録します"}</p>
      <DailyGame daily={active.daily} practice={active.practice} onFinish={finish} />
      <Button tone="plain" size="sm" onClick={() => setActive(null)}>一覧に戻る</Button>
    </> : <>
      {attemptExpired && !result && <Card className="p-4 text-sm text-muted">本番の時間が終わりました。練習でもう一度つないでみよう。</Card>}
      {submission && !result && !submit.error && <p role="status" className="py-4 text-center text-ai">タイムを記録しています…</p>}
      {submit.error && !result && <ErrorCard error={submit.error} retry={retryable && submission ? () => submit.mutate(submission, { onSuccess: () => setShowResult(true) }) : undefined} />}
      {start.error && <ErrorCard error={start.error} retry={startScored} />}
      {practiceTime !== null && <Card className="space-y-1 p-5 text-center" ><h2 className="font-kiwi text-xl">つながった！</h2><p className="font-mono text-2xl">{dailyTime(practiceTime)}</p><p className="text-xs text-muted">練習のタイムです。記録・報酬には反映されません。</p></Card>}
      {result && <Card className="space-y-2 p-4 text-center"><p className="font-bold text-ai">今日の記録 · {dailyTime(result.elapsed_ms)}</p><p className="text-sm text-muted">{myRank ? `フレンド内 ${myRank}位 · ` : ""}{result.shizuku}しずく獲得済み</p><Button tone="ai" size="sm" onClick={() => setShowResult(true)}>結果を見る</Button></Card>}
      {result && showResult && <ResultSheet heading="今日の回路、クリア！" lines={[
        { label: "記録タイム", value: dailyTime(result.elapsed_ms), tone: "ai" },
        { label: "しずく", value: `+${result.shizuku}`, tone: "leaf" },
        { label: "フレンド内の順位", value: myRank ? `${myRank}位` : "確認中…" },
      ]} primary={{ label: "ランキングを見る", onClick: () => setShowResult(false) }}><p className="mt-2 text-xs text-muted">今日の本番は記録済みです。練習は何度でも遊べます。</p>{ranking.error && <ErrorCard error={ranking.error} retry={() => void ranking.refetch()} />}</ResultSheet>}
      {!result && !attemptExpired && !submission && <Button block tone="ai" size="lg" disabled={start.isPending} onClick={startScored}>{start.isPending ? "準備中…" : daily.attempt ? "本番を続ける" : "本番をはじめる"}</Button>}
      <Button block tone="plain" disabled={submit.isPending || start.isPending || Boolean(submission && !result && retryable)} onClick={practice}>練習でつなぐ（記録なし）</Button>
    </>}

    <QueryState query={ranking}>{data => data.day === daily.day ? <DailyRankingList ranking={data} /> : <p className="text-sm text-muted">新しい日のランキングに切り替えています。</p>}</QueryState>
  </>;
}
