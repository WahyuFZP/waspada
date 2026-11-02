import final
from models import Finding

RELEASE = {"skema": ["v1", "v2"], "subjek": "Common Name: Penerbit", "sha256": "ab" * 32, "debug": False}


def parsed(**kw):
    base = {"sha256": "0" * 64, "package": "id.dana", "urls": [], "galat": [], "sertifikat": RELEASE}
    return base | kw


def test_registrable_handles_indonesian_second_level():
    assert final.registrable("api.m.dana.id") == "dana.id"
    assert final.registrable("registrasi.klikbca.co.id") == "klikbca.co.id"
    assert final.registrable("metrics1.data.hicloud.com") == "hicloud.com"


def test_domains_grouped_by_owner():
    urls = ["https://m.dana.id/a", "https://link.dana.id/b", "https://api.mixpanel.com/t", "https://dana.kitabisa.xyz"]
    rows = final.group_domains(urls, "id.dana")
    assert rows == [
        {"domain": "kitabisa.xyz", "jumlah": 1, "kategori": "lainnya"},  # yang perlu ditinjau tampil paling atas
        {"domain": "dana.id", "jumlah": 2, "kategori": "aplikasi"},
        {"domain": "mixpanel.com", "jumlah": 1, "kategori": "dikenal"},
    ]
    # merek di segmen ketiga package
    assert final.group_domains(["http://www.jamendo.com/x"], "com.teleca.jamendo")[0]["kategori"] == "aplikasi"


def test_hash_lookup_skipped_without_key(monkeypatch):
    monkeypatch.delenv("ABUSECH_AUTH_KEY", raising=False)
    assert final.lookup_hash("0" * 64)["status"] == "dilewati"


def test_clean_release_app_has_no_indication(monkeypatch):
    monkeypatch.delenv("ABUSECH_AUTH_KEY", raising=False)
    r = final.conclude(parsed(), {}, [], "Rendah")
    assert r["status"] == "Tidak ditemukan indikasi berbahaya"


def test_debug_certificate_is_suspicious(monkeypatch):
    monkeypatch.delenv("ABUSECH_AUTH_KEY", raising=False)
    r = final.conclude(parsed(sertifikat=RELEASE | {"debug": True}), {}, [], "Rendah")
    assert r["status"] == "Mencurigakan" and any("kunci debug" in a for a in r["alasan"])


def test_known_malware_hash_overrides_low_score(monkeypatch):
    monkeypatch.setattr(final, "lookup_hash", lambda _: {"status": "dikenal_malware", "keterangan": "Tercatat X."})
    r = final.conclude(parsed(), {}, [], "Rendah")
    assert r["status"] == "Berbahaya" and r["alasan"][0] == "Tercatat X."


def test_high_level_is_dangerous_and_lists_high_findings(monkeypatch):
    monkeypatch.delenv("ABUSECH_AUTH_KEY", raising=False)
    f = Finding("R11", "Mengirim data ke bot Telegram", "tinggi", 30)
    r = final.conclude(parsed(), {}, [f], "Tinggi")
    assert r["status"] == "Berbahaya" and "Mengirim data ke bot Telegram (R11)." in r["alasan"]
