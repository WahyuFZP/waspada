"use client";

import { MotionConfig } from "motion/react";
import { useCallback, useState } from "react";
import { AlertDetail } from "@/components/alert-detail";
import { AlertList } from "@/components/alert-list";
import { ConnectionStatus } from "@/components/connection-status";
import { CriticalToast } from "@/components/critical-toast";
import { NewsFeed } from "@/components/news-feed";
import { StatsBar } from "@/components/stats-bar";
import { useAlertStream } from "@/hooks/use-alert-stream";
import { API } from "@/lib/api";
import type { Alert } from "@/lib/types";

export default function Dashboard() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [toast, setToast] = useState<Alert | null>(null);
  const [freshIds, setFreshIds] = useState<Set<string>>(new Set());

  const { alerts, events, status, loaded } = useAlertStream((a) => {
    setFreshIds((prev) => new Set(prev).add(a.id));
    if (a.severity === "critical") setToast(a);
  });

  const open = useCallback((id: string) => {
    setToast(null);
    setSelectedId(id);
  }, []);
  const close = useCallback(() => setSelectedId(null), []);
  const dismissToast = useCallback(() => setToast(null), []);
  const selected = alerts.find((a) => a.id === selectedId) ?? null;

  return (
    <MotionConfig reducedMotion="user">
      <div inert={selected !== null} className="mx-auto flex min-h-dvh max-w-[1600px] flex-col gap-6 p-4 md:p-6">
        <header className="flex flex-wrap items-end justify-between gap-4 border-b border-line pb-5">
          <div>
            <h1 className="font-display text-4xl font-bold leading-none md:text-5xl">
              WASPADA
            </h1>
            <p className="mt-2 text-ink-muted">Pusat pemantauan isu strategis dari pemberitaan dalam dan luar negeri</p>
          </div>
          <ConnectionStatus status={status} />
        </header>

        {status === "reconnecting" && !loaded && (
          <p role="alert" className="rounded-md border border-sev-critical/50 bg-sev-critical/10 p-4 text-sm">
            Server pemantauan di <span className="font-data">{API}</span> belum dapat dijangkau. Mohon pastikan
            backend aktif (<span className="font-data">docker compose up</span>). Sistem akan menyambung ulang secara
            otomatis.
          </p>
        )}

        <StatsBar alerts={alerts} events={events} />

        <main className="grid flex-1 gap-8 xl:grid-cols-[minmax(0,1fr)_380px]">
          <AlertList alerts={alerts} loaded={loaded} freshIds={freshIds} onOpen={open} />
          <NewsFeed events={events} loaded={loaded} />
        </main>
      </div>

      <AlertDetail alert={selected} onClose={close} />
      <CriticalToast alert={selected ? null : toast} onOpen={open} onDismiss={dismissToast} />
    </MotionConfig>
  );
}
