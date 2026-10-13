/** Serializes snapshot work, shares identical portraits, and bounds in-memory image retention. */
export class PortraitQueue {
  private listeners = new Set<() => void>();
  private requests: { key: string; owner: string }[] = [];
  private images = new Map<string, string>();
  active: { key: string; owner: string } | undefined;
  version = 0;
  constructor(private capacity = 64) {}
  subscribe = (listener: () => void) => { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; };
  snapshot = () => this.version;
  image(key: string) { return this.images.get(key); }
  request(key: string, owner: string) {
    if (!this.images.has(key)) { this.requests.push({ key, owner }); this.pump(); }
    return () => {
      this.requests = this.requests.filter(item => item.owner !== owner);
      if (this.active?.owner === owner) { this.active = undefined; this.pump(); }
    };
  }
  finish(key: string, owner: string, image: string) {
    if (this.active?.owner !== owner || this.active.key !== key) return;
    this.images.delete(key); this.images.set(key, image);
    while (this.images.size > this.capacity) this.images.delete(this.images.keys().next().value!);
    this.requests = this.requests.filter(item => item.key !== key);
    this.active = undefined; this.pump();
  }
  private pump() {
    if (!this.active) this.active = this.requests.shift();
    this.version++; this.listeners.forEach(listener => listener());
  }
}
