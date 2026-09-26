import type { TierIndex, WeekRank } from "../expectation";

let context: AudioContext | undefined;
let master: GainNode | undefined;
let muted = false;
let resuming: Promise<void> | undefined;

/** Call init() or a cue inside the first pointer/key gesture to unlock browser audio. */
function audioContext(): AudioContext | undefined {
  if (muted || typeof window === "undefined") return undefined;
  try {
    if (!context || context.state === "closed") {
      const browser = window as typeof window & { webkitAudioContext?: typeof AudioContext };
      const Constructor = browser.AudioContext ?? browser.webkitAudioContext;
      if (!Constructor) return undefined;
      const next = new Constructor();
      const gain = next.createGain();
      gain.connect(next.destination);
      context = next;
      master = gain;
    }
    if (context.state === "suspended" && !resuming) {
      resuming = context.resume().catch(() => {
        // A later user gesture can retry when autoplay is blocked.
      }).finally(() => { resuming = undefined; });
    }
    return context;
  } catch {
    // Browsers may expose AudioContext but deny its construction or resumption.
    return undefined;
  }
}

export function init(): void { audioContext(); }
export function isMuted(): boolean { return muted; }

/** In-memory preference; also silence sounds that have already been scheduled. */
export function setMuted(value: boolean): void {
  muted = value;
  if (master && context?.state !== "closed") master.gain.value = value ? 0 : 1;
}

/** Frequencies in Hz; delay/duration in seconds; volume is linear gain (0..1). */
export function tone(
  frequency: number, delay = 0, duration = 0.15, type: OscillatorType = "triangle", volume = 0.1,
): void {
  if (![frequency, delay, duration, volume].every(Number.isFinite) ||
    frequency <= 0 || delay < 0 || duration <= 0 || volume <= 0) return;
  const ctx = audioContext();
  if (!ctx || !master) return;
  const oscillator = ctx.createOscillator();
  const envelope = ctx.createGain();
  const start = ctx.currentTime + delay;
  const end = start + duration;
  oscillator.type = type;
  oscillator.frequency.value = frequency;
  envelope.gain.setValueAtTime(0.0001, start);
  envelope.gain.exponentialRampToValueAtTime(Math.max(0.0001, Math.min(1, volume)),
    start + Math.min(0.012, duration / 2));
  envelope.gain.exponentialRampToValueAtTime(0.0001, end);
  oscillator.connect(envelope);
  envelope.connect(master);
  oscillator.onended = () => { oscillator.disconnect(); envelope.disconnect(); };
  oscillator.start(start);
  oscillator.stop(end + 0.05);
}

export function arp(
  frequencies: readonly number[], step = 0.07, duration = 0.3,
  type: OscillatorType = "triangle", volume = 0.1,
): void {
  frequencies.forEach((frequency, i) => tone(frequency, i * step, duration, type, volume));
}

export function chord(
  frequencies: readonly number[], delay = 0, duration = 0.6,
  type: OscillatorType = "triangle", volume = 0.07,
): void {
  frequencies.forEach((frequency) => tone(frequency, delay, duration, type, volume));
}

const PENTATONIC = [0, 2, 4, 7, 9] as const;
function boundedIndex(n: number, max: number): number {
  return Number.isFinite(n) ? Math.max(0, Math.min(max, Math.floor(n))) : 0;
}

/** Rising pentatonic pops repeat after three octaves, as in the planning demo. */
export function step(n: number): void {
  const note = boundedIndex(n, Number.MAX_SAFE_INTEGER) % 15;
  tone(392 * 2 ** ((12 * Math.floor(note / 5) + PENTATONIC[note % 5]) / 12),
    0, 0.1, "sine", 0.07);
}

export function bad(): void { tone(150, 0, 0.12, "square", 0.03); }
export function place(): void { tone(262, 0, 0.08, "triangle", 0.07); }
export function lineClear(lines: number): void {
  if (lines <= 0) return;
  const count = boundedIndex(lines, 8);
  arp([523, 659, 784, 1047, 1319, 1568, 1760, 2093].slice(0, count + 1), 0.045, 0.2);
}
export function combo(n: number): void {
  if (n <= 0) return;
  const root = 440 * 2 ** (boundedIndex(n - 1, 12) / 12);
  chord([root, root * 1.25, root * 1.5], 0, 0.2, "triangle", 0.05);
}
export function puzzleClear(): void { arp([523, 659, 784, 1047, 1319]); }
/** Zero-based star reveal index. */
export function star(i: number): void {
  tone([1047, 1319, 1568, 1760, 2093][boundedIndex(i, 4)], 0, 0.25, "triangle", 0.12);
}
export function greatSuccess(): void {
  arp([523, 659, 784, 1047], 0.09, 0.3);
  chord([523, 659, 784, 1047], 0.4, 0.9, "sine", 0.07);
}
export function omen(tier: TierIndex): void {
  tone([440, 587, 740, 988][tier], 0, 0.28, "triangle", 0.11);
}
export function mutation(): void { arp([988, 1175, 1480, 1976], 0.06, 0.2, "square", 0.04); }
export function drumroll(): void {
  for (let i = 0; i < 16; i++) tone(98 + i * 6, i * 0.065, 0.045, "sawtooth", 0.025 + i * 0.001);
}
export function rankReveal(rank: WeekRank): void {
  const notes: Record<WeekRank, readonly number[]> = {
    normal: [262, 330, 392], silver: [392, 494, 587],
    gold: [523, 659, 784, 1047], rainbow: [523, 659, 784, 1047, 1319],
  };
  chord(notes[rank], 0, rank === "rainbow" ? 1.2 : 0.6);
}
export function tap(): void { tone(440, 0, 0.06, "sine", 0.06); }
export function perfect(): void { chord([880, 1109, 1319], 0, 0.2, "triangle", 0.06); }

/** Optional object facade for consumers porting the demo's Sound calls. */
export const Sound = {
  init, isMuted, setMuted, tone, arp, chord, step, bad, place, lineClear, combo,
  puzzleClear, star, greatSuccess, omen, mutation, drumroll, rankReveal, tap, perfect,
};
