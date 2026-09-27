import type { Cue, Ingredient, Valence } from "./puzzles/types";

export const INGREDIENT_INFO: Record<Ingredient, { name: string; color: string; shade: string }> = {
  banana: { name: "バナナ", color: "#F2C94C", shade: "#C99A1C" },
  apple: { name: "りんご", color: "#E5484D", shade: "#A92A2F" },
  grape: { name: "ぶどう", color: "#8E6BD8", shade: "#5E43A3" },
  yeast: { name: "酵母", color: "#E6D5B4", shade: "#B09A6E" },
  agar: { name: "寒天", color: "#9ED8E6", shade: "#5FA5B6" },
};

export const CUE_INFO: Record<Cue, { name: string; short: string; kind: "odor" | "light" }> = {
  banana: { name: "バナナの匂い", short: "バナナ", kind: "odor" },
  apple_vinegar: { name: "りんご酢の匂い", short: "りんご酢", kind: "odor" },
  yeast: { name: "酵母の匂い", short: "酵母", kind: "odor" },
  grape: { name: "ぶどうの匂い", short: "ぶどう", kind: "odor" },
  blue_light: { name: "青い光の合図", short: "青い光", kind: "light" },
};

export const VALENCE_INFO: Record<Valence, { name: string; effect: string }> = {
  reward: { name: "あまいごほうび", effect: "が好きになる" },
  punish: { name: "にがいごはん", effect: "が苦手になる" },
};
