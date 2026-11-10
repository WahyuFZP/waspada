import { formatTime } from "@/lib/api";
import type { Event } from "@/lib/types";

type Row = { ip: string; count: number; last: string; geo: Event["geo"] };

// Siapa yang menyerang dan dari mana: IP sumber di log keamanan (SSH, Suricata), dikelompokkan dan diberi
// negara & pemilik jaringan oleh backend (DB-IP Lite, offline). IP internal dan rentang khusus diberi label
// apa adanya, tidak pernah ditebak lokasinya.
function place(geo: Event["geo"]) {
  if (!geo) return { where: "Belum ada data lokasi", owner: "Event lama, sebelum fitur GeoIP" };
  if (geo.scope === "internal") return { where: "Jaringan internal", owner: "Perangkat di dalam satuan" };
  if (geo.scope === "reserved") return { where: "Rentang khusus", owner: "IP dokumentasi/simulasi, bukan milik siapa pun" };
  return {
    where: geo.country ? `${geo.country} (${geo.country_code})` : "Negara tidak diketahui",
    owner: geo.org ? `AS${geo.asn} ${geo.org}` : "Pemilik jaringan tidak diketahui",
  };
}

export function AttackerIps({ events, loaded }: { events: Event[]; loaded: boolean }) {
  const byIp = new Map<string, Row>();
  for (const e of events) {
    if (!e.src_ip) continue;
    const row = byIp.get(e.src_ip);
    // events terurut terbaru dulu: event pertama yang ditemui = kejadian terakhir dari IP itu
    if (row) row.count += 1;
    else byIp.set(e.src_ip, { ip: e.src_ip, count: 1, last: e.timestamp, geo: e.geo });
  }
  const rows = [...byIp.values()].sort((a, b) => b.count - a.count).slice(0, 8);

  return (
    <section aria-labelledby="ip-title" className="flex flex-col gap-3">
      <h2 id="ip-title" className="font-pixel text-xl font-bold md:text-2xl">
        Asal IP penyerang
      </h2>
      {!loaded && <p className="text-ink-muted">Memuat kejadian…</p>}
      {loaded && rows.length === 0 && (
        <p className="rounded-md border border-dashed border-line p-4 text-ink-muted">
          Belum ada log keamanan dengan IP sumber. Login SSH dan peringatan Suricata akan tampil di sini beserta negara
          dan pemilik jaringannya.
        </p>
      )}
      {rows.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-line">
          <table className="w-full min-w-[620px] text-left text-base">
            <thead className="font-data text-xs text-ink-muted">
              <tr className="border-b border-line">
                <th className="px-4 py-3 font-normal">IP sumber</th>
                <th className="px-4 py-3 font-normal">Lokasi</th>
                <th className="px-4 py-3 font-normal">Pemilik jaringan</th>
                <th className="px-4 py-3 font-normal">Kejadian</th>
                <th className="px-4 py-3 font-normal">Terakhir</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => {
                const p = place(r.geo);
                return (
                  <tr key={r.ip} className="border-b border-line last:border-0">
                    <td className="font-data px-4 py-3">{r.ip}</td>
                    <td className="px-4 py-3">{p.where}</td>
                    <td className="px-4 py-3 text-ink-muted">{p.owner}</td>
                    <td className="font-data px-4 py-3">{r.count}</td>
                    <td className="font-data px-4 py-3 text-xs text-ink-muted">{formatTime(r.last)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      <p className="font-data text-xs text-ink-muted">
        Lokasi IP:{" "}
        <a href="https://db-ip.com" className="underline underline-offset-2 hover:text-ink" target="_blank" rel="noreferrer">
          DB-IP Lite
        </a>{" "}
        (CC BY 4.0), dibaca offline di server WASPADA. IP tidak dikirim ke layanan luar.
      </p>
    </section>
  );
}
