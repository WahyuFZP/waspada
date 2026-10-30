"""Skor berbasis bukti (PRD §8): setiap poin berasal dari rule yang terpicu."""


def score(findings):
    total = min(100, sum(f.bobot for f in findings))
    level = "Tinggi" if total >= 60 else "Sedang" if total >= 30 else "Rendah"
    return total, level
