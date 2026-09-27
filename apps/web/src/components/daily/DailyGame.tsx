"use client";

import { useCallback, useState } from "react";
import { TrainingGame, type TrainingFinish } from "@/components/games/TrainingGame";
import { dailyElapsed } from "@/game/daily-circuit";
import type { DailyCircuit } from "@/lib/api/hooks-daily";

/** The daily board uses the training component with its own persistent session clock. */
export function DailyGame({ daily, practice, onFinish }: {
  daily: DailyCircuit; practice: boolean; onFinish: (result: TrainingFinish) => void;
}) {
  const [receivedAt] = useState(() => performance.now());
  const elapsedTime = useCallback(() => dailyElapsed(
    daily.attempt!.started_at, daily.server_now, receivedAt, performance.now(),
  ), [daily, receivedAt]);
  return <TrainingGame params={daily.params} mode="daily" onFinish={onFinish}
    elapsedTime={practice ? undefined : elapsedTime} />;
}
