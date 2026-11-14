"""Analisa Akhir berbahasa awam untuk pemilik aplikasi (mencerminkan apk-scanner/final.py)."""
from scoring import PERINGKAT

STATUS = {"kritis": "Perlu perbaikan segera", "tinggi": "Perlu perbaikan segera",
          "sedang": "Beberapa hal perlu dibenahi", "rendah": "Beberapa hal perlu dibenahi",
          "info": "Tidak ditemukan masalah berarti"}


def conclude(findings, nilai):
    if not findings:
        return {"status": "Tidak ditemukan masalah berarti",
                "alasan": ["Pemeriksaan pasif tidak menemukan kelemahan. Ini bukan jaminan aman — "
                           "cek aktif (ZAP/Nuclei) dan tinjauan logika bisnis tetap perlu."],
                "saran": ["Pertahankan konfigurasi; jalankan pemeriksaan ulang secara berkala."]}
    serius = [f"{f.judul} ({f.id})." for f in findings if f.tingkat in ("kritis", "tinggi")]
    urut = sorted(findings, key=lambda f: PERINGKAT[f.tingkat], reverse=True)
    return {
        "status": STATUS[nilai["tertinggi"]],
        "alasan": serius or [f"{len(findings)} temuan tingkat rendah/sedang yang perlu dibenahi."],
        "saran": list(dict.fromkeys(f.perbaikan for f in urut))[:4],  # 4 langkah paling berdampak, tanpa duplikat
    }
