export function Ornament({ item }: { item?: string | null }) {
  if (!item) return null;
  return <svg aria-hidden="true" viewBox="0 0 64 64" className="h-full w-full drop-shadow-sm">
    {item === "banana_ornament" ? <>
      <path d="M9 13Q23 50 52 24Q44 56 24 53Q8 49 9 13Z" fill="#f7cc5e" stroke="#ad7931" strokeWidth="3" />
      <path d="M12 16Q20 37 39 35" fill="none" stroke="#fff0a4" strokeWidth="3" strokeLinecap="round" />
    </> : <>
      {[0, 72, 144, 216, 288].map(angle => <ellipse key={angle} cx="32" cy="18" rx="9" ry="15" transform={`rotate(${angle} 32 32)`} fill="#f5b7ca" stroke="#b96487" strokeWidth="2" />)}
      <circle cx="32" cy="32" r="9" fill="#f8dc77" stroke="#bb9550" strokeWidth="2" />
      <circle cx="29" cy="29" r="2" fill="#fff4b0" />
    </>}
  </svg>;
}
