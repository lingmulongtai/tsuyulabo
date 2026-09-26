import type { ReactNode } from "react";
import { TabBar } from "./TabBar";

/**
 * Phone-width column used by every in-game screen. On desktop it is centred with a soft backdrop so the
 * game still reads as a mobile app.
 */
export function AppShell({ children, hideTabs = false }: { children: ReactNode; hideTabs?: boolean }) {
  return (
    <div className="min-h-dvh bg-[radial-gradient(circle_at_50%_0%,var(--surface)_0%,var(--bg)_60%)]">
      <div className="relative mx-auto flex min-h-dvh w-full max-w-[440px] flex-col bg-bg sm:border-x sm:border-line-soft sm:shadow-[0_0_80px_-40px_rgba(15,40,35,0.45)]">
        <main className="flex-1 pb-4">{children}</main>
        {!hideTabs && <TabBar />}
      </div>
    </div>
  );
}
