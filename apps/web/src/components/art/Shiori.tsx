import { useId } from "react";

export type ShioriMood = "normal" | "smile" | "surprised" | "thinking";

/**
 * 研究員シオリ — the research partner. Bob haircut, round glasses, lab coat, a dew-drop hairpin. She is an AI and
 * never hides it: the small violet pin on her collar is the AI mark used across the app.
 */
export function Shiori({ mood = "normal", className, label = "研究員シオリ" }: { mood?: ShioriMood; className?: string; label?: string }) {
  const id = `sh${useId().replace(/[^a-zA-Z0-9]/g, "")}`;
  const mouth =
    mood === "smile" ? (
      <path d="M53 78 Q60 85 67 78" stroke="#8a3b3b" strokeWidth={2.4} fill="none" strokeLinecap="round" />
    ) : mood === "surprised" ? (
      <ellipse cx="60" cy="80" rx="3.6" ry="4.4" fill="#8a3b3b" />
    ) : mood === "thinking" ? (
      <path d="M54 80 Q59 78 66 80" stroke="#8a3b3b" strokeWidth={2.2} fill="none" strokeLinecap="round" />
    ) : (
      <path d="M55 79 Q60 82.5 65 79" stroke="#8a3b3b" strokeWidth={2.2} fill="none" strokeLinecap="round" />
    );
  const eyeRy = mood === "surprised" ? 5.4 : 4.4;

  return (
    <svg viewBox="0 0 120 120" role="img" aria-label={label} className={className}>
      <defs>
        <linearGradient id={`${id}hair`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#3b3552" />
          <stop offset="1" stopColor="#221e33" />
        </linearGradient>
        <radialGradient id={`${id}skin`} cx=".45" cy=".35" r=".75">
          <stop offset="0" stopColor="#fff1e6" />
          <stop offset="1" stopColor="#f6d5bf" />
        </radialGradient>
        <linearGradient id={`${id}coat`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#ffffff" />
          <stop offset="1" stopColor="#dfe9f2" />
        </linearGradient>
      </defs>

      {/* back hair */}
      <path d="M26 58 C24 30 40 16 60 16 C80 16 96 30 94 58 L96 86 C88 92 80 90 76 84 L44 84 C40 90 32 92 24 86 Z" fill={`url(#${id}hair)`} />

      {/* lab coat and shoulders */}
      <path d="M22 120 C22 100 36 92 60 92 C84 92 98 100 98 120 Z" fill={`url(#${id}coat)`} stroke="#b9c8d6" strokeWidth={1.5} />
      <path d="M60 94 L50 120 M60 94 L70 120" stroke="#b9c8d6" strokeWidth={1.5} />
      <path d="M52 92 L60 104 L68 92 Z" fill="#5f4fcf" />
      <circle cx="79" cy="104" r="4" fill="#a898ff" stroke="#5f4fcf" strokeWidth={1.4} />
      <path d="M77.4 104 h3.2 M79 102.4 v3.2" stroke="#fff" strokeWidth={1.1} strokeLinecap="round" />

      {/* neck and face */}
      <rect x="53" y="82" width="14" height="12" rx="5" fill="#f3cfb8" />
      <ellipse cx="60" cy="60" rx="27" ry="28" fill={`url(#${id}skin)`} />

      {/* fringe */}
      <path d="M33 56 C32 36 44 26 60 26 C77 26 89 37 87 56 C80 48 72 42 64 40 C60 46 50 52 33 56 Z" fill={`url(#${id}hair)`} />
      <path d="M44 34 Q54 30 64 34" stroke="#6b6590" strokeWidth={2} fill="none" strokeLinecap="round" opacity=".7" />

      {/* dew-drop hairpin */}
      <path d="M80 36 C77 41 76 43 76 45 a4 4 0 0 0 8 0 c0-2-1-4-4-9Z" fill="#7fd0e6" stroke="#2f8fae" strokeWidth={1.2} />

      {/* eyes */}
      <ellipse cx="49" cy="63" rx="3.6" ry={eyeRy} fill="#2b2540" />
      <ellipse cx="71" cy="63" rx="3.6" ry={eyeRy} fill="#2b2540" />
      <circle cx="50.2" cy="61.4" r="1.2" fill="#fff" />
      <circle cx="72.2" cy="61.4" r="1.2" fill="#fff" />

      {/* round glasses */}
      <g stroke="#5f4fcf" strokeWidth={2} fill="rgba(255,255,255,.18)">
        <circle cx="49" cy="63" r="9.5" />
        <circle cx="71" cy="63" r="9.5" />
      </g>
      <path d="M58.5 63 h3" stroke="#5f4fcf" strokeWidth={2} />
      <path d="M44 58 l3 -2" stroke="#fff" strokeWidth={1.6} strokeLinecap="round" opacity=".8" />

      {/* cheeks and mouth */}
      <ellipse cx="42" cy="74" rx="4.5" ry="2.6" fill="#ff9fb0" opacity=".45" />
      <ellipse cx="78" cy="74" rx="4.5" ry="2.6" fill="#ff9fb0" opacity=".45" />
      {mouth}
      {mood === "thinking" && <path d="M92 30 q4 -6 8 0 q4 6 8 0" stroke="#5f4fcf" strokeWidth={2} fill="none" strokeLinecap="round" opacity=".7" />}
    </svg>
  );
}
