// Kontrak dengan apk-scanner/backend (schema laporan PRD v1.2 §9).
export const APK_API = process.env.NEXT_PUBLIC_APK_API_URL ?? "http://localhost:8001";

export type Level = "Rendah" | "Sedang" | "Tinggi";

export type Finding = {
  rule_id: string;
  judul: string;
  tingkat: "rendah" | "sedang" | "tinggi";
  bobot: number;
  bukti: string[];
  penjelasan: string;
};

export type Verdict = "Berbahaya" | "Mencurigakan" | "Tidak ditemukan indikasi berbahaya";

export type FinalAnalysis = {
  status: Verdict;
  alasan: string[];
  saran: string[];
  intel: { status: "dikenal_malware" | "tidak_ditemukan" | "dilewati" | "galat"; keterangan: string };
  // kosong bila sertifikat tidak terbaca
  sertifikat: { skema?: string[]; subjek?: string | null; sha256?: string | null; berlaku_hingga?: string | null; debug?: boolean };
  domain: { domain: string; jumlah: number; kategori: "aplikasi" | "dikenal" | "lainnya" }[];
};

export type ScanResult = {
  schema_version: string;
  scan_id: string;
  scanned_at: string;
  file: { nama: string; ukuran_bytes: number; sha256: string };
  aplikasi: { package: string; version_name: string | null; version_code: number | null; min_sdk: number | null; target_sdk: number | null };
  permission: { semua: string[]; berbahaya: string[] };
  packer: { terdeteksi: boolean; detail: string[]; info_lain: Record<string, string[]>; galat?: string };
  url_ip: string[];
  temuan: Finding[];
  skor: number;
  level_risiko: Level;
  analisa_akhir?: FinalAnalysis; // tidak ada di laporan lama
  tahap_gagal?: string[]; // tidak ada di laporan lama
  catatan: string;
};

export type ScanSummary = Pick<ScanResult, "scan_id" | "scanned_at" | "skor" | "level_risiko"> & { nama: string; sha256: string };

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${APK_API}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(res.status === 404 ? "Laporan tidak ditemukan." : `HTTP ${res.status}`);
  return res.json();
}

export const listScans = () => get<ScanSummary[]>("/scans");
export const getScan = (id: string) => get<ScanResult>(`/scans/${encodeURIComponent(id)}`);

// XHR (bukan fetch) karena hanya XHR yang memberi progres unggah
export function scanApk(file: File, onProgress: (pct: number) => void): Promise<ScanResult> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${APK_API}/scan`);
    xhr.upload.onprogress = (e) => e.lengthComputable && onProgress(Math.round((e.loaded / e.total) * 100));
    xhr.onload = () => {
      let body: { detail?: string } & Partial<ScanResult> = {};
      try {
        body = JSON.parse(xhr.responseText);
      } catch {}
      if (xhr.status >= 200 && xhr.status < 300) resolve(body as ScanResult);
      else reject(new Error(body.detail ?? `HTTP ${xhr.status}`));
    };
    xhr.onerror = () => reject(new Error("Server pemeriksa APK tidak dapat dijangkau. Pastikan service apk-scanner aktif."));
    const form = new FormData();
    form.append("file", file);
    xhr.send(form);
  });
}

export const LEVEL_STYLE: Record<Level, string> = {
  Rendah: "border-siber-bright/50 bg-siber-bright/10 text-siber-bright",
  Sedang: "border-sev-medium/50 bg-sev-medium/10 text-sev-medium",
  Tinggi: "border-sev-critical/60 bg-sev-critical/15 text-sev-critical",
};

export const kb = (n: number) => (n < 1024 * 1024 ? `${(n / 1024).toFixed(0)} KB` : `${(n / 1024 / 1024).toFixed(1)} MB`);
