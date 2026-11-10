"use client";

import { AnimatePresence, motion } from "motion/react";
import { useEffect, useRef, useState } from "react";
import { eventLabel, facts, formatTime, groupLabel, handleAlert, isExternal, mitreUrl, originLabel, STATUS_LABEL } from "@/lib/api";
import type { Alert, AlertStatus } from "@/lib/types";
import { Segmented } from "./segmented";
import { SeverityBadge, StatusBadge } from "./severity-badge";
import { SourceLink } from "./source-link";

/** Tindak lanjut analis: status + catatan. Riwayat hanya bertambah, jadi tetap menjadi jejak audit. */
function Handling({ alert, onUpdated }: { alert: Alert; onUpdated: (a: Alert) => void }) {
  const [status, setStatus] = useState<AlertStatus>(alert.status ?? "baru");
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const unchanged = status === (alert.status ?? "baru") && !note.trim();

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    if (status === "selesai" && !note.trim()) return setError("Tulis hasil penanganan sebelum menandai selesai.");
    setSaving(true);
    setError(null);
    try {
      onUpdated(await handleAlert(alert.id, status, note));
      setNote("");
    } catch (err) {
      setError(`Gagal menyimpan: ${err instanceof Error ? err.message : err}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <section aria-labelledby="handling-title" className="mt-6 border-t border-line pt-5">
      <h3 id="handling-title" className="font-display text-2xl font-bold">
        Penanganan
      </h3>
      <form onSubmit={save} className="mt-3 flex flex-col gap-3">
        <Segmented
          id={`status-${alert.id}`}
          label="Status penanganan"
          value={status}
          onChange={setStatus}
          options={(["baru", "ditangani", "selesai"] as const).map((v) => ({ value: v, label: STATUS_LABEL[v] }))}
        />
        <label className="flex flex-col gap-1">
          <span className="font-data text-xs text-ink-muted">
            Catatan tindakan {status === "selesai" ? "(wajib)" : "(opsional)"}
          </span>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            maxLength={1000}
            rows={3}
            placeholder="mis. IP diblokir di firewall, akun direset, satuan dihubungi"
            className="rounded-md border border-line bg-bg px-3 py-2 text-base placeholder:text-ink-muted/60"
          />
        </label>
        {error && (
          <p role="alert" className="text-base text-sev-critical">
            {error}
          </p>
        )}
        <button
          type="submit"
          disabled={saving || unchanged}
          className="font-data min-h-11 self-start rounded-md border border-siber bg-siber/30 px-4 text-xs hover:bg-siber/50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {saving ? "Menyimpan…" : "Simpan penanganan"}
        </button>
      </form>
      {alert.handling?.length ? (
        <ol aria-label="Riwayat penanganan" className="mt-4 flex flex-col gap-2">
          {[...alert.handling].reverse().map((h, i) => (
            <li key={`${h.timestamp}-${i}`} className="rounded-md border border-line px-3 py-2">
              <p className="font-data flex flex-wrap items-center gap-2 text-xs text-ink-muted">
                <StatusBadge status={h.status} /> {formatTime(h.timestamp)}
              </p>
              {h.note && <p className="mt-1 text-base">{h.note}</p>}
            </li>
          ))}
        </ol>
      ) : (
        <p className="mt-3 text-base text-ink-muted">Belum ada tindakan tercatat.</p>
      )}
    </section>
  );
}

function span(alert: Alert) {
  const times = alert.events.map((e) => new Date(e.timestamp).getTime());
  const min = Math.round((Math.max(...times) - Math.min(...times)) / 60000);
  return min < 60 ? `${min} menit` : `${Math.floor(min / 60)} jam ${min % 60} menit`;
}

export function AlertDetail({
  alert,
  onClose,
  onUpdated,
}: {
  alert: Alert | null;
  onClose: () => void;
  onUpdated: (a: Alert) => void;
}) {
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
                  <StatusBadge status={alert.status} />
                  <span className="font-data text-xs text-ink-muted">{formatTime(alert.timestamp)}</span>
                </div>
                <h2 id="detail-title" className="font-body mt-2 text-2xl font-bold leading-tight md:text-3xl">
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

            <div className="overflow-y-auto p-5">
              <ol>
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
              {/* key: form kembali kosong saat analis membuka alert lain */}
              <Handling key={alert.id} alert={alert} onUpdated={onUpdated} />
            </div>

            <footer className="font-data border-t border-line px-5 py-3 text-xs text-ink-muted">
              ID peringatan {alert.id}
            </footer>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
