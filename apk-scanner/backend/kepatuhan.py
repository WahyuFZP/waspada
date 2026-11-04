"""Konteks kepatuhan & kanal lapor resmi Indonesia (#14). Kamus statis terkurasi, BUKAN nasihat hukum,
dan TIDAK melapor otomatis — hanya menjembatani temuan ke jalur RESMI (bukan main hakim sendiri)."""

DISCLAIMER = ("Informasi umum untuk membantu menempuh jalur resmi, BUKAN nasihat hukum. Untuk kasus nyata, "
              "simpan bukti dan konsultasikan dengan pihak berwenang atau penasihat hukum.")

_K = {
    "komdigi": {"nama": "Pengaduan konten Komdigi",
                "cara": "Laporkan aplikasi/konten yang menipu ke aduankonten.id (Kementerian Komunikasi dan Digital)."},
    "bank": {"nama": "Bank / e-wallet resmi yang ditiru",
             "cara": "Hubungi call center resmi penerbit asli agar aplikasi palsu ditindak dan nasabah diperingatkan."},
    "polisi": {"nama": "Kepolisian (patrolisiber.id)",
               "cara": "Bila ada korban atau kerugian, laporkan dugaan penipuan ke patrolisiber.id atau SPKT terdekat."},
    "bssn": {"nama": "BSSN / CSIRT",
             "cara": "Laporkan indikasi insiden siber ke BSSN (bssn.go.id) atau tim CSIRT terkait."},
}


def konteks(status, rule_ids):
    """status = analisa_akhir['status']; rule_ids = id rule terpicu. -> blok konteks atau None."""
    peniru = any(r in ("R13", "R25") for r in rule_ids)
    if status != "Berbahaya" and not peniru:
        return None
    kanal = ["komdigi"] + (["bank"] if peniru else []) + ["polisi", "bssn"]
    return {
        "relevansi": ("Aplikasi yang meniru merek resmi atau memperdaya pengguna dapat menyangkut UU ITE "
                      "(penipuan/manipulasi informasi elektronik) serta ketentuan pidana penipuan."),
        "kanal_lapor": [_K[k] for k in kanal],
        "disclaimer": DISCLAIMER,
    }
