"use client";

import { animate, createScope, scrambleText, stagger } from "animejs";
import { motion, useReducedMotion, useScroll, useSpring, useTransform, useVelocity } from "motion/react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Kentongan3D } from "@/components/objects-3d";
import { SignalLines } from "@/components/signal-lines";
import { NetworkScan } from "@/components/network-scan";

const rise = (delay: number) => ({
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] as const },
});

// ikon garis sederhana gaya kartu modul Wazuh
const ICONS = {
  radar: "M12 3a9 9 0 1 0 9 9M12 7a5 5 0 1 0 5 5M12 12l6-6",
  phone: "M8 2h8a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zM11 18h2M9 9l2 2 4-4",
  globe: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18M3.5 9h17M3.5 15h17M12 3c-2.5 2.6-2.5 15.4 0 18M12 3c2.5 2.6 2.5 15.4 0 18",
  clock: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18M12 7v5l3.5 2",
};

const MODULES = [
  {
    href: "/pemantauan",
    icon: ICONS.radar,
    title: "Pemantauan SIEM",
    tag: "Untuk analis & piket siber",
    desc: "Menggabungkan berita, log keamanan, dan daftar celah yang sedang dieksploitasi menjadi peringatan dini yang mudah dibaca.",
  },
  {
    href: "/apk",
    icon: ICONS.phone,
    title: "Pemeriksa APK",
    tag: "Untuk semua personel",
    desc: "Ragu dengan file aplikasi kiriman di WhatsApp? Unggah di sini sebelum dipasang. Kami periksa tanpa menjalankannya.",
  },
  {
    href: "/web",
    icon: ICONS.globe,
    title: "Pemeriksa Web",
    tag: "Untuk pemilik & pengembang situs",
    desc: "Periksa kelemahan keamanan aplikasi web Anda sendiri — header, TLS, cookie, berkas terekspos. Pasif, dengan izin, disertai saran perbaikan.",
  },
  {
    href: "/jadwal",
    icon: ICONS.clock,
    title: "Penjadwal Re-scan",
    tag: "Untuk pemilik & pengelola",
    desc: "Pindai ulang aset web Anda secara berkala dan dapatkan tanda bila keamanannya memburuk sejak pemeriksaan terakhir.",
  },
];

// ringkasan gaya agen Wazuh (Total/Aktif/Terputus); angkanya menggambarkan ilustrasi di sebelahnya, bukan data langsung.
// Gaya piksel: warna hanya untuk severity, sisanya abu-abu.
const TALLY = [
  { n: 6, label: "Perangkat dipantau", tone: "text-ink" },
  { n: 5, label: "Aman", tone: "text-ink-muted" },
  { n: 1, label: "Perlu dicek", tone: "text-sev-critical", critical: true },
];

// Kentongan berayun ke kanan-kiri saat digulir, seperti gantungan kunci: kecepatan gulir mendorongnya, pegas lembek
// membuatnya bergoyang beberapa kali dari gantungannya lalu diam. Tidak naik-turun. Diam di layar kecil & reduce motion.
function useKentonganScroll() {
  const reduce = useReducedMotion();
  const [desktop, setDesktop] = useState(false);
  useEffect(() => {
    const mq = matchMedia("(min-width: 768px)");
    const sync = () => setDesktop(mq.matches);
    sync();
    mq.addEventListener("change", sync);
    return () => mq.removeEventListener("change", sync);
  }, []);
  const { scrollY } = useScroll();
  const push = useTransform(useVelocity(scrollY), [-700, 0, 700], [-24, 0, 24], { clamp: true });
  const rotate = useSpring(push, { stiffness: 70, damping: 4, mass: 0.9 });
  return desktop && !reduce ? { rotate, originX: 0.5, originY: 0 } : undefined;
}

export default function Boot() {
  const root = useRef<HTMLElement>(null);
  const kentongan = useKentonganScroll();

  useEffect(() => {
    let scope: ReturnType<typeof createScope> | undefined;
    // dibuat di frame pertama: hitung naik dimulai dari 0, jadi bila browser belum menggambar, angka asli tetap tampil
    const id = requestAnimationFrame(() => {
      scope = createScope({
        root,
        mediaQueries: { reduce: "(prefers-reduced-motion: reduce)", small: "(max-width: 767px)" },
      }).add((self) => {
        if (self?.matches.reduce || self?.matches.small) return; // layar kecil & reduce motion: diam dan terbaca
        animate(".title", { innerHTML: scrambleText({ chars: "uppercase" }), duration: 1100, delay: 200 });
        animate(".tally-n", {
          innerHTML: [0, (el: unknown) => Number((el as HTMLElement).dataset.n)],
          modifier: (v: number) => Math.round(v),
          duration: 1400,
          delay: stagger(150, { start: 600 }),
          ease: "outExpo",
        });
        animate(".live-dot", { scale: [1, 2.4], opacity: [0.7, 0], duration: 1600, loop: true, ease: "outQuad" });
      });
    });
    return () => {
      cancelAnimationFrame(id);
      scope?.revert();
    };
  }, []);

  return (
    <main ref={root} className="relative min-h-dvh overflow-hidden">
      {/* latar: kisi piksel kasar, garis 2px tiap 32px, tanpa blur atau gradasi */}
      <svg aria-hidden className="fixed inset-0 -z-10 h-full w-full" shapeRendering="crispEdges">
        <defs>
          <pattern id="px-grid" width="32" height="32" patternUnits="userSpaceOnUse">
            <rect width="32" height="2" fill="var(--color-surface-2)" />
            <rect width="2" height="32" fill="var(--color-surface-2)" />
            <rect width="4" height="4" fill="var(--color-line)" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#px-grid)" />
      </svg>
      <div className="hidden md:block">
        <SignalLines />
      </div>

      <div className="relative mx-auto grid min-h-dvh max-w-6xl items-center gap-10 px-4 py-16 md:px-6 lg:grid-cols-[1fr_minmax(0,480px)]">
        <div className="flex min-w-0 flex-col gap-8">
          <motion.div {...rise(0)}>
            <p className="font-pixel inline-flex items-center gap-2 border-2 border-line bg-surface px-3 py-1 text-[11px] uppercase text-ink-muted">
              <span className="relative flex h-2 w-2">
                <span aria-hidden className="live-dot absolute inset-0 bg-ink" />
                <span className="relative h-2 w-2 bg-ink" />
              </span>
              Pusat Siber · sistem aktif
            </p>
            <motion.div className="mt-4 h-28 w-28 md:h-32 md:w-32" style={kentongan}>
              <Kentongan3D className="h-full w-full" />
            </motion.div>
            <h1 className="font-pixel mt-3 text-4xl font-bold leading-none md:text-6xl">
              <span className="title">WASPADA</span>
              <span aria-hidden className="px-cursor ml-1 inline-block h-[0.8em] w-[0.45em] translate-y-[0.05em] bg-ink" />
            </h1>
            <p className="font-data mt-3 text-xs tracking-wide text-ink-muted">
              Wide-Area Signal Processing for Alerting and Domain Awareness
            </p>
            <p className="mt-4 max-w-xl text-base text-ink-muted md:text-lg">
              Teman jaga keamanan digital satuan. Kami pantau kabar ancaman dan bantu memeriksa aplikasi mencurigakan,
              supaya Anda bisa bertindak <span className="font-pixel text-ink">sebelum</span> terlambat.
            </p>
          </motion.div>

          <motion.ul className="grid gap-5 sm:grid-cols-2" {...rise(0.2)}>
            {MODULES.map((m) => (
              <li key={m.href}>
                <Link href={m.href} className="px-block px-press group flex h-full flex-col gap-3 bg-surface p-5">
                  <span className="flex flex-col items-start gap-3">
                    <span className="grid h-10 w-10 place-items-center border-2 border-line bg-surface-2 text-ink">
                      <svg aria-hidden viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="square" strokeLinejoin="miter">
                        <path d={m.icon} />
                      </svg>
                    </span>
                    <span>
                      <span className="font-pixel block text-lg leading-tight">{m.title}</span>
                      <span className="font-data block text-[11px] text-ink-muted">{m.tag}</span>
                    </span>
                  </span>
                  <span className="text-base text-ink-muted">{m.desc}</span>
                  <span className="font-pixel mt-auto self-start border-2 border-ink bg-ink px-3 py-1 text-[11px] uppercase text-bg">
                    Masuk →
                  </span>
                </Link>
              </li>
            ))}
          </motion.ul>

          <motion.p className="text-base text-ink-muted" {...rise(0.35)}>
            Data demo bersifat sintetis atau berasal dari sumber publik. Murni pemantauan, bukan alat ofensif.
          </motion.p>
        </div>

        <motion.figure className="px-block min-w-0 bg-surface p-4" {...rise(0.15)}>
          <NetworkScan />
          <figcaption className="mt-3 grid grid-cols-3 gap-2 border-t-2 border-line pt-3 text-center">
            {TALLY.map((t) => (
              <span key={t.label}>
                <span data-n={t.n} className={`tally-n font-pixel block text-2xl font-bold ${t.tone}`}>
                  {t.n}
                </span>
                <span className="font-data inline-flex items-center gap-1 text-[11px] text-ink-muted">
                  {"critical" in t && <span aria-hidden className="px-pulse h-2 w-2 bg-sev-critical" />}
                  {t.label}
                </span>
              </span>
            ))}
          </figcaption>
        </motion.figure>
      </div>
    </main>
  );
}
