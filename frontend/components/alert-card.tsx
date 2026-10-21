"use client";

import { motion } from "motion/react";
import { formatTime, REGION_LABEL, topicLabel } from "@/lib/api";
import type { Alert } from "@/lib/types";
import { SeverityBadge } from "./severity-badge";

export function AlertCard({ alert, fresh, onOpen }: { alert: Alert; fresh: boolean; onOpen: () => void }) {
  const sources = new Set(alert.events.map((e) => e.source)).size;
  const regions = [...new Set(alert.events.map((e) => REGION_LABEL[e.region]))].join(" & ");
  const critical = alert.severity === "critical";

  return (
    <motion.li
      layout
      initial={{ opacity: 0, y: -16, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.98 }}
      transition={{ type: "spring", stiffness: 380, damping: 32 }}
    >
      <motion.button
        type="button"
        onClick={onOpen}
        // denyut 2x hanya untuk alert kritis yang baru tiba lewat stream, lalu diam
        animate={
          fresh && critical
            ? { boxShadow: ["0 0 0 0 rgba(240,82,82,0)", "0 0 0 6px rgba(240,82,82,0.35)", "0 0 0 0 rgba(240,82,82,0)"] }
            : undefined
        }
        transition={{ duration: 1.1, repeat: 1 }}
        className={`group flex w-full flex-col gap-3 rounded-xl border bg-white/[0.02] p-4 text-left transition-colors hover:bg-surface-2 ${
          critical ? "border-sev-critical/50" : "border-line"
        }`}
      >
        <span className="flex items-center justify-between gap-3">
          <SeverityBadge severity={alert.severity} />
          <span className="font-data text-xs text-ink-muted">{formatTime(alert.timestamp)}</span>
        </span>
        <span className="font-display text-2xl font-semibold leading-tight">{alert.rule}</span>
        <span className="font-data text-xs text-ink-muted">
          Topik {topicLabel(alert.group.topic)} · {alert.events.length} berita · {sources} media · {regions}
        </span>
        <span className="font-data text-xs text-ink-muted underline-offset-4 transition-colors group-hover:text-ink group-hover:underline">
          Lihat rangkaian kejadian
        </span>
      </motion.button>
    </motion.li>
  );
}
