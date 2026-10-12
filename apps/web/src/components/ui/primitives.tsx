import type { ButtonHTMLAttributes, ReactNode } from "react";
import { AmberIcon, DropIcon, FlaskIcon } from "./icons";

function cx(...parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(" ");
}

/* ------------------------------------------------------------------ Button */

type Tone = "eye" | "leaf" | "banana" | "ai" | "plain";

const TONES: Record<Tone, string> = {
  // Neutral controls share one attention colour for warnings.
  eye: "bg-[#e7bd78] text-[#29251e] border border-banana",
  leaf: "bg-surface-2 text-ink border border-line",
  banana: "bg-[#e7bd78] text-[#29251e] border border-banana",
  ai: "bg-surface-2 text-ink border border-line",
  plain: "bg-surface-2 text-ink border border-line-soft",
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  tone?: Tone;
  size?: "sm" | "md" | "lg";
  block?: boolean;
}

export function Button({ tone = "eye", size = "md", block, className, children, ...rest }: ButtonProps) {
  const sizes = { sm: "min-h-11 px-3 text-sm rounded-lg", md: "min-h-12 px-5 text-sm rounded-xl", lg: "min-h-14 px-6 text-base rounded-xl" };
  return (
    <button
      type="button"
      className={cx(
        "press inline-flex items-center justify-center gap-2 font-medium tracking-wide select-none backdrop-blur",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        TONES[tone],
        sizes[size],
        block && "w-full",
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  );
}

/* ------------------------------------------------------------------ Card */

export function Card({ className, children }: { className?: string; children: ReactNode }) {
  return <div className={cx("glass-panel rounded-xl shadow-[var(--shadow)]", className)}>{children}</div>;
}

/* ------------------------------------------------------------------ Meter */

export function Meter({ label, value, color, hint }: { label: string; value: number; color: string; hint?: string }) {
  const v = Math.max(0, Math.min(100, Math.round(value)));
  const low = v < 30;
  return (
    <div className="min-w-0">
      <div className="flex items-baseline justify-between text-xs font-bold text-muted">
        <span>{label}</span>
        <span className={cx("tabular font-mono", low ? "text-eye" : "text-ink")}>{hint ?? `${v}%`}</span>
      </div>
      <div className="mt-1 h-1 rounded-full bg-line-soft overflow-hidden" role="meter" aria-label={label} aria-valuenow={v} aria-valuemin={0} aria-valuemax={100}>
        <div className="h-full rounded-full transition-[width] duration-700 ease-out" style={{ width: `${v}%`, background: color }} />
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ Badge (real / model / game / AI) */

export type TruthKind = "real" | "model" | "game" | "ai";

const TRUTH: Record<TruthKind, { label: string; className: string }> = {
  real: { label: "本物", className: "bg-tint-leaf text-leaf" },
  model: { label: "育ちのしくみ", className: "bg-tint-banana text-banana" },
  game: { label: "ゲーム", className: "bg-tint-eye text-eye" },
  ai: { label: "AI", className: "bg-tint-ai text-ai" },
};

export function TruthBadge({ kind }: { kind: TruthKind }) {
  const t = TRUTH[kind];
  return <span className={cx("inline-flex items-center rounded-full px-2 py-px text-[0.68rem] font-bold leading-5", t.className)}>{t.label}</span>;
}

/* ------------------------------------------------------------------ Currency */

export function CurrencyPill({ kind, value }: { kind: "shizuku" | "research" | "kohaku"; value: number }) {
  const icon = kind === "shizuku" ? <DropIcon size={18} /> : kind === "kohaku" ? <AmberIcon size={18} /> : <FlaskIcon size={18} className="text-leaf" />;
  const label = kind === "shizuku" ? "しずく" : kind === "kohaku" ? "こはく" : "飼育の経験";
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-surface-2/85 border border-line-soft pl-1.5 pr-2.5 h-8 text-sm font-bold backdrop-blur" title={label}>
      {icon}
      <span className="tabular font-mono">{value.toLocaleString("ja-JP")}</span>
      <span className="sr-only">{label}</span>
    </span>
  );
}

/* ------------------------------------------------------------------ Stars */

export function Stars({ value, max = 5, size = 18, color = "var(--banana)" }: { value: number; max?: number; size?: number; color?: string }) {
  return (
    <span className="inline-flex gap-0.5" aria-label={`★${value}`}>
      {Array.from({ length: max }, (_, i) => (
        <svg key={i} width={size} height={size} viewBox="0 0 24 24" aria-hidden>
          <path
            d="m12 2.8 2.8 5.8 6.3.9-4.6 4.4 1.1 6.3L12 17.2l-5.6 3 1.1-6.3-4.6-4.4 6.3-.9Z"
            fill={i < value ? color : "var(--line-soft)"}
            stroke={i < value ? "var(--banana)" : "var(--line)"}
            strokeWidth={1.2}
            strokeLinejoin="round"
          />
        </svg>
      ))}
    </span>
  );
}

/* ------------------------------------------------------------------ Section title */

export function SectionTitle({ children, aside }: { children: ReactNode; aside?: ReactNode }) {
  return (
    <div className="flex items-center justify-between px-1 mb-2">
      <h2 className="font-kiwi text-[1.05rem] font-medium">{children}</h2>
      {aside}
    </div>
  );
}

export { cx };
