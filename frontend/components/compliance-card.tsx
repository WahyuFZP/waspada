// Kartu "Konteks & cara lapor resmi" (#14): jembatan temuan -> jalur resmi Indonesia. Dipakai APK & Web.
type Kepatuhan = { relevansi: string; kanal_lapor: { nama: string; cara: string }[]; disclaimer: string };

export function ComplianceCard({ k }: { k?: Kepatuhan | null }) {
  if (!k) return null;
  return (
    <section aria-label="Konteks dan cara lapor resmi" className="rounded-2xl border border-gold/40 bg-gold/5 p-5">
      <p className="font-data text-xs uppercase tracking-[0.12em] text-gold">Konteks &amp; cara lapor resmi</p>
      <p className="mt-2 text-sm text-ink">{k.relevansi}</p>
      <ul className="mt-3 flex flex-col gap-2">
        {k.kanal_lapor.map((c) => (
          <li key={c.nama} className="text-sm">
            <span className="font-semibold text-ink">{c.nama}</span>
            <span className="text-ink-muted"> — {c.cara}</span>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-xs italic text-ink-muted">{k.disclaimer}</p>
    </section>
  );
}
