// Kartu "Pelajari dulu" per temuan (#8): penjelasan awam yang bisa dibuka/tutup. Dipakai dashboard APK & Web.
export function LearnMore({ edu }: { edu?: { apa: string; kenapa: string; dampak: string } }) {
  if (!edu) return null;
  return (
    <details className="group mt-2 rounded-lg border border-line bg-surface-2/40">
      <summary className="flex cursor-pointer list-none items-center gap-1.5 px-3 py-2 font-data text-xs text-ink-muted hover:text-ink">
        <span className="inline-block transition-transform group-open:rotate-90">▸</span>
        Pelajari dulu
      </summary>
      <dl className="flex flex-col gap-2 px-3 pb-3 text-sm">
        <div>
          <dt className="font-data text-[11px] uppercase tracking-wide text-ink-muted">Apa ini</dt>
          <dd className="mt-0.5 text-ink">{edu.apa}</dd>
        </div>
        <div>
          <dt className="font-data text-[11px] uppercase tracking-wide text-ink-muted">Kenapa berisiko</dt>
          <dd className="mt-0.5 text-ink">{edu.kenapa}</dd>
        </div>
        <div>
          <dt className="font-data text-[11px] uppercase tracking-wide text-ink-muted">Kalau dibiarkan</dt>
          <dd className="mt-0.5 text-ink">{edu.dampak}</dd>
        </div>
      </dl>
    </details>
  );
}
