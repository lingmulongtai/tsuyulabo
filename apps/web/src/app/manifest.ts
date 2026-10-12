import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "ツユラボ",
    short_name: "ツユラボ",
    description: "本物のハエの脳で育つ。毎週1匹、卵から育てる飼育ゲーム。",
    lang: "ja",
    start_url: "/",
    display: "standalone",
    orientation: "portrait",
    background_color: "#141310",
    theme_color: "#141310",
    icons: [{ src: "/icon.svg", sizes: "any", type: "image/svg+xml", purpose: "any" }],
  };
}
