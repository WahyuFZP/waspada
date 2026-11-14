"use client";

import { useEffect, useState } from "react";
import { ModuleHeader } from "@/components/module-header";
import { formatTime } from "@/lib/api";
import { addJadwal, delJadwal, JADWAL_STATUS_STYLE, jalankanJadwal, type Jadwal, listJadwal } from "@/lib/web";

export default function JadwalPage() {
  const [rows, setRows] = useState<Jadwal[] | null>(null);
  const [error, setError] = useState(false);
  const [target, setTarget] = useState("");
  const [intervalJam, setIntervalJam] = useState(24);
  const [authorized, setAuthorized] = useState(false);
  const [busy, setBusy] = useState(false);
  const [pesan, setPesan] = useState<string | null>(null);

  const muat = () => listJadwal().then(setRows).catch(() => setError(true));
  useEffect(() => {
    muat();
  }, []);

  async function tambah(e: React.FormEvent) {
    e.preventDefault();
    if (busy || !target.trim() || !authorized) return;
    setBusy(true);
    setPesan(null);
    try {
      await addJadwal(target.trim(), intervalJam);
      setTarget("");
      setAuthorized(false);
      await muat();
    } catch (err) {
      setPesan((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function jalankan() {
    setBusy(true);
    setPesan(null);
    try {
      const h = await jalankanJadwal();
      setPesan(`${h.dijalankan} jadwal yang jatuh tempo dijalankan.`);
      await muat();
    } catch (err) {
      setPesan((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function hapus(id: string) {
    setPesan(null);
    try {
      await delJadwal(id);
      await muat();
    } catch (err) {
      setPesan((err as Error).message);
    }
  }

  const adaRegresi = rows?.some((r) => r.status === "regresi");

  return (
    <>
      <ModuleHeader active="jadwal" />
      <main className="mx-auto flex max-w-[1200px] flex-col gap-8 px-4 py-10 md:px-6">
        <header className="max-w-3xl">
          <h1 className="font-display text-4xl font-bold leading-tight md:text-6xl">Penjadwal re-scan</h1>
          <p className="mt-3 text-ink-muted md:text-lg">
            Jadwalkan pemeriksaan ulang berkala untuk aset web yang Anda miliki atau diizinkan menguji. Pemeriksaan tetap{" "}
            <span className="text-gold">pasif</span>, dan Anda diberi tanda bila posturnya <span className="text-gold">memburuk</span>{" "}
            dibanding pemeriksaan sebelumnya.
          </p>
        </header>

        {adaRegresi && (
          <p role="alert" className="rounded-lg border border-sev-critical/60 bg-sev-critical/10 p-3 text-sm text-sev-critical">
            ⚠ Ada aset dengan regresi keamanan sejak pemeriksaan terakhir — lihat kolom status di bawah.
          </p>
        )}

        <section aria-label="Tambah jadwal">
          <form onSubmit={tambah} className="flex flex-col gap-4 rounded-2xl border border-line bg-surface p-5 md:p-6">
            <div className="flex flex-col gap-4 md:flex-row">
              <label className="flex flex-1 flex-col gap-2">
                <span className="font-data text-xs text-ink-muted">Alamat target</span>
                <input
                  type="url"
                  inputMode="url"
                  required
                  value={target}
                  onChange={(e) => setTarget(e.target.value)}
                  placeholder="https://app-saya.example"
                  disabled={busy}
                  className="min-h-12 rounded-lg border border-line bg-bg px-4 font-data text-sm outline-none focus:border-siber disabled:opacity-60"
                />
              </label>
              <label className="flex flex-col gap-2 md:w-48">
                <span className="font-data text-xs text-ink-muted">Interval (jam)</span>
                <input
                  type="number"
                  min={1}
                  step={1}
                  value={intervalJam}
                  onChange={(e) => setIntervalJam(Math.max(1, Number(e.target.value) || 1))}
                  disabled={busy}
                  className="min-h-12 rounded-lg border border-line bg-bg px-4 font-data text-sm outline-none focus:border-siber disabled:opacity-60"
                />
              </label>
            </div>

            <label className="flex items-start gap-3 rounded-lg border border-gold/40 bg-gold/5 p-3">
              <input
                type="checkbox"
                checked={authorized}
                onChange={(e) => setAuthorized(e.target.checked)}
                disabled={busy}
                className="mt-0.5 h-4 w-4 shrink-0 accent-gold"
              />
              <span className="text-sm">
                Saya memiliki atau diizinkan menguji situs ini, dan menyetujui pemeriksaan ulang berkala atasnya.
                <span className="mt-0.5 block text-xs text-ink-muted">
                  Menjadwalkan = izin berulang. Memindai web orang lain tanpa izin melanggar UU ITE. Jadwal bisa dihapus kapan saja.
                </span>
              </span>
            </label>

            <div>
              <button
                type="submit"
                disabled={busy || !target.trim() || !authorized}
                className="font-display min-h-12 rounded-lg bg-gold px-6 text-base font-semibold text-bg transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Jadwalkan
              </button>
            </div>
          </form>
          <p role="status" className="mt-3 min-h-6 text-sm text-ink-muted">
            {pesan}
          </p>
        </section>

        <section aria-labelledby="jadwal-title" className="flex flex-col gap-3">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <h2 id="jadwal-title" className="font-display text-3xl font-bold">
              Jadwal aktif
            </h2>
            <button
              type="button"
              onClick={jalankan}
              disabled={busy || !rows?.length}
              className="font-data min-h-11 rounded-md border border-siber/50 bg-siber/10 px-3 text-xs text-siber-bright hover:bg-siber/20 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Jalankan yang jatuh tempo sekarang
            </button>
          </div>

          {error && (
            <p className="text-sev-critical">Jadwal tidak dapat dimuat. Pastikan service web-scanner aktif (port 8002).</p>
          )}
          {!rows && !error && <p className="text-ink-muted">Memuat jadwal…</p>}
          {rows?.length === 0 && (
            <p className="rounded-md border border-dashed border-line p-6 text-ink-muted">
              Belum ada jadwal. Tambahkan target di atas untuk memantau posturnya secara berkala.
            </p>
          )}
          {!!rows?.length && (
            <div className="overflow-x-auto rounded-xl border border-line">
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead className="font-data text-xs text-ink-muted">
                  <tr className="border-b border-line">
                    <th className="px-4 py-3 font-normal">Target</th>
                    <th className="px-4 py-3 font-normal">Interval</th>
                    <th className="px-4 py-3 font-normal">Status terakhir</th>
                    <th className="px-4 py-3 font-normal">Dijalankan</th>
                    <th className="px-4 py-3 font-normal" />
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.id} className="border-b border-line last:border-0 align-top hover:bg-surface-2">
                      <td className="px-4 py-3">
                        {r.last_scan_id ? (
                          <a href={`/web/${r.last_scan_id}`} className="font-data break-all underline-offset-4 hover:underline">
                            {r.target}
                          </a>
                        ) : (
                          <span className="font-data break-all">{r.target}</span>
                        )}
                      </td>
                      <td className="font-data whitespace-nowrap px-4 py-3 text-ink-muted">{r.interval_jam} jam</td>
                      <td className="px-4 py-3">
                        {r.status ? (
                          <span className={`font-data rounded-sm border px-2 py-0.5 text-xs capitalize ${JADWAL_STATUS_STYLE[r.status] ?? JADWAL_STATUS_STYLE.tetap}`}>
                            {r.status}
                          </span>
                        ) : (
                          <span className="text-xs text-ink-muted">belum pernah</span>
                        )}
                        {r.detail && <p className="mt-1 max-w-sm text-xs text-ink-muted">{r.detail}</p>}
                      </td>
                      <td className="font-data whitespace-nowrap px-4 py-3 text-xs text-ink-muted">
                        {r.last_run ? formatTime(r.last_run) : "—"}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          type="button"
                          onClick={() => hapus(r.id)}
                          className="font-data text-xs text-ink-muted underline-offset-4 hover:text-sev-critical hover:underline"
                        >
                          Hapus
                        </button>
                      </td>
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
