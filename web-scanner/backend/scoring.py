"""Postur risiko dari temuan. Berbasis bukti: satu kerentanan kritis sudah serius, jadi postur
ditentukan tingkat tertinggi + jumlah per tingkat, bukan sekadar penjumlahan."""
from collections import Counter

PERINGKAT = {"info": 0, "rendah": 1, "sedang": 2, "tinggi": 3, "kritis": 4}
POSTUR = {"kritis": "buruk", "tinggi": "buruk", "sedang": "perlu perbaikan", "rendah": "cukup", "info": "baik"}


def nilai(findings):
    if not findings:
        return {"postur": "baik", "tertinggi": "info", "jumlah": {}}
    tertinggi = max(findings, key=lambda f: PERINGKAT[f.tingkat]).tingkat
    return {"postur": POSTUR[tertinggi], "tertinggi": tertinggi,
            "jumlah": dict(Counter(f.tingkat for f in findings))}
