"use client";
import { useEffect, useRef, useState, type ReactNode } from "react";
import Link from "next/link";
import { ApiError } from "@/lib/api/client";
import { useIssuePuzzle, useSubmitPuzzle } from "@/lib/api/hooks";
import { puzzleParams } from "@/lib/api/puzzle";
import type { components } from "@/lib/api/schema";
import type { PuzzleContracts, PuzzleKind } from "@/game/puzzles/types";
import { ErrorCard, LoadingCard } from "../ui/QueryState";
import { Card } from "../ui/primitives";
import { ResultSheet, type EffectLine } from "./CareFrame";

type Result = components["schemas"]["PuzzleResult"];
export function PuzzleSession<K extends PuzzleKind>({ kind, practice = false, practiceParams, children }: {
  kind: K; practice?: boolean; practiceParams?: PuzzleContracts[K]["params"];
  children: (params: PuzzleContracts[K]["params"], finish: (submission: PuzzleContracts[K]["submission"], preview?: number) => void) => ReactNode;
}) {
  const issue = useIssuePuzzle();
  const submit = useSubmitPuzzle();
  const issued = useRef(false);
  const [submission, setSubmission] = useState<Record<string, unknown> | null>(null);
  const [practiceScore, setPracticeScore] = useState<number | null>(null);
  const { mutate } = issue;
  useEffect(() => {
    if (!practice && !issued.current) { issued.current = true; mutate({ kind }); }
  }, [kind, practice, mutate]);

  const offline = issue.error instanceof ApiError && issue.error.retryable && issue.error.code !== "invalid_response";
  const practicing = practice || (offline && Boolean(practiceParams));
  let params: PuzzleContracts[K]["params"] | undefined;
  let decodeError: unknown;
  try { params = practicing ? practiceParams : issue.data ? puzzleParams(kind, issue.data.params) : undefined; }
  catch (error) { decodeError = error; }

  const finish = (value: PuzzleContracts[K]["submission"], preview = 0) => {
    if (practicing) { setPracticeScore(preview); return; }
    if (submission || !issue.data) return;
    const body: Record<string, unknown> = Object.fromEntries(Object.entries(value));
    setSubmission(body);
    submit.mutate({ id: issue.data.puzzle_id, submission: body });
  };
  const retrySubmit = () => { if (submission && issue.data) submit.mutate({ id: issue.data.puzzle_id, submission }); };

  return <>
    {practicing && <Card className="p-3 text-sm text-muted" >{offline ? "研究所につながらないため、練習モードで遊べます。" : "練習モード"} 育成や報酬には反映されません。<Link href="/" className="ml-2 underline">ホームへ</Link></Card>}
    {decodeError ? <ErrorCard error={decodeError} /> : null}
    {!practicing && issue.error && <ErrorCard error={issue.error} retry={() => issue.mutate({ kind })} />}
    {!params && !issue.error && !decodeError && <LoadingCard />}
    {params && !submission && practiceScore === null && children(params, finish)}
    {submission && !submit.data && (submit.error ? <ErrorCard error={submit.error} retry={retrySubmit} /> : <LoadingCard />)}
    {submit.data && <PuzzleResult kind={kind} result={submit.data} />}
    {practiceScore !== null && <ResultSheet heading="練習おつかれさま！" lines={[{ label: "おいしさ", value: String(practiceScore) }]} primary={{ label: "ホームへ", href: "/" }}><p className="mt-2 text-sm text-muted">練習の結果です。育成には反映されません。</p></ResultSheet>}
  </>;
}

function PuzzleResult({ kind, result }: { kind: PuzzleKind; result: Result }) {
  const lines: EffectLine[] = [];
  if (result.score !== undefined) lines.push({ label: kind === "meal" ? "おいしさ" : "スコア", value: String(result.score), tone: "banana" });
  if (result.effects) {
    for (const [key, label] of [["hunger", "おなか"], ["growth", "成長ポイント"], ["cleanliness", "きれい"]]) {
      const value = result.effects[key];
      if (typeof value === "number") lines.push({ label, value: `${key === "cleanliness" ? "" : "+"}${value}`, tone: "leaf" });
    }
  }
  if (result.hit !== undefined) lines.push({ label: "羽化へのボーナス", value: result.hit ? "あり" : "なし" });
  const great = result.great_success ?? (result.hit ?? (result.score === 100));
  return <ResultSheet heading={kind === "pupation_site" ? result.hit ? "ぴったりの場所！" : "ここで見守ってみよう" : "お世話できました！"}
    great={great} greatLabel={kind === "meal" ? "大成功！" : kind === "pupation_site" ? "あたり！" : "PERFECT!"}
    lines={lines} primary={{ label: "ホームへ", href: "/" }}>
    {result.grades && <p className="mt-3 text-sm font-bold text-leaf">{result.grades.map(g => g.toUpperCase()).join(" / ")}</p>}
  </ResultSheet>;
}
