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
    assert rep["schema_version"] == "1.1" and rep["catatan"].startswith("Hasil ini adalah indikasi")
    assert os.path.exists(os.path.join(os.environ["DATA_DIR"], "apk", rep["file"]["sha256"] + ".apk"))

    assert client.get("/scans").json()[0]["scan_id"] == rep["scan_id"]
    assert client.get(f"/scans/{rep['scan_id']}").json() == rep
    assert client.get("/scans/tidak-ada").status_code == 404


def test_rejects_non_apk():
    r = client.post("/scan", files={"file": ("a.apk", b"bukan apk", "application/octet-stream")})
    assert r.status_code == 422 and "bukan file APK" in r.json()["detail"]
