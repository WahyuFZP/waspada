"use client";

import { animate, createScope, scrambleText, stagger } from "animejs";
import { motion } from "motion/react";
import Link from "next/link";
import { useEffect, useRef } from "react";
import { LogoMark } from "@/components/logo-mark";
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
];

// ringkasan gaya agen Wazuh (Total/Aktif/Terputus); angkanya menggambarkan ilustrasi di sebelahnya, bukan data langsung
const TALLY = [
  { n: 6, label: "Perangkat dipantau", tone: "text-ink" },
  { n: 5, label: "Aman", tone: "text-siber-bright" },
  { n: 1, label: "Perlu dicek", tone: "text-sev-critical" },
];

export default function Boot() {
  const root = useRef<HTMLElement>(null);

  useEffect(() => {
    const scope = createScope({ root, mediaQueries: { reduce: "(prefers-reduced-motion: reduce)" } }).add((self) => {
      if (self?.matches.reduce) return;
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
    return () => scope.revert();
  }, []);

  return (
    <main ref={root} className="relative min-h-dvh overflow-hidden">
      {/* latar tenang: kisi titik halus + dua cahaya lembut, menggantikan CRT yang terlalu ramai */}
      <div aria-hidden className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-[radial-gradient(var(--color-line)_1px,transparent_1px)] [background-size:24px_24px] [mask-image:radial-gradient(ellipse_at_center,black,transparent_75%)]" />
        <div className="absolute -left-40 -top-40 h-[480px] w-[480px] rounded-full bg-siber/20 blur-3xl" />
        <div className="absolute -bottom-48 -right-40 h-[520px] w-[520px] rounded-full bg-gold/10 blur-3xl" />
      </div>

      <div className="relative mx-auto grid min-h-dvh max-w-6xl items-center gap-10 px-4 py-16 md:px-6 lg:grid-cols-[1fr_minmax(0,480px)]">
        <div className="flex flex-col gap-8">
          <motion.div {...rise(0)}>
            <p className="font-data inline-flex items-center gap-2 rounded-full border border-line bg-surface/70 px-3 py-1 text-xs text-ink-muted">
              <span className="relative flex h-2 w-2">
                <span aria-hidden className="live-dot absolute inset-0 rounded-full bg-siber-bright" />
                <span className="relative h-2 w-2 rounded-full bg-siber-bright" />
              </span>
              Pusat Siber · sistem aktif
            </p>
            <LogoMark className="mt-4 h-16 w-16" />
            <h1 className="title font-display mt-3 text-6xl font-bold leading-none md:text-8xl">WASPADA</h1>
            <p className="font-data mt-2 text-xs tracking-wide text-siber-bright">
              Wide-Area Signal Processing for Alerting and Domain Awareness
            </p>
            <p className="mt-4 max-w-xl text-ink-muted md:text-lg">
              Teman jaga keamanan digital satuan. Kami pantau kabar ancaman dan bantu memeriksa aplikasi mencurigakan,
              supaya Anda bisa bertindak <span className="text-gold">sebelum</span> terlambat.
            </p>
          </motion.div>

          <motion.ul className="grid gap-4 sm:grid-cols-2" {...rise(0.2)}>
            {MODULES.map((m) => (
              <li key={m.href}>
                <Link
                  href={m.href}
                  className="group flex h-full flex-col gap-3 rounded-2xl border border-line bg-surface/80 p-5 backdrop-blur-sm transition-[border-color,background-color,transform] duration-300 hover:-translate-y-1 hover:border-gold hover:bg-surface"
                >
                  <span className="flex flex-col items-start gap-3">
                    <span className="grid h-10 w-10 place-items-center rounded-xl border border-line bg-surface-2 text-gold">
                      <svg aria-hidden viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                        <path d={m.icon} />
                      </svg>
                    </span>
                    <span>
                      <span className="font-display block text-2xl font-semibold leading-tight">{m.title}</span>
                      <span className="font-data block text-[11px] text-ink-muted">{m.tag}</span>
                    </span>
                  </span>
                  <span className="text-sm text-ink-muted">{m.desc}</span>
                  <span className="font-data mt-auto pt-1 text-xs text-gold">
                    Masuk <span className="inline-block transition-transform group-hover:translate-x-1">→</span>
                  </span>
                </Link>
              </li>
            ))}
          </motion.ul>

          <motion.p className="font-data text-xs text-ink-muted" {...rise(0.35)}>
            Data demo bersifat sintetis atau berasal dari sumber publik. Murni pemantauan, bukan alat ofensif.
          </motion.p>
        </div>

        <motion.figure className="rounded-2xl border border-line bg-surface/60 p-4 backdrop-blur-sm" {...rise(0.15)}>
          <NetworkScan />
          <figcaption className="mt-3 grid grid-cols-3 gap-2 border-t border-line pt-3 text-center">
            {TALLY.map((t) => (
              <span key={t.label}>
                <span data-n={t.n} className={`tally-n font-display block text-3xl font-bold ${t.tone}`}>
                  {t.n}
                </span>
                <span className="font-data text-[11px] text-ink-muted">{t.label}</span>
              </span>
            ))}
          </figcaption>
        </motion.figure>
      </div>
    </main>
  );
}
