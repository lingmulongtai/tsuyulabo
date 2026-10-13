const DAYS = ["月", "火", "水", "木", "金", "土", "日"] as const;

/** A thin growth line; the current day is amber and labelled for assistive technology. */
export function WeekStrip({ researchDay }: { researchDay: number }) {
  return <ol className="relative mt-2 flex justify-between border-t border-white/20" aria-label="この子の一週間">
    {DAYS.map((label, index) => {
      const day = index + 1, today = day === researchDay;
      return <li key={label} aria-current={today ? "date" : undefined} aria-label={`${day}日目（${label}）${day === 7 ? "・羽化" : ""}`}
        className="relative flex w-5 flex-col items-center pt-1 text-[9px] text-[#d5cab4]">
        <span aria-hidden="true" className={`absolute -top-[3px] size-[5px] rounded-full ${today ? "bg-[#e7bd78] shadow-[0_0_8px_2px_#e7bd7870]" : day < researchDay ? "bg-[#d5cab4]" : "bg-[#675f52]"}`} />
        <span aria-hidden="true">{label}</span>
      </li>;
    })}
  </ol>;
}
