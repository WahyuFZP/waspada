import type { Metadata } from "next";
import { Barlow_Condensed, IBM_Plex_Mono, Public_Sans } from "next/font/google";
import "./globals.css";

const display = Barlow_Condensed({ variable: "--font-barlow-condensed", subsets: ["latin"], weight: ["600", "700"] });
const body = Public_Sans({ variable: "--font-public-sans", subsets: ["latin"], weight: ["400", "500"] });
const data = IBM_Plex_Mono({ variable: "--font-plex-mono", subsets: ["latin"], weight: ["400", "500"] });

export const metadata: Metadata = {
  title: "WASPADA",
  description: "Pusat pemantauan isu strategis: korelasi berita dalam dan luar negeri",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="id">
      <body className={`${display.variable} ${body.variable} ${data.variable} antialiased`}>{children}</body>
    </html>
  );
}
