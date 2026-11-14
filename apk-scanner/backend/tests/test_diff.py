"""Tes diff antar-pemeriksaan (#10) apk: BARU/HILANG/TETAP + delta. Fungsi murni."""
from diff import diff


def _rep(sid, skor, level, temuan):
    return {"scan_id": sid, "scanned_at": sid, "skor": skor, "level_risiko": level, "temuan": temuan}


A = {"rule_id": "R11", "judul": "Mengirim data ke bot Telegram", "tingkat": "tinggi"}
B = {"rule_id": "R01", "judul": "Aplikasi dapat membaca SMS", "tingkat": "tinggi"}
C = {"rule_id": "R24", "judul": "Memuat pustaka native (.so)", "tingkat": "sedang"}


def test_diff_classifies_new_resolved_unchanged():
    lama = _rep("lama", 60, "Tinggi", [A, C])
    baru = _rep("baru", 55, "Sedang", [B, C])      # R11 teratasi, R01 regresi, R24 tetap
    d = diff(lama, baru)
    assert [f["rule_id"] for f in d["baru"]] == ["R01"]
    assert [f["rule_id"] for f in d["hilang"]] == ["R11"]
    assert [f["rule_id"] for f in d["tetap"]] == ["R24"]
    assert d["delta"]["skor_lama"] == 60 and d["delta"]["skor_baru"] == 55 and d["delta"]["level_baru"] == "Sedang"


def test_identical_reports_no_change():
    r = _rep("x", 0, "Rendah", [C])
    d = diff(r, r)
    assert d["baru"] == [] and d["hilang"] == [] and len(d["tetap"]) == 1
