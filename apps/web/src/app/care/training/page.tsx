"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useRef, useState } from "react";
import { CareFrame, ResultSheet } from "@/components/games/CareFrame";
import { TeachPicker } from "@/components/games/TeachPicker";
import { TrainingGame, type TrainingFinish } from "@/components/games/TrainingGame";
import { AppShell } from "@/components/shell/AppShell";
import { Card, Meter } from "@/components/ui/primitives";
import { ErrorCard, LoadingCard } from "@/components/ui/QueryState";
import { CUE_INFO, VALENCE_INFO } from "@/game/labels";
import { practiceTraining } from "@/game/practice";
import type { Cue, TrainingParams, Valence } from "@/game/puzzles/types";
import { useHome, useIssuePuzzle, useSubmitPuzzle } from "@/lib/api/hooks";
import { puzzleParams } from "@/lib/api/puzzle";
import { canPracticeOffline, trainingOutcome, type TrainingOutcome } from "@/lib/api/training-display";
import { preferencePercent, SKILL_LABELS } from "@/lib/display";

function TrainingRound({ practice = false, offline = false, round, remaining, locked, onAgain }: {
  practice?: boolean; offline?: boolean; round: number; remaining?: number; locked?: boolean; onAgain: () => void;
}) {
  const issue = useIssuePuzzle();
  const submit = useSubmitPuzzle();
  const started = useRef(false);
  const submitted = useRef(false);
  const [practiceSession, setPracticeSession] = useState(practice);
  const [choice, setChoice] = useState<{ cue: Cue; valence: Valence } | null>(null);
  const [finish, setFinish] = useState<TrainingFinish | null>(null);
  const practicing = practiceSession || canPracticeOffline(issue.error);
  let params: TrainingParams | undefined;
  let outcome: TrainingOutcome | undefined;
  let decodeError: unknown;
  try {
    params = practicing && choice ? practiceTraining(round, choice.cue, choice.valence) : issue.data ? puzzleParams("training", issue.data.params) : undefined;
    if (submit.data) outcome = trainingOutcome(submit.data);
  } catch (error) { decodeError = error; }

  const pick = (cue: Cue, valence: Valence) => {
    if (started.current || (!practicing && locked)) return;
    started.current = true;
    setChoice({ cue, valence });
    if (!navigator.onLine) setPracticeSession(true);
    else if (!practicing) issue.mutate({ kind: "training", cue, valence });
  };
  const onFinish = (value: TrainingFinish) => {
    if (submitted.current) return;
    submitted.current = true;
    setFinish(value);
    if (!practicing && issue.data) submit.mutate({ id: issue.data.puzzle_id, submission: { ...value.submission } });
  };

  return <>
    {practicing && <Card className="p-3 text-sm text-muted">{offline || canPracticeOffline(issue.error) ? "研究所につながらないため、練習モードで遊べます。" : "練習モード"} 育成や報酬には反映されません。</Card>}
    {!choice && <TeachPicker remaining={practicing ? undefined : remaining} disabled={!practicing && locked} onPick={pick} />}
    {!choice && locked && !practicing && <Card className="p-3 text-sm text-muted">今日のしつけはお休みです。<Link href="/care/training?practice=1" className="ml-2 underline">練習する</Link></Card>}
    {choice && !practicing && issue.isPending && <LoadingCard />}
    {choice && !practicing && issue.error && <ErrorCard error={issue.error} retry={() => issue.mutate({ kind: "training", ...choice })} />}
    {decodeError ? <ErrorCard error={decodeError} /> : null}
    {params && !finish && <TrainingGame params={params} onFinish={onFinish} />}
    {finish && !practicing && !submit.data && (submit.error ? <ErrorCard error={submit.error} retry={() => {
      if (issue.data) submit.mutate({ id: issue.data.puzzle_id, submission: { ...finish.submission } });
    }} /> : <LoadingCard />)}
    {params && finish && (practicing || outcome) && <ResultSheet
      heading={practicing ? "練習おつかれさま！" : "覚えた！"}
      great={outcome?.hirameki} greatLabel="ひらめき！"
      lines={[
        { label: "教えたこと", value: `${CUE_INFO[params.cue].short}${VALENCE_INFO[params.valence].effect}`, tone: "ai" },
        { label: "★", value: "★".repeat(outcome?.stars ?? finish.stars), tone: "banana" },
        ...(outcome?.skillUnlocked ? [{ label: "とくいワザ", value: SKILL_LABELS[outcome.skillUnlocked] ?? "新しいワザ", tone: "leaf" as const }] : []),
      ]}
      primary={{ label: "もう一回", onClick: onAgain }}>
      {outcome?.association && <div className="mt-3">
        <Meter label={`${CUE_INFO[outcome.association.cue].short}の新しい好み`} value={preferencePercent(outcome.association.value)} hint={outcome.association.value.toFixed(2)} color="linear-gradient(90deg,var(--ai),var(--leaf))" />
        <p className="flex justify-between text-xs text-muted"><span>苦手 −1</span><span>0</span><span>+1 好き</span></p>
      </div>}
      <p className="mt-2 text-xs text-muted">{practicing ? "練習の結果です。育成には反映されません。" : outcome?.association ? "キノコ体のつながりが変わりました（ゲーム内のモデル）。" : "学習中です。好みはあとから反映されます。"}</p>
      <Link href="/" className="mt-3 inline-block text-sm text-muted underline">ホームへ</Link>
    </ResultSheet>}
  </>;
}

function LiveTraining({ round, onAgain }: { round: number; onAgain: () => void }) {
  const home = useHome();
  const todo = home.data?.todo.find(item => item.action === "training");
  if (!home.data && (home.fetchStatus === "paused" || canPracticeOffline(home.error))) return <TrainingRound key={round} practice offline round={round} onAgain={onAgain} />;
  if (!home.data) return home.error ? <ErrorCard error={home.error} retry={() => void home.refetch()} /> : <LoadingCard />;
  return <TrainingRound key={round} round={round} onAgain={onAgain} remaining={todo?.remaining ?? undefined} locked={todo?.status !== "available"} />;
}

function TrainingSession() {
  const search = useSearchParams();
  const [round, setRound] = useState(0);
  const onAgain = () => setRound(value => value + 1);
  return search.get("practice") === "1" ? <TrainingRound key={`practice-${round}`} practice round={round} onAgain={onAgain} /> : <LiveTraining round={round} onAgain={onAgain} />;
}

export default function TrainingPage() {
  return <AppShell hideTabs><CareFrame title="しつけ" subtitle="回路パズルで、好き・苦手を教えよう">
    <Suspense fallback={<LoadingCard />}><TrainingSession /></Suspense>
  </CareFrame></AppShell>;
}
