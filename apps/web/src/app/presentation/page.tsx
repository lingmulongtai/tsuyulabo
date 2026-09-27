"use client";

import Link from "next/link";
import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { CareFrame } from "@/components/games/CareFrame";
import { PresentationBoard, type PresentationData } from "@/components/presentation/PresentationBoard";
import { AppShell } from "@/components/shell/AppShell";
import { Card } from "@/components/ui/primitives";
import { LoadingCard, QueryState } from "@/components/ui/QueryState";
import { useHome, usePresentation } from "@/lib/api/hooks";

/** Sample week from the planning document, available only in demo mode. */
const DEMO: PresentationData = {
  meal_points: 9800,
  training_points: 5120,
  care_points: 3500,
  care_miss: 0,
  penalty: 0,
  points: 18420,
  rank: "rainbow",
  shizuku: 3070,
  research_points: 460,
};

function ReadyPresentation() {
  const presentation = usePresentation();
  const router = useRouter();
  return <QueryState query={presentation}>{data => <PresentationBoard data={data} onNext={() => router.push("/eclosion")} />}</QueryState>;
}

function LivePresentation() {
  const home = useHome();
  return <QueryState query={home}>{data => data.week?.ready_to_eclose ? <ReadyPresentation /> : (
    <Card className="space-y-3 p-5 text-center">
      <h2 className="font-kiwi text-xl">発表会は、まだこれから</h2>
      <p className="text-sm text-muted">研究7日目の夜になったら、1週間の記録をいっしょに振り返ろう。</p>
      <Link href="/" className="inline-block font-bold text-leaf underline">ホームへもどる</Link>
    </Card>
  )}</QueryState>;
}

function PresentationSession() {
  const search = useSearchParams();
  const router = useRouter();
  return search.get("demo") === "1" ? <PresentationBoard data={DEMO} week={12} onNext={() => router.push("/eclosion?demo=1")} /> : <LivePresentation />;
}

export default function PresentationPage() {
  return (
    <AppShell hideTabs>
      <CareFrame title="研究発表会" subtitle="日曜の夜。1週間の結果とランク">
        <Suspense fallback={<LoadingCard />}><PresentationSession /></Suspense>
      </CareFrame>
    </AppShell>
  );
}
