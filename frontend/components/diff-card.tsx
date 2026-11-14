// Kartu "Perubahan sejak pemeriksaan lalu" (#10): regresi (baru), teratasi (hilang), delta. Dipakai APK & Web.
export function DiffCard({ baru, hilang, tetap, deltaText, waktuLama }: {
  baru: { judul: string }[];
  hilang: { judul: string }[];
  tetap: { judul: string }[];
  deltaText: string;
  waktuLama: string;
}) {
  return (
    <section aria-label="Perubahan sejak pemeriksaan lalu" className="rounded-2xl border border-line bg-surface p-5">
      <p className="font-data text-xs uppercase tracking-[0.12em] text-ink-muted">Perubahan sejak pemeriksaan lalu</p>
      <p className="mt-1 text-sm text-ink">
        Dibandingkan dengan pemeriksaan {waktuLama}. {deltaText}
      </p>
      <div className="mt-3 grid gap-4 md:grid-cols-2">
        <div>
          <p className="font-data text-xs text-sev-high">▲ Baru / regresi ({baru.length})</p>
          <ul className="mt-1 space-y-1 text-sm text-ink">
            {baru.length === 0 ? (
              <li className="text-ink-muted">Tidak ada.</li>
            ) : (
              baru.map((f) => <li key={f.judul}>{f.judul}</li>)
            )}
          </ul>
        </div>
        <div>
          <p className="font-data text-xs text-siber-bright">▼ Teratasi ({hilang.length})</p>
          <ul className="mt-1 space-y-1 text-sm">
            {hilang.length === 0 ? (
              <li className="text-ink-muted">Tidak ada.</li>
            ) : (
              hilang.map((f) => (
                <li key={f.judul} className="text-ink-muted line-through">
                  {f.judul}
                </li>
              ))
            )}
          </ul>
        </div>
      </div>
      <p className="mt-3 font-data text-xs text-ink-muted">{tetap.length} temuan tidak berubah.</p>
    </section>
  );
}
