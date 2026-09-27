"use client";

import { useId } from "react";

/** A waxing moon and a progress arc share the server's gauge value. */
export function CircadianRing({ gauge, compact = false }: { gauge: number; compact?: boolean }) {
  const maskId = useId();
  const value = Math.max(0, Math.min(100, Math.round(gauge)));
  return <div role="meter" aria-label="体内時計ゲージ" aria-valuemin={0} aria-valuemax={100} aria-valuenow={value}
    className={compact ? "size-10 shrink-0" : "w-28 shrink-0 text-center"}>
    <svg viewBox="0 0 64 64" aria-hidden="true" className="w-full text-ai">
      <defs><mask id={maskId}>
        <circle cx="32" cy="32" r="16" fill="white" />
        <circle cx={32 - 36 * value / 100} cy="32" r="16" fill="black" />
      </mask></defs>
      <circle cx="32" cy="32" r="28" fill="none" stroke="var(--line-soft)" strokeWidth="4" />
      <circle cx="32" cy="32" r="28" fill="none" stroke="currentColor" strokeWidth="4"
        pathLength="100" strokeDasharray={`${value} 100`} transform="rotate(-90 32 32)" />
      <circle cx="32" cy="32" r="16" fill="var(--line-soft)" />
      <circle cx="32" cy="32" r="16" fill="var(--banana)" mask={`url(#${maskId})`} />
    </svg>
    {!compact && <p className="font-mono text-xl font-bold text-ai">{value}<span className="text-xs text-muted"> / 100</span></p>}
  </div>;
}
