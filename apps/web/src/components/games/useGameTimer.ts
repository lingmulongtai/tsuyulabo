"use client";
import { useEffect, useRef, useState } from "react";

export function useGameTimer(limit: number) {
  const origin = useRef(0);
  const [running, setRunning] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    if (!running) return;
    let frame = 0;
    const tick = () => {
      const next = Math.round(performance.now() - origin.current);
      setElapsed(Math.min(limit, next));
      if (next >= limit) setRunning(false);
      else frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [limit, running]);
  return { elapsed, running, expired: elapsed >= limit,
    now: () => Math.round(performance.now() - origin.current),
    start: () => { origin.current = performance.now(); setElapsed(0); setRunning(true); },
    stop: () => setRunning(false),
  };
}
