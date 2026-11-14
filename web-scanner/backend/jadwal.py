"""Logika murni penjadwal re-scan (#19): kapan jatuh tempo, dan apakah hasil = regresi.

Tidak memindai/menyimpan apa pun sendiri (itu tugas endpoint di main.py) — hanya keputusan,
agar mudah diuji. "Regresi" = postur memburuk ATAU muncul temuan serius baru dibanding scan sebelumnya.
"""
from datetime import datetime, timedelta

from scoring import PERINGKAT  # info<rendah<sedang<tinggi<kritis


def jatuh_tempo(row, now):
    """now = datetime aware. Belum pernah dijalankan -> jatuh tempo; selain itu bila sudah lewat interval."""
    if not row.get("last_run"):
        return True
    return now - datetime.fromisoformat(row["last_run"]) >= timedelta(hours=float(row["interval_jam"]))


def nilai_regresi(d):
    """d = diff.diff(lama, baru) -> (status, detail). status: regresi | membaik | tetap."""
    delta = d["delta"]
    rb, rl = PERINGKAT.get(delta["tertinggi_baru"], 0), PERINGKAT.get(delta["tertinggi_lama"], 0)
    serius_baru = [f for f in d["baru"] if f["tingkat"] in ("tinggi", "kritis")]
    if rb > rl or serius_baru:
        sebab = []
        if rb > rl:
            sebab.append(f"postur memburuk ({delta['tertinggi_lama']} → {delta['tertinggi_baru']})")
        if serius_baru:
            sebab.append(f"{len(serius_baru)} temuan serius baru")
        return "regresi", "; ".join(sebab)
    if rb < rl or (d["hilang"] and not d["baru"]):
        return "membaik", f"postur {delta['tertinggi_lama']} → {delta['tertinggi_baru']}, {len(d['hilang'])} temuan teratasi"
    return "tetap", "tidak ada perubahan berarti"
