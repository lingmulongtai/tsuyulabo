/** Best-effort vibration; unsupported and policy-blocked browsers are silent no-ops. */
export function buzz(pattern: number | readonly number[]): void {
  if (typeof navigator === "undefined" || typeof navigator.vibrate !== "function") return;
  try {
    navigator.vibrate(typeof pattern === "number" ? pattern : [...pattern]);
  } catch {
    // Vibration is optional feedback, never a reason to interrupt gameplay.
  }
}
