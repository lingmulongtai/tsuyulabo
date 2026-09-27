"use client";

import { useMemo } from "react";

export const RAINBOW = ["#FF6B8B", "#FFC857", "#7EE0A1", "#5EC8F2", "#A78BFA"];
export const GOLD = ["#FFD54A", "#FFFFFF", "#FFC857"];

function makeParticles(count: number, colors: string[], spread: number, seed: number) {
  let s = seed * 9301 + 49297;
  const rand = () => {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };
  return Array.from({ length: count }, (_, i) => {
    const a = rand() * Math.PI * 2;
    const r = spread * (0.4 + rand() * 0.8);
    return { i, dx: Math.cos(a) * r, dy: Math.sin(a) * r, rot: `${Math.round(rand() * 540)}deg`, c: colors[i % colors.length], sq: i % 3 === 0 };
  });
}

/**
 * A one-shot particle burst. Re-mount it (change `key`) to fire again. Pure CSS, so it is cheap and respects
 * reduced-motion.
 */
export function Burst({ count = 30, colors = RAINBOW, spread = 150, seed = 1 }: { count?: number; colors?: string[]; spread?: number; seed?: number }) {
  const particles = useMemo(() => makeParticles(count, colors, spread, seed), [count, colors, spread, seed]);

  return (
    <div className="pointer-events-none absolute left-1/2 top-1/2 size-0" aria-hidden>
      {particles.map((p) => (
        <span
          key={p.i}
          className={`burst-pt${p.sq ? " sq" : ""}`}
          style={{ "--dx": `${p.dx}px`, "--dy": `${p.dy}px`, "--rot": p.rot, "--c": p.c } as React.CSSProperties}
        />
      ))}
    </div>
  );
}
