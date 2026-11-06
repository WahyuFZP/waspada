import { SEVERITY_LABEL, STATUS_LABEL } from "@/lib/api";
import type { AlertStatus, Severity } from "@/lib/types";

const STYLE: Record<Severity, string> = {
  critical: "border-sev-critical/60 bg-sev-critical/15 text-sev-critical",
  high: "border-sev-high/50 bg-sev-high/10 text-sev-high",
  medium: "border-sev-medium/40 bg-sev-medium/10 text-sev-medium",
  low: "border-sev-low/40 bg-sev-low/10 text-sev-low",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span className={`font-data inline-flex rounded-sm border px-2 py-0.5 text-xs font-medium uppercase ${STYLE[severity]}`}>
      {SEVERITY_LABEL[severity]}
    </span>
  );
}

const STATUS_STYLE: Record<AlertStatus, string> = {
  baru: "border-line text-ink",
  ditangani: "border-gold/50 bg-gold/10 text-gold",
  selesai: "border-siber-bright/50 bg-siber-bright/10 text-siber-bright",
};

export function StatusBadge({ status = "baru" }: { status?: AlertStatus }) {
  return (
    <span className={`font-data inline-flex rounded-sm border px-2 py-0.5 text-xs ${STATUS_STYLE[status]}`}>
      {STATUS_LABEL[status]}
    </span>
  );
}
