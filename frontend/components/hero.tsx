"use client";

import { motion } from "motion/react";
import type { StreamStatus } from "@/hooks/use-alert-stream";
import { NetworkGlobe } from "./network-globe";

const rise = (delay: number) => ({
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] as const },
});

export function Hero({ status, pulseKey }: { status: StreamStatus; pulseKey: string | null }) {
  return (
    <section aria-labelledby="hero-title" className="relative isolate overflow-hidden px-4 pb-16 pt-14 md:pb-24 md:pt-20">
      {/* satu glow sebagai titik fokus di belakang judul (disetujui pemilik), hijau perisai Pussiberad */}
      <div
        aria-hidden
        className="absolute left-1/2 top-1/2 -z-10 h-[520px] w-[820px] max-w-[160vw] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(ellipse_at_center,rgba(63,122,64,0.45),transparent_65%)] blur-2xl"
      />
      <motion.div
        aria-hidden
        className="absolute left-1/2 top-1/2 -z-10 aspect-square w-[min(720px,140vw)] -translate-x-1/2 -translate-y-1/2 opacity-80"
        initial={{ opacity: 0, scale: 0.92 }}
        animate={{ opacity: 0.8, scale: 1 }}
        transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
      >
        <NetworkGlobe live={status === "live"} pulseKey={pulseKey} />
      </motion.div>

      <div className="mx-auto max-w-6xl text-center">
        <h1 id="hero-title" className="font-display text-5xl font-bold leading-[0.95] sm:text-6xl md:text-8xl">
          <motion.span className="block" {...rise(0)}>
            Satu kejadian tampak biasa.
          </motion.span>
          <motion.span className="block text-gold" {...rise(0.12)}>
            Rangkaiannya adalah ancaman.
          </motion.span>
        </h1>
        <motion.p className="mx-auto mt-6 max-w-2xl text-base text-ink-muted md:text-lg" {...rise(0.25)}>
          WASPADA mengorelasikan log keamanan satuan, katalog kerentanan yang sedang dieksploitasi (CISA KEV), dan
          pemberitaan dalam serta luar negeri, lalu memberi peringatan otomatis lengkap dengan teknik MITRE ATT&amp;CK,
          sebelum analis harus menyaring ribuan kejadian secara manual.
        </motion.p>
        <motion.div className="mt-8 flex flex-wrap justify-center gap-3" {...rise(0.35)}>
          <a
            href="#pemantauan"
            className="font-data inline-flex min-h-12 items-center rounded-lg bg-gold px-5 text-sm font-medium text-bg transition hover:brightness-110"
          >
            Buka pemantauan langsung
          </a>
          <a
            href="#arus-berita"
            className="font-data inline-flex min-h-12 items-center rounded-lg border border-line bg-white/[0.03] px-5 text-sm transition hover:bg-white/[0.07]"
          >
            Lihat arus berita
          </a>
        </motion.div>
      </div>
    </section>
  );
}
