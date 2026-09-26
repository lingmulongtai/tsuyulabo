import Link from "next/link";
import type { ReactNode } from "react";
import type { ActionKind, TodoItem } from "@/lib/types";
import { BottleIcon, CircuitIcon, LeafSpotIcon, MealIcon, MoonIcon, SunIcon, ThermoIcon } from "../ui/icons";

interface ActionMeta {
  label: string;
  icon: ReactNode;
  href: string;
  accent: string;
}

const META: Record<ActionKind, ActionMeta> = {
  meal: { label: "ごはん", icon: <MealIcon size={34} />, href: "/care/meal", accent: "var(--banana)" },
  training: { label: "しつけ", icon: <CircuitIcon size={34} />, href: "/care/training", accent: "var(--ai)" },
  cleaning: { label: "そうじ", icon: <BottleIcon size={34} />, href: "/care/cleaning", accent: "var(--leaf)" },
  temperature: { label: "温度", icon: <ThermoIcon size={34} />, href: "/care/temperature", accent: "var(--eye)" },
  pupation_site: { label: "場所えらび", icon: <LeafSpotIcon size={34} />, href: "/care/pupation", accent: "var(--leaf)" },
  sleep: { label: "おやすみ", icon: <MoonIcon size={34} />, href: "/care/sleep", accent: "#8a7cf0" },
  wake: { label: "おはよう", icon: <SunIcon size={34} />, href: "/care/sleep", accent: "#e3ae35" },
};

function timeOf(iso?: string | null) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleTimeString("ja-JP", { hour: "2-digit", minute: "2-digit", timeZone: "Asia/Tokyo" });
}

function statusText(item: TodoItem) {
  if (item.status === "done") return "済";
  if (item.status === "locked") return item.available_at ? `${timeOf(item.available_at)}から` : "まだ";
  if (item.remaining !== undefined) return `あと${item.remaining}回`;
  return "できる！";
}

/**
 * The big buttons. One tile per action kind; when several todo items share a kind (e.g. three meals)
 * the most actionable one wins.
 */
export function ActionGrid({ todo }: { todo: TodoItem[] }) {
  const rank = { available: 0, locked: 1, done: 2 } as const;
  const byKind = new Map<ActionKind, TodoItem>();
  for (const item of todo) {
    const kind = item.action === "wake" ? "sleep" : item.action;
    const prev = byKind.get(kind);
    if (!prev || rank[item.status] < rank[prev.status]) byKind.set(kind, item);
  }
  const tiles = [...byKind.values()].slice(0, 4);

  return (
    <div className="grid grid-cols-4 gap-2">
      {tiles.map((item) => {
        const m = META[item.action];
        const available = item.status === "available";
        return (
          <Link
            key={item.action}
            href={available ? m.href : "#"}
            aria-disabled={!available}
            className={`press relative flex aspect-[1/1.12] flex-col items-center justify-center gap-1 rounded-3xl border-2 bg-surface-2 text-sm font-bold ${
              available ? "border-transparent shadow-[0_4px_0_0_var(--line)]" : "border-line-soft opacity-70 pointer-events-none"
            }`}
            style={available ? { boxShadow: `0 4px 0 0 ${m.accent}`, borderColor: m.accent } : undefined}
          >
            {available && <span className="absolute -top-1.5 right-1.5 size-3 rounded-full bg-eye ring-2 ring-bg motion-safe:animate-bounce" aria-hidden />}
            {m.icon}
            <span>{m.label}</span>
            <span className={`text-[0.65rem] ${available ? "text-eye" : "text-muted"}`}>{statusText(item)}</span>
          </Link>
        );
      })}
    </div>
  );
}

export { META as ACTION_META, statusText };
