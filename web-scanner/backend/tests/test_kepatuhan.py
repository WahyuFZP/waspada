"""Tes konteks kepatuhan (#14) web: hanya untuk postur tinggi/kritis, dengan disclaimer."""
from kepatuhan import konteks


def test_exposed_secret_adds_pdp_and_bssn():
    k = konteks("kritis", ["W-H03", "W-H01"])
    assert k and any("BSSN" in c["nama"] for c in k["kanal_lapor"])
    assert any("UU PDP" in c["nama"] or "PDP" in c["nama"] for c in k["kanal_lapor"])
    assert "BUKAN nasihat hukum" in k["disclaimer"]


def test_high_without_leak_still_bssn_no_pdp():
    k = konteks("tinggi", ["W-A02-01"])
    assert k and [c["nama"] for c in k["kanal_lapor"]] == ["BSSN / CSIRT"]


def test_low_posture_gives_nothing():
    assert konteks("rendah", ["W-H05"]) is None
