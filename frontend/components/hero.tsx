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
      {/* latar kisi piksel, seragam dengan landing; menggantikan glow blur. Judul tetap font tegak agar mudah dibaca */}
      <svg aria-hidden className="absolute inset-0 -z-20 h-full w-full" shapeRendering="crispEdges">
        <defs>
          <pattern id="hero-px-grid" width="32" height="32" patternUnits="userSpaceOnUse">
            <rect width="32" height="2" fill="var(--color-surface-2)" />
            <rect width="2" height="32" fill="var(--color-surface-2)" />
            <rect width="4" height="4" fill="var(--color-line)" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#hero-px-grid)" />
      </svg>
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
        <h1 id="hero-title" className="font-body text-3xl font-bold leading-[1.1] sm:text-5xl md:text-6xl">
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
          {/* tombol blok piksel: bayangan offset keras yang kempis saat ditekan (.px-press) */}
          <a
            href="#pemantauan"
            className="px-press font-pixel inline-flex min-h-12 items-center border-2 border-gold bg-gold px-5 text-xs uppercase text-bg shadow-[4px_4px_0_0_var(--color-gold-deep)] hover:brightness-110"
          >
            Buka pemantauan langsung
          </a>
          <a
            href="#arus-berita"
            className="px-block px-press font-pixel inline-flex min-h-12 items-center bg-surface px-5 text-xs uppercase"
          >
            Lihat arus berita
          </a>
        </motion.div>
      </div>
    </section>
  );
}
