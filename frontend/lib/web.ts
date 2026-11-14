// Kontrak dengan web-scanner/backend (skema laporan web-0.1). Cermin lib/apk.ts.
export const WEB_API = process.env.NEXT_PUBLIC_WEB_API_URL ?? "http://localhost:8002";

export type Tingkat = "info" | "rendah" | "sedang" | "tinggi" | "kritis";
export type Postur = "baik" | "cukup" | "perlu perbaikan" | "buruk";

export type Finding = {
  id: string;
  kategori: string; // referensi OWASP, mis. "A05:2021 Security Misconfiguration"
  judul: string;
  tingkat: Tingkat;
  perbaikan: string;
  bukti: string[];
  lokasi: string;
  cwe: string;
  keyakinan: "rendah" | "sedang" | "tinggi";
  dampak: string;
  referensi: string[];
  cuplikan?: Record<string, string>; // {nginx, apache} konfigurasi siap-tempel (opsional)
  edukasi?: { apa: string; kenapa: string; dampak: string }; // kartu "Pelajari dulu" (opsional)
};

export type Ringkasan = { postur: Postur; tertinggi: Tingkat; jumlah: Partial<Record<Tingkat, number>> };
export type AnalisaAkhir = { status: string; alasan: string[]; saran: string[] };

export type Otorisasi = { dikonfirmasi: boolean; pernyataan: string; target: string; waktu: string; operator: string | null };

export type WebReport = {
  schema_version: string;
  scan_id: string;
  scanned_at: string;
  target: string;
  otorisasi?: Otorisasi; // rekaman authorization-first (#13); opsional untuk laporan lama
  konteks_kepatuhan?: { relevansi: string; kanal_lapor: { nama: string; cara: string }[]; disclaimer: string } | null;
  temuan: Finding[];
  ringkasan: Ringkasan;
  analisa_akhir: AnalisaAkhir;
  tahap_gagal: string[];
  catatan: string;
};

export type WebSummary = Pick<WebReport, "scan_id" | "scanned_at" | "target"> & {
  postur: Postur;
  tertinggi: Tingkat;
  jumlah_temuan: number;
};

export type WebDiff = {
  baru: Finding[];
  hilang: Finding[];
  tetap: Finding[];
  delta: { postur_lama: Postur; postur_baru: Postur; tertinggi_lama: Tingkat; tertinggi_baru: Tingkat; temuan_lama: number; temuan_baru: number };
  pembanding: { lama: { scan_id: string; scanned_at: string }; baru: { scan_id: string; scanned_at: string } };
};

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${WEB_API}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(res.status === 404 ? "Laporan tidak ditemukan." : `HTTP ${res.status}`);
  return res.json();
}

export const listWebscans = () => get<WebSummary[]>("/webscans");
export const getWebscan = (id: string) => get<WebReport>(`/webscans/${encodeURIComponent(id)}`);
export const diffWebscan = (id: string, vs: string) =>
  get<WebDiff>(`/webscans/${encodeURIComponent(id)}/diff?vs=${encodeURIComponent(vs)}`);

export type VerifHasil = { status: "teratasi" | "masih ada" | "berubah" | "galat"; pesan: string; temuan?: Finding | null };
export async function verifikasiTemuan(scanId: string, rule: string, judul: string): Promise<VerifHasil> {
  const res = await fetch(
    `${WEB_API}/webscans/${encodeURIComponent(scanId)}/verifikasi?rule=${encodeURIComponent(rule)}&judul=${encodeURIComponent(judul)}`,
    { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ authorized: true }) },
  );
  const body: { detail?: string } & Partial<VerifHasil> = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail ?? `HTTP ${res.status}`);
  return body as VerifHasil;
}

export type ScanReq = { target: string; authorized: boolean; periksa_berkas: boolean; delay?: number; periksa_tls?: boolean };

export async function scanWeb(req: ScanReq): Promise<WebReport> {
  let res: Response;
  try {
    res = await fetch(`${WEB_API}/webscan`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(req),
    });
  } catch {
    throw new Error("Server pemeriksa web tidak dapat dijangkau. Pastikan service web-scanner aktif (port 8002).");
  }
  const body: { detail?: string } & Partial<WebReport> = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail ?? `HTTP ${res.status}`);
  return body as WebReport;
}

// ---- Penjadwal re-scan (#19) ----
export type Jadwal = {
  id: string;
  target: string;
  host: string;
  interval_jam: number;
  dibuat: string;
  last_run: string | null;
  last_scan_id: string | null;
  status: "regresi" | "membaik" | "tetap" | "baru" | "gagal" | null;
  detail: string | null;
};

export type JadwalRun = {
  dijalankan: number;
  hasil: { target: string; status: string; detail: string; scan_id: string | null }[];
};

export const listJadwal = () => get<Jadwal[]>("/jadwal");

export async function addJadwal(target: string, interval_jam: number): Promise<Jadwal> {
  const res = await fetch(`${WEB_API}/jadwal`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ target, authorized: true, interval_jam }), // authorized: digating checkbox wajib di UI
  });
  const body: { detail?: string } & Partial<Jadwal> = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail ?? `HTTP ${res.status}`);
  return body as Jadwal;
}

export async function delJadwal(id: string): Promise<void> {
  const res = await fetch(`${WEB_API}/jadwal/${encodeURIComponent(id)}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
}

export async function jalankanJadwal(): Promise<JadwalRun> {
  const res = await fetch(`${WEB_API}/jadwal/jalankan`, { method: "POST" });
  const body: { detail?: string } & Partial<JadwalRun> = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail ?? `HTTP ${res.status}`);
  return body as JadwalRun;
}

export const JADWAL_STATUS_STYLE: Record<string, string> = {
  regresi: "border-sev-critical/60 bg-sev-critical/15 text-sev-critical",
  gagal: "border-sev-high/50 bg-sev-high/10 text-sev-high",
  membaik: "border-siber-bright/50 bg-siber-bright/10 text-siber-bright",
  baru: "border-siber/40 bg-siber/10 text-siber-bright",
  tetap: "border-line bg-surface-2 text-ink-muted",
};

// 5 pita tingkat -> token severity yang sudah ada (lihat severity-badge.tsx)
export const TINGKAT_STYLE: Record<Tingkat, string> = {
  kritis: "border-sev-critical/60 bg-sev-critical/15 text-sev-critical",
  tinggi: "border-sev-high/50 bg-sev-high/10 text-sev-high",
  sedang: "border-sev-medium/40 bg-sev-medium/10 text-sev-medium",
  rendah: "border-sev-low/40 bg-sev-low/10 text-sev-low",
  info: "border-line bg-surface-2 text-ink-muted",
};

export const TINGKAT_LABEL: Record<Tingkat, string> = {
  kritis: "Kritis",
  tinggi: "Tinggi",
  sedang: "Sedang",
  rendah: "Rendah",
  info: "Info",
};

export const POSTUR_STYLE: Record<Postur, string> = {
  buruk: "border-sev-critical/60 bg-sev-critical/15 text-sev-critical",
  "perlu perbaikan": "border-sev-medium/50 bg-sev-medium/10 text-sev-medium",
  cukup: "border-sev-low/50 bg-sev-low/10 text-sev-low",
  baik: "border-siber-bright/50 bg-siber-bright/10 text-siber-bright",
};

export const POSTUR_SUMMARY: Record<Postur, string> = {
  buruk: "Ditemukan kelemahan tingkat tinggi atau kritis. Sebaiknya diperbaiki sebelum aplikasi dipakai luas.",
  "perlu perbaikan": "Ada beberapa hal yang perlu dibenahi untuk memperkuat keamanan.",
  cukup: "Hanya kelemahan ringan. Sebaiknya dirapikan saat ada waktu.",
  baik: "Pemeriksaan pasif tidak menemukan kelemahan berarti. Tetap lakukan cek aktif secara berkala.",
};
