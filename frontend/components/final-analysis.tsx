import { motion } from "motion/react";
import type { FinalAnalysis, Verdict } from "@/lib/apk";

const STATUS_STYLE: Record<Verdict, string> = {
  Berbahaya: "border-sev-critical/60 text-sev-critical",
  Mencurigakan: "border-sev-high/60 text-sev-high",
  "Tidak ditemukan indikasi berbahaya": "border-siber-bright/50 text-siber-bright",
};

const KATEGORI = {
  lainnya: { label: "Perlu ditinjau", style: "text-sev-high" },
  aplikasi: { label: "Milik aplikasi", style: "text-siber-bright" },
  dikenal: { label: "Layanan umum", style: "text-ink-muted" },
} as const;

const INTEL_STYLE = {
  dikenal_malware: "text-sev-critical",
  tidak_ditemukan: "text-siber-bright",
  dilewati: "text-ink-muted",
  galat: "text-ink-muted",
} as const;

// Kesimpulan otomatis setelah scan: ditulis untuk pengguna awam, detail teknis di bawahnya untuk analis
export function FinalAnalysisCard({ a }: { a: FinalAnalysis }) {
  const c = a.sertifikat;
  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
      aria-labelledby="akhir-title"
      className={`rounded-2xl border bg-surface p-5 md:p-6 ${STATUS_STYLE[a.status]}`}
    >
      <p className="font-data text-xs uppercase tracking-[0.12em]">Analisa akhir otomatis</p>
      <h2 id="akhir-title" className="font-body mt-1 text-3xl font-bold md:text-4xl">
        {a.status}
      </h2>

      <div className="mt-4 grid gap-6 text-ink md:grid-cols-2">
        <div>
          <h3 className="font-data text-xs text-ink-muted">Mengapa</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-base">
            {a.alasan.map((x) => (
              <li key={x}>{x}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="font-data text-xs text-ink-muted">Yang perlu Anda lakukan</h3>
          <ol className="mt-2 list-decimal space-y-1 pl-5 text-base">
            {a.saran.map((x) => (
              <li key={x}>{x}</li>
            ))}
          </ol>
        </div>
      </div>

      <div className="mt-6 grid gap-4 border-t border-line pt-4 text-ink lg:grid-cols-3">
        <div className="min-w-0">
          <h3 className="font-data text-xs text-ink-muted">Sertifikat penandatangan</h3>
          {c.skema ? (
            <div className="mt-2 space-y-1 text-base">
              <p>{c.subjek ?? "Tanpa sertifikat"}</p>
              <p className="font-data text-xs text-ink-muted">
                Skema {c.skema.join(", ") || "-"} · berlaku s.d. {c.berlaku_hingga ?? "-"}
                {c.debug && <span className="text-sev-high"> · kunci debug</span>}
              </p>
              {c.sha256 && <p className="font-data break-all text-[11px] text-ink-muted">SHA-256 {c.sha256}</p>}
            </div>
          ) : (
            <p className="mt-2 text-base text-ink-muted">Tidak dapat dibaca.</p>
          )}
        </div>

        <div className="min-w-0">
          <h3 className="font-data text-xs text-ink-muted">Basis data malware (MalwareBazaar)</h3>
          <p className={`mt-2 text-sm ${INTEL_STYLE[a.intel.status]}`}>{a.intel.keterangan}</p>
        </div>

        <div className="min-w-0">
          <h3 className="font-data text-xs text-ink-muted">Domain tujuan ({a.domain.length})</h3>
          <ul className="mt-2 max-h-40 space-y-0.5 overflow-y-auto pr-1">
            {a.domain.length === 0 && <li className="text-base text-ink-muted">Tidak ada.</li>}
            {a.domain.map((d) => (
              <li key={d.domain} className="font-data flex justify-between gap-2 text-xs">
                <span className="break-all">
                  {d.domain} <span className="text-ink-muted">×{d.jumlah}</span>
                </span>
                <span className={`shrink-0 ${KATEGORI[d.kategori].style}`}>{KATEGORI[d.kategori].label}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </motion.section>
  );
}
