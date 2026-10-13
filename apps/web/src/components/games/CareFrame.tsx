"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { CareStage, useCareStage } from "../vivarium/CareStage";
import glass from "../ui/material.module.css";
import motion from "../ui/motion.module.css";
import { useEffect, type ReactNode } from "react";
import { buzz } from "@/game/audio/haptics";
import * as Sound from "@/game/audio/sound";
import { Button } from "../ui/primitives";

/** Header + body used by every care minigame screen. */
export function CareFrame({ title, subtitle, children }: { title: string; subtitle?: string; children: ReactNode }) {
  const care = usePathname().startsWith("/care/");
  const header = <header className={`${care ? `${glass.glass} fixed inset-x-3 top-[max(12px,env(safe-area-inset-top))] z-30 rounded-2xl px-3 py-2` : ""} flex items-center gap-3`}>
    <Link href="/" className="press grid size-11 shrink-0 place-items-center rounded-full border border-line-soft" aria-label="ホームへもどる">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden><path d="m15 5-7 7 7 7" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" /></svg>
    </Link>
    <div className="min-w-0"><h1 className="font-kiwi text-lg leading-tight">{title}</h1>{subtitle && <p className="text-[11px] text-muted">{subtitle}</p>}</div>
  </header>;
  if (care) return <CareStage>{header}<div className="pointer-events-none fixed inset-x-0 bottom-0 mx-auto h-[58dvh] max-w-xl px-3">
    <section aria-label={title} className={`${glass.glass} ${motion.enter} pointer-events-auto relative z-20 h-full overflow-y-auto overscroll-contain rounded-t-3xl p-4 pb-20`}><div className="mb-3 mx-auto h-0.5 w-8 rounded-full bg-white/30" aria-hidden="true" /><div className="flex flex-col gap-3">{children}</div></section>
  </div></CareStage>;
  return <div className={`${motion.enter} mx-auto flex min-h-dvh max-w-2xl flex-col gap-3 px-4 pb-6 pt-[max(12px,env(safe-area-inset-top))]`}>{header}{children}</div>;
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
  inline = false,
}: {
  heading: string;
  great?: boolean;
  greatLabel?: string;
  lines: EffectLine[];
  children?: ReactNode;
  primary: { label: string; href?: string; onClick?: () => void };
  inline?: boolean;
}) {
  const embedded = Boolean(useCareStage()) || inline;
  useEffect(() => {
    if (!great) return;
    Sound.greatSuccess();
    buzz([30, 40, 30]);
  }, [great]);

  const toneClass = { leaf: "text-leaf", eye: "text-eye", banana: "text-banana", ai: "text-ai" } as const;

  return (
    <div className={embedded ? "grid place-items-center" : "fixed inset-0 z-50 grid place-items-center bg-black/60 p-6 backdrop-blur-sm"}>
      <div className="relative w-full max-w-sm overflow-hidden glass-panel rounded-xl p-6 text-center shadow-2xl pop-in">
        {great && (
          <div className="absolute inset-x-0 top-0 h-28 bg-[radial-gradient(circle_at_50%_0%,rgba(255,213,74,.45),transparent_70%)]" aria-hidden />
        )}
        {great && <div className="relative mb-1 font-kiwi text-3xl text-banana drop-shadow-sm pop-in">{greatLabel}</div>}
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
