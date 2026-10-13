"use client";
import { useState } from "react";
import { Button } from "../ui/primitives";
import { diaryImage } from "./share-card";
import type { DiaryEntry } from "./hooks";

export function ShareCard({ entry, name }: { entry: DiaryEntry; name: string }) {
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");
  async function exportCard(share: boolean) {
    if (busy) return;
    setBusy(true); setStatus("");
    try {
      const blob = await diaryImage(entry.text, name, entry.day);
      const file = new File([blob], `tsuyu-diary-${entry.day}.png`, { type: "image/png" });
      if (share && navigator.canShare?.({ files: [file] })) {
        await navigator.share({ files: [file], title: `${name}の観察日記` });
      } else {
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a"); link.href = url; link.download = file.name;
        document.body.append(link); link.click(); link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        setStatus("日記の画像を保存しました。");
      }
    } catch (error) {
      if (!(error instanceof DOMException && error.name === "AbortError")) setStatus("画像を保存できませんでした。もう一度お試しください。");
    } finally { setBusy(false); }
  }
  return <div className="space-y-2">
    <div className="flex flex-wrap gap-2"><Button disabled={busy} onClick={() => void exportCard(false)}>日記を画像で保存</Button><Button disabled={busy} onClick={() => void exportCard(true)}>共有</Button></div>
    {status && <p role="status" className="text-xs text-muted">{status}</p>}
  </div>;
}
