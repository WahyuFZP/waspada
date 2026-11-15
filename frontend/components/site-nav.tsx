"use client";

import Link from "next/link";
import { useState } from "react";
import { ConnectionStatus } from "@/components/connection-status";
import { LogoMark } from "@/components/logo-mark";
import { SignalLines } from "@/components/signal-lines";
import type { StreamStatus } from "@/hooks/use-alert-stream";

type Halaman = "pemantauan" | "log" | "apk" | "web" | "jadwal";
const MENU: [Halaman | null, string, string][] = [
  ["pemantauan", "/pemantauan", "Pemantauan"],
  [null, "/pemantauan#arus-berita", "Arus kejadian"], // bagian dari halaman pemantauan, bukan halaman sendiri
  ["log", "/log", "Log keamanan"],
  ["apk", "/apk", "Pemeriksa APK"],
  ["web", "/web", "Pemeriksa Web"],
  ["jadwal", "/jadwal", "Penjadwal"],
];

// Satu nav untuk semua halaman SIEM dan pemeriksa. `status` diisi halaman yang membuka aliran SSE (status koneksi
// di kanan); `wide` menyamakan lebar dengan konten halaman SIEM (1400px) vs halaman pemeriksa (1200px).
// Ponsel: tombol menu membuka daftar ke bawah (menu geser ke samping terasa seperti bug); md ke atas: satu baris.
export function SiteNav({ active, status, wide = false }: { active?: Halaman; status?: StreamStatus; wide?: boolean }) {
  const [buka, setBuka] = useState(false);
  const tautan = (cls: string) =>
    MENU.map(([key, href, label]) => (
      <li key={href}>
        <Link href={href} onClick={() => setBuka(false)} aria-current={active === key ? "page" : undefined}
          className={[cls, active === key ? "text-gold" : "text-ink-muted hover:text-ink"].filter(Boolean).join(" ")}>
          {label}
        </Link>
      </li>
    ));

  return (
    <>
      <SignalLines />
      <nav className="sticky top-0 z-30 border-b border-line bg-bg/85 backdrop-blur-md print:hidden">
        <div className={`mx-auto flex h-16 items-center gap-4 px-4 md:gap-8 md:px-6 ${wide ? "max-w-[1400px]" : "max-w-[1200px]"}`}>
          <Link href="/" className="flex shrink-0 items-center gap-2 font-pixel text-xl font-bold leading-none">
            <LogoMark className="h-[34px] w-[34px]" />
            WASPADA
          </Link>
          <ul className="font-data hidden flex-1 gap-6 whitespace-nowrap text-xs md:flex">{tautan("")}</ul>
          <div className="ml-auto flex min-w-0 items-center gap-3">
            {status && (
              <div className="min-w-0 overflow-hidden whitespace-nowrap">
                <ConnectionStatus status={status} />
              </div>
            )}
            <button
              type="button"
              onClick={() => setBuka((b) => !b)}
              aria-expanded={buka}
              aria-controls="menu-ponsel"
              aria-label={buka ? "Tutup menu" : "Buka menu"}
              className="flex h-10 w-10 shrink-0 items-center justify-center border-2 border-line text-ink hover:border-ink-muted md:hidden"
            >
              {/* ikon garis tiga / silang, digambar piksel agar seragam dengan logo */}
              <svg viewBox="0 0 16 16" aria-hidden className="h-4 w-4" shapeRendering="crispEdges" fill="currentColor">
                {buka ? (
                  <path d="M2 3h2v2H2zM4 5h2v2H4zM6 7h4v2H6zM4 9h2v2H4zM2 11h2v2H2zM12 3h2v2h-2zM10 5h2v2h-2zM10 9h2v2h-2zM12 11h2v2h-2z" />
                ) : (
                  <path d="M1 3h14v2H1zM1 7h14v2H1zM1 11h14v2H1z" />
                )}
              </svg>
            </button>
          </div>
        </div>
        {buka && (
          <ul id="menu-ponsel" className="font-data flex flex-col border-t border-line px-4 pb-3 pt-1 text-sm md:hidden">
            {tautan("block py-3")}
          </ul>
        )}
      </nav>
    </>
  );
}
