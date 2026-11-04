import type { Alert, Event, Severity } from "./types";

export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

export const getAlerts = () => get<Alert[]>("/alerts");
// sources: mis. "auth,suricata" untuk halaman log, agar log keamanan tidak terdorong keluar oleh berita
export const getEvents = (sources?: string) => get<Event[]>(sources ? `/events?sources=${sources}` : "/events");

export const SEVERITY_RANK: Record<Severity, number> = { critical: 3, high: 2, medium: 1, low: 0 };

export const SEVERITY_LABEL: Record<Severity, string> = {
  critical: "Kritis",
  high: "Tinggi",
  medium: "Sedang",
  low: "Rendah",
};

export const REGION_LABEL = { domestic: "Dalam negeri", foreign: "Luar negeri" } as const;

// asal kejadian: berita punya region, log keamanan tidak (internal), KEV adalah intel ancaman eksternal
export const originLabel = (e: Event) =>
  e.region ? REGION_LABEL[e.region] : e.source === "cisa_kev" ? "Intel ancaman" : "Log internal";

// sumber dari luar satuan (media asing, intel ancaman) diberi penanda emas di timeline
export const isExternal = (e: Event) => e.region === "foreign" || e.source === "cisa_kev";

// rincian teknis log keamanan dalam satu baris; kosong untuk berita
export const facts = (e: Event) =>
  [
    e.host && `host ${e.host}`,
    e.src_ip && `dari ${e.src_ip}`,
    e.user && `user ${e.user}`,
    e.dest_port != null && `port ${e.dest_port}`,
    e.cve,
  ]
    .filter(Boolean)
    .join(" · ");

const EVENT_LABEL: Record<string, string> = {
  "news.incident": "Insiden",
  "news.diplomatic": "Diplomatik",
  "news.military": "Militer",
  "news.economic": "Ekonomi",
  "auth.failed": "Login gagal",
  "auth.success": "Login berhasil",
  "ids.scan": "Pemindaian",
  "ids.exploit_attempt": "Upaya eksploitasi",
  "ids.alert": "Alert IDS",
  "vuln.kev_match": "Kerentanan KEV",
};
export const eventLabel = (t: string) => EVENT_LABEL[t] ?? t;

const GROUP_LABEL: Record<string, string> = { topic: "Topik", host: "Host", src_ip: "IP sumber", user: "User" };
// {host: "srv-web-01", src_ip: "203.0.113.50"} -> "Host srv-web-01 · IP sumber 203.0.113.50"
export const groupLabel = (group: Record<string, string>) =>
  Object.entries(group)
    .map(([k, v]) => `${GROUP_LABEL[k] ?? k} ${k === "topic" ? topicLabel(v) : v}`)
    .join(" · ");

// T1110 -> https://attack.mitre.org/techniques/T1110/, T1110.001 -> .../T1110/001/
export const mitreUrl = (id: string) => `https://attack.mitre.org/techniques/${id.replace(".", "/")}/`;

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
