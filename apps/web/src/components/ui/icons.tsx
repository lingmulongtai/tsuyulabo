import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement> & { size?: number };

function base({ size = 20, ...rest }: IconProps): SVGProps<SVGSVGElement> {
  return { width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.5, "aria-hidden": true, ...rest };
}

/** しずく — the free currency. */
export function DropIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M12 2.5C9 7 6 10.2 6 14a6 6 0 0 0 12 0c0-3.8-3-7-6-11.5Z" fill="none" stroke="currentColor" strokeWidth={1.4} />
      <path d="M9.2 13.2c0 1.6.9 2.9 2.3 3.4" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" />
    </svg>
  );
}

/** こはく — the paid currency (amber). */
export function AmberIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M12 2.8 19.5 8v8L12 21.2 4.5 16V8Z" fill="none" stroke="currentColor" strokeWidth={1.4} />
      <path d="M8 9.2 12 6.6" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" />
    </svg>
  );
}

/** 飼育の経験 — a growing stem. */
export function FlaskIcon(props: IconProps) {
  return <svg {...base(props)}><path d="M12 21V8M12 14C6 14 4 10 4 6c6 0 8 3 8 8Zm0-4c0-5 3-7 8-7 0 5-3 7-8 7Z" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" /></svg>;
}

export function MealIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <rect x="3" y="11" width="6" height="6" rx="1.4" fill="none" />
      <rect x="9" y="11" width="6" height="6" rx="1.4" fill="none" />
      <rect x="9" y="5" width="6" height="6" rx="1.4" fill="none" />
      <rect x="15" y="11" width="6" height="6" rx="1.4" fill="none" />
      <path d="M3 19.5h18" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" />
    </svg>
  );
}

export function CircuitIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M5 5h6v7h8v7" stroke="currentColor" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" />
      <defs>
        <linearGradient id="ci" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#FFD66B" />
          <stop offset=".5" stopColor="#7EE0C8" />
          <stop offset="1" stopColor="#FF6B8B" />
        </linearGradient>
      </defs>
      <circle cx="5" cy="5" r="2.6" fill="none" stroke="currentColor" strokeWidth={1.2} />
      <circle cx="19" cy="19" r="2.6" fill="none" stroke="currentColor" strokeWidth={1.2} />
    </svg>
  );
}

export function BottleIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M8 3h8v2.4H8zM8.6 5.4h6.8v12a3.4 3.4 0 0 1-6.8 0Z" stroke="currentColor" strokeWidth={1.6} strokeLinejoin="round" />
      <path d="M8.6 14.5h6.8v2.9a3.4 3.4 0 0 1-6.8 0Z" fill="none" />
      <path d="M18.5 7.5 20.5 6M19 10.5h2" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" />
    </svg>
  );
}

export function MoonIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M19.5 14.6A7.8 7.8 0 0 1 9.4 4.5a7.8 7.8 0 1 0 10.1 10.1Z" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinejoin="round" />
      <circle cx="17" cy="5" r="1" fill="none" />
      <circle cx="20" cy="8.5" r=".7" fill="none" />
    </svg>
  );
}

export function SunIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <circle cx="12" cy="12" r="4.2" fill="none" stroke="currentColor" strokeWidth={1.4} />
      <g stroke="currentColor" strokeWidth={1.8} strokeLinecap="round">
        <path d="M12 2.8v2M12 19.2v2M2.8 12h2M19.2 12h2M5.5 5.5l1.4 1.4M17.1 17.1l1.4 1.4M5.5 18.5l1.4-1.4M17.1 6.9l1.4-1.4" />
      </g>
    </svg>
  );
}

export function ThermoIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M10 4.5a2 2 0 0 1 4 0v9.3a4 4 0 1 1-4 0Z" stroke="currentColor" strokeWidth={1.6} />
      <circle cx="12" cy="17" r="2.2" fill="none" />
      <path d="M12 9v6" stroke="currentColor" strokeWidth={2} strokeLinecap="round" />
    </svg>
  );
}

export function LeafSpotIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M4 20c0-8 5-14 16-16-1 11-7 16-16 16Z" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinejoin="round" />
      <path d="M4 20 14 10" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round" />
    </svg>
  );
}

export function HomeTabIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M9 3h6M10 3v4.5a6.5 6.5 0 1 0 4 0V3" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" />
      <path d="M7 15.5a5 5 0 0 0 10 0" fill="none" stroke="currentColor" />
    </svg>
  );
}

export function TeamTabIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <circle cx="8" cy="9" r="3" stroke="currentColor" strokeWidth={1.8} />
      <circle cx="16" cy="9" r="3" stroke="currentColor" strokeWidth={1.8} />
      <path d="M2.8 19c.6-3 2.6-4.6 5.2-4.6s4.6 1.6 5.2 4.6M10.8 19c.6-3 2.6-4.6 5.2-4.6s4.6 1.6 5.2 4.6" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" />
    </svg>
  );
}

export function BookTabIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5Z" stroke="currentColor" strokeWidth={1.8} strokeLinejoin="round" />
      <path d="M4 20.5A2.5 2.5 0 0 1 6.5 18H20v3H6.5A2.5 2.5 0 0 1 4 20.5Z" stroke="currentColor" strokeWidth={1.8} strokeLinejoin="round" />
      <circle cx="12" cy="10" r="2.6" fill="none" stroke="currentColor" />
    </svg>
  );
}

export function FriendsTabIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M12 20.5s-7.5-4.3-7.5-10A4.2 4.2 0 0 1 12 8a4.2 4.2 0 0 1 7.5 2.5c0 5.7-7.5 10-7.5 10Z" stroke="currentColor" strokeWidth={1.8} strokeLinejoin="round" />
    </svg>
  );
}

export function ChevronRight(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="m9 5 7 7-7 7" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function CheckIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="m5 12.5 4.2 4.2L19 7" stroke="currentColor" strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function LockIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <rect x="5" y="10.5" width="14" height="10" rx="2.5" stroke="currentColor" strokeWidth={1.8} />
      <path d="M8.5 10.5V8a3.5 3.5 0 0 1 7 0v2.5" stroke="currentColor" strokeWidth={1.8} />
    </svg>
  );
}
