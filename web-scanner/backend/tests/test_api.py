"""API diuji dengan FastAPI TestClient; fetch.observe di-monkeypatch agar tanpa jaringan."""
import os
import tempfile

os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="webscan-test-"))  # jangan tulis ke repo

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402

client = TestClient(main.app)


def _obs(base, host, **k):
    return {"status": 200, "final_url": base + "/", "headers": {}, "https": base.startswith("https"),
            "set_cookies": [], "exposed": [{"path": "/.env", "status": 200}], "errors": []}


def test_rejects_without_authorization():
    r = client.post("/webscan", json={"target": "https://contoh.example"})
    assert r.status_code == 403 and "otorisasi" in r.json()["detail"].lower()


def test_rejects_invalid_scheme():
    r = client.post("/webscan", json={"target": "ftp://contoh.example", "authorized": True})
    assert r.status_code == 403


def test_scan_runs_persists_and_is_retrievable(monkeypatch):
    monkeypatch.setattr(main.fetch, "observe", _obs)
    r = client.post("/webscan", json={"target": "https://contoh.example", "authorized": True})
    assert r.status_code == 200
    body = r.json()
    assert body["ringkasan"]["tertinggi"] == "kritis"  # /.env terekspos -> kritis
    sid = body["scan_id"]
    assert client.get(f"/webscans/{sid}").status_code == 200
    assert any(row["scan_id"] == sid for row in client.get("/webscans").json())


def test_unknown_scan_is_404():
    assert client.get("/webscans/tidak-ada").status_code == 404


def test_otorisasi_recorded(monkeypatch):
    monkeypatch.setattr(main.fetch, "observe", _obs)
    body = client.post("/webscan", json={"target": "https://contoh.example", "authorized": True, "operator": "tim-x"}).json()
    o = body["otorisasi"]
    assert o["dikonfirmasi"] is True and o["operator"] == "tim-x"
    assert o["target"] == body["target"] and o["waktu"] == body["scanned_at"]


def test_verifikasi_teratasi_dan_izin_wajib(monkeypatch):
    monkeypatch.setattr(main.fetch, "observe", _obs)  # /.env terekspos -> W-H03
    sid = client.post("/webscan", json={"target": "https://contoh.example", "authorized": True}).json()["scan_id"]
    p = {"rule": "W-H03", "judul": "Berkas sensitif terekspos: /.env"}
    assert client.post(f"/webscans/{sid}/verifikasi", params=p, json={"authorized": False}).status_code == 403
    assert client.post(f"/webscans/{sid}/verifikasi", params=p, json={"authorized": True}).json()["status"] == "masih ada"
    monkeypatch.setattr(main.fetch, "observe",  # ditambal: tak lagi mengekspos -> teratasi
                        lambda base, host, **k: {"status": 200, "final_url": base + "/", "headers": {},
                                                 "https": base.startswith("https"), "set_cookies": [], "exposed": [], "errors": []})
    assert client.post(f"/webscans/{sid}/verifikasi", params=p, json={"authorized": True}).json()["status"] == "teratasi"
