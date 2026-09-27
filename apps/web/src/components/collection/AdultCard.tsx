import Link from "next/link";
import type { ReactNode } from "react";
import type { components } from "@/lib/api/schema";
import { STRAIN_LABELS } from "../art/palette";
import { Tsuyu } from "../art/Tsuyu";
import { Card, Stars } from "../ui/primitives";

export function AdultCard({ adult, children, link = true }: { adult: components["schemas"]["Adult"]; children?: ReactNode; link?: boolean }) {
  const summary = <><Tsuyu strain={adult.strain} sex={adult.sex} className="size-24 shrink-0" label={adult.name} /><div>
    <h3 className="font-bold">{adult.name}</h3><p className="text-xs text-muted">{STRAIN_LABELS[adult.strain].name} ・ {adult.sex === "f" ? "♀" : "♂"} ・ Lv.{adult.level}</p><Stars value={adult.stars} size={16} />
  </div></>;
  return <Card className="p-3">{link ? <Link href={`/adults/${adult.id}`} className="flex items-center gap-3">{summary}</Link> : <div className="flex items-center gap-3">{summary}</div>}{children}</Card>;
}
