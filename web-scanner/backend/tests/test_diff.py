"""Tes diff antar-pemeriksaan (#10) web: BARU/HILANG/TETAP + delta. Fungsi murni."""
from diff import diff


def _rep(sid, postur, tertinggi, temuan):
    return {"scan_id": sid, "scanned_at": sid, "target": "https://x",
            "ringkasan": {"postur": postur, "tertinggi": tertinggi, "jumlah": {}}, "temuan": temuan}


A = {"id": "W-A02-01", "judul": "Situs dilayani lewat HTTP tanpa enkripsi", "tingkat": "tinggi"}
B = {"id": "W-H03", "judul": "Berkas sensitif terekspos: /.env", "tingkat": "kritis"}
C = {"id": "W-H05", "judul": "X-Content-Type-Options tidak ada", "tingkat": "rendah"}


def test_diff_classifies_new_resolved_unchanged():
    lama = _rep("lama", "perlu perbaikan", "tinggi", [A, C])  # A dilayani HTTP + C
    baru = _rep("baru", "buruk", "kritis", [B, C])            # A teratasi, B regresi, C tetap
    d = diff(lama, baru)
    assert [f["id"] for f in d["baru"]] == ["W-H03"]
    assert [f["id"] for f in d["hilang"]] == ["W-A02-01"]
    assert [f["id"] for f in d["tetap"]] == ["W-H05"]
    assert d["delta"]["tertinggi_lama"] == "tinggi" and d["delta"]["tertinggi_baru"] == "kritis"


def test_identical_reports_no_change():
    r = _rep("x", "baik", "info", [C])
    d = diff(r, r)
    assert d["baru"] == [] and d["hilang"] == [] and len(d["tetap"]) == 1
