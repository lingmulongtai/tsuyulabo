import type { Slot, TodoItem } from "@/lib/types";
import { CheckIcon, LockIcon } from "../ui/icons";
import { Card } from "../ui/primitives";
import { ACTION_META, statusText } from "./ActionGrid";

const SLOT_LABEL: Record<Slot, string> = { morning: "朝", noon: "昼", night: "夜" };

/** 「きょうのやること」 — everything that can be done today, in order. */
export function TodoList({ todo }: { todo: TodoItem[] }) {
  return (
    <Card className="px-4 py-3">
      <h2 className="mb-1.5 font-kiwi text-[0.95rem]">きょうのやること</h2>
      <ul className="divide-y divide-line-soft">
        {todo.map((item, i) => {
          const m = ACTION_META[item.action];
          const label = item.slot ? `${SLOT_LABEL[item.slot]}${m.label}` : m.label;
          return (
            <li key={`${item.action}-${item.slot ?? i}`} className="flex items-center justify-between gap-3 py-1.5 text-sm">
              <span className="flex items-center gap-2">
                <span
                  className={`grid size-5 place-items-center rounded-full ${
                    item.status === "done" ? "bg-leaf text-white" : item.status === "available" ? "bg-eye text-white" : "bg-line-soft text-muted"
                  }`}
                >
                  {item.status === "done" ? <CheckIcon size={13} /> : item.status === "locked" ? <LockIcon size={11} /> : <span className="size-1.5 rounded-full bg-white" />}
                </span>
                {label}
              </span>
              <span className={`text-xs font-bold ${item.status === "available" ? "text-eye" : item.status === "done" ? "text-leaf" : "text-muted"}`}>
                {statusText(item)}
              </span>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
