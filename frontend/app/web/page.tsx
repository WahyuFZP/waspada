"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ModuleHeader } from "@/components/module-header";
import { formatTime } from "@/lib/api";
import { listWebscans, POSTUR_STYLE, scanWeb, type WebSummary } from "@/lib/web";

export default function WebScanPage() {
  const router = useRouter();
  const [target, setTarget] = useState("");
  const [authorized, setAuthorized] = useState(false);
  const [periksaBerkas, setPeriksaBerkas] = useState(true);
  const [periksaTls, setPeriksaTls] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<WebSummary[] | null>(null);
  const [historyError, setHistoryError] = useState(false);

  useEffect(() => {
    listWebscans()
      .then(setHistory)
      .catch(() => setHistoryError(true));
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (busy || !target.trim() || !authorized) return;
    setError(null);
    setBusy(true);
    try {
      const r = await scanWeb({ target: target.trim(), authorized, periksa_berkas: periksaBerkas, periksa_tls: periksaTls });
      router.push(`/web/${r.scan_id}`);
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  }

  return (
    <>
      <ModuleHeader active="web" />
      <main className="mx-auto flex max-w-[1200px] flex-col gap-8 px-4 py-10 md:px-6">
        <header className="max-w-3xl">
          <h1 className="font-display text-4xl font-bold leading-tight md:text-6xl">Periksa keamanan web Anda</h1>
          <p className="mt-3 text-ink-muted md:text-lg">
            Masukkan alamat aplikasi web milik Anda sendiri atau yang Anda diizinkan menguji. Pemeriksaan bersifat{" "}
            <span className="text-gold">pasif</span>: hanya mengambil respons dan mengamatinya — tidak menyerang, tidak
            mengubah data. Hasilnya berupa kelemahan untuk ditinjau beserta saran perbaikan.
          </p>
        </header>

        <section aria-label="Pindai web">
          <form onSubmit={submit} className="flex flex-col gap-4 rounded-2xl border border-line bg-surface p-5 md:p-6">
            <label className="flex flex-col gap-2">
              <span className="font-data text-xs text-ink-muted">Alamat target</span>
              <input
                type="url"
                inputMode="url"
                required
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder="http://localhost:3000"
                disabled={busy}
                className="min-h-12 rounded-lg border border-line bg-bg px-4 font-data text-sm outline-none focus:border-siber disabled:opacity-60"
              />
            </label>

            <label className="flex items-start gap-3 rounded-lg border border-gold/40 bg-gold/5 p-3">
              <input
                type="checkbox"
                checked={authorized}
                onChange={(e) => setAuthorized(e.target.checked)}
                disabled={busy}
                className="mt-0.5 h-4 w-4 shrink-0 accent-gold"
              />
              <span className="text-sm">
                Saya memiliki atau diizinkan menguji situs ini.
                <span className="mt-0.5 block text-xs text-ink-muted">
                  Memindai web milik orang lain tanpa izin melanggar UU ITE. Tanpa centang ini, pemeriksaan ditolak.
                </span>
              </span>
            </label>

            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={periksaBerkas}
                onChange={(e) => setPeriksaBerkas(e.target.checked)}
                disabled={busy}
                className="h-4 w-4 shrink-0 accent-siber"
              />
              <span className="text-sm">
                Cek berkas sensitif yang mungkin terekspos (<span className="font-data text-xs">.git</span>,{" "}
                <span className="font-data text-xs">.env</span>, dll.)
              </span>
            </label>

            <label className="flex items-start gap-3">
              <input
                type="checkbox"
                checked={periksaTls}
                onChange={(e) => setPeriksaTls(e.target.checked)}
                disabled={busy}
                className="mt-0.5 h-4 w-4 shrink-0 accent-siber"
              />
              <span className="text-sm">
                Periksa TLS lanjutan (protokol usang, cipher lemah, tanpa PFS)
                <span className="mt-0.5 block text-xs text-ink-muted">
                  Pemeriksaan ini <span className="text-gold">AKTIF</span> — membuka beberapa koneksi handshake ke
                  server (bukan pasif). Jalankan hanya pada aset milik Anda atau yang Anda diizinkan menguji.
                </span>
              </span>
            </label>

            <div className="flex flex-wrap items-center gap-3">
              <button
                type="submit"
                disabled={busy || !target.trim() || !authorized}
                className="font-display min-h-12 rounded-lg bg-gold px-6 text-base font-semibold text-bg transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {busy ? "Memeriksa…" : "Periksa sekarang"}
              </button>
              {busy && <span className="font-data text-xs text-ink-muted">Mengambil respons & mengamati…</span>}
            </div>
          </form>
          <p role="status" className="mt-3 min-h-6 text-sm text-sev-critical">
            {error && `Gagal memeriksa: ${error}`}
          </p>
        </section>

        <section aria-labelledby="riwayat-title" className="flex flex-col gap-3">
          <h2 id="riwayat-title" className="font-display text-3xl font-bold">
            Riwayat pemeriksaan
          </h2>
          {historyError && (
            <p className="text-sev-critical">
              Riwayat tidak dapat dimuat. Pastikan service web-scanner aktif (port 8002).
            </p>
          )}
          {!history && !historyError && <p className="text-ink-muted">Memuat riwayat…</p>}
          {history?.length === 0 && (
            <p className="rounded-md border border-dashed border-line p-6 text-ink-muted">
              Belum ada web yang diperiksa. Masukkan alamat di atas untuk memulai.
            </p>
          )}
          {!!history?.length && (
            <div className="overflow-x-auto rounded-xl border border-line">
              <table className="w-full min-w-[560px] text-left text-sm">
                <thead className="font-data text-xs text-ink-muted">
                  <tr className="border-b border-line">
                    <th className="px-4 py-3 font-normal">Target</th>
                    <th className="px-4 py-3 font-normal">Postur</th>
                    <th className="px-4 py-3 font-normal">Temuan</th>
                    <th className="px-4 py-3 font-normal">Waktu</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((s) => (
                    <tr key={s.scan_id} className="border-b border-line last:border-0 hover:bg-surface-2">
                      <td className="px-4 py-3">
                        <Link
                          href={`/web/${s.scan_id}`}
                          className="font-data break-all underline-offset-4 hover:underline"
                        >
                          {s.target}
                        </Link>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`font-data rounded-sm border px-2 py-0.5 text-xs capitalize ${POSTUR_STYLE[s.postur]}`}>
                          {s.postur}
                        </span>
                      </td>
                      <td className="font-data px-4 py-3">{s.jumlah_temuan}</td>
                      <td className="font-data px-4 py-3 text-xs text-ink-muted">{formatTime(s.scanned_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </>
  );
}
