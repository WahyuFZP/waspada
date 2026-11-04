// Kontrak dengan backend: skema event & alert di README root ("Skema event").
export type Severity = "low" | "medium" | "high" | "critical";

export type Event = {
  timestamp: string;
  source: string; // nama media, atau "auth" / "suricata" / "cisa_kev"
  event_type: string;
  title: string;
  url?: string | null;
  demo?: boolean; // data simulasi dari replay
  // berita (OSINT)
  region?: "domestic" | "foreign";
  topic?: string;
  // log keamanan & intel ancaman
  host?: string;
  src_ip?: string;
  user?: string;
  dest_port?: number | null;
  cve?: string | null;
  raw?: Record<string, unknown>; // record asli dari sumber (mis. baris auth.log di raw.line)
  // lokasi IP sumber (DB-IP Lite, offline); tidak ada di event lama sebelum fitur GeoIP
  geo?: {
    scope: "public" | "internal" | "reserved";
    country_code?: string | null;
    country?: string | null;
    asn?: number | null;
    org?: string | null;
  };
};

export type Alert = {
  id: string;
  rule: string;
  severity: Severity;
  group: Record<string, string>;
  timestamp: string;
  events: Event[];
  mitre?: { id: string; name: string }[];
};
