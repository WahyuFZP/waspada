import type { Metadata } from "next";
import { Barlow_Condensed, IBM_Plex_Mono, Pixelify_Sans, Silkscreen } from "next/font/google";
import "./globals.css";

const display = Barlow_Condensed({ variable: "--font-barlow-condensed", subsets: ["latin"], weight: ["600", "700"] });
// teks informasi bergaya piksel tapi tetap huruf besar-kecil, jadi kalimat panjang masih enak dibaca
const body = Pixelify_Sans({ variable: "--font-pixelify", subsets: ["latin"], weight: ["400", "500", "700"] });
const data = IBM_Plex_Mono({ variable: "--font-plex-mono", subsets: ["latin"], weight: ["400", "500"] });
// font piksel khusus landing (judul, badge, tombol); teks panjang tetap memakai mono agar terbaca
const pixel = Silkscreen({ variable: "--font-silkscreen", subsets: ["latin"], weight: ["400", "700"] });

export const metadata: Metadata = {
  title: "WASPADA",
  description: "Pusat pemantauan isu strategis: korelasi berita dalam dan luar negeri",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="id">
      <body className={`${display.variable} ${body.variable} ${data.variable} ${pixel.variable} antialiased`}>{children}</body>
    </html>
  );
}
