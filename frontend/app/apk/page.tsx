"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { ApkHeader } from "@/components/apk-header";
import { Phone3D } from "@/components/objects-3d";
import { Reveal } from "@/components/reveal";
import { formatTime } from "@/lib/api";
import { LEVEL_STYLE, listScans, scanApk, type ScanSummary } from "@/lib/apk";

export default function ApkUploadPage() {
  const router = useRouter();
  const input = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);
  const [busy, setBusy] = useState<{ name: string; pct: number } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<ScanSummary[] | null>(null);
  const [historyError, setHistoryError] = useState(false);

  useEffect(() => {
    listScans()
      .then(setHistory)
      .catch(() => setHistoryError(true));
  }, []);

  async function start(file?: File) {
    if (!file || busy) return;
    if (!file.name.toLowerCase().endsWith(".apk")) {
      setError("Pilih file berakhiran .apk.");
      return;
    }
    setError(null);
    setBusy({ name: file.name, pct: 0 });
    try {
      const r = await scanApk(file, (pct) => setBusy({ name: file.name, pct }));
      router.push(`/apk/${r.scan_id}`);
    } catch (e) {
      setError((e as Error).message);
      setBusy(null);
    }
  }

  return (
    <>
      <ApkHeader />
      <main className="mx-auto flex max-w-[1200px] flex-col gap-8 px-4 py-10 md:px-6">
        <header className="grid items-center gap-8 md:grid-cols-[minmax(0,1fr)_auto]">
          <Reveal className="max-w-3xl">
            <h1 className="font-body text-3xl font-bold leading-tight md:text-5xl">Periksa APK sebelum dipasang</h1>
            <p className="mt-3 text-ink-muted md:text-lg">
              Unggah file APK yang didapat di luar Play Store, misalnya kiriman WhatsApp berupa undangan, foto paket, atau
              surat tilang. File hanya dibaca, tidak pernah dipasang atau dijalankan. Hasilnya berupa indikasi untuk
              ditinjau, bukan vonis akhir.
            </p>
          </Reveal>
          {/* di HP disembunyikan: kotak unggah lebih penting di layar sempit, dan progres sudah tertulis di sana */}
          <Phone3D scanning={!!busy} className="ml-36 mr-10 mt-8 hidden h-72 w-40 md:block" />
        </header>

        <Reveal delay={0.1}>
        <section aria-label="Unggah APK">
          <button
            type="button"
            onClick={() => input.current?.click()}
            onDragOver={(e) => {
              e.preventDefault();
              setDrag(true);
            }}
            onDragLeave={() => setDrag(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDrag(false);
              start(e.dataTransfer.files[0]);
            }}
            disabled={!!busy}
            className={`slab flex min-h-52 w-full flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed px-6 text-center ${
              drag ? "border-gold bg-gold/10" : "border-line bg-surface hover:border-siber"
            } disabled:cursor-wait`}
          >
            {busy ? (
              <>
                <span className="font-display text-2xl font-semibold">
                  {busy.pct < 100 ? `Mengunggah ${busy.pct}%` : "Menganalisis…"}
                </span>
                <span className="font-data text-xs text-ink-muted">{busy.name}</span>
                <span aria-hidden className="h-1.5 w-full max-w-sm overflow-hidden rounded-full bg-line">
                  <span className="block h-full bg-gold transition-[width]" style={{ width: `${busy.pct}%` }} />
                </span>
              </>
            ) : (
              <>
                <span className="font-display text-2xl font-semibold">Tarik file APK ke sini</span>
                <span className="text-ink-muted">atau klik untuk memilih file (maks. 150 MB)</span>
              </>
            )}
          </button>
          <input
            ref={input}
            type="file"
            accept=".apk,application/vnd.android.package-archive"
            className="sr-only"
            tabIndex={-1}
            onChange={(e) => {
              start(e.target.files?.[0]);
              e.target.value = "";
            }}
          />
          <p role="status" className="mt-3 min-h-6 text-base text-sev-critical">
            {error && `Gagal memeriksa: ${error}`}
          </p>
        </section>
        </Reveal>

        <Reveal>
        <section aria-labelledby="riwayat-title" className="flex flex-col gap-3">
          <h2 id="riwayat-title" className="font-pixel text-xl font-bold md:text-2xl">
            Riwayat pemeriksaan
          </h2>
          {historyError && (
            <p className="text-sev-critical">
              Riwayat tidak dapat dimuat. Pastikan service apk-scanner aktif (docker compose up apk-scanner).
            </p>
          )}
          {!history && !historyError && <p className="text-ink-muted">Memuat riwayat…</p>}
          {history?.length === 0 && (
            <p className="rounded-md border border-dashed border-line p-6 text-ink-muted">
              Belum ada APK yang diperiksa. Unggah file di atas untuk memulai.
            </p>
          )}
          {!!history?.length && (
            <div className="overflow-x-auto rounded-xl border border-line">
              <table className="w-full min-w-[560px] text-left text-base">
                <thead className="font-data text-xs text-ink-muted">
                  <tr className="border-b border-line">
                    <th className="px-4 py-3 font-normal">File</th>
                    <th className="px-4 py-3 font-normal">Risiko</th>
                    <th className="px-4 py-3 font-normal">Skor</th>
                    <th className="px-4 py-3 font-normal">Waktu</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((s) => (
                    <tr key={s.scan_id} className="border-b border-line last:border-0 hover:bg-surface-2">
                      <td className="px-4 py-3">
                        <Link href={`/apk/${s.scan_id}`} className="underline-offset-4 hover:underline">
                          {s.nama}
                        </Link>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`font-data rounded-sm border px-2 py-0.5 text-xs ${LEVEL_STYLE[s.level_risiko]}`}>
                          {s.level_risiko}
                        </span>
                      </td>
                      <td className="font-data px-4 py-3">{s.skor}</td>
                      <td className="font-data px-4 py-3 text-xs text-ink-muted">{formatTime(s.scanned_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
        </Reveal>
      </main>
    </>
  );
}
