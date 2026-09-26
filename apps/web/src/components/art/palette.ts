/** Colours for each strain. Wild type (Canton-S) is the base; mutants override parts of it. */

export type Strain = "wild" | "white" | "yellow" | "ebony" | "curly" | "vestigial";
export type Sex = "m" | "f";
export type WingType = "normal" | "curly" | "vestigial";

/** [highlight, mid, shade, outline] */
type Ramp = readonly [string, string, string, string];

export interface FlyPalette {
  head: Ramp;
  body: Ramp;
  stripe: string;
  eye: Ramp;
  pupil: string;
  leg: string;
  wings: WingType;
}

const WILD: FlyPalette = {
  head: ["#FBE3B6", "#EDBB76", "#C88A43", "#9C6428"],
  body: ["#F4C98A", "#DC9D52", "#A96A2D", "#8A5422"],
  stripe: "#5E3515",
  eye: ["#FF8C8C", "#E3243C", "#A50E25", "#6E0716"],
  pupil: "#1B0307",
  leg: "#4A2F1C",
  wings: "normal",
};

const OVERRIDES: Record<Strain, Partial<FlyPalette>> = {
  wild: {},
  white: { eye: ["#FFFFFF", "#F4EFE7", "#D8CDBD", "#A89880"], pupil: "#7C6F62" },
  yellow: {
    head: ["#FFF6CF", "#F6DA6A", "#D9B437", "#B08E1E"],
    body: ["#FFF1B8", "#F2D35B", "#CFA92E", "#A8871C"],
    stripe: "#B8862A",
    leg: "#7A5A22",
  },
  ebony: {
    head: ["#A48C77", "#6E5642", "#4A3828", "#2E2016"],
    body: ["#8E735C", "#5A4636", "#3A2B20", "#231810"],
    stripe: "#1A110B",
    leg: "#1E140D",
  },
  curly: { wings: "curly" },
  vestigial: { wings: "vestigial" },
};

export function paletteFor(strain: Strain): FlyPalette {
  return { ...WILD, ...OVERRIDES[strain] };
}

export const STRAIN_LABELS: Record<Strain, { name: string; gene: string; note?: string }> = {
  wild: { name: "野生型", gene: "Canton-S" },
  white: { name: "白い目", gene: "white" },
  yellow: { name: "黄色い体", gene: "yellow" },
  ebony: { name: "黒い体", gene: "ebony" },
  curly: { name: "縮れ羽", gene: "Curly", note: "飛ぶのが苦手" },
  vestigial: { name: "小さな羽", gene: "vestigial", note: "飛べない" },
};
