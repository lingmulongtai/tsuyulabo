import type { Metadata, Viewport } from "next";
import { IBM_Plex_Mono, Noto_Serif_JP, Noto_Sans_JP } from "next/font/google";
import "./globals.css";
import { Providers } from "./Providers";

const notoSans = Noto_Sans_JP({
  variable: "--font-noto-sans",
  weight: ["400", "500", "700"],
  subsets: ["latin"],
  preload: false,
});

const notoSerif = Noto_Serif_JP({
  variable: "--font-noto-serif",
  weight: ["500"],
  subsets: ["latin"],
  display: "swap",
  preload: false,
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  weight: ["400", "500"],
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ツユラボ",
  description: "手のひらの小さな命を、本当に育てている。ごはんを作り、しつけ、世代をつなぐ飼育ゲーム。",
  applicationName: "ツユラボ",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#141310" },
    { media: "(prefers-color-scheme: dark)", color: "#141310" },
  ],
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ja" className={`${notoSans.variable} ${notoSerif.variable} ${plexMono.variable} h-full antialiased`}>
      <body className="min-h-full"><Providers>{children}</Providers></body>
    </html>
  );
}
