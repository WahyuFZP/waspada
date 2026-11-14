"""Tes jembatan opsional web scanner -> SIEM (#16): opt-in, pemetaan band, potong field, fail-safe."""
import httpx

import siem

LAPORAN = {
    "scan_id": "abc", "scanned_at": "2026-11-04T12:00:00+07:00", "target": "https://contoh.example/app",
    "ringkasan": {"postur": "buruk", "tertinggi": "kritis", "jumlah": {"kritis": 1}},
    "temuan": [{"judul": "Berkas .env terekspos", "tingkat": "kritis", "bukti": ["RAHASIA"]},
               {"judul": "CSP lemah", "tingkat": "sedang", "bukti": []}] * 5,  # 10 temuan: uji potong ke 8
    "analisa_akhir": {"status": "Perlu perbaikan segera", "saran": ["Hapus .env dari webroot."]},
}


def _tangkap(monkeypatch):
    calls = []

    class R:
        def raise_for_status(self):
            pass

    monkeypatch.setattr(siem.httpx, "post", lambda url, json, timeout, headers=None: calls.append((url, json, headers)) or R())
    return calls


def test_kirim_saat_aktif_dan_kritis(monkeypatch):
    monkeypatch.setenv("SIEM_INGEST_URL", "http://127.0.0.1:8000/ingest")
    calls = _tangkap(monkeypatch)
    siem.kirim(LAPORAN)
    assert len(calls) == 1
    url, ev, _ = calls[0]
    assert url == "http://127.0.0.1:8000/ingest"
    assert ev["kind"] == "scanner" and ev["scanner"] == "web" and ev["severity"] == "critical"
    assert ev["host"] == "contoh.example" and ev["timestamp"] == LAPORAN["scanned_at"]
    assert len(ev["temuan"]) == 8  # dipotong dari 10
    assert ev["temuan"][0] == {"judul": "Berkas .env terekspos", "tingkat": "kritis"}  # hanya judul+tingkat, bukti tak ikut


def test_band_tinggi_memetakan_high(monkeypatch):
    monkeypatch.setenv("SIEM_INGEST_URL", "http://127.0.0.1:8000/ingest")
    calls = _tangkap(monkeypatch)
    siem.kirim({**LAPORAN, "ringkasan": {"postur": "buruk", "tertinggi": "tinggi", "jumlah": {}}})
    assert calls[0][1]["severity"] == "high"


def test_tidak_kirim_saat_nonaktif(monkeypatch):
    monkeypatch.delenv("SIEM_INGEST_URL", raising=False)
    calls = _tangkap(monkeypatch)
    siem.kirim(LAPORAN)
    assert calls == []


def test_tidak_kirim_band_rendah(monkeypatch):
    monkeypatch.setenv("SIEM_INGEST_URL", "http://127.0.0.1:8000/ingest")
    calls = _tangkap(monkeypatch)
    siem.kirim({**LAPORAN, "ringkasan": {"postur": "perlu perbaikan", "tertinggi": "sedang", "jumlah": {}}})
    assert calls == []


def test_fail_safe_saat_siem_mati(monkeypatch):
    monkeypatch.setenv("SIEM_INGEST_URL", "http://127.0.0.1:8000/ingest")

    def boom(*a, **k):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(siem.httpx, "post", boom)
    siem.kirim(LAPORAN)  # tidak boleh melempar
