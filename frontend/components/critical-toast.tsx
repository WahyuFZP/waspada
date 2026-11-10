"use client";

import { AnimatePresence, motion } from "motion/react";
import { useEffect } from "react";
import { groupLabel } from "@/lib/api";
import type { Alert } from "@/lib/types";

export function CriticalToast({
  alert,
  onOpen,
  onDismiss,
}: {
  alert: Alert | null;
  onOpen: (id: string) => void;
  onDismiss: () => void;
}) {
  useEffect(() => {
    if (!alert) return;
    const t = setTimeout(onDismiss, 8000);
    return () => clearTimeout(t);
  }, [alert, onDismiss]);

  return (
    <div aria-live="assertive" className="pointer-events-none fixed inset-x-4 top-4 z-50 flex justify-center">
      <AnimatePresence>
        {alert && (
          <motion.div
            key={alert.id}
            role="alert"
            initial={{ y: -80, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -80, opacity: 0 }}
            transition={{ type: "spring", stiffness: 420, damping: 32 }}
            className="pointer-events-auto flex w-full max-w-xl flex-wrap items-center gap-3 rounded-md border border-sev-critical/70 bg-surface p-4 shadow-xl"
          >
            <div className="min-w-0 flex-1">
              <p className="font-data text-xs uppercase text-sev-critical">Peringatan kritis</p>
              <p className="font-display text-xl font-semibold leading-tight">{alert.rule}</p>
              <p className="text-base text-ink-muted">{groupLabel(alert.group)}. Mohon segera ditinjau.</p>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => onOpen(alert.id)}
                className="font-data min-h-11 rounded-md bg-sev-critical px-3 text-xs font-medium text-bg hover:brightness-110"
              >
                Tinjau sekarang
              </button>
              <button
                type="button"
                onClick={onDismiss}
                className="font-data min-h-11 rounded-md border border-line px-3 text-xs hover:bg-surface-2"
              >
                Abaikan
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
