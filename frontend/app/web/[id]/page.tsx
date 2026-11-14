"use client";

import { motion } from "motion/react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ModuleHeader } from "@/components/module-header";
import { LearnMore } from "@/components/learn-more";
import { DiffCard } from "@/components/diff-card";
import { ComplianceCard } from "@/components/compliance-card";
import { formatTime, hostOf } from "@/lib/api";
import {
  diffWebscan,
  getWebscan,
  listWebscans,
  POSTUR_STYLE,
  POSTUR_SUMMARY,
  TINGKAT_LABEL,
  TINGKAT_STYLE,
  verifikasiTemuan,
  type Finding,
  type Tingkat,
  type VerifHasil,
  type WebDiff,
  type WebReport,
} from "@/lib/web";

const TINGKAT_TEXT: Record<Tingkat, string> = {
  kritis: "text-sev-critical",
  tinggi: "text-sev-high",
  sedang: "text-sev-medium",
  rendah: "text-sev-low",
  info: "text-ink-muted",
};

// urutan pita untuk ringkasan "jumlah per tingkat"
const ORDER: Tingkat[] = ["kritis", "tinggi", "sedang", "rendah", "info"];

const VERIF_STYLE: Record<string, string> = {
  teratasi: "text-siber-bright",
  "masih ada": "text-sev-high",
  berubah: "text-sev-medium",
  galat: "text-sev-critical",
};

function downloadJson(r: WebReport) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(r, null, 2)], { type: "application/json" }));
  const a = Object.assign(document.createElement("a"), { href: url, download: `laporan-web-${r.scan_id.slice(0, 12)}.json` });
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

function FindingCard({ f, i, scanId, target }: { f: Finding; i: number; scanId: string; target: string }) {
  const [verif, setVerif] = useState<VerifHasil | null>(null);
  const [cek, setCek] = useState(false);
  const verifikasi = async () => {
    if (!window.confirm(`Verifikasi akan memindai ulang ${target} (pasif, dengan izin Anda). Lanjutkan?`)) return;
    setCek(true);
    setVerif(null);
    try {
      setVerif(await verifikasiTemuan(scanId, f.id, f.judul));
    } catch (e) {
      setVerif({ status: "galat", pesan: (e as Error).message });
    } finally {
      setCek(false);
    }
  };
  return (
    <motion.li
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.15 + i * 0.06 }}
      className="rounded-xl border border-line bg-surface p-4"
    >
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="font-display text-2xl font-semibold leading-tight">{f.judul}</h3>
        <span className="font-data text-xs">
          <span className={TINGKAT_TEXT[f.tingkat]}>{TINGKAT_LABEL[f.tingkat].toUpperCase()}</span>
          <span className="text-ink-muted">
            {" · "}
            {f.id}
            {f.kategori && ` · ${f.kategori}`}
          </span>
        </span>
      </div>

      {f.dampak && <p className="mt-1 text-ink-muted">{f.dampak}</p>}

      <LearnMore edu={f.edukasi} />

      <div className="mt-3 rounded-lg border border-siber/30 bg-siber/5 p-3">
        <p className="font-data text-xs text-siber-bright">Perbaikan</p>
        <p className="mt-1 text-sm text-ink">{f.perbaikan}</p>
        {f.cuplikan &&
          Object.entries(f.cuplikan).map(([server, snippet]) => (
            <div key={server} className="mt-2 overflow-hidden rounded-md border border-line bg-bg">
              <div className="flex items-center justify-between px-2 py-1">
                <span className="font-data text-[11px] uppercase tracking-wide text-ink-muted">{server}</span>
                <button
                  type="button"
                  onClick={() => navigator.clipboard?.writeText(snippet)}
                  className="font-data min-h-8 text-[11px] text-siber-bright hover:underline"
                >
                  Salin
                </button>
              </div>
              <pre className="overflow-x-auto whitespace-pre-wrap break-all border-t border-line px-2 py-1.5 font-data text-[11px] text-ink">
                {snippet}
              </pre>
            </div>
          ))}
      </div>

      {!!f.bukti.length && (
        <ul aria-label="Bukti" className="mt-3 flex flex-wrap gap-1.5">
          {f.bukti.map((b) => (
            <li key={b} className="font-data break-all rounded-sm bg-surface-2 px-2 py-0.5 text-xs">
              {b}
            </li>
          ))}
        </ul>
      )}

      <div className="font-data mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-ink-muted">
        {f.lokasi && <span className="break-all">{f.lokasi}</span>}
        {f.cwe && <span>{f.cwe}</span>}
        <span>keyakinan {f.keyakinan}</span>
        {f.referensi.map((r) => (
          <a key={r} href={r} target="_blank" rel="noreferrer" className="text-siber-bright underline-offset-2 hover:underline">
            {hostOf(r) ?? "referensi"}
          </a>
        ))}
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2 print:hidden">
        <button
          type="button"
          onClick={verifikasi}
          disabled={cek}
          className="font-data min-h-8 rounded-md border border-siber/50 bg-siber/10 px-2.5 text-[11px] text-siber-bright hover:bg-siber/20 disabled:opacity-50"
        >
          {cek ? "Memverifikasi…" : "Verifikasi perbaikan"}
        </button>
        {verif && <span className={`font-data text-[11px] ${VERIF_STYLE[verif.status] ?? "text-ink-muted"}`}>{verif.pesan}</span>}
      </div>
    </motion.li>
  );
}

export default function WebResultPage() {
  const { id } = useParams<{ id: string }>();
  const [r, setR] = useState<WebReport | null>(null);
  const [beda, setBeda] = useState<WebDiff | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getWebscan(id)
      .then(setR)
      .catch((e) => setError((e as Error).message));
  }, [id]);

  // bandingkan otomatis dengan pemeriksaan sebelumnya pada target yang sama (bila ada)
  useEffect(() => {
    if (!r) return;
    listWebscans()
      .then((hist) => {
        const prev = hist.find((s) => s.target === r.target && s.scan_id !== r.scan_id && s.scanned_at < r.scanned_at);
        if (prev) return diffWebscan(r.scan_id, prev.scan_id).then(setBeda);
      })
      .catch(() => {});
  }, [r]);

  return (
    <>
      <ModuleHeader active="web" />
      <main className="mx-auto flex max-w-[1200px] flex-col gap-6 px-4 py-10 md:px-6">
        <Link href="/web" className="font-data text-xs text-ink-muted hover:text-ink print:hidden">
          ← Periksa web lain
        </Link>
        {error && (
          <p role="alert" className="text-sev-critical">
            {error} Pastikan service web-scanner aktif, atau kembali ke riwayat.
          </p>
        )}
        {!r && !error && <p className="text-ink-muted">Memuat laporan…</p>}

        {r && (
          <>
            <motion.section
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              aria-label="Ringkasan postur"
              className={`flex flex-col gap-4 rounded-2xl border p-6 md:flex-row md:items-center md:justify-between ${POSTUR_STYLE[r.ringkasan.postur]}`}
            >
              <div className="min-w-0">
                <p className="font-data text-xs uppercase tracking-[0.12em]">Postur {r.ringkasan.postur}</p>
                <h1 className="font-display mt-1 break-all text-3xl font-bold text-ink md:text-4xl">{r.target}</h1>
                <p className="mt-2 max-w-2xl text-ink">{POSTUR_SUMMARY[r.ringkasan.postur]}</p>
              </div>
              <div className="shrink-0 text-center">
                <p className="font-display text-7xl font-bold leading-none">{r.temuan.length}</p>
                <p className="font-data text-xs">temuan</p>
              </div>
            </motion.section>

            {beda && (
              <DiffCard
                baru={beda.baru}
                hilang={beda.hilang}
                tetap={beda.tetap}
                waktuLama={formatTime(beda.pembanding.lama.scanned_at)}
                deltaText={`Postur ${beda.delta.postur_lama} → ${beda.delta.postur_baru}, temuan ${beda.delta.temuan_lama} → ${beda.delta.temuan_baru}.`}
              />
            )}

            <motion.section
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.1 }}
              aria-labelledby="akhir-title"
              className="rounded-2xl border border-line bg-surface p-5 md:p-6"
            >
              <p className="font-data text-xs uppercase tracking-[0.12em] text-ink-muted">Analisa akhir otomatis</p>
              <h2 id="akhir-title" className="font-display mt-1 text-4xl font-bold">
                {r.analisa_akhir.status}
              </h2>
              <div className="mt-4 grid gap-6 text-ink md:grid-cols-2">
                <div>
                  <h3 className="font-data text-xs text-ink-muted">Mengapa</h3>
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
                    {r.analisa_akhir.alasan.map((x) => (
                      <li key={x}>{x}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3 className="font-data text-xs text-ink-muted">Yang perlu Anda lakukan</h3>
                  <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm">
                    {r.analisa_akhir.saran.map((x) => (
                      <li key={x}>{x}</li>
                    ))}
                  </ol>
                </div>
              </div>
            </motion.section>

            <ComplianceCard k={r.konteks_kepatuhan} />

            {!!r.tahap_gagal?.length && (
              <div role="alert" className="rounded-lg border border-sev-high/50 bg-sev-high/10 p-4 text-sm">
                <p className="font-semibold text-sev-high">Pemeriksaan tidak lengkap</p>
                <p className="mt-1 text-ink">
                  Bagian berikut tidak dapat diambil, sehingga sebagian kelemahan mungkin belum terlihat:
                </p>
                <ul className="font-data mt-2 list-disc pl-5 text-xs text-ink-muted">
                  {r.tahap_gagal.map((g) => (
                    <li key={g} className="break-all">
                      {g}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <section aria-labelledby="temuan-title" className="flex flex-col gap-3">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <h2 id="temuan-title" className="font-display text-3xl font-bold">
                  Temuan ({r.temuan.length})
                </h2>
                <div className="flex gap-2 print:hidden">
                  <button
                    type="button"
                    onClick={() => window.print()}
                    className="font-data min-h-11 rounded-md border border-siber/50 bg-siber/10 px-3 text-xs text-siber-bright hover:bg-siber/20"
                  >
                    Cetak / PDF
                  </button>
                  <button
                    type="button"
                    onClick={() => downloadJson(r)}
                    className="font-data min-h-11 rounded-md border border-gold/50 bg-gold/10 px-3 text-xs text-gold hover:bg-gold/20"
                  >
                    Unduh laporan JSON
                  </button>
                </div>
              </div>
              {r.temuan.length === 0 && (
                <p className="rounded-md border border-dashed border-line p-6 text-ink-muted">
                  Tidak ada kelemahan pasif yang terdeteksi. Ini berarti tidak ditemukan indikator, bukan jaminan aman.
                </p>
              )}
              <ul className="flex flex-col gap-3">
                {r.temuan.map((f, i) => (
                  <FindingCard key={f.judul} f={f} i={i} scanId={r.scan_id} target={r.target} />
                ))}
              </ul>
            </section>

            <section aria-labelledby="meta-title" className="rounded-xl border border-line bg-surface p-4">
              <h2 id="meta-title" className="font-display text-2xl font-bold">
                Pemeriksaan
              </h2>
              <dl className="mt-3 flex flex-col gap-1.5">
                <Row label="Target" value={<span className="font-data break-all text-xs">{r.target}</span>} />
                <Row
                  label="Per tingkat"
                  value={
                    <span className="flex flex-wrap gap-1.5">
                      {ORDER.filter((t) => r.ringkasan.jumlah[t]).map((t) => (
                        <span key={t} className={`font-data rounded-sm border px-2 py-0.5 text-xs ${TINGKAT_STYLE[t]}`}>
                          {TINGKAT_LABEL[t]} {r.ringkasan.jumlah[t]}
                        </span>
                      ))}
                      {!r.temuan.length && <span className="text-ink-muted">-</span>}
                    </span>
                  }
                />
                <Row label="Diperiksa" value={formatTime(r.scanned_at)} />
                <Row label="Skema" value={<span className="font-data text-xs">{r.schema_version}</span>} />
                {r.otorisasi && (
                  <Row
                    label="Otorisasi"
                    value={
                      <span>
                        ✓ Izin dikonfirmasi{r.otorisasi.operator ? ` · operator ${r.otorisasi.operator}` : ""}{" "}
                        <Link href="/web/audit" className="text-siber-bright underline-offset-2 hover:underline">
                          lihat jejak audit
                        </Link>
                      </span>
                    }
                  />
                )}
              </dl>
            </section>

            <p className="text-sm text-ink-muted">{r.catatan}</p>
          </>
        )}
      </main>
    </>
  );
}
