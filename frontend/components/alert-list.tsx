"use client";

import { AnimatePresence } from "motion/react";
import { useState } from "react";
import { SEVERITY_LABEL, SEVERITY_RANK } from "@/lib/api";
import type { Alert, Severity } from "@/lib/types";
import { AlertCard } from "./alert-card";
import { Segmented } from "./segmented";

type Sort = "severity" | "newest";
const LEVELS: Severity[] = ["critical", "high", "medium", "low"];

export function AlertList({
  alerts,
  loaded,
  freshIds,
  onOpen,
}: {
  alerts: Alert[];
  loaded: boolean;
  freshIds: Set<string>;
  onOpen: (id: string) => void;
}) {
  const [sort, setSort] = useState<Sort>("severity");
  const [hidden, setHidden] = useState<Set<Severity>>(new Set());

  const toggle = (s: Severity) =>
    setHidden((prev) => {
      const next = new Set(prev);
      if (!next.delete(s)) next.add(s);
      return next;
    });

  const shown = alerts
    .filter((a) => !hidden.has(a.severity))
    .sort((a, b) =>
      sort === "severity" && a.severity !== b.severity
        ? SEVERITY_RANK[b.severity] - SEVERITY_RANK[a.severity]
        : b.timestamp.localeCompare(a.timestamp),
    );

  return (
    <section aria-labelledby="alerts-title" className="flex min-w-0 flex-col gap-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h2 id="alerts-title" className="font-display text-3xl font-bold">
          Peringatan
        </h2>
        <Segmented
          id="alert-sort"
          label="Urutkan peringatan"
          value={sort}
          onChange={setSort}
          options={[
            { value: "severity", label: "Tingkat ancaman" },
            { value: "newest", label: "Terbaru" },
          ]}
        />
      </div>

      <div role="group" aria-label="Saring tingkat ancaman" className="flex flex-wrap gap-2">
        {LEVELS.map((s) => (
          <button
            key={s}
            type="button"
            aria-pressed={!hidden.has(s)}
            onClick={() => toggle(s)}
            className={`font-data min-h-11 rounded-md border px-3 text-xs transition-colors ${
              hidden.has(s) ? "border-line text-ink-muted line-through" : "border-army bg-army/40 text-ink"
            }`}
          >
            {SEVERITY_LABEL[s]} ({alerts.filter((a) => a.severity === s).length})
          </button>
        ))}
      </div>

      {!loaded ? (
        <p className="text-ink-muted">Memuat peringatan dari server pemantauan…</p>
      ) : alerts.length === 0 ? (
        <p className="max-w-prose rounded-md border border-dashed border-line p-6 text-ink-muted">
          Belum ada peringatan. Sistem sedang memantau arus berita; peringatan akan tampil di sini secara otomatis
          ketika rangkaian pemberitaan memenuhi aturan korelasi.
        </p>
      ) : shown.length === 0 ? (
        <div className="rounded-md border border-dashed border-line p-6 text-ink-muted">
          <p>Tidak ada peringatan pada tingkat ancaman yang dipilih.</p>
          <button
            type="button"
            onClick={() => setHidden(new Set())}
            className="font-data mt-3 min-h-11 rounded-md border border-line px-3 text-xs text-ink hover:bg-surface-2"
          >
            Tampilkan semua tingkat
          </button>
        </div>
      ) : (
        <ul className="grid gap-3 md:grid-cols-2">
          <AnimatePresence initial={false}>
            {shown.map((a) => (
              <AlertCard key={a.id} alert={a} fresh={freshIds.has(a.id)} onOpen={() => onOpen(a.id)} />
            ))}
          </AnimatePresence>
        </ul>
      )}
    </section>
  );
}
