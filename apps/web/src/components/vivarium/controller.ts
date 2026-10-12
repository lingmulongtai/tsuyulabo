import { randomSource } from "./random";
import type { Behaviour, Point, Stage, VivariumHandle } from "./types";
import { displayStage } from "./types";

export interface Pose {
  position: [number, number, number];
  heading: number;
  phase: number;
  speed: number;
  groom: number;
  feed: number;
  flight: number;
  burrow: number;
}
const approachAngle = (from: number, to: number, amount: number) =>
  from + Math.atan2(Math.sin(to - from), Math.cos(to - from)) * amount;

/** The decoder owns the action. Randomness only varies posture, heading and timing. */
export class BehaviourController implements VivariumHandle {
  readonly pose: Pose = { position: [0, -0.99, 0.12], heading: -0.55, phase: 0, speed: 0, groom: 0, feed: 0, flight: 0, burrow: 0 };
  private action: Behaviour = "rest";
  private target: Point = [0.65, -1.08, -0.2];
  private random: () => number;
  private remaining = 0;
  private wander = 0;
  private time = 0;
  private flightTimer = 0;
  private flightActive = false;
  private strideVariation = 1;
  constructor(seed = "tsuyu") { this.random = randomSource(seed); this.pose.phase = this.random() * Math.PI * 2; }
  get behaviour(): Behaviour { return this.action; }
  setBehaviour(behaviour: Behaviour) { this.action = behaviour; }
  pointOfInterest(point: Point) {
    if (point.every(Number.isFinite)) this.target = [...point];
  }
  update(delta: number, stage: Stage, reducedMotion = false, canFly = true): Pose {
    if (!Number.isFinite(delta) || delta <= 0) return this.pose;
    const dt = Math.min(delta, 0.05) * (reducedMotion ? 0.35 : 1);
    const p = this.pose;
    const kind = displayStage(stage);
    if (kind === "egg" || kind === "pupa") return p;
    this.time += dt;
    this.remaining -= dt;
    if (this.remaining <= 0) {
      this.remaining = 0.6 + this.random() * 2;
      this.wander = (this.random() - 0.5) * 1.8;
      this.strideVariation = 0.85 + this.random() * 0.3;
    }
    const action = this.action;
    const fleeing = action === "escape" || action === "flee";
    const moving = ["walk", "approach", "avoid", "escape", "flee", "fly"].includes(action);
    let desiredSpeed = moving ? (fleeing ? 0.75 : action === "fly" ? 0.52 : 0.13) : 0;
    let heading = p.heading + this.wander * dt;
    if (action === "approach" || action === "avoid" || fleeing) {
      const dx = this.target[0] - p.position[0], dz = this.target[2] - p.position[2];
      heading = Math.atan2(dx, dz) + (action !== "approach" ? Math.PI : 0);
      if (action === "approach" && Math.hypot(dx, dz) < 0.18) desiredSpeed = 0;
    }
    if (action === "turn_left") heading = p.heading + dt * 1.6;
    if (action === "turn_right") heading = p.heading - dt * 1.6;
    const radius = Math.hypot(p.position[0], p.position[2]);
    const boundary = kind === "adult" ? 0.49 : 0.72;
    if (radius > boundary - 0.1 && Math.sin(heading) * p.position[0] + Math.cos(heading) * p.position[2] > 0)
      heading = Math.atan2(-p.position[0], -p.position[2]);
    const blend = 1 - Math.exp(-dt * 7);
    p.heading = approachAngle(p.heading, heading, action.startsWith("turn_") ? 1 : blend);
    p.speed += (desiredSpeed * this.strideVariation * (kind === "larva" ? 0.3 : 1) - p.speed) * blend;
    p.position[0] += Math.sin(p.heading) * p.speed * dt;
    p.position[2] += Math.cos(p.heading) * p.speed * dt;
    const r = Math.hypot(p.position[0], p.position[2]);
    if (r > boundary) { p.position[0] *= boundary / r; p.position[2] *= boundary / r; }
    p.groom += ((action === "groom" ? 1 : 0) - p.groom) * blend;
    p.feed += ((action === "feed" ? 1 : 0) - p.feed) * blend;
    // Flights land between bursts; this is motor realization, not a new brain decision.
    if (canFly && kind === "adult" && (action === "fly" || fleeing)) {
      this.flightTimer -= dt;
      if (this.flightTimer <= 0) {
        this.flightActive = !this.flightActive;
        this.flightTimer = (this.flightActive ? 0.65 : 0.4) + this.random() * 1.7;
      }
    } else { this.flightActive = false; this.flightTimer = 0; }
    const airborne = this.flightActive;
    p.flight += ((airborne ? 1 : 0) - p.flight) * (1 - Math.exp(-dt * 2.5));
    p.burrow += ((kind === "larva" && (action === "burrow" || action === "feed") ? 1 : 0) - p.burrow) * blend;
    p.position[1] = -0.99 + p.flight * (0.65 + Math.sin(this.time * 1.4) * 0.2) - p.burrow * 0.1;
    p.phase += dt * (kind === "larva" ? 3 : 4 + p.speed * 32);
    return p;
  }
}
