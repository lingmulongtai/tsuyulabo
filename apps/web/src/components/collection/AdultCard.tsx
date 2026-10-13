import Link from "next/link";
import type { ReactNode } from "react";
import type { components } from "@/lib/api/schema";
import { STRAIN_LABELS } from "../art/palette";
import { Portrait } from "../vivarium/Portrait";
import { Card, Stars } from "../ui/primitives";

export function AdultCard({ adult, children, link = true }: { adult: components["schemas"]["Adult"]; children?: ReactNode; link?: boolean }) {
  const summary = <><div className="w-28 shrink-0"><Portrait stage="adult" seed={adult.id} sex={adult.sex} traits={adult.phenotypes} label={adult.name} /></div><div className="min-w-0">
    <h3 className="font-kiwi break-words text-base">{adult.name}</h3><p className="mt-1 text-[11px] text-muted">{STRAIN_LABELS[adult.strain].name} ・ {adult.sex === "f" ? "♀" : "♂"} ・ Lv.{adult.level}</p><Stars value={adult.stars} size={13} />
  </div></>;
  return <Card className="space-y-3 p-3">{link ? <Link href={`/adults/${adult.id}`} className="flex items-center gap-4">{summary}</Link> : <div className="flex items-center gap-4">{summary}</div>}{children}</Card>;
}
