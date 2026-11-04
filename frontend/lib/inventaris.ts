// Inventaris aset lintas-pemeriksa (#17): gabungkan riwayat web + apk menjadi satu baris per ASET
// (bukan per scan — "bersihkan baris ganda"), dengan postur terakhirnya. Murni turunan dari dua endpoint
// daftar yang sudah ada (/webscans, /scans); tidak ada data baru di backend.
import { LEVEL_STYLE, type Level, type ScanSummary } from "@/lib/apk";
import { POSTUR_STYLE, type Postur, type WebSummary } from "@/lib/web";

export type AsetRow = {
  kunci: string; // kunci dedup, mis. "web:contoh.example" / "apk:com.contoh.app"
  tipe: "web" | "apk";
  nama: string; // host (web) / package (apk)
  postur: string; // label pita: postur web | level_risiko apk
  style: string; // kelas badge (POSTUR_STYLE / LEVEL_STYLE)
  rank: number; // 0..4, menyeragamkan severity web & apk untuk urut + ember portofolio
  jumlahScan: number;
  terakhir: string; // scanned_at scan terbaru aset ini
  href: string; // /web/{id} | /apk/{id} dari scan terbaru
};

// Seragamkan dua skala pita ke 0..4 agar aset web & apk bisa diurut bersama (makin tinggi makin berisiko).
const RANK_WEB: Record<Postur, number> = { buruk: 4, "perlu perbaikan": 2, cukup: 1, baik: 0 };
const RANK_APK: Record<Level, number> = { Tinggi: 4, Sedang: 2, Rendah: 0 };

// Aset web = origin (host:port), bukan URL lengkap: scan http/https atau path berbeda = satu aset yang sama.
function kunciWeb(target: string): string {
  try {
    return new URL(target).host || target;
  } catch {
    return target;
  }
}

function tambah(map: Map<string, AsetRow>, row: AsetRow) {
  const ada = map.get(row.kunci);
  if (!ada) {
    map.set(row.kunci, row);
    return;
  }
  const jumlah = ada.jumlahScan + 1;
  if (row.terakhir > ada.terakhir) {
    row.jumlahScan = jumlah; // pendatang lebih baru -> ia yang mewakili aset
    map.set(row.kunci, row);
  } else {
    ada.jumlahScan = jumlah; // yang tersimpan lebih baru; cukup tambah hitungan
  }
}

export function bangunInventaris(web: WebSummary[], apk: ScanSummary[]): AsetRow[] {
  const map = new Map<string, AsetRow>();
  for (const s of web) {
    const nama = kunciWeb(s.target);
    tambah(map, {
      kunci: `web:${nama}`, tipe: "web", nama, postur: s.postur, style: POSTUR_STYLE[s.postur],
      rank: RANK_WEB[s.postur], jumlahScan: 1, terakhir: s.scanned_at, href: `/web/${s.scan_id}`,
    });
  }
  for (const s of apk) {
    const id = s.package || s.sha256; // laporan lama tanpa package: pakai sha256 agar tetap muncul
    tambah(map, {
      kunci: `apk:${id}`, tipe: "apk", nama: s.package || s.nama, postur: s.level_risiko,
      style: LEVEL_STYLE[s.level_risiko], rank: RANK_APK[s.level_risiko], jumlahScan: 1,
      terakhir: s.scanned_at, href: `/apk/${s.scan_id}`,
    });
  }
  return [...map.values()].sort((a, b) => b.rank - a.rank || b.terakhir.localeCompare(a.terakhir));
}

export function ringkasPortofolio(rows: AsetRow[]) {
  return {
    total: rows.length,
    tinggi: rows.filter((r) => r.rank === 4).length, // web buruk / apk Tinggi
    perhatian: rows.filter((r) => r.rank === 2).length, // web perlu perbaikan / apk Sedang
    rapi: rows.filter((r) => r.rank <= 1).length, // web baik·cukup / apk Rendah
  };
}
