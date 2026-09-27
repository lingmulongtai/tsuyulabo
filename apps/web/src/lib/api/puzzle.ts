import type { PuzzleContracts, PuzzleKind } from "@/game/puzzles/types";
import { SHAPES } from "@/game/puzzles/meal";
import { ApiError } from "./client";

const record = (value: unknown): value is Record<string, unknown> => Boolean(value) && typeof value === "object" && !Array.isArray(value);
const finite = (value: unknown): value is number => typeof value === "number" && Number.isFinite(value);
const positive = (value: unknown): value is number => finite(value) && value > 0;
const integer = (value: unknown): value is number => positive(value) && Number.isInteger(value);

/** Narrow the unstructured params in the exported API at the game boundary. */
export function puzzleParams<K extends PuzzleKind>(kind: K, value: unknown): PuzzleContracts[K]["params"] {
  let valid = false;
  if (record(value)) {
    switch (kind) {
      case "meal": {
        const ingredients = ["banana", "apple", "grape", "yeast", "agar"];
        valid = integer(value.rows) && value.rows <= 12 && integer(value.cols) && value.cols <= 12 &&
          positive(value.time_limit_ms) && integer(value.hand_size) && ingredients.includes(String(value.theme)) &&
          Array.isArray(value.pieces) && value.pieces.length > 0 && value.pieces.every(p => record(p) &&
            typeof p.shape === "string" && Object.hasOwn(SHAPES, p.shape) && ingredients.includes(String(p.ingredient)));
        break;
      }
      case "cleaning":
        valid = positive(value.period_ms) && value.taps === 3 && finite(value.phase) && record(value.zone) &&
          finite(value.zone.center) && value.zone.center >= 0 && value.zone.center <= 1 &&
          positive(value.zone.perfect) && positive(value.zone.good) && value.zone.perfect <= value.zone.good;
        break;
      case "temperature":
        valid = positive(value.period_ms) && finite(value.phase) && finite(value.center_c) && positive(value.amp_c);
        break;
      case "pupation_site":
        valid = typeof value.hint === "string" && Array.isArray(value.options) && value.options.length === 3 &&
          value.options.every(p => record(p) && typeof p.id === "string" && typeof p.label === "string" && typeof p.detail === "string");
        break;
      case "training":
        valid = integer(value.n) && value.n <= 6 && Array.isArray(value.checkpoints) && value.checkpoints.length > 1 &&
          value.checkpoints.every(p => record(p) && finite(p.cell) && integer(p.k)) &&
          ["banana", "apple_vinegar", "yeast", "grape", "blue_light"].includes(String(value.cue)) && ["reward", "punish"].includes(String(value.valence));
    }
  }
  if (!valid) throw new ApiError(502, "invalid_response", "問題を読み取れませんでした。ホームから開き直してください。");
  return value as unknown as PuzzleContracts[K]["params"];
}
