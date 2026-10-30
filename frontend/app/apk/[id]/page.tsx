"use client";

import { motion } from "motion/react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ApkHeader } from "@/components/apk-header";
import { formatTime } from "@/lib/api";
import { getScan, kb, LEVEL_STYLE, type ScanResult } from "@/lib/apk";

const TINGKAT_STYLE = {
  tinggi: "text-sev-critical",
  sedang: "text-sev-medium",
  rendah: "text-ink-muted",
} as const;

const SUMMARY: Record<ScanResult["level_risiko"], string> = {
  Tinggi: "Ditemukan beberapa ciri aplikasi pencuri OTP atau data perbankan. Jangan pasang aplikasi ini.",
  Sedang: "Ditemukan ciri yang perlu diwaspadai. Pasang hanya bila Anda yakin dengan sumbernya.",
  Rendah: "Tidak ditemukan indikator berbahaya yang kuat. Tetap pastikan sumber aplikasi tepercaya.",
};

function downloadJson(r: ScanResult) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(r, null, 2)], { type: "application/json" }));
  const a = Object.assign(document.createElement("a"), { href: url, download: `laporan-apk-${r.file.sha256.slice(0, 12)}.json` });
  a.click();
  URL.revokeObjectURL(url);
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[120px_minmax(0,1fr)] gap-2">
      <dt className="font-data text-xs text-ink-muted">{label}</dt>
      <dd className="min-w-0 break-words text-sm">{value ?? <span className="text-ink-muted">-</span>}</dd>
    </div>
  );
}

export default function ApkResultPage() {
  const { id } = useParams<{ id: string }>();
  const [r, setR] = useState<ScanResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getScan(id)
      .then(setR)
      .catch((e) => setError((e as Error).message));
  }, [id]);

  return (
    <>
      <ApkHeader />
      <main className="mx-auto flex max-w-[1200px] flex-col gap-6 px-4 py-10 md:px-6">
        <Link href="/apk" className="font-data text-xs text-ink-muted hover:text-ink">
          ← Periksa APK lain
        </Link>
        {error && (
          <p role="alert" className="text-sev-critical">
            {error} Pastikan service apk-scanner aktif, atau kembali ke riwayat.
          </p>
        )}
        {!r && !error && <p className="text-ink-muted">Memuat laporan…</p>}

        {r && (
          <>
            <motion.section
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              aria-label="Ringkasan risiko"
              className={`flex flex-col gap-4 rounded-2xl border p-6 md:flex-row md:items-center md:justify-between ${LEVEL_STYLE[r.level_risiko]}`}
            >
              <div className="min-w-0">
                <p className="font-data text-xs uppercase tracking-[0.12em]">Risiko {r.level_risiko}</p>
                <h1 className="font-display mt-1 break-all text-3xl font-bold text-ink md:text-4xl">{r.file.nama}</h1>
                <p className="mt-2 max-w-2xl text-ink">{SUMMARY[r.level_risiko]}</p>
              </div>
              <div className="shrink-0 text-center">
                <p className="font-display text-7xl font-bold leading-none">{r.skor}</p>
                <p className="font-data text-xs">dari 100</p>
              </div>
            </motion.section>

            <section aria-labelledby="temuan-title" className="flex flex-col gap-3">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <h2 id="temuan-title" className="font-display text-3xl font-bold">
                  Temuan ({r.temuan.length})
                </h2>
                <button
                  type="button"
                  onClick={() => downloadJson(r)}
                  className="font-data min-h-11 rounded-md border border-gold/50 bg-gold/10 px-3 text-xs text-gold hover:bg-gold/20"
                >
                  Unduh laporan JSON
                </button>
              </div>
              {r.temuan.length === 0 && (
                <p className="rounded-md border border-dashed border-line p-6 text-ink-muted">
                  Tidak ada aturan yang terpicu. Ini berarti tidak ditemukan indikator, bukan jaminan aplikasi aman.
                </p>
              )}
              <ul className="flex flex-col gap-3">
                {r.temuan.map((f, i) => (
                  <motion.li
                    key={f.rule_id}
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.15 + i * 0.06 }}
                    className="rounded-xl border border-line bg-surface p-4"
                  >
                    <div className="flex flex-wrap items-baseline justify-between gap-2">
                      <h3 className="font-display text-2xl font-semibold leading-tight">{f.judul}</h3>
                      <span className="font-data text-xs">
                        <span className={TINGKAT_STYLE[f.tingkat]}>{f.tingkat.toUpperCase()}</span>
                        <span className="text-ink-muted"> · {f.rule_id} · +{f.bobot}</span>
                      </span>
                    </div>
                    <p className="mt-1 text-ink-muted">{f.penjelasan}</p>
                    <ul aria-label="Bukti" className="mt-3 flex flex-wrap gap-1.5">
                      {f.bukti.map((b) => (
                        <li key={b} className="font-data break-all rounded-sm bg-surface-2 px-2 py-0.5 text-xs">
                          {b}
                        </li>
                      ))}
                    </ul>
                  </motion.li>
                ))}
              </ul>
            </section>

            <div className="grid gap-6 lg:grid-cols-2">
              <section aria-labelledby="meta-title" className="rounded-xl border border-line bg-surface p-4">
                <h2 id="meta-title" className="font-display text-2xl font-bold">
                  Aplikasi
                </h2>
                <dl className="mt-3 flex flex-col gap-1.5">
                  <Row label="Package" value={<span className="font-data text-xs">{r.aplikasi.package}</span>} />
                  <Row label="Versi" value={`${r.aplikasi.version_name ?? "-"} (${r.aplikasi.version_code ?? "-"})`} />
                  <Row label="SDK min/target" value={`${r.aplikasi.min_sdk ?? "-"} / ${r.aplikasi.target_sdk ?? "-"}`} />
                  <Row label="Ukuran" value={kb(r.file.ukuran_bytes)} />
                  <Row label="SHA-256" value={<span className="font-data break-all text-xs">{r.file.sha256}</span>} />
                  <Row label="Diperiksa" value={formatTime(r.scanned_at)} />
                  <Row
                    label="Packer"
                    value={
                      r.packer.galat ??
                      (r.packer.terdeteksi ? r.packer.detail.join(", ") : "Tidak terdeteksi packer/obfuscator")
                    }
                  />
                </dl>
              </section>

              <section aria-labelledby="perm-title" className="rounded-xl border border-line bg-surface p-4">
                <h2 id="perm-title" className="font-display text-2xl font-bold">
                  Izin berisiko ({r.permission.berbahaya.length} dari {r.permission.semua.length})
                </h2>
                <ul className="mt-3 flex flex-wrap gap-1.5">
                  {r.permission.berbahaya.length === 0 && <li className="text-sm text-ink-muted">Tidak ada.</li>}
                  {r.permission.berbahaya.map((p) => (
                    <li key={p} className="font-data rounded-sm bg-surface-2 px-2 py-0.5 text-xs">
                      {p.replace("android.permission.", "")}
                    </li>
                  ))}
                </ul>
                <h3 className="font-data mt-5 text-xs text-ink-muted">URL & IP tertanam ({r.url_ip.length})</h3>
                <ul className="mt-2 max-h-48 overflow-y-auto">
                  {r.url_ip.length === 0 && <li className="text-sm text-ink-muted">Tidak ada.</li>}
                  {r.url_ip.map((u) => (
                    <li key={u} className="font-data break-all py-0.5 text-xs">
                      {u}
                    </li>
                  ))}
                </ul>
              </section>
            </div>

            <p className="text-sm text-ink-muted">{r.catatan}</p>
          </>
        )}
      </main>
    </>
  );
}
