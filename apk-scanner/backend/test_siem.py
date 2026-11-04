"""Tes jembatan opsional apk scanner -> SIEM (#16): opt-in, pemetaan band, potong field, fail-safe."""
import httpx

import siem

LAPORAN = {
    "scan_id": "xyz", "scanned_at": "2026-11-04T12:00:00+07:00",
    "aplikasi": {"package": "com.contoh.app"},
    "level_risiko": "Tinggi",
    "temuan": [{"judul": "Minta izin SMS + internet", "tingkat": "tinggi", "bukti": ["x"]}],
    "analisa_akhir": {"status": "Berbahaya", "saran": ["Jangan pasang aplikasi ini."]},
}


def _tangkap(monkeypatch):
    calls = []

    class R:
        def raise_for_status(self):
            pass

    monkeypatch.setattr(siem.httpx, "post", lambda url, json, timeout: calls.append((url, json)) or R())
    return calls


def test_kirim_level_tinggi_critical(monkeypatch):
    monkeypatch.setenv("SIEM_INGEST_URL", "http://127.0.0.1:8000/ingest")
    calls = _tangkap(monkeypatch)
    siem.kirim(LAPORAN)
    assert len(calls) == 1
    ev = calls[0][1]
    assert ev["kind"] == "scanner" and ev["scanner"] == "apk" and ev["severity"] == "critical"
    assert ev["host"] == "com.contoh.app" and ev["timestamp"] == LAPORAN["scanned_at"]
    assert ev["temuan"][0] == {"judul": "Minta izin SMS + internet", "tingkat": "tinggi"}  # bukti tak ikut


def test_level_sedang_high(monkeypatch):
    monkeypatch.setenv("SIEM_INGEST_URL", "http://127.0.0.1:8000/ingest")
    calls = _tangkap(monkeypatch)
    siem.kirim({**LAPORAN, "level_risiko": "Sedang", "analisa_akhir": {"status": "Mencurigakan", "saran": []}})
    assert calls[0][1]["severity"] == "high"


def test_tidak_kirim_level_rendah(monkeypatch):
    monkeypatch.setenv("SIEM_INGEST_URL", "http://127.0.0.1:8000/ingest")
    calls = _tangkap(monkeypatch)
    siem.kirim({**LAPORAN, "level_risiko": "Rendah"})
    assert calls == []


def test_tidak_kirim_saat_nonaktif(monkeypatch):
    monkeypatch.delenv("SIEM_INGEST_URL", raising=False)
    calls = _tangkap(monkeypatch)
    siem.kirim(LAPORAN)
    assert calls == []


def test_fail_safe_saat_siem_mati(monkeypatch):
    monkeypatch.setenv("SIEM_INGEST_URL", "http://127.0.0.1:8000/ingest")

    def boom(*a, **k):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(siem.httpx, "post", boom)
    siem.kirim(LAPORAN)  # tidak boleh melempar
