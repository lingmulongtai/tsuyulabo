"use client";

import { useRouter } from "next/navigation";
import { CareFrame } from "@/components/games/CareFrame";
import { PresentationBoard, type PresentationData } from "@/components/presentation/PresentationBoard";
import { AppShell } from "@/components/shell/AppShell";

/** Sample week (the planning document's example) until the page reads GET /v1/weeks/current/presentation. */
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

export default function PresentationPage() {
  const router = useRouter();
  return (
    <AppShell hideTabs>
      <CareFrame title="研究発表会" subtitle="日曜の夜。1週間の結果とランク">
        <PresentationBoard data={DEMO} week={12} onNext={() => router.push("/eclosion")} />
      </CareFrame>
    </AppShell>
  );
}
