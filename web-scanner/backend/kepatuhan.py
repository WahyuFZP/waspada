"""Konteks kepatuhan & kanal lapor resmi Indonesia (#14) untuk pemilik aset web. Kamus statis terkurasi,
BUKAN nasihat hukum, dan TIDAK melapor otomatis."""

DISCLAIMER = ("Informasi umum untuk membantu menempuh jalur resmi, BUKAN nasihat hukum. Untuk kasus nyata, "
              "simpan bukti dan konsultasikan dengan pihak berwenang atau penasihat hukum.")

_K = {
    "bssn": {"nama": "BSSN / CSIRT",
             "cara": "Laporkan indikasi insiden atau kebocoran ke BSSN (bssn.go.id) atau tim CSIRT instansi Anda."},
    "pdp": {"nama": "Kewajiban pelindungan data (UU PDP)",
            "cara": "Bila data pribadi pengguna berpotensi terdampak, penuhi kewajiban pengamanan & notifikasi sesuai UU PDP."},
}


def konteks(tertinggi, ids):
    """tertinggi = ringkasan['tertinggi']; ids = id temuan terpicu. -> blok konteks atau None."""
    if tertinggi not in ("tinggi", "kritis"):
        return None
    bocor = "W-H03" in ids
    relevansi = ("Kelemahan tinggi/kritis pada aset Anda berisiko kebocoran data. Akses tak sah oleh pihak lain "
                 "diatur UU ITE; bila data pribadi terdampak, berlaku kewajiban UU PDP.") if bocor else (
                 "Kelemahan tinggi/kritis sebaiknya segera diperbaiki sebelum dieksploitasi; akses tak sah oleh "
                 "pihak lain diatur UU ITE.")
    kanal = ["bssn"] + (["pdp"] if bocor else [])
    return {"relevansi": relevansi, "kanal_lapor": [_K[k] for k in kanal], "disclaimer": DISCLAIMER}
