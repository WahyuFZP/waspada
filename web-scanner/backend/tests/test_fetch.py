"""Tes pure untuk ekstraksi subresource (SRI) di fetch, tanpa jaringan."""
from fetch import _skrip_urls, _subresources

HTML = """
<script src="https://cdn.other.com/a.js"></script>
<script src="https://cdn.other.com/b.js" integrity="sha384-xxx"></script>
<script src="/local/c.js"></script>
<link rel="stylesheet" href="https://cdn.other.com/s.css">
<link rel="stylesheet" href="/local/s.css">
"""


def test_only_cross_origin_without_integrity():
    out = {s["url"] for s in _subresources(HTML, "https://app.example/", "app.example")}
    # b.js punya integrity, dua aset lokal di-skip -> sisa dua lintas-origin tanpa integrity
    assert out == {"https://cdn.other.com/a.js", "https://cdn.other.com/s.css"}


def test_same_origin_only_yields_nothing():
    html = '<script src="/app.js"></script><link rel="stylesheet" href="/app.css">'
    assert _subresources(html, "https://app.example/", "app.example") == []


def test_skrip_urls_absolute_all_tags():
    # semua <script>/<link> jadi URL absolut (untuk SCA), termasuk same-origin & yang ber-integrity
    out = _skrip_urls(HTML, "https://app.example/")
    assert "https://app.example/local/c.js" in out and "https://cdn.other.com/b.js" in out
    assert len(out) == 5
