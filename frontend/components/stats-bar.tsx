"use client";

import { AnimatePresence, motion } from "motion/react";
import type { Alert, Event } from "@/lib/types";

function Stat({ label, value, tone = "text-ink" }: { label: string; value: number; tone?: string }) {
  return (
    <div className="rounded-md border border-line bg-surface px-4 py-3">
      <dt className="font-data text-xs text-ink-muted">{label}</dt>
      <dd className={`font-display mt-1 h-10 overflow-hidden text-4xl font-bold leading-10 tabular-nums ${tone}`}>
        <AnimatePresence mode="popLayout" initial={false}>
          <motion.span
            key={value}
            className="block"
            initial={{ y: -16, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 16, opacity: 0 }}
            transition={{ duration: 0.25 }}
          >
            {value}
          </motion.span>
        </AnimatePresence>
      </dd>
    </div>
  );
}

export function StatsBar({ alerts, events }: { alerts: Alert[]; events: Event[] }) {
  const critical = alerts.filter((a) => a.severity === "critical").length;
  return (
    <dl className="grid grid-cols-2 gap-3 md:grid-cols-4">
      <Stat label="Peringatan" value={alerts.length} />
      <Stat label="Tingkat kritis" value={critical} tone={critical ? "text-sev-critical" : "text-ink"} />
      <Stat label="Media terpantau" value={new Set(events.map((e) => e.source)).size} />
      <Stat label="Berita terkorelasi" value={events.length} />
    </dl>
  );
}
