"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Kontrak = skema event/alert di backend (README "Skema event")
type Event = {
  timestamp: string;
  source: string;
  region: "domestic" | "foreign";
  event_type: string;
  topic: string;
  title: string;
  url?: string | null;
};
type Alert = {
  id: string;
  rule: string;
  severity: "low" | "medium" | "high" | "critical";
  group: Record<string, string>;
  timestamp: string;
  events: Event[];
};

const SEVERITY: Record<Alert["severity"], string> = {
  low: "bg-sky-500/15 text-sky-300 ring-sky-500/40",
  medium: "bg-yellow-500/15 text-yellow-300 ring-yellow-500/40",
  high: "bg-orange-500/15 text-orange-300 ring-orange-500/40",
  critical: "bg-red-500/20 text-red-300 ring-red-500/60",
};

const time = (ts: string) =>
  new Date(ts).toLocaleString("id-ID", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });

function Badge({ severity }: { severity: Alert["severity"] }) {
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-semibold uppercase ring-1 ${SEVERITY[severity]}`}>
      {severity}
    </span>
  );
}

export default function Dashboard() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [live, setLive] = useState(false);

  useEffect(() => {
    Promise.all([fetch(`${API}/alerts`), fetch(`${API}/events`)])
      .then(([a, e]) => Promise.all([a.json(), e.json()]))
      .then(([a, e]) => {
        setAlerts(a);
        setEvents(e);
      })
      .catch(() => setLive(false));

    const es = new EventSource(`${API}/stream`);
    es.onopen = () => setLive(true);
    es.onerror = () => setLive(false); // EventSource reconnect otomatis
    es.addEventListener("event", (m) => setEvents((prev) => [JSON.parse(m.data), ...prev].slice(0, 200)));
    es.addEventListener("alert", (m) => {
      const alert: Alert = JSON.parse(m.data);
      setAlerts((prev) => [alert, ...prev]);
      setSelected(alert.id);
    });
    return () => es.close();
  }, []);

  const current = alerts.find((a) => a.id === selected) ?? alerts[0];

  return (
    <main className="mx-auto flex min-h-screen max-w-7xl flex-col gap-4 p-4 md:p-6">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div>
          <h1 className="font-mono text-2xl font-bold tracking-widest">WASPADA</h1>
          <p className="text-sm text-white/50">OSINT-SIEM: korelasi berita dalam &amp; luar negeri</p>
        </div>
        <div className="flex items-center gap-4 font-mono text-sm">
          <span>{events.length} event</span>
          <span>{alerts.length} alert</span>
          <span className={`flex items-center gap-2 ${live ? "text-emerald-400" : "text-red-400"}`}>
            <span className={`h-2 w-2 rounded-full ${live ? "animate-pulse bg-emerald-400" : "bg-red-400"}`} />
            {live ? "LIVE" : "TERPUTUS"}
          </span>
        </div>
      </header>

      <div className="grid flex-1 gap-4 lg:grid-cols-[320px_1fr_360px]">
        <section aria-label="Daftar alert" className="flex flex-col gap-2">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-white/50">Alert</h2>
          {alerts.length === 0 && <p className="text-sm text-white/40">Belum ada alert. Jalankan replay skenario.</p>}
          {alerts.map((a) => (
            <button
              key={a.id}
              onClick={() => setSelected(a.id)}
              className={`rounded-lg border p-3 text-left transition ${
                a.id === current?.id ? "border-white/40 bg-white/10" : "border-white/10 hover:bg-white/5"
              } ${a.severity === "critical" ? "shadow-[0_0_20px_rgba(239,68,68,0.25)]" : ""}`}
            >
              <div className="flex items-center justify-between gap-2">
                <Badge severity={a.severity} />
                <span className="font-mono text-xs text-white/50">{time(a.timestamp)}</span>
              </div>
              <p className="mt-2 font-medium">{a.rule}</p>
              <p className="font-mono text-xs text-white/50">topic: {a.group.topic}</p>
            </button>
          ))}
        </section>

        <section aria-label="Timeline alert" className="rounded-lg border border-white/10 p-4">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-white/50">Timeline event pendukung</h2>
          {current ? (
            <>
              <div className="mt-3 flex flex-wrap items-center gap-3">
                <Badge severity={current.severity} />
                <h3 className="text-lg font-semibold">{current.rule}</h3>
              </div>
              <ol className="mt-6 space-y-5 border-l border-white/15 pl-5">
                {current.events.map((e, i) => (
                  <li key={i} className="relative">
                    <span className="absolute -left-[26px] top-1.5 h-3 w-3 rounded-full border-2 border-black bg-white/70" />
                    <p className="font-mono text-xs text-white/50">
                      {time(e.timestamp)} · {e.source} · {e.region === "domestic" ? "dalam negeri" : "luar negeri"} ·{" "}
                      {e.event_type}
                    </p>
                    <p className="mt-1">
                      {e.url ? (
                        <a href={e.url} target="_blank" rel="noreferrer" className="hover:underline">
                          {e.title}
                        </a>
                      ) : (
                        e.title
                      )}
                    </p>
                  </li>
                ))}
              </ol>
            </>
          ) : (
            <p className="mt-3 text-sm text-white/40">Pilih alert untuk melihat rangkaian kejadiannya.</p>
          )}
        </section>

        <section aria-label="Feed event" className="flex flex-col gap-2">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-white/50">Event masuk</h2>
          <ul className="max-h-[75vh] space-y-2 overflow-y-auto pr-1">
            {events.map((e, i) => (
              <li key={`${e.timestamp}-${e.event_type}-${i}`} className="rounded border border-white/10 p-2 text-sm">
                <p className="font-mono text-xs text-white/50">
                  {time(e.timestamp)} · {e.source} · {e.topic} · {e.event_type}
                </p>
                <p className="mt-1 line-clamp-2">{e.title}</p>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </main>
  );
}
