"use client";
import type { ReactNode } from "react";
import { TabBar } from "./TabBar";
import { DevTimePanel } from "./DevTimePanel";

/** The scene owns the viewport; navigation floats above its lower edge. */
export function AppShell({ children, hideTabs = false }: { children: ReactNode; hideTabs?: boolean }) {
  return <div className="relative min-h-dvh">
    <main className={hideTabs ? "min-h-dvh" : "min-h-dvh pb-[calc(64px+env(safe-area-inset-bottom))]"}>{children}</main>
    {!hideTabs && <TabBar />}
    <DevTimePanel />
  </div>;
}
