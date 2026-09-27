export const SCENARIOS = {
  sugar: "砂糖をあげる",
  bitter: "苦いものをあげる",
  "sugar+bitter": "砂糖と苦いもの",
  looming: "影を近づける",
  light_left: "左から光をあてる",
  light_right: "右から光をあてる",
  antenna_touch: "触角にふれる",
  liked_odor: "バナナの匂い（好きの観察）",
  disliked_odor: "バナナの匂い（苦手の観察）",
  rest: "そっと見守る",
} as const;

export type Scenario = keyof typeof SCENARIOS;
export type GroupKind = "sensory" | "inter" | "output" | "modulatory";
export interface ActivityGroup {
  name: string;
  kind: GroupKind;
  circuit: string;
  rates: number[];
}
export interface ActivityEdge {
  pre_group: string;
  post_group: string;
  weight_sum: number;
  sign: "excitatory" | "inhibitory";
}
export interface BrainActivity {
  groups: ActivityGroup[];
  edges: ActivityEdge[];
  scenario: Scenario;
  duration_ms: number;
}

export const CIRCUITS: Record<string, string> = {
  feeding: "食べる",
  escape: "逃げる",
  steering: "歩く・曲がる",
  grooming: "身づくろい",
  olfaction_mb: "匂いと学習",
};

// Generic model populations must not receive the badge for named biological cell types.
export const REAL_NAMES = new Set([
  "Gr64f", "Gr66a", "MN9", "LPLC2", "LC4", "DNp01", "DNa02_L", "DNa02_R",
  "JO", "aDN", "ORN", "PN", "KC", "APL", "MBON_ap", "MBON_av", "PAM", "PPL1",
]);
