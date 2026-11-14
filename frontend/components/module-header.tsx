import Link from "next/link";
import { LogoMark } from "@/components/logo-mark";
import { SignalLines } from "@/components/signal-lines";

type Modul = "apk" | "web" | "inventaris" | "jadwal";
const MODUL: [Modul, string, string][] = [
  ["apk", "/apk", "Pemeriksa APK"],
  ["web", "/web", "Pemeriksa Web"],
  ["inventaris", "/inventaris", "Inventaris Aset"],
  ["jadwal", "/jadwal", "Penjadwal"],
];

// nav bersama modul pemeriksa; latar sinyal dipasang di sini sekali untuk semua halaman modul
export function ModuleHeader({ active }: { active?: Modul }) {
  return (
    <>
      <SignalLines />
      <nav className="sticky top-0 z-30 border-b border-line bg-bg/85 backdrop-blur-md print:hidden">
        <div className="mx-auto flex h-16 max-w-[1200px] items-center justify-between gap-4 px-4 md:px-6">
          <div className="flex min-w-0 items-center gap-6">
            <Link href="/" className="flex shrink-0 items-center gap-2 font-pixel text-xl font-bold leading-none">
              <LogoMark className="h-[34px] w-[34px]" />
              WASPADA
            </Link>
            {/* layar sempit: menu digulir ke samping, bukan meluber keluar halaman */}
            <div className="flex min-w-0 gap-5 overflow-x-auto whitespace-nowrap">
              {MODUL.map(([key, href, label]) => (
                <Link key={key} href={href}
                  className={`font-data text-xs hover:text-gold ${active === key ? "text-gold" : "text-ink"}`}>
                  {label}
                </Link>
              ))}
            </div>
          </div>
          <Link href="/pemantauan" className="hidden shrink-0 font-data text-xs text-ink-muted hover:text-ink md:inline">
            Kembali ke pemantauan
          </Link>
        </div>
      </nav>
    </>
  );
}
