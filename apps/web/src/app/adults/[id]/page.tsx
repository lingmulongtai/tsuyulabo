import Link from "next/link";
import { AppShell } from "@/components/shell/AppShell";
import { CareFrame } from "@/components/games/CareFrame";
import { AdultDetail } from "@/components/collection/AdultDetail";

export default async function AdultPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <AppShell>
      <CareFrame title="ツユの観察ノート">
        <AdultDetail id={id} />
        <Link
          href={`/adults/${encodeURIComponent(id)}/brain`}
          className="press block rounded-3xl border-2 border-[#5f4fcf] bg-tint-ai px-4 py-3 text-center font-bold text-ai"
        >
          この子の脳をのぞく →
        </Link>
      </CareFrame>
    </AppShell>
  );
}
