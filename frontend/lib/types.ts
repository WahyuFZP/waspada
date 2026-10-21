// Kontrak dengan backend: skema event & alert di README root ("Skema event").
export type Severity = "low" | "medium" | "high" | "critical";

export type Event = {
  timestamp: string;
  source: string;
  region: "domestic" | "foreign";
  event_type: string;
  topic: string;
  title: string;
  url?: string | null;
};

export type Alert = {
  id: string;
  rule: string;
  severity: Severity;
  group: Record<string, string>;
  timestamp: string;
  events: Event[];
};
