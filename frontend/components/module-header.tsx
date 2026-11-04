import Link from "next/link";
import { LogoMark } from "@/components/logo-mark";

// nav bersama modul pemeriksa (APK & Web); `active` menyorot modul yang sedang dibuka
export function ModuleHeader({ active }: { active?: "apk" | "web" }) {
  const link = (href: string, label: string, key: "apk" | "web") =>
    `font-data text-xs hover:text-gold ${active === key ? "text-gold" : "text-ink"}`;
  return (
    <nav className="sticky top-0 z-30 border-b border-line bg-bg/85 backdrop-blur-md print:hidden">
      <div className="mx-auto flex h-16 max-w-[1200px] items-center justify-between gap-4 px-4 md:px-6">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2 font-display text-2xl font-bold leading-none">
            <LogoMark className="h-7 w-7" />
            WASPADA
          </Link>
          <Link href="/apk" className={link("/apk", "Pemeriksa APK", "apk")}>
            Pemeriksa APK
          </Link>
          <Link href="/web" className={link("/web", "Pemeriksa Web", "web")}>
            Pemeriksa Web
          </Link>
        </div>
        <Link href="/pemantauan" className="font-data text-xs text-ink-muted hover:text-ink">
          Kembali ke pemantauan
        </Link>
      </div>
    </nav>
  );
}
