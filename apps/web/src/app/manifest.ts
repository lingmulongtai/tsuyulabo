import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "ツユラボ",
    short_name: "ツユラボ",
    description: "本物のハエの脳で育つ。毎週1匹、卵から育てる育成研究ゲーム。",
    lang: "ja",
    start_url: "/",
    display: "standalone",
    orientation: "portrait",
    background_color: "#e8f2ef",
    theme_color: "#e8f2ef",
    icons: [{ src: "/icon.svg", sizes: "any", type: "image/svg+xml", purpose: "any" }],
  };
}
