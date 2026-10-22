import type { StreamStatus } from "@/hooks/use-alert-stream";

const STATUS: Record<StreamStatus, { label: string; dot: string; text: string }> = {
  live: { label: "Terhubung", dot: "bg-siber-bright", text: "text-siber-bright" },
  connecting: { label: "Menghubungkan", dot: "bg-ink-muted", text: "text-ink-muted" },
  reconnecting: { label: "Terputus, menyambung ulang", dot: "bg-sev-critical", text: "text-sev-critical" },
};

export function ConnectionStatus({ status }: { status: StreamStatus }) {
  const s = STATUS[status];
  return (
    <p role="status" className={`font-data flex items-center gap-2 text-xs ${s.text}`}>
      <span aria-hidden className={`h-2 w-2 rounded-full ${s.dot}`} />
      {s.label}
    </p>
  );
}
