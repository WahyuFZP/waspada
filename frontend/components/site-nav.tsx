import Link from "next/link";
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
export function SiteNav({ active, status, wide = false }: { active?: Halaman; status?: StreamStatus; wide?: boolean }) {
  return (
    <>
      <SignalLines />
      <nav className="sticky top-0 z-30 border-b border-line bg-bg/85 backdrop-blur-md print:hidden">
        {/* ponsel: logo + status di baris atas, menu selebar layar di baris kedua (digulir ke samping);
            md ke atas: satu baris setinggi 16. `order` hanya mengubah letak, urutan baca tetap logo, menu, status */}
        <div className={`mx-auto flex flex-wrap items-center justify-between gap-x-8 gap-y-3 px-4 py-3 md:h-16 md:flex-nowrap md:px-6 md:py-0 ${wide ? "max-w-[1400px]" : "max-w-[1200px]"}`}>
          <Link href="/" className="order-1 flex shrink-0 items-center gap-2 font-pixel text-xl font-bold leading-none">
            <LogoMark className="h-[34px] w-[34px]" />
            WASPADA
          </Link>
          <ul className="font-data order-3 flex w-full min-w-0 gap-6 overflow-x-auto whitespace-nowrap text-xs md:order-2 md:w-auto md:flex-1">
            {MENU.map(([key, href, label]) => (
              <li key={href}>
                <Link href={href} aria-current={active === key ? "page" : undefined}
                  className={active === key ? "text-gold" : "text-ink-muted hover:text-ink"}>
                  {label}
                </Link>
              </li>
            ))}
          </ul>
          {status && (
            <div className="order-2 shrink-0 md:order-3">
              <ConnectionStatus status={status} />
            </div>
          )}
        </div>
      </nav>
    </>
  );
}
