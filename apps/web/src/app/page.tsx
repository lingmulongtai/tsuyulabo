"use client";
import Link from "next/link";
import { HomeScreen } from "@/components/home/HomeScreen";
import { AppShell } from "@/components/shell/AppShell";
import { BreedingStart } from "@/components/breeding/BreedingStart";
import { Card } from "@/components/ui/primitives";
import { QueryState } from "@/components/ui/QueryState";
import { useHome } from "@/lib/api/hooks";

const DEMO_ACTIVITIES = [
  {
    index: "01",
    href: "/care/meal?practice=1",
    category: "お世話の練習",
    label: "ごはんづくりを練習する",
    description: "素材を配合して栄養バランスと香りの変化を確かめます。",
    primary: true,
  },
  {
    index: "02",
    href: "/care/training?practice=1",
    category: "お世話の練習",
    label: "しつけを練習する",
    description: "刺激と応答のタイミングから、好き嫌いの育ち方を体験します。",
    primary: false,
  },
  {
    index: "03",
    href: "/eclosion?demo=1",
    category: "観察デモ",
    label: "羽化のデモを見る",
    description: "さなぎから羽化へ移り変わる一瞬の演出を確認できます。",
    primary: false,
  },
  {
    index: "04",
    href: "/presentation?demo=1",
    category: "観察デモ",
    label: "羽化の日のデモを見る",
    description: "羽化の日に届く記録と次の世代への引き継ぎを体験します。",
    primary: false,
  },
] as const;

export default function Home() {
  if (process.env.NODE_ENV === "production" && !process.env.NEXT_PUBLIC_API_URL?.trim()) {
    return (
      <AppShell hideTabs>
        <div className="mx-auto flex min-h-dvh w-full max-w-4xl flex-col justify-between px-5 py-8 sm:px-8 sm:py-12">
          <header className="flex items-center justify-between border-b border-line-soft pb-4">
            <div className="flex items-center gap-2.5">
              <span className="grid size-7 place-items-center rounded-md border border-line-soft bg-surface-2 text-banana" aria-hidden="true">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 3C8.5 8 6 11.2 6 14.5a6 6 0 0 0 12 0C18 11.2 15.5 8 12 3Z" />
                  <path d="M12 10v6" />
                </svg>
              </span>
              <span className="font-kiwi text-base font-medium text-ink">ツユラボ</span>
            </div>
            <span className="font-mono text-xs text-muted tabular">公開デモ / 記録非保存</span>
          </header>

          <div className="my-auto py-8 sm:py-12">
            <div className="max-w-2xl space-y-3">
              <p className="font-mono text-xs text-banana">標本観察ノート ・ 体験版</p>
              <h1 className="font-kiwi text-3xl font-medium tracking-tight text-ink sm:text-4xl">
                ツユラボへようこそ
              </h1>
              <p className="text-sm leading-relaxed text-muted sm:text-base">
                手のひらの小さな命を、本当に育てている。ごはんを配合し、好き嫌いを育て、世代をつなぐ飼育ゲームです。
              </p>
            </div>

            <nav aria-label="公開デモ" className="mt-8 grid gap-3 sm:grid-cols-2">
              {DEMO_ACTIVITIES.map(({ index, href, category, label, description, primary }) => (
                <Link
                  key={href}
                  href={href}
                  className={`group flex flex-col justify-between rounded-xl border p-5 transition-colors focus-visible:outline-2 focus-visible:outline-banana ${
                    primary
                      ? "border-banana/55 bg-surface-2 hover:border-banana"
                      : "border-line-soft bg-surface hover:border-line hover:bg-surface-2"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-xs text-muted tabular">
                      {index} ・ {category}
                    </span>
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden="true"
                      className={primary ? "text-banana" : "text-muted transition-colors group-hover:text-ink"}
                    >
                      <path d="M5 12h14" />
                      <path d="m13 6 6 6-6 6" />
                    </svg>
                  </div>
                  <div className="mt-5 space-y-1.5">
                    <p className={`text-base font-medium ${primary ? "text-banana" : "text-ink"}`}>
                      {label}
                    </p>
                    <p className="text-xs leading-relaxed text-muted">{description}</p>
                  </div>
                </Link>
              ))}
            </nav>

            <Card className="mt-6 flex flex-col gap-1.5 px-4 py-3.5 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-xs text-muted">
                ここは公開デモです。練習と羽化のようすを体験できます。育成の記録や報酬は保存されません。
              </p>
              <span className="shrink-0 font-mono text-xs text-leaf tabular">4つの体験メニュー</span>
            </Card>
          </div>

          <footer className="flex items-center justify-between border-t border-line-soft pt-4 text-xs text-muted">
            <span>ツユラボ 飼育観察ワークベンチ</span>
            <span className="font-mono tabular">Tsuyulabo</span>
          </footer>
        </div>
      </AppShell>
    );
  }
  return <LiveHome />;
}

function LiveHome() {
  const home = useHome();
  return (
    <AppShell>
      <div><QueryState query={home}>{data => <HomeScreen data={data} hero={!data.week && <BreedingStart />} footer={<>
        <Link href="/shiori" className="min-h-11 p-3 text-center text-sm text-muted underline">観察日記を読む</Link>
        <Link href="/care/meal?practice=1" className="text-center text-sm text-muted underline">ごはんづくりの練習</Link>
      </>} />}</QueryState></div>
    </AppShell>
  );
}
