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
  meal: { label: "ごはん", icon: <MealIcon size={24} />, href: "/care/meal", accent: "var(--line)" },
  training: { label: "しつけ", icon: <CircuitIcon size={24} />, href: "/care/training", accent: "var(--line)" },
  cleaning: { label: "そうじ", icon: <BottleIcon size={24} />, href: "/care/cleaning", accent: "var(--line)" },
  temperature: { label: "温度", icon: <ThermoIcon size={24} />, href: "/care/temperature", accent: "var(--line)" },
  pupation_site: { label: "場所えらび", icon: <LeafSpotIcon size={24} />, href: "/care/pupation", accent: "var(--line)" },
  sleep: { label: "おやすみ", icon: <MoonIcon size={24} />, href: "/care/sleep", accent: "var(--line)" },
  wake: { label: "おはよう", icon: <SunIcon size={24} />, href: "/care/sleep", accent: "var(--line)" },
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
  return "世話できます";
}

/**
 * The big buttons. One tile per action kind; when several todo items share a kind (e.g. three meals)
 * the most actionable one wins.
 */
export function ActionGrid({ todo, compact = false }: { todo: TodoItem[]; compact?: boolean }) {
  const rank = { available: 0, locked: 1, done: 2 } as const;
  const byKind = new Map<ActionKind, TodoItem>();
  for (const item of todo) {
    const kind = item.action === "wake" ? "sleep" : item.action;
    const prev = byKind.get(kind);
    if (!prev || rank[item.status] < rank[prev.status]) byKind.set(kind, item);
  }
  const tiles = [...byKind.values()];

  return (
    <div className="grid grid-cols-3 gap-2">
      {tiles.map((item) => {
        const m = META[item.action];
        const available = item.status === "available";
        return (
          <Link
            key={item.action}
            href={available ? m.href : "#"}
            aria-disabled={!available}
            tabIndex={available ? undefined : -1}
            className={`press relative flex ${compact ? "min-h-11 py-2" : "aspect-[1/1.12]"} flex-col items-center justify-center gap-1 glass-panel rounded-xl border text-sm font-medium ${
              available ? "border-line" : "border-line-soft opacity-70 pointer-events-none"
            }`}
            style={available ? { borderColor: m.accent } : undefined}
          >
            {!compact && m.icon}
            <span>{m.label}</span>
            <span className={`text-[0.65rem] ${available ? "text-ink" : "text-muted"}`}>{statusText(item)}</span>
          </Link>
        );
      })}
    </div>
  );
}

export { META as ACTION_META, statusText };
