import Link from "next/link";
import { AppShell } from "@/components/shell/AppShell";
import { NotificationSettings } from "@/components/settings/NotificationSettings";

export default function SettingsPage() {
  return <AppShell><div className="space-y-5 px-4 py-6">
    <header className="flex items-center justify-between">
      <h1 className="font-kiwi text-2xl">設定</h1>
      <Link href="/" className="rounded-xl p-2 text-sm font-bold text-leaf underline">ホームへ</Link>
    </header>
    <NotificationSettings />
  </div></AppShell>;
}
