"""Diff antar-pemeriksaan (#10): bandingkan dua laporan tersimpan -> temuan BARU/HILANG/TETAP + delta.
Fungsi murni, tanpa scan/storage baru. Temuan di-key per rule_id (satu rule = satu temuan per laporan)."""


def _key(f):
    return f["rule_id"]


def diff(lama, baru):
    """lama = laporan acuan (lebih lama), baru = laporan sekarang. baru muncul = regresi, hilang = teratasi."""
    kl = {_key(f): f for f in lama.get("temuan", [])}
    kb = {_key(f): f for f in baru.get("temuan", [])}
    return {
        "baru": [f for k, f in kb.items() if k not in kl],
        "hilang": [f for k, f in kl.items() if k not in kb],
        "tetap": [f for k, f in kb.items() if k in kl],
        "delta": {"skor_lama": lama.get("skor"), "skor_baru": baru.get("skor"),
                  "level_lama": lama.get("level_risiko"), "level_baru": baru.get("level_risiko"),
                  "temuan_lama": len(lama.get("temuan", [])), "temuan_baru": len(baru.get("temuan", []))},
        "pembanding": {"lama": {"scan_id": lama.get("scan_id"), "scanned_at": lama.get("scanned_at")},
                       "baru": {"scan_id": baru.get("scan_id"), "scanned_at": baru.get("scanned_at")}},
    }
