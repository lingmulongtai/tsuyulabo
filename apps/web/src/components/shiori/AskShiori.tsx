"use client";
import { useState } from "react";
import { useJob, useShioriAsk } from "@/lib/api/hooks";
import { shioriAnswer } from "@/lib/display";
import { ShioriBubble } from "../home/ShioriBubble";
import { Button, Card, TruthBadge } from "../ui/primitives";
import { ErrorCard } from "../ui/QueryState";

export function AskShiori({ initialQuestion = "", context = "" }: { initialQuestion?: string; context?: string }) {
  const [question, setQuestion] = useState(initialQuestion);
  const [jobId, setJobId] = useState<string>();
  const ask = useShioriAsk();
  const job = useJob(jobId);
  const working = ask.isPending || Boolean(jobId && (!job.data || ["pending", "running"].includes(job.data.status)) && !job.error);
  const answer = shioriAnswer(job.data?.result ?? null);
  const send = () => {
    const text = question.trim();
    if (!text || working) return;
    setJobId(undefined);
    ask.mutate(`${context}${text}`, { onSuccess: data => setJobId(data.job_id) });
  };
  return <div className="space-y-4">
    <Card className="space-y-3 p-4">
      <div className="flex items-center gap-2"><h2 className="font-kiwi">シオリに聞いてみよう</h2><TruthBadge kind="ai" /></div>
      <form onSubmit={event => { event.preventDefault(); send(); }} className="space-y-3">
        <label htmlFor="shiori-question" className="block text-sm text-muted">気になること</label>
        <textarea id="shiori-question" value={question} onChange={event => setQuestion(event.target.value)} maxLength={2000 - context.length} rows={3} disabled={working}
          placeholder="なんでりんご酢から離れるの？" className="w-full resize-y rounded-2xl border border-line bg-bg p-3 text-sm" />
        <Button type="submit" block tone="ai" disabled={working || !question.trim()}>{working ? "観察記録を調べています…" : "シオリに聞く"}</Button>
      </form>
      <p className="text-xs text-muted">ゲーム内のモデルで測った結果です</p>
    </Card>
    {ask.error && <ErrorCard error={ask.error} retry={send} />}
    {working && <Card className="p-5 text-sm text-ai"><p role="status" className="motion-safe:animate-pulse">シオリが記録や実験を確かめています。少し待っていてね。</p></Card>}
    {job.error && <ErrorCard error={job.error} retry={() => void job.refetch()} />}
    {job.data?.status === "failed" && <ErrorCard error={new Error(typeof job.data.error?.message === "string" ? job.data.error.message : "調べものがうまくいきませんでした。もう一度質問できます。")} />}
    {job.data?.status === "succeeded" && (answer.answer ? <>
      <ShioriBubble title="シオリからの答え" text={answer.answer} evidence={answer.evidence} />
      <p className="px-3 text-xs text-muted">ゲーム内のモデルで測った結果です</p>
    </> : <ErrorCard error={new Error("答えを読み取れませんでした。もう一度質問してください。")} />)}
  </div>;
}
