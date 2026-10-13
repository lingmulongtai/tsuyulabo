/** A short observation counts only time during which the player can watch it. */
export class MomentClock {
  private remaining: number;
  private last: number | null = null;
  constructor(duration: number) { this.remaining = duration; }
  resume(now: number) { this.last = now; }
  advance(now: number) {
    if (this.last !== null) this.remaining -= Math.max(0, now - this.last);
    this.last = now;
    return this.remaining <= 0;
  }
  suspend(now: number) { this.advance(now); this.last = null; }
}
