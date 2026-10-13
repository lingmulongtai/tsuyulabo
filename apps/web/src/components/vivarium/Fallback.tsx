import Image from "next/image";
import { displayStage, type Stage } from "./types";

export function Fallback({ stage = "adult", message = "静止画で表示しています", loading = false }: { stage?: Stage; message?: string; loading?: boolean }) {
  return <div style={{ position: "absolute", inset: 0, background: "#33392e" }} data-vivarium-fallback data-vivarium-loading={loading || undefined}>
    <Image src={`/vivarium/fallback-${displayStage(stage)}.webp`} alt="飼育びんの中のショウジョウバエ" fill sizes="100vw" style={{ objectFit: "cover" }} unoptimized priority />
    <span role="status" style={{ position: "absolute", bottom: 20, left: 20, color: "#eee7d5", fontSize: 12 }}>{message}</span>
  </div>;
}
