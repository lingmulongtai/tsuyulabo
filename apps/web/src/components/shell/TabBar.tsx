"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookTabIcon, FriendsTabIcon, HomeTabIcon, TeamTabIcon } from "../ui/icons";

const TABS = [
  { href: "/", label: "お世話", Icon: HomeTabIcon },
  { href: "/team", label: "コロニー", Icon: TeamTabIcon },
  { href: "/zukan", label: "図鑑", Icon: BookTabIcon },
  { href: "/friends", label: "フレンド", Icon: FriendsTabIcon },
] as const;

export function TabBar() {
  const pathname = usePathname();
  return (
    <nav
      aria-label="メインメニュー"
      className="sticky bottom-0 z-30 grid grid-cols-4 border-t border-line-soft bg-surface-2 backdrop-blur-xl pb-[env(safe-area-inset-bottom)]"
    >
      {TABS.map(({ href, label, Icon }) => {
        const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            aria-current={active ? "page" : undefined}
            className={`flex flex-col items-center gap-0.5 pt-2 pb-2.5 text-[0.7rem] font-medium transition-colors min-h-14 ${
              active ? "text-banana" : "text-muted hover:text-ink"
            }`}
          >
            <Icon size={24} />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
