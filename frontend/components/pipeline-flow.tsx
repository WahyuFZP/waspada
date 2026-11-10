"use client";

import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useEffect, useRef, useState } from "react";
import type { Alert, Event } from "@/lib/types";

// Alur korelasi WASPADA. Setiap event nyata dari stream memunculkan paket Ingest -> Korelasi,
// setiap alert nyata memunculkan paket Korelasi -> Peringatan. Tanpa data baru, alur diam.
const STAGES = [
  { name: "Ingest", desc: "21 media RSS masuk lewat satu pintu" },
  { name: "Normalisasi", desc: "Artikel jadi event: topik & kategori" },
  { name: "Korelasi", desc: "Rangkaian dicocokkan dengan aturan" },
  { name: "Peringatan", desc: "Dashboard & Discord, tanpa refresh" },
];
const X = [12.5, 37.5, 62.5, 87.5]; // pusat tiap tahap dalam persen lebar

type Packet = { id: number; kind: "event" | "alert" };

export function PipelineFlow({ events, alerts, loaded }: { events: Event[]; alerts: Alert[]; loaded: boolean }) {
  const reduce = useReducedMotion();
  const [packets, setPackets] = useState<Packet[]>([]);
  const seen = useRef<{ event?: Event; alert?: Alert } | null>(null);
  const nextId = useRef(0);

  useEffect(() => {
    if (!loaded) return;
    // muatan awal dari REST bukan kejadian baru: catat saja item teratasnya
    const prev = seen.current;
    seen.current = { event: events[0], alert: alerts[0] };
    if (!prev) return;
    // item baru dari stream ditambahkan di depan; posisi item teratas sebelumnya = jumlah yang baru.
    // Tidak ditemukan (-1) berarti daftar dimuat ulang saat menyambung kembali, bukan kejadian baru.
    const fresh = <T,>(list: T[], top?: T) => (top === undefined ? list.length : Math.max(list.indexOf(top), 0));
    const newEvents = Math.min(fresh(events, prev.event), 5);
    const newAlerts = Math.min(fresh(alerts, prev.alert), 3);
    if (reduce || (!newEvents && !newAlerts)) return;
    const add: Packet[] = [
      ...Array.from({ length: newEvents }, () => ({ id: nextId.current++, kind: "event" as const })),
      ...Array.from({ length: newAlerts }, () => ({ id: nextId.current++, kind: "alert" as const })),
    ];
    setPackets((p) => [...p, ...add].slice(-12));
  }, [events, alerts, loaded, reduce]);

  const done = (id: number) => setPackets((p) => p.filter((x) => x.id !== id));

  return (
    <section aria-label="Alur korelasi" className="mx-auto mb-10 max-w-[1400px] px-4 md:px-6">
      <div className="relative">
        {/* rel penghubung antar tahap */}
        <div aria-hidden className="absolute left-[12.5%] right-[12.5%] top-5 h-0.5 -translate-y-1/2 bg-line" />
        <AnimatePresence>
          {packets.map((p, i) => (
            <motion.span
              key={p.id}
              aria-hidden
              className={`absolute top-5 h-2.5 w-2.5 -translate-x-1/2 -translate-y-1/2 ${
                p.kind === "alert" ? "bg-sev-critical" : "bg-gold"
              }`}
              initial={{ left: `${p.kind === "alert" ? X[2] : X[0]}%`, opacity: 0 }}
              animate={{ left: `${p.kind === "alert" ? X[3] : X[2]}%`, opacity: [0, 1, 1, 0] }}
              transition={{ duration: p.kind === "alert" ? 0.9 : 1.6, delay: (i % 5) * 0.18, ease: "easeInOut" }}
              onAnimationComplete={() => done(p.id)}
            />
          ))}
        </AnimatePresence>

        <ol className="relative grid grid-cols-4 gap-2">
          {STAGES.map((s, i) => (
            <li key={s.name} className="flex flex-col items-center text-center">
              <span
                className={`font-pixel relative z-10 flex h-10 w-10 items-center justify-center border-2 text-xs shadow-[3px_3px_0_0_var(--color-line)] ${
                  i === 3 ? "border-gold bg-surface text-gold" : "border-siber bg-surface text-siber-bright"
                }`}
              >
                {String(i + 1).padStart(2, "0")}
              </span>
              <span className="font-display mt-2 text-lg font-semibold leading-tight md:text-xl">{s.name}</span>
              <span className="hidden text-sm text-ink-muted md:block">{s.desc}</span>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
