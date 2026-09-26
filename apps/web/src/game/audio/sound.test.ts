import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

function browserAudio() {
  const nodes: ReturnType<typeof makeOscillator>[] = [];
  const gains: ReturnType<typeof makeGain>[] = [];
  function makeOscillator() {
    return {
      type: "sine", frequency: { value: 0 }, onended: undefined as (() => void) | undefined,
      connect: vi.fn(), disconnect: vi.fn(), start: vi.fn(), stop: vi.fn(),
    };
  }
  function makeGain() {
    return {
      gain: { value: 1, setValueAtTime: vi.fn(), exponentialRampToValueAtTime: vi.fn() },
      connect: vi.fn(), disconnect: vi.fn(),
    };
  }
  const resume = vi.fn(async () => {});
  const constructed = vi.fn();
  class MockContext {
    currentTime = 10;
    state: AudioContextState = "suspended";
    destination = {};
    resume = resume;
    constructor() { constructed(); }
    createOscillator() { const node = makeOscillator(); nodes.push(node); return node; }
    createGain() { const gain = makeGain(); gains.push(gain); return gain; }
  }
  vi.stubGlobal("window", { AudioContext: MockContext });
  return { nodes, gains, resume, constructed, MockContext };
}

beforeEach(() => { vi.resetModules(); });
afterEach(() => { vi.unstubAllGlobals(); });

describe("sound", () => {
  it("is safe to import and call during SSR", async () => {
    vi.stubGlobal("window", undefined);
    const sound = await import("./sound");
    sound.init(); sound.puzzleClear(); sound.setMuted(true); sound.setMuted(false);
    expect(sound.isMuted()).toBe(false);
  });

  it("creates one lazy context and resumes it from a cue", async () => {
    const mock = browserAudio();
    const { tone, init } = await import("./sound");
    expect(mock.constructed).not.toHaveBeenCalled();
    tone(440); init(); tone(880);
    expect(mock.constructed).toHaveBeenCalledTimes(1);
    expect(mock.resume).toHaveBeenCalledTimes(1);
    expect(mock.nodes).toHaveLength(2);
  });

  it("schedules envelopes and releases nodes after playback", async () => {
    const mock = browserAudio();
    const { tone } = await import("./sound");
    tone(440, 0.2, 0.3, "square", 0.07);
    const node = mock.nodes[0];
    expect(node.type).toBe("square");
    expect(node.frequency.value).toBe(440);
    expect(node.start).toHaveBeenCalledWith(10.2);
    expect(node.stop.mock.calls[0][0]).toBeCloseTo(10.55);
    expect(mock.gains[1].gain.setValueAtTime).toHaveBeenCalledWith(0.0001, 10.2);
    expect(mock.gains[1].gain.exponentialRampToValueAtTime.mock.calls.map(([v]) => v))
      .toEqual([0.07, 0.0001]);
    node.onended?.();
    expect(node.disconnect).toHaveBeenCalledOnce();
    expect(mock.gains[1].disconnect).toHaveBeenCalledOnce();
  });

  it("mutes pending audio immediately and creates nothing while muted", async () => {
    const mock = browserAudio();
    const sound = await import("./sound");
    sound.setMuted(true); sound.tap();
    expect(sound.isMuted()).toBe(true);
    expect(mock.constructed).not.toHaveBeenCalled();
    sound.setMuted(false); sound.tap(); sound.setMuted(true); sound.perfect();
    expect(mock.gains[0].gain.value).toBe(0);
    expect(mock.nodes).toHaveLength(1);
    sound.setMuted(false); sound.tap();
    expect(mock.gains[0].gain.value).toBe(1);
    expect(mock.nodes).toHaveLength(2);
  });

  it("schedules arpeggios sequentially and chords simultaneously", async () => {
    const mock = browserAudio();
    const { arp, chord } = await import("./sound");
    arp([440, 550, 660], 0.1); chord([220, 330], 0.5);
    expect(mock.nodes.map((node) => node.frequency.value)).toEqual([440, 550, 660, 220, 330]);
    expect(mock.nodes.map((node) => node.start.mock.calls[0][0])).toEqual([10, 10.1, 10.2, 10.5, 10.5]);
  });

  it("plays pentatonic steps, ascending omens, and every named cue", async () => {
    const mock = browserAudio();
    const sound = await import("./sound");
    for (let n = 0; n < 16; n++) sound.step(n);
    expect(mock.nodes[0].frequency.value).toBe(392);
    expect(mock.nodes[1].frequency.value).toBeCloseTo(392 * 2 ** (2 / 12));
    expect(mock.nodes[5].frequency.value).toBe(784);
    expect(mock.nodes[15].frequency.value).toBe(392);
    for (const tier of [0, 1, 2, 3] as const) sound.omen(tier);
    expect(mock.nodes.slice(-4).map((node) => node.frequency.value)).toEqual([440, 587, 740, 988]);
    const cues = [sound.bad, sound.place, () => sound.lineClear(2), () => sound.combo(3),
      sound.puzzleClear, () => sound.star(0), sound.greatSuccess, sound.mutation,
      sound.drumroll, sound.tap, sound.perfect];
    for (const cue of cues) {
      const before = mock.nodes.length;
      cue();
      expect(mock.nodes.length).toBeGreaterThan(before);
    }
    for (const rank of ["normal", "silver", "gold", "rainbow"] as const) sound.rankReveal(rank);
    expect(mock.nodes.every((node) => Number.isFinite(node.frequency.value))).toBe(true);
    expect(sound.Sound.tone).toBe(sound.tone);
  });

  it("ignores invalid tone inputs and handles very short envelopes", async () => {
    const mock = browserAudio();
    const sound = await import("./sound");
    sound.tone(NaN); sound.tone(-1); sound.tone(440, -1); sound.tone(440, 0, 0);
    sound.tone(440, 0, 1, "sine", 0); sound.lineClear(0); sound.combo(0);
    expect(mock.nodes).toHaveLength(0);
    sound.tone(440, 0, 0.001);
    const calls = mock.gains[1].gain.exponentialRampToValueAtTime.mock.calls;
    expect(calls[0][1]).toBeLessThan(calls[1][1]);
  });

  it("handles unsupported browsers and constructor failures", async () => {
    vi.stubGlobal("window", {});
    const sound = await import("./sound");
    expect(() => sound.tap()).not.toThrow();
    vi.stubGlobal("window", { AudioContext: class { constructor() { throw new Error("denied"); } } });
    expect(() => sound.tap()).not.toThrow();
  });

  it("supports the prefixed constructor and safely retries blocked resume", async () => {
    const mock = browserAudio();
    vi.stubGlobal("window", { webkitAudioContext: mock.MockContext });
    mock.resume.mockRejectedValueOnce(new Error("gesture required"));
    const sound = await import("./sound");
    sound.init();
    await new Promise<void>((resolve) => setTimeout(resolve, 0));
    sound.init();
    expect(mock.resume).toHaveBeenCalledTimes(2);
  });
});
