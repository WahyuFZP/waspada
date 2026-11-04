"""Tes konteks kepatuhan (#14) apk: hanya muncul untuk kasus berbahaya/peniru, dengan disclaimer."""
from kepatuhan import konteks


def test_berbahaya_gives_channels():
    k = konteks("Berbahaya", ["R07", "R11"])
    assert k and "UU ITE" in k["relevansi"] and any("Komdigi" in c["nama"] for c in k["kanal_lapor"])
    assert "BUKAN nasihat hukum" in k["disclaimer"]


def test_impersonation_includes_bank_even_if_only_suspicious():
    k = konteks("Mencurigakan", ["R13"])  # peniru -> tetap muncul + kanal bank
    assert k and any("Bank" in c["nama"] or "bank" in c["nama"] for c in k["kanal_lapor"])


def test_clean_gives_nothing():
    assert konteks("Tidak ditemukan indikasi berbahaya", ["R21"]) is None
