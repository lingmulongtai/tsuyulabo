"use client";
import Link from "next/link";
import { HomeScreen } from "@/components/home/HomeScreen";
import { AppShell } from "@/components/shell/AppShell";
import { BreedingStart } from "@/components/breeding/BreedingStart";
import { QueryState } from "@/components/ui/QueryState";
import { useHome } from "@/lib/api/hooks";

export default function Home() {
  if (process.env.NODE_ENV === "production" && !process.env.NEXT_PUBLIC_API_URL?.trim()) {
    return <AppShell hideTabs>
      <div className="px-4 py-8">
        <Card className="space-y-4 p-5 text-center">
          <FlyArt stage="egg" className="mx-auto h-40 w-40" />
          <h1 className="font-kiwi text-2xl">ツユラボへようこそ</h1>
          <p className="text-sm text-muted">ただいま公開デモでご案内しています。まずはミニゲームや、羽化のようすを気軽に体験してみてね。</p>
          <p className="text-sm text-muted">デモでは育成の記録や報酬は保存されません。</p>
          <nav aria-label="公開デモ" className="grid gap-3">
            {[
              ["/care/meal?practice=1", "ごはんづくりを練習する"],
              ["/care/training?practice=1", "しつけを練習する"],
              ["/eclosion?demo=1", "羽化のデモを見る"],
              ["/presentation?demo=1", "研究発表会のデモを見る"],
            ].map(([href, label]) => <Link key={href} href={href} className="rounded-2xl bg-tint-leaf p-3 font-bold text-leaf underline focus-visible:outline-2 focus-visible:outline-leaf">{label}</Link>)}
          </nav>
        </Card>
      </div>
    </AppShell>;
  }
  return <LiveHome />;
}

function LiveHome() {
  const home = useHome();
  return (
    <AppShell>
      <div className="py-3"><QueryState query={home}>{data => <HomeScreen data={data} hero={!data.week && <BreedingStart />} footer={<>
        <Link href="/shiori" className="rounded-2xl bg-tint-ai p-3 text-center font-bold text-ai">シオリに聞く</Link>
        <Link href="/care/meal?practice=1" className="text-center text-sm text-muted underline">ごはんづくりの練習</Link>
      </>} />}</QueryState></div>
    </AppShell>
  );
}
