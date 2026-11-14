"""Diff antar-pemeriksaan (#10): bandingkan dua laporan tersimpan -> temuan BARU/HILANG/TETAP + delta.
Fungsi murni, tanpa scan/jaringan/storage baru. Temuan di-key per (id, judul) karena satu id bisa
muncul banyak kali (mis. W-H03 per berkas)."""


def _key(f):
    return (f["id"], f["judul"])


def diff(lama, baru):
    """lama = laporan acuan (lebih lama), baru = laporan sekarang. baru muncul = regresi, hilang = teratasi."""
    kl = {_key(f): f for f in lama.get("temuan", [])}
    kb = {_key(f): f for f in baru.get("temuan", [])}
    rl, rb = lama.get("ringkasan", {}), baru.get("ringkasan", {})
    return {
        "baru": [f for k, f in kb.items() if k not in kl],
        "hilang": [f for k, f in kl.items() if k not in kb],
        "tetap": [f for k, f in kb.items() if k in kl],
        "delta": {"postur_lama": rl.get("postur"), "postur_baru": rb.get("postur"),
                  "tertinggi_lama": rl.get("tertinggi"), "tertinggi_baru": rb.get("tertinggi"),
                  "temuan_lama": len(lama.get("temuan", [])), "temuan_baru": len(baru.get("temuan", []))},
        "pembanding": {"lama": {"scan_id": lama.get("scan_id"), "scanned_at": lama.get("scanned_at")},
                       "baru": {"scan_id": baru.get("scan_id"), "scanned_at": baru.get("scanned_at")}},
    }
