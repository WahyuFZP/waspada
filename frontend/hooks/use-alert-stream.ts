"use client";

import { useEffect, useState } from "react";
import { API, getAlerts, getEvents } from "@/lib/api";
import type { Alert, Event } from "@/lib/types";

export type StreamStatus = "connecting" | "live" | "reconnecting";

/** Data awal lewat REST, lalu alert & event baru lewat SSE /stream. sources membatasi event ke sumber tertentu. */
export function useAlertStream(onAlert?: (a: Alert) => void, sources?: string) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [status, setStatus] = useState<StreamStatus>("connecting");
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let active = true;
    // dipanggil di setiap (re)connect: alert yang terlewat selama terputus ikut termuat
    const load = () =>
      Promise.all([getAlerts(), getEvents(sources)])
        .then(([a, e]) => {
          if (!active) return;
          setAlerts(a);
          setEvents(e);
          setLoaded(true);
        })
        .catch(() => active && setStatus("reconnecting"));

    const es = new EventSource(`${API}/stream`);
    es.onopen = () => {
      setStatus("live");
      load();
    };
    es.onerror = () => setStatus("reconnecting"); // EventSource menyambung ulang sendiri
    es.addEventListener("event", (m) => {
      const ev: Event = JSON.parse(m.data);
      if (sources && !sources.split(",").includes(ev.source)) return;
      setEvents((prev) => [ev, ...prev].slice(0, 200));
    });
    es.addEventListener("alert", (m) => {
      const alert: Alert = JSON.parse(m.data);
      setAlerts((prev) => (prev.some((a) => a.id === alert.id) ? prev : [alert, ...prev]));
      onAlert?.(alert);
    });
    return () => {
      active = false;
      es.close();
    };
    // onAlert sengaja tidak jadi dependency: satu koneksi SSE selama halaman hidup
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { alerts, events, status, loaded };
}
