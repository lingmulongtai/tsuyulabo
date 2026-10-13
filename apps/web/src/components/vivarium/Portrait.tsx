"use client";
import Image from "next/image";
import { useEffect, useId, useRef, useSyncExternalStore } from "react";
import { Vivarium, type VivariumProps } from "./Vivarium";
import { displayStage } from "./types";
import { PortraitQueue } from "./portrait-queue";

const queue = new PortraitQueue();

/** A real renderer snapshot, lazily produced one context at a time and reused in lists. */
export function Portrait({ label, known = true, ...props }: VivariumProps & { label: string; known?: boolean }) {
  const holder = useRef<HTMLDivElement>(null), owner = useId();
  const key = JSON.stringify([props.seed, props.stage ?? "adult", props.sex, props.traits, props.environment]);
  useSyncExternalStore(queue.subscribe, queue.snapshot, () => 0);
  useEffect(() => {
    if (!known || !holder.current) return;
    let release: (() => void) | undefined;
    const observer = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && !release) release = queue.request(key, owner);
      else if (!entries[0].isIntersecting && release) { release(); release = undefined; }
    }, { rootMargin: "80px" });
    observer.observe(holder.current);
    return () => { observer.disconnect(); release?.(); };
  }, [key, owner, known]);
  const source = queue.image(key);
  return <div ref={holder} className="relative aspect-square w-full overflow-hidden rounded-xl bg-[#211e19]" data-portrait data-portrait-ready={Boolean(source)}>
    {!known ? <span className="absolute inset-0 grid place-items-center text-2xl text-muted" aria-label="まだ出会っていません">?</span> : source ? <Image src={source} alt={source.startsWith("/vivarium/fallback-") ? `${label}（共通の静止画）` : label} fill sizes="160px" unoptimized style={{ objectFit: "cover" }} /> : queue.active?.owner === owner ? <Snapshot key={key} {...props} label={label} onDone={image => queue.finish(key, owner, image)} /> : <span className="absolute inset-0 grid place-items-center text-[10px] text-muted" role="status">姿を映しています</span>}
  </div>;
}

function Snapshot({ onDone, label, ...props }: VivariumProps & { label: string; onDone: (image: string) => void }) {
  const holder = useRef<HTMLDivElement>(null);
  const callback = useRef(onDone);
  useEffect(() => { callback.current = onDone; }, [onDone]);
  useEffect(() => {
    let frame = 0, settled = 0;
    const fallback = `/vivarium/fallback-${displayStage(props.stage ?? "adult")}.webp`;
    const timeout = setTimeout(() => callback.current(fallback), 20_000);
    const capture = () => {
      const canvas = holder.current?.querySelector("canvas[data-ready='true']");
      const unavailable = holder.current?.querySelector("[data-vivarium-fallback]:not([data-vivarium-loading])");
      if (canvas instanceof HTMLCanvasElement && ++settled > 3) {
        try { callback.current(canvas.toDataURL("image/webp", .85)); } catch { callback.current(fallback); }
        clearTimeout(timeout);
      } else if (unavailable && !unavailable.closest("canvas")) {
        // Fiber retains hidden fallback HTML inside supported canvases.
        clearTimeout(timeout); callback.current(fallback);
      } else frame = requestAnimationFrame(capture);
    };
    frame = requestAnimationFrame(capture);
    return () => { cancelAnimationFrame(frame); clearTimeout(timeout); };
  }, [props.stage]);
  return <div ref={holder} className="absolute inset-0" aria-label={label}>
    <Vivarium {...props} framing="close" paused quality="low" snapshot />
  </div>;
}
