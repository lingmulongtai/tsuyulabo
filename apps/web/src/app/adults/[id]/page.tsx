import { AppShell } from "@/components/shell/AppShell";
import { CareFrame } from "@/components/games/CareFrame";
import { AdultDetail } from "@/components/collection/AdultDetail";

export default async function AdultPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <AppShell><CareFrame title="ツユの観察ノート"><AdultDetail id={id} /></CareFrame></AppShell>;
}
