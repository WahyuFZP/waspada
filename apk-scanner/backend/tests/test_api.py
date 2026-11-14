import os
import tempfile

os.environ["DATA_DIR"] = tempfile.mkdtemp()  # sebelum import main: jangan menulis ke data asli

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402

client = TestClient(main.app)


def test_scan_flow_on_real_apk(benign_apk):
    path = benign_apk("com.politedroid_4.apk")
    with open(path, "rb") as fh:
        r = client.post("/scan", files={"file": ("../../undangan nikah.apk", fh, "application/vnd.android.package-archive")})
    assert r.status_code == 200, r.text
    rep = r.json()
    assert rep["file"]["nama"] == "undangan nikah.apk"  # path dari klien dibuang
    assert rep["aplikasi"]["package"] == "com.politedroid" and rep["level_risiko"] == "Rendah"
    assert rep["schema_version"] == "1.2" and rep["catatan"].startswith("Hasil ini adalah indikasi")
    assert os.path.exists(os.path.join(os.environ["DATA_DIR"], "apk", rep["file"]["sha256"] + ".apk"))

    assert client.get("/scans").json()[0]["scan_id"] == rep["scan_id"]
    assert client.get(f"/scans/{rep['scan_id']}").json() == rep
    assert client.get("/scans/tidak-ada").status_code == 404


def test_rejects_non_apk():
    r = client.post("/scan", files={"file": ("a.apk", b"bukan apk", "application/octet-stream")})
    assert r.status_code == 422 and "bukan file APK" in r.json()["detail"]


def test_slow_analysis_times_out(benign_apk, monkeypatch):
    import time
    monkeypatch.setattr(main, "ANALYZE_TIMEOUT", 0.2)
    monkeypatch.setattr(main, "analyze", lambda *_: time.sleep(1))
    with open(benign_apk("com.politedroid_4.apk"), "rb") as fh:
        r = client.post("/scan", files={"file": ("a.apk", fh, "application/vnd.android.package-archive")})
    assert r.status_code == 504 and "melebihi" in r.json()["detail"]


def test_corrupt_manifest_is_scanned_not_rejected(tmp_path, monkeypatch):
    # inti anti-evasion #3: manifest rusak -> 200 dengan R27 + muatan arsip tetap tertangkap, bukan 422 diam-diam
    import zipfile
    import parser as parser_mod

    def boom(_):
        raise Exception("AXML rusak")

    monkeypatch.setattr(parser_mod, "APK", boom)
    apk = tmp_path / "rusak.apk"
    with zipfile.ZipFile(apk, "w") as z:
        z.writestr("AndroidManifest.xml", b"ini bukan AXML")
        z.writestr("classes.dex", b"dex\n035\x00")
        z.writestr("assets/payload.txt", parser_mod.EICAR)
    with open(apk, "rb") as fh:
        r = client.post("/scan", files={"file": ("rusak.apk", fh, "application/vnd.android.package-archive")})
    assert r.status_code == 200, r.text
    hit = {t["rule_id"] for t in r.json()["temuan"]}
    assert "R27" in hit and "R18" in hit  # manifest rusak DAN EICAR tetap tertangkap
