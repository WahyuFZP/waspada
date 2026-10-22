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
