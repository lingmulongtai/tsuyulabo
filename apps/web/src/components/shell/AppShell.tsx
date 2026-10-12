import type { ReactNode } from "react";
import { TabBar } from "./TabBar";
import { DevTimePanel } from "./DevTimePanel";

/**
 * Phone-width column used by every in-game screen. On desktop it is centred with a soft backdrop so the
 * game still reads as a mobile app.
 */
export function AppShell({ children, hideTabs = false }: { children: ReactNode; hideTabs?: boolean }) {
  return (
    <div className="min-h-dvh bg-transparent">
      <div className="relative mx-auto flex min-h-dvh w-full max-w-[440px] flex-col bg-surface backdrop-blur-sm sm:border-x sm:border-line-soft">
        <main className="flex-1 pb-4">{children}</main>
        {!hideTabs && <TabBar />}
        <DevTimePanel />
      </div>
    </div>
  );
}
