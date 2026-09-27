/** Translate a server snapshot into a monotonic session clock, independent of device time. */
export function dailyElapsed(startedAt: string, serverNow: string, receivedAt: number, now: number): number {
  return Math.max(0, Math.floor(Date.parse(serverNow) - Date.parse(startedAt) + now - receivedAt));
}

export function dailyTime(elapsedMs: number): string {
  return `${(elapsedMs / 1000).toFixed(2)}秒`;
}
