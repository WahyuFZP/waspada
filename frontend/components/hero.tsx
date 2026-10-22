"use client";

import { motion } from "motion/react";
import type { StreamStatus } from "@/hooks/use-alert-stream";

const rise = (delay: number) => ({
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] as const },
});

export function Hero({ status }: { status: StreamStatus }) {
  return (
    <section aria-labelledby="hero-title" className="relative isolate overflow-hidden px-4 pb-16 pt-14 md:pb-24 md:pt-20">
      {/* satu glow sebagai titik fokus di belakang judul (disetujui pemilik, warna TNI-AD) */}
      <div
        aria-hidden
        className="absolute left-1/2 top-1/2 -z-10 h-[520px] w-[820px] max-w-[160vw] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(ellipse_at_center,rgba(75,83,32,0.55),transparent_65%)] blur-2xl"
      />
      <div
        aria-hidden
        className={`radar absolute left-1/2 top-1/2 -z-10 aspect-square w-[min(720px,140vw)] -translate-x-1/2 -translate-y-1/2 ${
          status === "live" ? "is-live" : ""
        }`}
      >
        <div className="absolute inset-0 rounded-full border border-army/40" />
        <div className="absolute inset-[18%] rounded-full border border-army/30" />
        <div className="absolute inset-[36%] rounded-full border border-dashed border-army/30" />
        <div className="radar-ping absolute inset-[18%] rounded-full border border-gold/40 opacity-0" />
        <div className="radar-sweep absolute inset-0 rounded-full bg-[conic-gradient(from_0deg,rgba(212,167,44,0.18),transparent_18%)]" />
      </div>

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
