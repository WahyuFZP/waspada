"use client";

import { AnimatePresence, motion } from "motion/react";
import { useEffect, useRef } from "react";
import { eventLabel, facts, formatTime, groupLabel, isExternal, mitreUrl, originLabel } from "@/lib/api";
import type { Alert } from "@/lib/types";
import { SeverityBadge } from "./severity-badge";
import { SourceLink } from "./source-link";

function span(alert: Alert) {
  const times = alert.events.map((e) => new Date(e.timestamp).getTime());
  const min = Math.round((Math.max(...times) - Math.min(...times)) / 60000);
  return min < 60 ? `${min} menit` : `${Math.floor(min / 60)} jam ${min % 60} menit`;
}

export function AlertDetail({ alert, onClose }: { alert: Alert | null; onClose: () => void }) {
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!alert) return;
    const opener = document.activeElement as HTMLElement | null;
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
      opener?.focus(); // kembalikan fokus ke kartu yang membuka dialog
    };
  }, [alert, onClose]);

  return (
    <AnimatePresence>
      {alert && (
        <motion.div
          key="overlay"
          className="fixed inset-0 z-40 flex items-end justify-center bg-black/60 md:items-center md:p-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-labelledby="detail-title"
            onClick={(e) => e.stopPropagation()}
            initial={{ y: 40, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 40, opacity: 0 }}
            transition={{ type: "spring", stiffness: 360, damping: 34 }}
            className="flex max-h-[90dvh] w-full flex-col overflow-hidden rounded-t-lg border border-line bg-surface shadow-2xl md:max-w-2xl md:rounded-lg"
          >
            <header className="flex items-start justify-between gap-4 border-b border-line p-5">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-3">
                  <SeverityBadge severity={alert.severity} />
                  <span className="font-data text-xs text-ink-muted">{formatTime(alert.timestamp)}</span>
                </div>
                <h2 id="detail-title" className="font-display mt-2 text-3xl font-bold leading-tight md:text-4xl">
                  {alert.rule}
                </h2>
                <p className="mt-2 text-ink-muted">
                  {groupLabel(alert.group)}: {alert.events.length} kejadian dari{" "}
                  {new Set(alert.events.map((e) => e.source)).size} sumber dalam rentang {span(alert)}. Setiap kejadian
                  tampak biasa; rangkaiannya memenuhi aturan korelasi.
                </p>
                {alert.mitre?.length ? (
                  <ul aria-label="Teknik MITRE ATT&CK" className="mt-3 flex flex-wrap gap-2">
                    {alert.mitre.map((t) => (
                      <li key={t.id}>
                        <a
                          href={mitreUrl(t.id)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-data inline-flex min-h-9 items-center rounded-md border border-gold/40 bg-gold/10 px-2.5 text-xs text-gold hover:bg-gold/20"
                        >
                          {t.id} {t.name}
                          <span className="sr-only"> (membuka MITRE ATT&CK di tab baru)</span>
                        </a>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
              <button
                ref={closeRef}
                type="button"
                onClick={onClose}
                className="font-data min-h-11 shrink-0 rounded-md border border-line px-3 text-xs hover:bg-surface-2"
              >
                Tutup
              </button>
            </header>

            <ol className="overflow-y-auto p-5">
              {alert.events.map((e, i) => (
                <motion.li
                  key={i}
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.15 + i * 0.12, duration: 0.3 }}
                  className="relative border-l border-line pb-6 pl-6 last:pb-0"
                >
                  <span
                    aria-hidden
                    className={`absolute -left-[6px] top-1 h-[11px] w-[11px] rounded-full border-2 border-surface ${
                      isExternal(e) ? "bg-gold" : "bg-ink"
                    }`}
                  />
                  <p className="font-data text-xs text-ink-muted">
                    Langkah {i + 1} · {formatTime(e.timestamp)} · {e.source} · {originLabel(e)} ·{" "}
                    {eventLabel(e.event_type)}
                    {e.demo && <span className="ml-2 rounded-sm bg-surface-2 px-1.5 py-0.5">Simulasi</span>}
                  </p>
                  <p className="mt-1 leading-snug">{e.title}</p>
                  {facts(e) && <p className="font-data mt-1 text-xs text-ink-muted">{facts(e)}</p>}
                  {(e.url || e.region) && <SourceLink url={e.url} />}
                </motion.li>
              ))}
            </ol>

            <footer className="font-data border-t border-line px-5 py-3 text-xs text-ink-muted">
              ID peringatan {alert.id}
            </footer>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
