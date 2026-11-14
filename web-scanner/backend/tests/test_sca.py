"""Tes SCA pasif (OWASP A06) tanpa jaringan: versi pustaka ditebak dari nama file lalu dicocokkan DB."""
from sca import periksa


def test_detects_outdated_jquery():
    [r] = periksa(["https://cdn.example/jquery-3.4.1.min.js"])
    assert r["nama"] == "jquery" and r["versi"] == "3.4.1" and r["cve"]


def test_safe_jquery_version_not_flagged():
    assert periksa(["https://cdn.example/jquery-3.6.0.min.js"]) == []


def test_bootstrap_version_line_aware():
    assert periksa(["https://cdn.example/bootstrap.3.3.7.min.css"])      # 3.x < 3.4.1 -> rentan
    assert periksa(["https://cdn.example/bootstrap-4.5.0.min.js"]) == []  # 4.x >= 4.3.1 -> aman


def test_unknown_library_ignored():
    assert periksa(["https://cdn.example/mystery-widget-1.0.0.js"]) == []


def test_library_without_version_in_filename_skipped():
    assert periksa(["https://cdn.example/jquery.min.js"]) == []
