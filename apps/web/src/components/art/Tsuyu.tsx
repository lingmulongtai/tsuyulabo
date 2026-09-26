import { useId } from "react";
import { paletteFor, type Sex, type Strain, type WingType } from "./palette";

export interface TsuyuProps {
  strain?: Strain;
  sex?: Sex;
  /** Idle motion: bobbing, wing flicks, antenna twitches. */
  animated?: boolean;
  label?: string;
  className?: string;
}

const WING_PATHS: Record<"normal" | "vestigial", { l: string; r: string; vl: string[]; vr: string[] }> = {
  normal: {
    l: "M112 140 C92 118 50 92 30 106 C14 118 28 148 60 158 C84 166 104 156 112 140 Z",
    r: "M128 140 C148 118 190 92 210 106 C226 118 212 148 180 158 C156 166 136 156 128 140 Z",
    vl: ["M110 140 Q72 118 36 110", "M110 143 Q74 138 40 136", "M109 147 Q84 156 62 154"],
    vr: ["M130 140 Q168 118 204 110", "M130 143 Q166 138 200 136", "M131 147 Q156 156 178 154"],
  },
  vestigial: {
    l: "M112 140 C104 130 88 126 82 134 C76 142 86 152 96 150 C104 148 108 146 112 140 Z",
    r: "M128 140 C136 130 152 126 158 134 C164 142 154 152 144 150 C136 148 132 146 128 140 Z",
    vl: ["M108 140 Q96 136 88 138"],
    vr: ["M132 140 Q144 136 152 138"],
  },
};

function Wings({ id, type }: { id: string; type: WingType }) {
  const w = WING_PATHS[type === "vestigial" ? "vestigial" : "normal"];
  const curl = type === "curly";
  const veins = (paths: string[]) => (
    <g stroke="#9FC9C5" strokeWidth={1.3} fill="none" opacity={0.9}>
      {paths.map((d) => (
        <path key={d} d={d} />
      ))}
    </g>
  );
  return (
    <>
      <g className="wl">
        <g transform={curl ? "rotate(36 112 140)" : undefined}>
          <path d={w.l} fill={`url(#${id}w)`} stroke="#8DB9B6" strokeWidth={2} />
          {veins(w.vl)}
          {type !== "vestigial" && (
            <path d="M44 110 Q70 104 96 124" stroke="#fff" strokeWidth={3} opacity={0.75} fill="none" strokeLinecap="round" />
          )}
        </g>
      </g>
      <g className="wr">
        <g transform={curl ? "rotate(-36 128 140)" : undefined}>
          <path d={w.r} fill={`url(#${id}w)`} stroke="#8DB9B6" strokeWidth={2} />
          {veins(w.vr)}
          {type !== "vestigial" && (
            <path d="M196 110 Q170 104 144 124" stroke="#fff" strokeWidth={3} opacity={0.75} fill="none" strokeLinecap="round" />
          )}
        </g>
      </g>
    </>
  );
}

/**
 * ツユ — the adult fly. Deformed but anatomically honest: compound eyes with a pseudopupil, three ocelli,
 * feathery aristae, bristles, grooming pose, a dark abdomen tip on males, iridescent wings.
 */
export function Tsuyu({ strain = "wild", sex = "m", animated = false, label = "ツユ", className }: TsuyuProps) {
  const id = `ts${useId().replace(/[^a-zA-Z0-9]/g, "")}`;
  const s = paletteFor(strain);
  const { head: h, body: b, eye: e, leg } = s;
  const male = sex === "m";

  return (
    <svg viewBox="0 0 240 240" role="img" aria-label={label} className={`${animated ? "ts-anim " : ""}${className ?? ""}`}>
      <defs>
        <radialGradient id={`${id}h`} cx=".38" cy=".3" r=".78">
          <stop offset="0" stopColor={h[0]} />
          <stop offset=".55" stopColor={h[1]} />
          <stop offset="1" stopColor={h[2]} />
        </radialGradient>
        <radialGradient id={`${id}b`} cx=".35" cy=".28" r=".85">
          <stop offset="0" stopColor={b[0]} />
          <stop offset=".55" stopColor={b[1]} />
          <stop offset="1" stopColor={b[2]} />
        </radialGradient>
        <radialGradient id={`${id}e`} cx=".4" cy=".32" r=".75">
          <stop offset="0" stopColor={e[0]} />
          <stop offset=".42" stopColor={e[1]} />
          <stop offset=".85" stopColor={e[2]} />
          <stop offset="1" stopColor={e[3]} />
        </radialGradient>
        <radialGradient id={`${id}pp`}>
          <stop offset="0" stopColor={s.pupil} stopOpacity=".95" />
          <stop offset=".72" stopColor={s.pupil} stopOpacity=".9" />
          <stop offset="1" stopColor={s.pupil} stopOpacity="0" />
        </radialGradient>
        <linearGradient id={`${id}w`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#fff" stopOpacity=".95" />
          <stop offset=".35" stopColor="#CDEFF5" stopOpacity=".72" />
          <stop offset=".6" stopColor="#FFD2EC" stopOpacity=".58" />
          <stop offset=".82" stopColor="#D6F4CE" stopOpacity=".58" />
          <stop offset="1" stopColor="#FFEBB8" stopOpacity=".55" />
        </linearGradient>
        <pattern id={`${id}f`} width="6" height="5.4" patternUnits="userSpaceOnUse">
          <circle cx="1.5" cy="1.4" r="1.05" fill="#fff" fillOpacity=".2" />
          <circle cx="4.5" cy="4.1" r="1.05" fill="#fff" fillOpacity=".2" />
        </pattern>
        <filter id={`${id}bl`} x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="4" />
        </filter>
        <filter id={`${id}bs`} x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="2.2" />
        </filter>
        <clipPath id={`${id}ac`}>
          <ellipse cx="120" cy="168" rx="42" ry="38" />
        </clipPath>
      </defs>

      {/* contact shadow */}
      <ellipse cx="120" cy="221" rx="58" ry="8" fill="#1E2C29" opacity=".2" filter={`url(#${id}bl)`} />

      <g className="bob">
        <Wings id={id} type={s.wings} />

        {/* hind and middle legs */}
        <g stroke={leg} strokeWidth={5} strokeLinecap="round" fill="none">
          <path d="M100 170 Q78 180 70 202" />
          <path d="M108 186 Q96 202 98 214" />
          <path d="M140 170 Q162 180 170 202" />
          <path d="M132 186 Q144 202 142 214" />
        </g>
        <g fill={leg}>
          <circle cx="70" cy="203" r="4.3" />
          <circle cx="98" cy="215" r="4.3" />
          <circle cx="170" cy="203" r="4.3" />
          <circle cx="142" cy="215" r="4.3" />
        </g>

        {/* abdomen with stripes; males have a dark tip */}
        <ellipse cx="120" cy="168" rx="42" ry="38" fill={`url(#${id}b)`} stroke={b[3]} strokeWidth={2.5} />
        <g clipPath={`url(#${id}ac)`}>
          <path d="M72 166 Q120 184 168 166" stroke={s.stripe} strokeWidth={8} fill="none" opacity=".85" />
          <path d="M74 183 Q120 201 166 183" stroke={s.stripe} strokeWidth={9} fill="none" opacity=".85" />
          {male ? (
            <ellipse cx="120" cy="207" rx="36" ry="14" fill={s.stripe} opacity=".92" />
          ) : (
            <path d="M80 198 Q120 214 160 198" stroke={s.stripe} strokeWidth={7} fill="none" opacity=".8" />
          )}
        </g>
        <ellipse cx="104" cy="152" rx="14" ry="6" transform="rotate(-20 104 152)" fill="#fff" opacity=".35" />
        <ellipse cx="120" cy="142" rx="36" ry="9" fill="#4A2A10" opacity=".3" filter={`url(#${id}bs)`} />

        {/* front legs held together (grooming pose) */}
        <g stroke={leg} strokeWidth={5} strokeLinecap="round" fill="none">
          <path d="M104 146 Q92 162 110 170" />
          <path d="M136 146 Q148 162 130 170" />
        </g>
        <circle cx="113" cy="170" r="5.2" fill={leg} />
        <circle cx="127" cy="170" r="5.2" fill={leg} />
        <circle cx="111.5" cy="168.5" r="1.6" fill="#fff" opacity=".5" />
        <circle cx="125.5" cy="168.5" r="1.6" fill="#fff" opacity=".5" />

        {/* head */}
        <ellipse cx="120" cy="88" rx="62" ry="54" fill={`url(#${id}h)`} stroke={h[3]} strokeWidth={2.5} />
        <ellipse cx="98" cy="52" rx="24" ry="9" transform="rotate(-18 98 52)" fill="#fff" opacity=".4" />
        <path d="M166 52 Q186 78 178 112" stroke="#fff" strokeWidth={3} opacity=".45" fill="none" strokeLinecap="round" />

        {/* bristles (the "ahoge") */}
        <g stroke={leg} strokeWidth={2.4} strokeLinecap="round" fill="none">
          <path d="M110 38 Q106 22 96 16" />
          <path d="M130 38 Q134 22 144 16" />
        </g>

        {/* three ocelli */}
        <g stroke={e[3]} strokeWidth={0.8}>
          <circle cx="120" cy="45" r="3.4" fill={e[1]} />
          <circle cx="112.5" cy="52" r="2.9" fill={e[1]} />
          <circle cx="127.5" cy="52" r="2.9" fill={e[1]} />
        </g>
        <g fill="#fff">
          <circle cx="119" cy="44" r="1" />
          <circle cx="111.7" cy="51.2" r=".9" />
          <circle cx="126.7" cy="51.2" r=".9" />
        </g>

        {/* compound eyes with facets */}
        <g transform="rotate(-8 84 92)">
          <ellipse cx="84" cy="92" rx="30" ry="35" fill={`url(#${id}e)`} stroke={e[3]} strokeWidth={2.5} />
          <ellipse cx="84" cy="92" rx="29" ry="34" fill={`url(#${id}f)`} />
        </g>
        <g transform="rotate(8 156 92)">
          <ellipse cx="156" cy="92" rx="30" ry="35" fill={`url(#${id}e)`} stroke={e[3]} strokeWidth={2.5} />
          <ellipse cx="156" cy="92" rx="29" ry="34" fill={`url(#${id}f)`} />
        </g>

        {/* pseudopupils used as pupils */}
        <ellipse cx="91" cy="100" rx="11" ry="14" fill={`url(#${id}pp)`} />
        <ellipse cx="149" cy="100" rx="11" ry="14" fill={`url(#${id}pp)`} />
        <g fill="#fff" opacity=".9">
          <circle cx="87" cy="95" r="2.3" />
          <circle cx="145" cy="95" r="2.3" />
        </g>
        <g fill="#fff">
          <ellipse cx="74" cy="75" rx="10" ry="7" transform="rotate(-25 74 75)" opacity=".95" />
          <circle cx="99" cy="113" r="3.6" opacity=".85" />
          <circle cx="68" cy="93" r="1.8" opacity=".7" />
          <ellipse cx="146" cy="75" rx="10" ry="7" transform="rotate(-25 146 75)" opacity=".95" />
          <circle cx="171" cy="113" r="3.6" opacity=".85" />
          <circle cx="140" cy="93" r="1.8" opacity=".7" />
        </g>
        <g stroke={e[0]} strokeWidth={2} opacity=".55" fill="none" strokeLinecap="round">
          <path d="M108 70 Q116 92 106 118" />
          <path d="M180 70 Q188 92 178 118" />
        </g>

        {/* cheeks and mouth */}
        <g filter={`url(#${id}bs)`} fill="#FF7F98" opacity=".55">
          <ellipse cx="104" cy="127" rx="10" ry="5.5" />
          <ellipse cx="136" cy="127" rx="10" ry="5.5" />
        </g>
        <path d="M114 129 Q120 135 126 129" stroke="#6B3A17" strokeWidth={2.4} fill="none" strokeLinecap="round" />

        {/* antennae with feathery aristae */}
        <g className="ant">
          <ellipse cx="112" cy="72" rx="5" ry="6" fill={h[1]} stroke={h[3]} strokeWidth={1.5} />
          <ellipse cx="128" cy="72" rx="5" ry="6" fill={h[1]} stroke={h[3]} strokeWidth={1.5} />
          <g stroke={leg} strokeWidth={1.8} strokeLinecap="round" fill="none">
            <path d="M111 68 Q104 50 90 42" />
            <path d="M129 68 Q136 50 150 42" />
          </g>
          <g stroke={leg} strokeWidth={1.1} strokeLinecap="round" fill="none" opacity=".8">
            <path d="M106 58 l-4 1 M102 52.5 l-4 -1 M98 48 l-3 -2 M106 58 l3 -3 M102 52.5 l2 -3.5 M98 48 l1 -3.5" />
            <path d="M134 58 l4 1 M138 52.5 l4 -1 M142 48 l3 -2 M134 58 l-3 -3 M138 52.5 l-2 -3.5 M142 48 l-1 -3.5" />
          </g>
          <circle cx="90" cy="42" r="2.3" fill={leg} />
          <circle cx="150" cy="42" r="2.3" fill={leg} />
        </g>
      </g>
    </svg>
  );
}
