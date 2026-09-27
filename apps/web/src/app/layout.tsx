import type { Metadata, Viewport } from "next";
import { IBM_Plex_Mono, Kiwi_Maru, Zen_Maru_Gothic } from "next/font/google";
import "./globals.css";
import { Providers } from "./Providers";

const zenMaru = Zen_Maru_Gothic({
  variable: "--font-zen-maru",
  weight: ["400", "500", "700", "900"],
  subsets: ["latin"],
  preload: false,
});

const kiwiMaru = Kiwi_Maru({
  variable: "--font-kiwi-maru",
  weight: ["400", "500"],
  subsets: ["latin"],
  preload: false,
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  weight: ["400", "500"],
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ツユラボ",
  description: "本物のハエの脳で育つ。毎週1匹、卵から育てる育成研究ゲーム。",
  applicationName: "ツユラボ",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#e8f2ef" },
    { media: "(prefers-color-scheme: dark)", color: "#0f1d1a" },
  ],
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ja" className={`${zenMaru.variable} ${kiwiMaru.variable} ${plexMono.variable} h-full antialiased`}>
      <body className="min-h-full"><Providers>{children}</Providers></body>
    </html>
  );
}
