"use client";
import { useEffect, useRef, useState } from "react";
import { useFriendLab } from "@/lib/api/hooks";
import { Portrait } from "../vivarium/Portrait";

/** The friend list only knows users; fetch visible shelves before showing an actual individual. */
export function FriendPortrait({ id, name }: { id: string; name: string }) {
  const holder = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  const lab = useFriendLab(visible ? id : "");
  useEffect(() => {
    if (!holder.current) return;
    const observer = new IntersectionObserver(entries => { if (entries[0].isIntersecting) { setVisible(true); observer.disconnect(); } }, { rootMargin: "80px" });
    observer.observe(holder.current);
    return () => observer.disconnect();
  }, []);
  const adult = lab.data?.team.members[0] ?? lab.data?.adults[0];
  return <div ref={holder} className="w-20 shrink-0">
    {adult ? <Portrait stage="adult" seed={adult.id} sex={adult.sex} traits={adult.phenotypes} label={`${name}さんの${adult.name}`} /> : lab.data?.week ? <Portrait stage={lab.data.week.stage} seed={`friend-week-${id}`} label={`${name}さんが育てている子`} /> : <div className="grid aspect-square place-items-center rounded-xl border border-line-soft text-[10px] text-muted">{lab.isError ? "飼育棚へ" : lab.data ? "おやすみ中" : "姿を確認中"}</div>}
  </div>;
}
