export function FlyAccessory({ item }: { item?: string | null }) {
  if (!item) return null;
  return <svg aria-hidden="true" viewBox="0 0 100 42" className="absolute left-1/2 top-[19%] z-10 w-[37%] -translate-x-1/2 overflow-visible">
    {item === "leaf_hat" ? <>
      <path d="M13 25Q31 2 70 7Q69 32 34 33Z" fill="#8ac779" stroke="#39765b" strokeWidth="3" />
      <path d="M24 26Q44 17 61 13" fill="none" stroke="#d9efa4" strokeWidth="3" />
      <path d="M5 29Q49 39 91 27" fill="none" stroke="#39765b" strokeWidth="5" strokeLinecap="round" />
    </> : <>
      <path d="M45 22Q20 -1 13 12Q12 28 45 28M55 22Q81 -1 87 12Q88 28 55 28" fill="#8dd8e7" stroke="#388494" strokeWidth="3" />
      <ellipse cx="50" cy="24" rx="8" ry="7" fill="#c4f0f2" stroke="#388494" strokeWidth="3" />
      <path d="M32 25L21 40M68 25L79 40" stroke="#388494" strokeWidth="4" strokeLinecap="round" />
    </>}
  </svg>;
}
