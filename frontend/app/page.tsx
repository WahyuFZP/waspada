"use client";

import { motion } from "motion/react";
import Link from "next/link";
import { CrtBackground } from "@/shaders/crt/CrtBackground";

const rise = (delay: number) => ({
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] as const },
});

const MODULES = [
  {
    href: "/pemantauan",
    title: "Pemantauan SIEM",
    desc: "Korelasi OSINT berita, log keamanan, dan intel ancaman CISA KEV menjadi peringatan dini.",
  },
  {
    href: "/apk",
    title: "Pemeriksa APK",
    desc: "Analisis statis file APK untuk mendeteksi ciri pencuri OTP dan banking trojan sebelum dipasang.",
  },
];

export default function Boot() {
  return (
    <main className="relative min-h-dvh overflow-hidden">
      {/* latar CRT terminal (ThreeUI), dekoratif */}
      <div aria-hidden className="fixed inset-0 -z-10">
        <CrtBackground
          variant="terminal"
          speed={1.0}
          typeSpeed={1.0}
          motion={1.0}
          hue={0}
          saturation={1.0}
          brightness={1.0}
          opacity={1.0}
        />
        {/* scrim agar teks terbaca di atas phosphor yang terang */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(7,13,8,0.55),rgba(7,13,8,0.9))]" />
      </div>

      <div className="relative mx-auto flex min-h-dvh max-w-3xl flex-col items-center justify-center gap-8 px-4 py-16 text-center">
        <motion.div {...rise(0)}>
          <p className="font-data text-xs uppercase tracking-[0.3em] text-siber-bright">Pusat Siber</p>
          <h1 className="font-display mt-2 text-6xl font-bold leading-none md:text-8xl">WASPADA</h1>
          <p className="mt-4 max-w-xl text-ink-muted md:text-lg">
            Deteksi dini ancaman siber dari pemberitaan, log keamanan satuan, hingga aplikasi berbahaya. Pilih modul
            untuk mulai.
          </p>
        </motion.div>

        <motion.ul className="grid w-full gap-4 sm:grid-cols-2" {...rise(0.2)}>
          {MODULES.map((m) => (
            <li key={m.href}>
              <Link
                href={m.href}
                className="group flex h-full flex-col gap-2 rounded-2xl border border-line bg-bg/70 p-5 text-left backdrop-blur-sm transition-colors hover:border-gold hover:bg-bg/85"
              >
                <span className="font-display text-2xl font-semibold">{m.title}</span>
                <span className="text-sm text-ink-muted">{m.desc}</span>
                <span className="font-data mt-auto pt-2 text-xs text-gold opacity-0 transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100">
                  Masuk →
                </span>
              </Link>
            </li>
          ))}
        </motion.ul>

        <motion.p className="font-data text-xs text-ink-muted" {...rise(0.35)}>
          Data demo bersifat sintetis atau berasal dari sumber publik. Murni pemantauan, bukan alat ofensif.
        </motion.p>
      </div>
    </main>
  );
}
