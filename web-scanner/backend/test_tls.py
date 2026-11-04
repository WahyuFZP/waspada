"""Tes klasifikasi TLS murni (#20). Jalur jaringan (handshake aktif) diverifikasi terpisah
terhadap fixture HTTPS lokal (lemah/usang vs modern vs non-TLS)."""
import tls


def test_tanpa_pfs():
    assert tls._tanpa_pfs("AES256-GCM-SHA384")  # pertukaran kunci RSA -> tanpa PFS
    assert not tls._tanpa_pfs("ECDHE-RSA-AES256-GCM-SHA384")
    assert not tls._tanpa_pfs("DHE-RSA-AES128-GCM-SHA256")


def test_lemah():
    assert "RC4" in (tls._lemah("RC4-MD5", 128) or "")
    assert tls._lemah("ECDHE-RSA-AES128-GCM-SHA256", 64)  # < 128 bit
    assert "AECDH" in (tls._lemah("AECDH-AES256-SHA", 256) or "")  # anonim
    assert tls._lemah("ECDHE-RSA-AES256-GCM-SHA384", 256) is None  # kuat -> aman


def test_probe_host_tanpa_tls_dilewati_tanpa_error():
    # host tanpa layanan TLS -> [] + catatan (bukan exception), agar scan tetap jalan
    findings, catatan = tls.probe("127.0.0.1", 1, timeout=2)
    assert findings == [] and catatan
