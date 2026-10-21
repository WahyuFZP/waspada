import type { Alert, Event, Severity } from "./types";

export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

export const getAlerts = () => get<Alert[]>("/alerts");
export const getEvents = () => get<Event[]>("/events");

export const SEVERITY_RANK: Record<Severity, number> = { critical: 3, high: 2, medium: 1, low: 0 };

export const SEVERITY_LABEL: Record<Severity, string> = {
  critical: "Kritis",
  high: "Tinggi",
  medium: "Sedang",
  low: "Rendah",
};

export const REGION_LABEL = { domestic: "Dalam negeri", foreign: "Luar negeri" } as const;

const EVENT_LABEL: Record<string, string> = {
  "news.incident": "Insiden",
  "news.diplomatic": "Diplomatik",
  "news.military": "Militer",
  "news.economic": "Ekonomi",
};
export const eventLabel = (t: string) => EVENT_LABEL[t] ?? t;

// "https://www.antaranews.com/berita/123" -> "antaranews.com"; backend sudah menolak url selain http(s)
export const hostOf = (url?: string | null) => {
  try {
    return url ? new URL(url).hostname.replace(/^www\./, "") : null;
  } catch {
    return null;
  }
};

// "siber_nasional" -> "Siber nasional"
export const topicLabel = (t?: string) => (t ? t[0].toUpperCase() + t.slice(1).replace(/_/g, " ") : "-");

export const formatTime = (ts: string) =>
  new Date(ts).toLocaleString("id-ID", {
    timeZone: "Asia/Jakarta",
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }) + " WIB";
