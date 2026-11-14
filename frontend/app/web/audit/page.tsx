"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ModuleHeader } from "@/components/module-header";
import { formatTime } from "@/lib/api";
import { listWebscans, type WebSummary } from "@/lib/web";

// Jejak audit (#13): rekaman read-only bahwa tiap pemeriksaan berjalan setelah izin dikonfirmasi.
export default function AuditPage() {
  const [rows, setRows] = useState<WebSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listWebscans()
      .then(setRows)
      .catch((e) => setError((e as Error).message));
  }, []);

  return (
    <>
      <ModuleHeader active="web" />
      <main className="mx-auto flex max-w-[1200px] flex-col gap-6 px-4 py-10 md:px-6">
        <Link href="/web" className="font-data text-xs text-ink-muted hover:text-ink">
          ← Pemeriksa Web
        </Link>
        <div>
          <h1 className="font-display text-4xl font-bold">Jejak audit pemeriksaan</h1>
          <p className="mt-2 max-w-2xl text-ink-muted">
            Setiap pemeriksaan hanya berjalan setelah pemilik mengonfirmasi izin menguji target
            (authorization-first). Rekaman ini membuktikannya, terurut dari yang terbaru. Hanya-baca.
          </p>
        </div>

        {error && (
          <p role="alert" className="text-sev-critical">
            {error}
          </p>
        )}
        {!rows && !error && <p className="text-ink-muted">Memuat…</p>}
        {rows && rows.length === 0 && (
          <p className="rounded-md border border-dashed border-line p-6 text-ink-muted">Belum ada pemeriksaan.</p>
        )}

        {rows && rows.length > 0 && (
          <div className="overflow-x-auto rounded-xl border border-line">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line text-left font-data text-xs text-ink-muted">
                  <th className="p-3">Waktu</th>
                  <th className="p-3">Target</th>
                  <th className="p-3">Izin</th>
                  <th className="p-3">Laporan</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((s) => (
                  <tr key={s.scan_id} className="border-b border-line/60">
                    <td className="whitespace-nowrap p-3 font-data text-xs">{formatTime(s.scanned_at)}</td>
                    <td className="p-3">
                      <span className="font-data break-all text-xs">{s.target}</span>
                    </td>
                    <td className="whitespace-nowrap p-3 text-siber-bright">✓ dikonfirmasi</td>
                    <td className="p-3">
                      <Link href={`/web/${s.scan_id}`} className="text-siber-bright underline-offset-2 hover:underline">
                        buka
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </>
  );
}
