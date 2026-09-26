/** JSON contracts shared with the server. Random rewards are not part of verification. */
export type InvalidReason =
  | "not_in_hand" | "already_placed" | "out_of_bounds" | "cell_occupied"
  | "time_exceeded" | "non_monotonic_time" | "wrong_length" | "not_adjacent"
  | "revisit" | "bad_start" | "bad_end" | "checkpoint_order" | "wrong_tap_count";

export type InvalidResult = { readonly valid: false; readonly reason: InvalidReason };
export type VerifyResult<T> = ({ readonly valid: true } & T) | InvalidResult;
export type Ingredient = "banana" | "apple" | "grape" | "yeast" | "agar";
export type Shape =
  | "m1" | "d2h" | "d2v" | "i3h" | "i3v" | "l3a" | "l3b" | "l3c" | "l3d"
  | "o4" | "i4h" | "i4v" | "t4" | "l4" | "s4" | "i5h" | "i5v" | "o9";
export interface MealPiece { readonly shape: Shape; readonly ingredient: Ingredient }
export interface MealParams {
  readonly rows: number;
  readonly cols: number;
  readonly time_limit_ms: number;
  readonly hand_size: number;
  readonly theme: Ingredient;
  readonly pieces: readonly MealPiece[];
}
export interface MealMove {
  readonly p: number;
  readonly r: number;
  readonly c: number;
  readonly t: number;
}
export interface MealSubmission { readonly moves: readonly MealMove[]; readonly elapsed_ms: number }
export interface MealScore {
  readonly score: number;
  readonly lines: number;
  readonly max_combo: number;
  readonly theme_cells: number;
}
export type MealVerifyResult = VerifyResult<MealScore>;

export type Cue = "banana" | "apple_vinegar" | "yeast" | "grape" | "blue_light";
export type Valence = "reward" | "punish";
export type Stars = 1 | 2 | 3;
export interface TrainingParams {
  readonly n: number;
  readonly checkpoints: readonly { readonly cell: number; readonly k: number }[];
  readonly cue: Cue;
  readonly valence: Valence;
}
export interface TrainingSubmission { readonly path: readonly number[]; readonly elapsed_ms: number }
export type TrainingVerifyResult = VerifyResult<{ readonly stars: Stars }>;

export type Grade = "perfect" | "good" | "miss";
export interface CleaningParams {
  readonly period_ms: number;
  readonly taps: number;
  readonly zone: { readonly center: number; readonly perfect: number; readonly good: number };
  readonly phase: number;
}
export interface CleaningSubmission { readonly taps: readonly number[]; readonly elapsed_ms: number }
export type CleaningVerifyResult = VerifyResult<{
  readonly score: number;
  readonly grades: readonly Grade[];
}>;
export interface TemperatureParams {
  readonly period_ms: number;
  readonly center_c: number;
  readonly amp_c: number;
  readonly phase: number;
}
export interface TemperatureSubmission { readonly stop_ms: number; readonly elapsed_ms: number }
export interface TemperatureScore { readonly score: number; readonly grade: Grade }
export type TemperatureVerifyResult = VerifyResult<TemperatureScore>;

export interface PupationSiteParams {
  readonly options: readonly {
    readonly id: string; readonly label: string; readonly detail: string;
  }[];
  readonly hint: string;
}
export interface PupationSiteSubmission { readonly choice: string }
/** Only the server can determine a hit; there is no client-side scoring engine. */
export type PupationSiteVerifyResult = VerifyResult<{ readonly hit: boolean }>;
export interface PuzzleContracts {
  meal: { params: MealParams; submission: MealSubmission; result: MealVerifyResult };
  training: { params: TrainingParams; submission: TrainingSubmission; result: TrainingVerifyResult };
  cleaning: { params: CleaningParams; submission: CleaningSubmission; result: CleaningVerifyResult };
  temperature: {
    params: TemperatureParams; submission: TemperatureSubmission; result: TemperatureVerifyResult;
  };
  pupation_site: {
    params: PupationSiteParams; submission: PupationSiteSubmission; result: PupationSiteVerifyResult;
  };
}
export type PuzzleKind = keyof PuzzleContracts;
