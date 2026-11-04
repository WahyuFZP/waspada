"""Tes gerbang otorisasi/lingkup. Termasuk validasi port (#20: port dipakai oleh tls.probe)."""
import pytest

from scope import OutOfScope, authorize


def test_tanpa_otorisasi_ditolak():
    with pytest.raises(OutOfScope):
        authorize("https://contoh.example", False)


def test_port_tak_sah_ditolak():
    with pytest.raises(OutOfScope):
        authorize("https://contoh.example:70000", True)  # di luar 0-65535
    with pytest.raises(OutOfScope):
        authorize("https://contoh.example:abc", True)  # bukan angka


def test_target_sah_dengan_port():
    base, host = authorize("https://contoh.example:8443", True)
    assert host == "contoh.example" and base == "https://contoh.example:8443"
