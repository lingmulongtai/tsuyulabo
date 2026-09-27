import { AppShell } from "@/components/shell/AppShell";
import { CareFrame } from "@/components/games/CareFrame";
import { FriendLab } from "@/components/friends/FriendLab";

export default async function FriendPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <AppShell><CareFrame title="フレンドの研究室"><FriendLab id={id} /></CareFrame></AppShell>;
}
