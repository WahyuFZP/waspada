"use client";

import { AnimatePresence, motion } from "motion/react";
import { useState } from "react";
import { eventLabel } from "@/lib/api";
import type { Event } from "@/lib/types";
import { Segmented } from "./segmented";

const MIN = 60_000;
const ACTIVE_MS = 5 * MIN; // pengirim dianggap aktif bila ada log dalam 5 menit terakhir

const TONE: Record<string, string> = {
  "auth.failed": "text-sev-high",
  "auth.success": "text-siber-bright",
  "ids.scan": "text-sev-medium",
  "ids.exploit_attempt": "text-sev-critical",
  "ids.alert": "text-sev-medium",
};

const clock = (ts: string) =>
  new Date(ts).toLocaleTimeString("id-ID", { timeZone: "Asia/Jakarta", hour: "2-digit", minute: "2-digit", second: "2-digit" });

const ago = (ms: number) => {
  const m = Math.round(ms / MIN);
  if (m < 1) return "baru saja";
  if (m < 60) return `${m} mnt lalu`;
  return m < 48 * 60 ? `${Math.round(m / 60)} jam lalu` : `${Math.round(m / 1440)} hari lalu`;
};

const where = (e: Event) =>
  !e.geo ? "-" : e.geo.scope === "internal" ? "Internal" : e.geo.scope === "reserved" ? "Khusus" : (e.geo.country_code ?? "?");

// baris log seperti di server: auth.log memakai baris aslinya, Suricata memakai signature
const rawLine = (e: Event) => {
  const line = e.raw?.line;
  return typeof line === "string" ? line : e.title;
};

/** Baris log per menit, 30 menit terakhir. Satu seri (jumlah log); rinciannya di tooltip dan di kotak statistik. */
export function ActivityChart({ events, now }: { events: Event[]; now: number }) {
  const [hover, setHover] = useState<number | null>(null);
  const start = Math.floor(now / MIN) * MIN - 29 * MIN;
  const buckets = Array.from({ length: 30 }, (_, i) => ({ t: start + i * MIN, total: 0, failed: 0, success: 0, ids: 0 }));
  for (const e of events) {
    const i = Math.floor((Date.parse(e.timestamp) - start) / MIN);
    if (i < 0 || i >= 30) continue;
    const b = buckets[i];
    b.total += 1;
    if (e.event_type === "auth.failed") b.failed += 1;
    else if (e.event_type === "auth.success") b.success += 1;
    else b.ids += 1;
  }
  const max = Math.max(1, ...buckets.map((b) => b.total));
  const sum = buckets.reduce((s, b) => s + b.total, 0);
  const hhmm = (t: number) => new Date(t).toLocaleTimeString("id-ID", { timeZone: "Asia/Jakarta", hour: "2-digit", minute: "2-digit" });

  return (
    <section aria-labelledby="chart-title" className="flex min-w-0 flex-col gap-3 rounded-2xl border border-line bg-surface p-4 md:p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="chart-title" className="font-display text-2xl font-bold">
          Log per menit
        </h2>
        <span className="font-data text-xs text-ink-muted">30 menit terakhir · {sum} baris</span>
      </div>
      {sum === 0 ? (
        <p className="flex h-40 items-center justify-center rounded-md border border-dashed border-line px-4 text-center text-sm text-ink-muted">
          Belum ada log dalam 30 menit terakhir.
        </p>
      ) : (
        <div className="relative">
          <span className="font-data absolute -top-1 left-0 text-[11px] text-ink-muted">{max}</span>
          <div
            role="img"
            aria-label={`${sum} baris log dalam 30 menit terakhir, puncak ${max} baris per menit`}
            className="flex h-40 items-end gap-[2px] border-b border-line pl-7"
            onMouseLeave={() => setHover(null)}
          >
            {buckets.map((b, i) => (
              <div key={b.t} className="flex h-full flex-1 items-end" onMouseEnter={() => setHover(i)}>
                <motion.div
                  className={`w-full rounded-t-[4px] ${b.total ? "bg-siber-bright" : "bg-line"} ${hover === i ? "opacity-100" : "opacity-85"}`}
                  initial={false}
                  animate={{ height: b.total ? `${(b.total / max) * 100}%` : 2 }}
                  transition={{ type: "spring", stiffness: 260, damping: 26 }}
                />
              </div>
            ))}
          </div>
          {hover !== null && (
            <div
              className="font-data pointer-events-none absolute -top-12 z-10 -translate-x-1/2 whitespace-nowrap rounded-md border border-line bg-bg px-2.5 py-1.5 text-xs shadow-lg"
              style={{ left: `calc(1.75rem + (100% - 1.75rem) * ${(hover + 0.5) / 30})` }}
            >
              <span className="text-ink">
                {hhmm(buckets[hover].t)} · {buckets[hover].total} baris
              </span>
              <span className="block text-ink-muted">
                gagal {buckets[hover].failed} · berhasil {buckets[hover].success} · IDS {buckets[hover].ids}
              </span>
            </div>
          )}
          <div className="font-data mt-1 flex justify-between pl-7 text-[11px] text-ink-muted">
            <span>{hhmm(start)}</span>
            <span>sekarang</span>
          </div>
        </div>
      )}
    </section>
  );
}

/** Siapa yang mengirim log: per host, kapan terakhir, dan apakah pengirimnya masih aktif. */
export function SourceStatus({ events, now }: { events: Event[]; now: number }) {
  const hosts = new Map<string, { count: number; last: number; sources: Set<string> }>();
  for (const e of events) {
    const key = e.host ?? "?";
    const h = hosts.get(key) ?? { count: 0, last: 0, sources: new Set<string>() };
    h.count += 1;
    h.last = Math.max(h.last, Date.parse(e.timestamp));
    h.sources.add(e.source === "auth" ? "auth.log (SSH)" : "eve.json (Suricata)");
    hosts.set(key, h);
  }
  const rows = [...hosts.entries()].sort((a, b) => b[1].last - a[1].last);

  return (
    <section aria-labelledby="src-title" className="flex min-w-0 flex-col gap-3 rounded-2xl border border-line bg-surface p-4 md:p-5">
      <h2 id="src-title" className="font-display text-2xl font-bold">
        Sumber log
      </h2>
      {rows.length === 0 && <p className="text-sm text-ink-muted">Belum ada server yang mengirim log.</p>}
      <ul className="flex flex-col gap-2">
        {rows.map(([host, h]) => {
          const active = now - h.last < ACTIVE_MS;
          return (
            <li key={host} className="flex items-center justify-between gap-3 rounded-lg border border-line px-3 py-2.5">
              <span className="flex min-w-0 items-center gap-2.5">
                <span className="relative flex h-2.5 w-2.5 shrink-0">
                  {active && <span aria-hidden className="absolute inset-0 animate-ping rounded-full bg-siber-bright opacity-60 motion-reduce:hidden" />}
                  <span className={`relative h-2.5 w-2.5 rounded-full ${active ? "bg-siber-bright" : "bg-ink-muted/50"}`} />
                </span>
                <span className="min-w-0">
                  <span className="font-data block truncate text-sm">{host}</span>
                  <span className="font-data block text-[11px] text-ink-muted">
                    {[...h.sources].join(", ")} · {h.count} baris
                  </span>
                </span>
              </span>
              <span className={`font-data shrink-0 text-right text-[11px] ${active ? "text-siber-bright" : "text-ink-muted"}`}>
                {active ? "Aktif" : "Diam"}
                <span className="block text-ink-muted">{ago(now - h.last)}</span>
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

type Filter = "all" | "auth.failed" | "auth.success" | "ids";

/** Aliran baris log live: yang terbaru di atas, baris baru meluncur masuk dengan sorotan yang memudar. */
export function LogStream({ events, loaded }: { events: Event[]; loaded: boolean }) {
  const [filter, setFilter] = useState<Filter>("all");
  const [query, setQuery] = useState("");
  const q = query.trim().toLowerCase();
  const shown = events
    .filter((e) => filter === "all" || (filter === "ids" ? e.source === "suricata" : e.event_type === filter))
    .filter((e) => !q || (e.src_ip ?? "").includes(q) || (e.host ?? "").toLowerCase().includes(q))
    .slice(0, 60);
  // kunci stabil dari isi baris (event tidak punya id); duplikat diberi nomor dari yang tertua agar tidak bergeser
  const seen = new Map<string, number>();
  const rows = [...shown]
    .reverse()
    .map((e) => {
      const base = `${e.timestamp}|${e.src_ip}|${rawLine(e)}`;
      const n = (seen.get(base) ?? 0) + 1;
      seen.set(base, n);
      return { e, key: `${base}#${n}` };
    })
    .reverse();

  return (
    <section aria-labelledby="stream-title" className="flex min-w-0 flex-col gap-3">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h2 id="stream-title" className="font-display text-3xl font-bold">
          Aliran log
        </h2>
        <label className="flex flex-col gap-1">
          <span className="font-data text-xs text-ink-muted">Cari IP atau host</span>
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="mis. 172.18.0.7"
            className="font-data min-h-11 w-60 rounded-md border border-line bg-surface px-3 text-sm placeholder:text-ink-muted/60"
          />
        </label>
      </div>
      <Segmented
        id="log-filter"
        label="Saring jenis log"
        value={filter}
        onChange={setFilter}
        options={[
          { value: "all", label: "Semua" },
          { value: "auth.failed", label: "Login gagal" },
          { value: "auth.success", label: "Login berhasil" },
          { value: "ids", label: "IDS" },
        ]}
      />
      {!loaded && <p className="text-ink-muted">Memuat log…</p>}
      {loaded && shown.length === 0 && (
        <p className="rounded-md border border-dashed border-line p-4 text-sm text-ink-muted">
          {events.length === 0
            ? "Belum ada log. Jalankan pengirim log di server, atau coba login ke server latihan: ssh latihan@localhost -p 2222"
            : "Tidak ada log yang cocok dengan saringan ini."}
        </p>
      )}
      <ol className="relative flex flex-col overflow-hidden rounded-xl border border-line bg-bg/80">
        <AnimatePresence initial={false}>
          {rows.map(({ e, key }) => (
            <motion.li
              key={key}
              layout="position"
              initial={{ opacity: 0, y: -14, backgroundColor: "rgba(214,175,88,0.18)" }}
              animate={{ opacity: 1, y: 0, backgroundColor: "rgba(214,175,88,0)" }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.5, backgroundColor: { duration: 2.2 } }}
              className="grid grid-cols-[auto_minmax(0,1fr)] gap-x-3 gap-y-1 border-b border-line px-3 py-2 last:border-0 md:grid-cols-[5.5rem_9rem_7rem_minmax(0,1fr)]"
            >
              <span className="font-data text-xs text-ink-muted">{clock(e.timestamp)}</span>
              <span className={`font-data text-xs ${TONE[e.event_type] ?? "text-ink"}`}>{eventLabel(e.event_type)}</span>
              <span className="font-data text-xs text-ink-muted">
                {e.src_ip ?? "-"} <span className="text-ink-muted/70">· {where(e)}</span>
              </span>
              <span className="font-data col-span-2 break-all text-xs text-ink md:col-span-1">{rawLine(e)}</span>
            </motion.li>
          ))}
        </AnimatePresence>
      </ol>
    </section>
  );
}
