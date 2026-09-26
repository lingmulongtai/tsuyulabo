"use client";

import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";
import { buzz } from "@/game/audio/haptics";
import * as Sound from "@/game/audio/sound";
import { Button } from "../ui/primitives";

/** Header + body used by every care minigame screen. */
export function CareFrame({ title, subtitle, children }: { title: string; subtitle?: string; children: ReactNode }) {
  return (
    <div className="flex min-h-dvh flex-col gap-3 px-4 pb-6 pt-[max(12px,env(safe-area-inset-top))]">
      <header className="flex items-center gap-3">
        <Link href="/" className="press grid size-10 place-items-center rounded-2xl border border-line-soft bg-surface-2" aria-label="ホームへもどる">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden>
            <path d="m15 5-7 7 7 7" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </Link>
        <div className="min-w-0">
          <h1 className="font-kiwi text-xl leading-tight">{title}</h1>
          {subtitle && <p className="text-xs text-muted">{subtitle}</p>}
        </div>
      </header>
      {children}
    </div>
  );
}

export interface EffectLine {
  label: string;
  value: string;
  tone?: "leaf" | "eye" | "banana" | "ai";
}

/**
 * The result sheet after a minigame. `great` triggers the flash + fanfare used for 大成功 / ひらめき / PERFECT.
 */
export function ResultSheet({
  heading,
  great,
  greatLabel = "大成功！",
  lines,
  children,
  primary,
}: {
  heading: string;
  great?: boolean;
  greatLabel?: string;
  lines: EffectLine[];
  children?: ReactNode;
  primary: { label: string; href?: string; onClick?: () => void };
}) {
  const [flash, setFlash] = useState(Boolean(great));
  useEffect(() => {
    if (!great) return;
    Sound.greatSuccess();
    buzz([30, 40, 30]);
    const t = setTimeout(() => setFlash(false), 700);
    return () => clearTimeout(t);
  }, [great]);

  const toneClass = { leaf: "text-leaf", eye: "text-eye", banana: "text-[#b98512] dark:text-banana", ai: "text-ai" } as const;

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-[#10201d]/65 p-6 backdrop-blur-sm">
      {flash && <div className="pointer-events-none fixed inset-0 bg-white motion-safe:animate-[ping_0.7s_ease-out_1]" />}
      <div className="relative w-full max-w-sm overflow-hidden rounded-[28px] bg-surface-2 p-6 text-center shadow-2xl pop-in">
        {great && (
          <div className="absolute inset-x-0 top-0 h-28 bg-[radial-gradient(circle_at_50%_0%,rgba(255,213,74,.45),transparent_70%)]" aria-hidden />
        )}
        {great && <div className="relative mb-1 font-kiwi text-3xl text-[#c98a12] drop-shadow-sm pop-in">{greatLabel}</div>}
        <div className="relative font-kiwi text-xl">{heading}</div>
        {children}
        <ul className="relative mt-4 space-y-1.5 text-left">
          {lines.map((l) => (
            <li key={l.label} className="flex items-center justify-between rounded-2xl bg-bg px-4 py-2 text-sm">
              <span className="text-muted">{l.label}</span>
              <span className={`font-mono font-bold ${l.tone ? toneClass[l.tone] : ""}`}>{l.value}</span>
            </li>
          ))}
        </ul>
        {primary.href ? (
          <Link href={primary.href} className="mt-5 block">
            <Button block size="lg" tabIndex={-1}>
              {primary.label}
            </Button>
          </Link>
        ) : (
          <Button className="mt-5" block size="lg" onClick={primary.onClick}>
            {primary.label}
          </Button>
        )}
      </div>
    </div>
  );
}
