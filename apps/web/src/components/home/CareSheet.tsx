"use client";
import { useId, useRef, useState, type ReactNode } from "react";
import glass from "../ui/material.module.css";
import motion from "../ui/motion.module.css";
import styles from "./care-sheet.module.css";

/** A non-modal sheet. The vial stays interactive and full contents mount only when expanded. */
export function CareSheet({ preview, children }: { preview: ReactNode; children: ReactNode }) {
  const [expanded, setExpanded] = useState(false);
  const [dragHeight, setDragHeight] = useState<number>();
  const id = useId(), drag = useRef<{ y: number; height: number } | null>(null), moved = useRef(false);
  return <section aria-label="今日のお世話" data-care-sheet data-expanded={expanded} style={dragHeight === undefined ? undefined : { height: dragHeight, transition: "none" }} className={`${styles.sheet} ${glass.glass} ${motion.spring} ${motion.enter}`}>
    <button type="button" className={styles.handle} aria-label={expanded ? "今日のお世話を閉じる" : "今日のお世話をすべて見る"} aria-expanded={expanded} aria-controls={id}
      onPointerDown={event => { drag.current = { y: event.clientY, height: event.currentTarget.parentElement!.getBoundingClientRect().height }; moved.current = false; event.currentTarget.setPointerCapture(event.pointerId); }}
      onPointerMove={event => {
        if (!drag.current) return;
        const minimum = innerHeight <= 500 ? 140 : Math.max(172, Math.min(220, innerHeight * .24));
        setDragHeight(Math.max(minimum, Math.min(680, innerHeight * .72, drag.current.height + drag.current.y - event.clientY)));
      }}
      onPointerUp={event => {
        if (drag.current !== null && Math.abs(event.clientY - drag.current.y) > 24) { moved.current = true; setExpanded(event.clientY < drag.current.y); }
        drag.current = null; setDragHeight(undefined);
      }}
      onPointerCancel={() => { drag.current = null; moved.current = false; setDragHeight(undefined); }}
      onKeyDown={event => { if (["ArrowUp", "ArrowDown", "Escape"].includes(event.key)) { event.preventDefault(); setExpanded(event.key === "ArrowUp"); } }}
      onClick={() => { if (!moved.current) setExpanded(value => !value); moved.current = false; }}>
      <span aria-hidden="true" className={styles.grip} /><span className="text-xs">今日のお世話</span><span className="sr-only">{expanded ? "を閉じる" : "をすべて見る"}</span>
      <span aria-hidden="true" className="ml-auto text-[#d5cab4]">{expanded ? "↓" : "↑"}</span>
    </button>
    <div id={id} className={styles.content}>{expanded ? children : preview}</div>
  </section>;
}
