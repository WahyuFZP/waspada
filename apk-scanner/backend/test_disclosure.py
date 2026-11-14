"""Tes draf responsible-disclosure (#18): konten faktual, bahasa aman (hedged), tanpa auto-kirim."""
from dataclasses import dataclass

import disclosure


@dataclass
class F:
    rule_id: str
    judul: str
    tingkat: str


PARSED = {
    "package": "com.bank.palsu", "sha256": "a" * 64,
    "dangerous_permissions": ["android.permission.READ_SMS", "android.permission.SYSTEM_ALERT_WINDOW"],
}
AKHIR = {
    "status": "Berbahaya",
    "sertifikat": {"skema": ["v2"], "debug": True, "subjek": "CN=Android Debug"},
    "intel": {"status": "tidak_ditemukan", "keterangan": "-"},
    "domain": [{"domain": "evil.example", "jumlah": 3, "kategori": "lainnya"},
               {"domain": "google.com", "jumlah": 1, "kategori": "dikenal"}],
}
FINDINGS = [F("R16", "Meniru aplikasi resmi", "tinggi"), F("R04", "Minta izin SMS", "sedang")]


def test_draf_berisi_fakta_kunci():
    d = disclosure.draf("bank-palsu.apk", PARSED, AKHIR, FINDINGS)
    t = f"{d['subjek']}\n{d['badan']}"
    assert "com.bank.palsu" in t and "a" * 64 in t
    assert "READ_SMS" in t and "Meniru aplikasi resmi" in t
    assert "evil.example" in t and "google.com" not in t  # hanya domain 'lainnya' yang dibawa
    assert "kunci debug" in t  # penandatangan debug tersurat
    assert "menyamar" in d["badan"] and "menyamar" in d["subjek"]  # peniru (R16): badan DAN subjek konsisten


def test_bahasa_aman_dan_tidak_auto_kirim():
    d = disclosure.draf("x.apk", PARSED, AKHIR, FINDINGS)
    assert "bukan vonis final" in d["badan"]  # tidak menuduh pasti
    low = d["catatan"].lower()
    assert "tidak" in low and "mengirim" in low  # tegaskan WASPADA tidak mengirim
    assert "bukan nasihat hukum" in low
    assert d["subjek"].startswith("Dugaan")  # hedged, bukan vonis


def test_tanpa_peniru_tanpa_baris_menyamar():
    # Berbahaya tapi BUKAN peniru (tanpa R16/R28): kata "menyamar" tak boleh muncul, termasuk di subjek
    d = disclosure.draf("x.apk", PARSED, AKHIR, [F("R04", "Minta izin SMS", "tinggi")])
    assert "menyamar" not in d["badan"]
    assert "menyamar" not in d["subjek"]
