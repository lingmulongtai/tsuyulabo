"use client";
import { useState } from "react";
import { useHome, useJob } from "@/lib/api/hooks";
import type { Cue } from "@/game/puzzles/types";
import type { Behaviour } from "../vivarium/types";
import { CareVial } from "../vivarium/CareVial";
import { OdourMoment } from "../vivarium/OdourMoment";

export function TrainingConsequence({ cue, result }: { cue: Cue; result: unknown }) {
  const home = useHome();
  const [action, setAction] = useState<Behaviour>();
  const record = result && typeof result === "object" ? result as Record<string, unknown> : {};
  const pending = record.learning_status === "pending";
  const job = useJob(pending && typeof record.job_id === "string" ? record.job_id : undefined);
  return <section className="space-y-3" aria-label="しつけのあとの様子">
    <CareVial behaviour={action} pointOfInterest={[0.48, -1.08, -0.2]} />
    {home.data?.week && <OdourMoment flyId={home.data.week.id} cue={cue} onBehaviour={setAction} disabled={pending && job.data?.status !== "succeeded"} />}
    {job.data?.status === "failed" && <p role="status" className="text-sm">しつけの反映を待っています。あとでホームから様子を見てください。</p>}
  </section>;
}
