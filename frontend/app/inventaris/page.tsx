"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ModuleHeader } from "@/components/module-header";
import { formatTime } from "@/lib/api";
import { listScans } from "@/lib/apk";
import { bangunInventaris, ringkasPortofolio, type AsetRow } from "@/lib/inventaris";
import { listWebscans } from "@/lib/web";

export default function InventarisPage() {
  const [rows, setRows] = useState<AsetRow[] | null>(null);
  const [error, setError] = useState(false); // kedua service gagal
  const [sebagian, setSebagian] = useState(false); // satu service gagal

  useEffect(() => {
    Promise.allSettled([listWebscans(), listScans()]).then(([w, a]) => {
      if (w.status === "rejected" && a.status === "rejected") {
        setError(true);
        return;
      }
      setSebagian(w.status === "rejected" || a.status === "rejected");
      setRows(
        bangunInventaris(w.status === "fulfilled" ? w.value : [], a.status === "fulfilled" ? a.value : []),
      );
    });
  }, []);

  const ringkas = rows ? ringkasPortofolio(rows) : null;

  return (
    <>
      <ModuleHeader active="inventaris" />
      <main className="mx-auto flex max-w-[1200px] flex-col gap-8 px-4 py-10 md:px-6">
        <header className="max-w-3xl">
          <h1 className="font-display text-4xl font-bold leading-tight md:text-6xl">Inventaris aset</h1>
          <p className="mt-3 text-ink-muted md:text-lg">
            Semua aset yang pernah diperiksa — situs web dan aplikasi — dalam satu daftar ringkas. Tiap aset tampil sekali
            dengan <span className="text-gold">postur terakhirnya</span>, walau diperiksa berkali-kali.
          </p>
        </header>

        {ringkas && (
          <dl className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Tile label="Total aset" value={ringkas.total} />
            <Tile label="Berisiko tinggi" value={ringkas.tinggi} tone={ringkas.tinggi ? "text-sev-critical" : "text-ink"} />
            <Tile label="Perlu perhatian" value={ringkas.perhatian} tone={ringkas.perhatian ? "text-sev-medium" : "text-ink"} />
            <Tile label="Rapi" value={ringkas.rapi} tone="text-siber-bright" />
          </dl>
        )}

        {sebagian && (
          <p className="rounded-md border border-sev-medium/40 bg-sev-medium/5 p-3 text-sm text-ink-muted">
            Sebagian daftar tidak dapat dimuat — satu service pemeriksa mungkin tidak aktif, jadi daftar ini mungkin belum
            lengkap.
          </p>
        )}

        <section aria-labelledby="aset-title" className="flex flex-col gap-3">
          <h2 id="aset-title" className="sr-only">
            Daftar aset
          </h2>
          {error && (
            <p className="text-sev-critical">
              Inventaris tidak dapat dimuat. Pastikan service web-scanner (port 8002) dan apk-scanner (port 8001) aktif.
            </p>
          )}
          {!rows && !error && <p className="text-ink-muted">Memuat inventaris…</p>}
          {rows?.length === 0 && (
            <p className="rounded-md border border-dashed border-line p-6 text-ink-muted">
              Belum ada aset yang diperiksa. Mulai dari{" "}
              <Link href="/web" className="text-gold underline-offset-4 hover:underline">
                Pemeriksa Web
              </Link>{" "}
              atau{" "}
              <Link href="/apk" className="text-gold underline-offset-4 hover:underline">
                Pemeriksa APK
              </Link>
              .
            </p>
          )}
          {!!rows?.length && (
            <div className="overflow-x-auto rounded-xl border border-line">
              <table className="w-full min-w-[640px] text-left text-sm">
                <thead className="font-data text-xs text-ink-muted">
                  <tr className="border-b border-line">
                    <th className="px-4 py-3 font-normal">Aset</th>
                    <th className="px-4 py-3 font-normal">Jenis</th>
                    <th className="px-4 py-3 font-normal">Postur terakhir</th>
                    <th className="px-4 py-3 font-normal">Scan</th>
                    <th className="px-4 py-3 font-normal">Terakhir</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.kunci} className="border-b border-line last:border-0 hover:bg-surface-2">
                      <td className="px-4 py-3">
                        <Link href={r.href} className="font-data break-all underline-offset-4 hover:underline">
                          {r.nama}
                        </Link>
                      </td>
                      <td className="px-4 py-3">
                        <span className="font-data rounded-sm border border-line bg-surface-2 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-ink-muted">
                          {r.tipe}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`font-data rounded-sm border px-2 py-0.5 text-xs capitalize ${r.style}`}>
                          {r.postur}
                        </span>
                      </td>
                      <td className="font-data px-4 py-3">{r.jumlahScan}</td>
                      <td className="font-data px-4 py-3 text-xs text-ink-muted">{formatTime(r.terakhir)}</td>
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

function Tile({ label, value, tone = "text-ink" }: { label: string; value: number; tone?: string }) {
  return (
    <div className="rounded-xl border border-line bg-surface px-4 py-4">
      <dt className="font-data text-[11px] uppercase tracking-[0.12em] text-ink-muted">{label}</dt>
      <dd className={`font-display mt-1 text-4xl font-bold leading-none tabular-nums ${tone}`}>{value}</dd>
    </div>
  );
}
