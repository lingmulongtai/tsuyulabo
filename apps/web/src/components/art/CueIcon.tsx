export type CueId = "banana" | "apple_vinegar" | "yeast" | "grape" | "blue_light";

/** Small drawn icons for the training / race cues, in the same style as the rest of the art. */
export function CueIcon({ cue, size = 20, className }: { cue: CueId | string; size?: number; className?: string }) {
  const common = { width: size, height: size, viewBox: "0 0 24 24", className, "aria-hidden": true } as const;
  switch (cue) {
    case "banana":
      return (
        <svg {...common}>
          <path d="M5 6c1 8 6 13 14 12 1-.1 1.4-1.3.6-1.9C13 15 9 11 7.6 5.3 7.3 4.2 4.8 4.6 5 6Z" fill="#F2C94C" stroke="#B8862A" strokeWidth={1.3} strokeLinejoin="round" />
          <path d="M6.6 6.6c1.5 5 4.5 8.3 9 9.8" stroke="#fff6cf" strokeWidth={1.4} strokeLinecap="round" fill="none" />
          <path d="M5.4 5.2 4.8 3.6" stroke="#6b4a12" strokeWidth={1.6} strokeLinecap="round" />
        </svg>
      );
    case "apple_vinegar":
      return (
        <svg {...common}>
          <path d="M9.5 3h5v2.6c0 .6.3 1.1.8 1.5 1.6 1.1 2.7 3 2.7 5.2V19a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2v-6.7c0-2.2 1.1-4.1 2.7-5.2.5-.4.8-.9.8-1.5Z" fill="#fde7e7" stroke="#A92A2F" strokeWidth={1.3} strokeLinejoin="round" />
          <path d="M6.2 13h11.6v6a2 2 0 0 1-2 2H8.2a2 2 0 0 1-2-2Z" fill="#E5484D" opacity={0.85} />
          <path d="M9 3h6" stroke="#A92A2F" strokeWidth={1.6} strokeLinecap="round" />
          <path d="M8.4 15.2v3" stroke="#fff" strokeWidth={1.3} strokeLinecap="round" opacity={0.8} />
        </svg>
      );
    case "yeast":
      return (
        <svg {...common}>
          <circle cx="9" cy="13" r="5" fill="#E6D5B4" stroke="#8a7248" strokeWidth={1.2} />
          <circle cx="15.5" cy="9.5" r="3.6" fill="#F0E4CB" stroke="#8a7248" strokeWidth={1.2} />
          <circle cx="16" cy="16.5" r="2.4" fill="#F0E4CB" stroke="#8a7248" strokeWidth={1.1} />
          <circle cx="7.5" cy="11.5" r="1.2" fill="#fff" opacity={0.8} />
        </svg>
      );
    case "grape":
      return (
        <svg {...common}>
          <path d="M12 3.5c.3 1.3 1.3 2.1 2.8 2.3" stroke="#3f7a2e" strokeWidth={1.5} strokeLinecap="round" fill="none" />
          {[
            [9.5, 8.5],
            [14.5, 8.5],
            [12, 12],
            [7.5, 12.5],
            [16.5, 12.5],
            [10, 16],
            [14, 16],
            [12, 19.5],
          ].map(([cx, cy]) => (
            <circle key={`${cx}-${cy}`} cx={cx} cy={cy} r={2.5} fill="#8E6BD8" stroke="#5E43A3" strokeWidth={1} />
          ))}
          <circle cx="9" cy="7.8" r=".8" fill="#fff" opacity={0.8} />
        </svg>
      );
    case "blue_light":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9" fill="#5EC8F2" opacity={0.25} />
          <circle cx="12" cy="12" r="5.2" fill="#5EC8F2" stroke="#2F8FAE" strokeWidth={1.3} />
          <circle cx="10.4" cy="10.4" r="1.6" fill="#fff" opacity={0.85} />
        </svg>
      );
    default:
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="5" fill="currentColor" opacity={0.5} />
        </svg>
      );
  }
}
