const DAYS = ["月", "火", "水", "木", "金", "土", "日"] as const;

/** Seven research days; past days are filled, today is highlighted, day 7 carries the eclosion mark. */
export function WeekStrip({ researchDay }: { researchDay: number }) {
  return (
    <ol className="grid grid-cols-7 gap-1.5" aria-label="1週間の研究">
      {DAYS.map((d, i) => {
        const day = i + 1;
        const today = day === researchDay;
        const past = day < researchDay;
        return (
          <li
            key={d}
            aria-current={today ? "date" : undefined}
            className={`relative flex h-11 flex-col items-center justify-center rounded-2xl text-sm font-bold transition-colors ${
              today
                ? "bg-eye text-white shadow-[0_3px_0_0_#9c1428]"
                : past
                  ? "bg-tint-leaf text-leaf"
                  : "bg-surface-2 text-muted border border-line-soft"
            }`}
          >
            <span className="leading-none">{d}</span>
            <span className={`mt-0.5 text-[0.6rem] leading-none ${today ? "text-white/85" : ""}`}>
              {day === 7 ? "羽化" : `${day}日目`}
            </span>
            {past && (
              <span className="absolute -right-0.5 -top-0.5 size-3 rounded-full bg-leaf ring-2 ring-bg" aria-label="済" />
            )}
          </li>
        );
      })}
    </ol>
  );
}
