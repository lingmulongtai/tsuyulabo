import { useId } from "react";

function uid(raw: string) {
  return raw.replace(/[^a-zA-Z0-9]/g, "");
}

interface ArtProps {
  className?: string;
  label?: string;
}

/** Egg on food, with the two respiratory filaments on top (true to the real egg). */
export function Egg({ className, label = "卵" }: ArtProps) {
  const p = `eg${uid(useId())}`;
  return (
    <svg viewBox="0 0 240 240" role="img" aria-label={label} className={className}>
      <defs>
        <radialGradient id={`${p}g`} cx=".35" cy=".3" r=".8">
          <stop offset="0" stopColor="#FFFFFF" />
          <stop offset=".6" stopColor="#F5EFE3" />
          <stop offset="1" stopColor="#D8CCB6" />
        </radialGradient>
        <radialGradient id={`${p}f`} cx=".5" cy=".3" r=".8">
          <stop offset="0" stopColor="#FBE08A" />
          <stop offset="1" stopColor="#D9A93A" />
        </radialGradient>
        <linearGradient id={`${p}i`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#FFD2EC" />
          <stop offset=".5" stopColor="#CDEFF5" />
          <stop offset="1" stopColor="#FFEBB8" />
        </linearGradient>
        <filter id={`${p}b`} x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="3" />
        </filter>
      </defs>
      <ellipse cx="120" cy="206" rx="80" ry="18" fill={`url(#${p}f)`} stroke="#C9962A" strokeWidth={2} />
      <g fill="#E9BF55">
        <circle cx="78" cy="204" r="3" />
        <circle cx="150" cy="211" r="2.5" />
        <circle cx="172" cy="201" r="2.2" />
        <circle cx="100" cy="212" r="2" />
      </g>
      <ellipse cx="122" cy="194" rx="34" ry="7" fill="#7A5A1A" opacity=".3" filter={`url(#${p}b)`} />
      <g className="art-breathe">
        <path d="M110 84 Q102 58 88 44" stroke="#CFC3AC" strokeWidth={7} strokeLinecap="round" fill="none" />
        <path d="M110 84 Q102 58 88 44" stroke="#FFFFFF" strokeWidth={3} strokeLinecap="round" fill="none" />
        <path d="M126 82 Q130 56 144 42" stroke="#CFC3AC" strokeWidth={7} strokeLinecap="round" fill="none" />
        <path d="M126 82 Q130 56 144 42" stroke="#FFFFFF" strokeWidth={3} strokeLinecap="round" fill="none" />
        <ellipse cx="120" cy="138" rx="36" ry="58" transform="rotate(-8 120 138)" fill={`url(#${p}g)`} stroke="#B9AC94" strokeWidth={2.5} />
        <ellipse cx="104" cy="118" rx="9" ry="22" transform="rotate(-8 104 118)" fill="#fff" opacity=".9" />
        <path d="M142 112 Q152 142 140 172" stroke={`url(#${p}i)`} strokeWidth={5} opacity=".7" fill="none" strokeLinecap="round" />
      </g>
    </svg>
  );
}

export interface LarvaProps extends ArtProps {
  /** 1–3 instar; the third instar is bigger and see-through (gut visible). */
  instar?: 1 | 2 | 3;
  /** Wandering larvae stretch out and lift their head. */
  wandering?: boolean;
}

export function Larva({ className, label = "幼虫", instar = 2, wandering = false }: LarvaProps) {
  const p = `lv${uid(useId())}`;
  const scale = instar === 1 ? 0.72 : instar === 2 ? 0.86 : 1;
  const see = instar === 3 || wandering;
  return (
    <svg viewBox="0 0 240 240" role="img" aria-label={label} className={className}>
      <defs>
        <radialGradient id={`${p}g`} cx=".35" cy=".3" r=".85">
          <stop offset="0" stopColor="#FFFFFF" stopOpacity={see ? 0.92 : 1} />
          <stop offset=".55" stopColor="#FBF4E4" stopOpacity={see ? 0.85 : 1} />
          <stop offset="1" stopColor="#E3D1AE" />
        </radialGradient>
        <filter id={`${p}b`} x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="3" />
        </filter>
      </defs>
      <ellipse cx="124" cy="192" rx={72 * scale} ry="9" fill="#1E2C29" opacity=".18" filter={`url(#${p}b)`} />
      <g transform={`translate(${124 - 124 * scale} ${188 - 188 * scale}) scale(${scale})`}>
        <g className={wandering ? "art-wiggle" : "art-breathe"} transform={wandering ? "rotate(-6 124 150)" : undefined}>
          <path
            d="M50 150 C50 122 78 112 120 112 C164 112 196 122 198 148 C200 174 168 184 122 184 C78 184 50 178 50 150 Z"
            fill={`url(#${p}g)`}
            stroke="#BDAA86"
            strokeWidth={2.5}
          />
          {see ? (
            <g opacity=".75">
              <path d="M78 150 Q104 132 132 150 Q156 166 182 148" stroke="#E0B04A" strokeWidth={10} fill="none" strokeLinecap="round" />
              <path d="M84 158 Q112 170 150 158" stroke="#C98B3A" strokeWidth={5} fill="none" strokeLinecap="round" opacity=".7" />
            </g>
          ) : (
            <path d="M86 154 Q126 138 176 150" stroke="#CDB68C" strokeWidth={12} opacity=".35" fill="none" strokeLinecap="round" />
          )}
          <g stroke="#D6C29C" strokeWidth={2} fill="none" opacity=".9">
            <path d="M78 118 Q72 150 78 180" />
            <path d="M98 114 Q92 150 98 183" />
            <path d="M118 113 Q112 150 118 184" />
            <path d="M138 113 Q132 150 138 184" />
            <path d="M158 115 Q152 150 158 182" />
            <path d="M177 120 Q172 150 177 177" />
          </g>
          <ellipse cx="114" cy="124" rx="36" ry="5" fill="#fff" opacity=".85" />
          {/* mouth hooks, eye spot, blush, smile, posterior spiracles */}
          <path d="M52 146 L39 149 L52 154 Z" fill="#2A1E14" />
          <circle cx="65" cy="138" r="3.6" fill="#2A1E14" />
          <circle cx="64" cy="137" r="1.1" fill="#fff" />
          <ellipse cx="74" cy="159" rx="8" ry="4.5" fill="#FF8FA3" opacity=".5" filter={`url(#${p}b)`} />
          <path d="M56 160 Q60 164 65 161" stroke="#6B3A17" strokeWidth={2} fill="none" strokeLinecap="round" />
          <g fill="#B98A4E">
            <circle cx="197" cy="143" r="3" />
            <circle cx="197" cy="153" r="3" />
          </g>
        </g>
      </g>
    </svg>
  );
}

export interface PupaProps extends ArtProps {
  /** Close to eclosion the red eyes show through the case. 0 = none, 1 = strong. */
  eyeShow?: number;
  shaking?: boolean;
}

export function Pupa({ className, label = "さなぎ", eyeShow = 0.5, shaking = false }: PupaProps) {
  const p = `pu${uid(useId())}`;
  return (
    <svg viewBox="0 0 240 240" role="img" aria-label={label} className={className}>
      <defs>
        <radialGradient id={`${p}g`} cx=".38" cy=".3" r=".85">
          <stop offset="0" stopColor="#F0C78A" />
          <stop offset=".55" stopColor="#C38D4E" />
          <stop offset="1" stopColor="#8B5728" />
        </radialGradient>
        <filter id={`${p}b`} x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="3" />
        </filter>
      </defs>
      <ellipse cx="120" cy="214" rx="44" ry="8" fill="#1E2C29" opacity=".2" filter={`url(#${p}b)`} />
      <g className={shaking ? "art-wiggle" : "art-breathe"}>
        <g stroke="#6E4320" strokeWidth={4} strokeLinecap="round">
          <path d="M104 50 L92 26" />
          <path d="M136 50 L148 26" />
        </g>
        <circle cx="91" cy="24" r="3.6" fill="#6E4320" />
        <circle cx="149" cy="24" r="3.6" fill="#6E4320" />
        <path
          d="M120 42 C150 42 164 72 162 122 C160 178 148 208 120 208 C92 208 80 178 78 122 C76 72 90 42 120 42 Z"
          fill={`url(#${p}g)`}
          stroke="#6E4320"
          strokeWidth={2.5}
        />
        <g filter={`url(#${p}b)`} fill="#C8243A" opacity={0.15 + 0.6 * Math.min(1, Math.max(0, eyeShow))}>
          <ellipse cx="104" cy="80" rx="12" ry="10" />
          <ellipse cx="136" cy="80" rx="12" ry="10" />
        </g>
        <g stroke="#E7C08A" strokeWidth={6} opacity=".35" fill="none" strokeLinecap="round">
          <path d="M98 110 Q90 140 102 162" />
          <path d="M142 110 Q150 140 138 162" />
        </g>
        <g stroke="#9C6A35" strokeWidth={2.5} fill="none" opacity=".75">
          <path d="M82 120 Q120 132 158 120" />
          <path d="M82 142 Q120 154 158 142" />
          <path d="M84 164 Q120 176 156 164" />
          <path d="M90 186 Q120 196 150 186" />
        </g>
        <ellipse cx="100" cy="88" rx="8" ry="24" transform="rotate(-6 100 88)" fill="#fff" opacity=".45" />
      </g>
    </svg>
  );
}
