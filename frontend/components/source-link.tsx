import { hostOf } from "@/lib/api";

/** Baris "Sumber: antaranews.com" yang membuka artikel asli di tab baru. */
export function SourceLink({ url }: { url?: string | null }) {
  const host = hostOf(url);
  if (!url || !host) return <p className="font-data mt-2 text-xs text-ink-muted">Sumber: tautan tidak tersedia</p>;
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="font-data mt-2 inline-flex min-h-11 items-center gap-1 text-xs text-gold underline-offset-4 hover:underline md:min-h-0"
    >
      Sumber: {host}
      <span className="sr-only"> (membuka artikel asli di tab baru)</span>
    </a>
  );
}
