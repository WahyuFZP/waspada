"use client";

import { motion, MotionConfig } from "motion/react";
import { useCallback, useState } from "react";
import { AlertDetail } from "@/components/alert-detail";
import { AlertList } from "@/components/alert-list";
import { ConnectionStatus } from "@/components/connection-status";
import { CriticalToast } from "@/components/critical-toast";
import { Hero } from "@/components/hero";
import { NewsFeed } from "@/components/news-feed";
import { PipelineFlow } from "@/components/pipeline-flow";
import { StatsBar } from "@/components/stats-bar";
import { useAlertStream } from "@/hooks/use-alert-stream";
import { API } from "@/lib/api";
import type { Alert } from "@/lib/types";

export default function Dashboard() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [toast, setToast] = useState<Alert | null>(null);
  const [freshIds, setFreshIds] = useState<Set<string>>(new Set());
  const [pulseKey, setPulseKey] = useState<string | null>(null); // alert terbaru dari stream -> denyut inti jaring

  const { alerts, events, status, loaded } = useAlertStream((a) => {
    setFreshIds((prev) => new Set(prev).add(a.id));
    setPulseKey(a.id);
    if (a.severity === "critical") setToast(a);
  });

  const open = useCallback((id: string) => {
    setToast(null);
    setSelectedId(id);
  }, []);
  const close = useCallback(() => setSelectedId(null), []);
  const dismissToast = useCallback(() => setToast(null), []);
  const selected = alerts.find((a) => a.id === selectedId) ?? null;
  const live = status === "live";

  return (
    <MotionConfig reducedMotion="user">
      <div inert={selected !== null}>
        <nav className="sticky top-0 z-30 border-b border-line bg-bg/85 backdrop-blur-md">
          <div className="mx-auto flex h-16 max-w-[1400px] items-center justify-between gap-4 px-4 md:px-6">
            <div className="flex items-center gap-8">
              <a href="#" className="font-display text-2xl font-bold leading-none">
                WASPADA
              </a>
              <ul className="font-data hidden gap-6 text-xs text-ink-muted sm:flex">
                <li>
                  <a href="#pemantauan" className="hover:text-ink">
                    Pemantauan
                  </a>
                </li>
                <li>
                  <a href="#arus-berita" className="hover:text-ink">
                    Arus kejadian
                  </a>
                </li>
              </ul>
            </div>
            <ConnectionStatus status={status} />
          </div>
        </nav>

        <Hero status={status} pulseKey={pulseKey} />

        <PipelineFlow events={events} alerts={alerts} loaded={loaded} />

        <section
          id="pemantauan"
          aria-label="Pemantauan langsung"
          className="mx-auto mb-16 max-w-[1400px] px-4 md:px-6"
        >
          {/* muncul sekali saat digulir ke layar: mengarahkan mata dari alur korelasi ke panel */}
          <motion.div
            initial={{ opacity: 0, y: 32 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.1 }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            className="overflow-hidden rounded-2xl border border-line bg-surface shadow-[0_30px_80px_-30px_rgba(0,0,0,0.8)]"
          >
            {/* bingkai jendela gaya template (disetujui pemilik); status di kanan mencerminkan koneksi SSE nyata */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-4 py-3 md:px-5">
              <div className="flex items-center gap-4">
                <span aria-hidden className="flex gap-1.5">
                  <span className="h-3 w-3 rounded-full bg-[#5a2b2b]" />
                  <span className="h-3 w-3 rounded-full bg-[#5a4d26]" />
                  <span className="h-3 w-3 rounded-full bg-[#2f4a2a]" />
                </span>
                <span className="font-data text-xs text-ink-muted">
                  waspada <span aria-hidden>/</span> <span className="text-ink">pemantauan_isu</span>
                </span>
              </div>
              <span
                className={`font-data rounded-md border px-2.5 py-1 text-[11px] uppercase tracking-[0.12em] ${
                  live ? "border-siber bg-siber/30 text-ink" : "border-sev-critical/50 bg-sev-critical/10 text-sev-critical"
                }`}
              >
                {live ? "Pemantauan aktif" : "Pemantauan terputus"}
              </span>
            </div>

            <div className="flex flex-col gap-6 p-4 md:p-6">
              {status === "reconnecting" && !loaded && (
                <p role="alert" className="rounded-lg border border-sev-critical/50 bg-sev-critical/10 p-4 text-sm">
                  Server pemantauan di <span className="font-data">{API}</span> belum dapat dijangkau. Mohon pastikan
                  backend aktif (<span className="font-data">docker compose up</span>). Sistem akan menyambung ulang
                  secara otomatis.
                </p>
              )}

              <StatsBar alerts={alerts} events={events} />

              <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_400px]">
                <AlertList alerts={alerts} loaded={loaded} freshIds={freshIds} onOpen={open} />
                <NewsFeed events={events} loaded={loaded} />
              </div>
            </div>
          </motion.div>
        </section>

        <footer className="font-data border-t border-line px-4 py-6 text-center text-xs text-ink-muted">
          WASPADA · Data demo bersifat sintetis atau berasal dari RSS publik. Murni pemantauan, bukan alat ofensif.
        </footer>
      </div>

      <AlertDetail alert={selected} onClose={close} />
      <CriticalToast alert={selected ? null : toast} onOpen={open} onDismiss={dismissToast} />
    </MotionConfig>
  );
}
