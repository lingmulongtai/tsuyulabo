"use client";

import { useEffect, useRef, useState } from "react";
import { buzz } from "@/game/audio/haptics";
import * as Sound from "@/game/audio/sound";
import type { TierIndex } from "@/game/expectation";
import { Tsuyu } from "../art/Tsuyu";
import { Pupa } from "../art/Stages";
import { STRAIN_LABELS, type Sex, type Strain } from "../art/palette";
import { Burst, GOLD, RAINBOW } from "../effects/Burst";
import { Button, Stars } from "../ui/primitives";
import { TIER_COLORS, TIER_NAMES, traitName } from "./traits";

export interface EclosionResult {
  tier: TierIndex;
  /** Colours shown in order; may include a fake-out step above the final tier (spec §7). */
  omen_sequence: number[];
  adult: { name: string; strain: Strain; sex: Sex; stars: number; traits: string[] };
}

type Phase = "idle" | "omen" | "reveal";

function glowStyle(tier: number): React.CSSProperties {
  const c = TIER_COLORS[tier];
  if (c === "rainbow") {
    return { background: "conic-gradient(#ff6b8b,#ffc857,#7ee0a1,#5ec8f2,#a78bfa,#ff6b8b)", filter: "blur(22px)" };
  }
  return { background: `radial-gradient(circle, ${c} 0%, ${c}88 40%, transparent 70%)`, filter: "blur(10px)" };
}

/**
 * 羽化の演出. The pupa shakes while the omen light climbs white → blue → gold → rainbow; rainbow means a mutation
 * is guaranteed. The result itself was decided by the server before the show starts.
 */
export function EclosionStage({ result, onStart, onDone, doneLabel = "飼育室へ" }: { result: EclosionResult | null; onStart?: () => void; onDone: () => void; doneLabel?: string }) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [glow, setGlow] = useState<number | null>(null);
  const [cut, setCut] = useState(false);
  const [flash, setFlash] = useState(false);
  const [starsShown, setStarsShown] = useState(0);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  useEffect(() => () => timers.current.forEach(clearTimeout), []);

  const later = (ms: number, fn: () => void) => {
    timers.current.push(setTimeout(fn, ms));
  };

  // Start the show as soon as the server result arrives.
  useEffect(() => {
    if (!result || phase !== "omen") return;
    const seq = result.omen_sequence.length ? result.omen_sequence : [0];
    const step = 560;
    const at = 700;
    for (let z = 0; z < 4; z++) Sound.tone(98 + z * 6, z * 0.15, 0.14, "sawtooth", 0.03);
    seq.forEach((t, i) => {
      later(at + i * step, () => {
        setGlow(t);
        Sound.omen(t as TierIndex);
        if (t >= 2) buzz(30);
        if (t === 3) {
          setCut(true);
          Sound.mutation();
        }
      });
    });
    const end = at + seq.length * step + (result.tier === 3 ? 900 : 350);
    later(end, () => {
      setCut(false);
      setFlash(true);
      setPhase("reveal");
      Sound.chord(result.tier === 3 ? [523, 659, 784, 1047, 1319] : [523, 659, 784], 0, result.tier === 3 ? 1.2 : 0.6, "triangle", 0.07);
      later(500, () => setFlash(false));
      for (let q = 0; q < result.adult.stars; q++) {
        later(380 + q * 220, () => {
          setStarsShown(q + 1);
          Sound.tone(880 + q * 180, 0, 0.18, "triangle", 0.1);
        });
      }
    });
    // timers are cleared on unmount
  }, [result, phase]);

  const start = () => {
    Sound.init();
    setPhase("omen");
    onStart?.();
  };

  const skip = () => {
    if (!result) return;
    timers.current.forEach(clearTimeout);
    timers.current = [];
    setCut(false);
    setGlow(result.tier);
    setPhase("reveal");
    setStarsShown(result.adult.stars);
  };

  const tier = result?.tier ?? 0;
  const rainbow = tier === 3;

  return (
    <div className="relative aspect-[1/1.18] w-full overflow-hidden rounded-[32px] bg-[radial-gradient(circle_at_50%_55%,#2e5750,#10201d_72%)] text-white shadow-[var(--shadow)]">
      {/* glow under the pupa */}
      {glow !== null && phase !== "reveal" && (
        <div className={`absolute left-1/2 top-[52%] size-[62%] -translate-x-1/2 -translate-y-1/2 rounded-full glow-pulse ${glow === 3 ? "spin-slow" : ""}`} style={glowStyle(glow)} />
      )}

      {phase !== "reveal" && (
        <div className={`absolute left-1/2 top-[50%] w-[46%] -translate-x-1/2 -translate-y-1/2 ${phase === "omen" ? ((glow ?? 0) >= 2 ? "shake-hard" : "art-wiggle") : ""}`}>
          <Pupa eyeShow={1} className="block h-auto w-full" />
        </div>
      )}

      {phase === "idle" && (
        <div className="absolute inset-x-6 bottom-6 flex flex-col items-center gap-2 text-center">
          <p className="text-sm text-white/80">殻ごしに、赤い目が透けて見える……</p>
          <Button tone="banana" size="lg" onClick={start}>
            羽化させる
          </Button>
        </div>
      )}

      {phase === "omen" && (
        <button type="button" onClick={skip} disabled={!result} className="absolute right-3 top-3 rounded-full bg-white/15 px-3 py-1 text-xs font-bold backdrop-blur disabled:opacity-40">
          スキップ
        </button>
      )}

      {/* Shiori cut-in for the rainbow omen */}
      {cut && (
        <div className="absolute inset-x-0 top-[12%] slide-cut">
          <div className="mx-4 flex items-center gap-3 rounded-2xl bg-[#5f4fcf] px-4 py-3 shadow-2xl">
            <span className="grid size-10 place-items-center rounded-full bg-white font-kiwi text-lg text-[#5f4fcf]">シ</span>
            <span className="font-kiwi text-xl">これは……！？</span>
          </div>
        </div>
      )}

      {flash && <div className="pointer-events-none absolute inset-0 bg-white motion-safe:animate-[ping_0.5s_ease-out_1]" />}

      {phase === "reveal" && result && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-1 px-5 text-center">
          {tier >= 2 && <Burst key="b" count={rainbow ? 46 : 24} colors={rainbow ? RAINBOW : GOLD} spread={rainbow ? 190 : 140} />}
          <div
            className={`font-kiwi text-3xl pop-in ${rainbow ? "rainbow-text" : ""}`}
            style={rainbow ? undefined : { color: TIER_COLORS[tier] as string }}
          >
            {TIER_NAMES[tier]}
          </div>
          <div className="w-[62%] pop-in">
            <Tsuyu strain={result.adult.strain} sex={result.adult.sex} animated label={result.adult.name} className="block h-auto w-full" />
          </div>
          <Stars value={starsShown} size={26} />
          <div className="mt-1 text-sm">
            <span className="font-bold">{result.adult.name}</span>　{result.adult.sex === "m" ? "オス" : "メス"}　{STRAIN_LABELS[result.adult.strain].name}
          </div>
          <div className="mt-1 flex flex-wrap justify-center gap-1.5">
            {result.adult.traits.map((t) => (
              <span key={t} className="rounded-full bg-white/15 px-2.5 py-0.5 text-xs">
                {traitName(t)}
              </span>
            ))}
          </div>
          <Button className="mt-3" tone="eye" onClick={onDone}>
            {doneLabel}
          </Button>
        </div>
      )}
    </div>
  );
}
