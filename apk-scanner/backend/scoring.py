"""Skor berbasis bukti (PRD §8): setiap poin berasal dari rule yang terpicu."""

# Kapabilitas umum (native/.so, FCM, baca identitas) lazim di aplikasi sah (Flutter, Firebase, analitik).
# Kontribusinya ke skor risiko DIBATASI agar app sah tak dicap berbahaya; indikator berisiko nyata
# (non-kapabilitas) tetap dihitung penuh, jadi deteksi malware tidak melemah (lihat tests/test_scoring.py).
KAP_MAKS = 29  # kapabilitas umum sendirian: maksimal "Rendah" (di bawah ambang Sedang = 30)


def score(findings):
    real = sum(f.bobot for f in findings if not f.kapabilitas)
    kap = sum(f.bobot for f in findings if f.kapabilitas)
    total = min(100, real + min(kap, KAP_MAKS))
    level = "Tinggi" if total >= 60 else "Sedang" if total >= 30 else "Rendah"
    return total, level
