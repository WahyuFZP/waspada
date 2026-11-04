"""Rule pasif diuji dengan amatan buatan (tanpa jaringan), seperti test_rules.py pemeriksa APK."""
from rules import evaluate

HARDENED = {
    "content-security-policy": "default-src 'self'; frame-ancestors 'none'",
    "strict-transport-security": "max-age=63072000; includeSubDomains",
    "x-content-type-options": "nosniff",
    "referrer-policy": "strict-origin-when-cross-origin",
    "permissions-policy": "geolocation=()",
    "x-frame-options": "DENY",
}


def obs(**kw):
    base = {"status": 200, "final_url": "https://x.example/", "headers": {}, "https": True,
            "set_cookies": [], "exposed": [], "tls": {"ok": True, "days_left": 300}}
    base.update(kw)
    return base


def ids(o):
    return {f.id for f in evaluate(o)}


def test_failed_fetch_yields_nothing():
    assert evaluate({"errors": ["boom"]}) == []


def test_all_headers_missing_each_flagged():
    found = ids(obs())
    assert {"W-H01", "W-A02-02", "W-H05", "W-H06", "W-H07", "W-H04"}.issubset(found)  # CSP, HSTS, XCTO, Referrer, Permissions, clickjacking


def test_fully_hardened_https_is_clean():
    assert evaluate(obs(headers=HARDENED)) == []


def test_http_site_flagged_and_hsts_not_checked():
    found = ids(obs(https=False, final_url="http://x.example/", tls={}))
    assert "W-A02-01" in found       # HTTP tanpa enkripsi
    assert "W-A02-02" not in found   # HSTS tidak dicek pada HTTP


def test_cookie_missing_flags():
    [f] = [x for x in evaluate(obs(headers=HARDENED, set_cookies=["sid=abc; Path=/"])) if x.id == "W-A07-01"]
    assert all(k in f.judul for k in ("Secure", "HttpOnly", "SameSite"))


def test_cookie_on_http_does_not_demand_secure():
    o = obs(https=False, final_url="http://x.example/", tls={}, set_cookies=["sid=abc; HttpOnly; SameSite=Lax"])
    assert [x for x in evaluate(o) if x.id == "W-A07-01"] == []  # Secure tidak dituntut di HTTP


def test_cors_wildcard_with_credentials_is_high():
    o = obs(headers={**HARDENED, "access-control-allow-origin": "*", "access-control-allow-credentials": "true"})
    [f] = [x for x in evaluate(o) if x.id == "W-H02"]
    assert f.tingkat == "tinggi"


def test_exposed_git_is_critical_env_too():
    for path in ("/.git/HEAD", "/.env"):
        [f] = [x for x in evaluate(obs(headers=HARDENED, exposed=[{"path": path, "status": 200}])) if x.id == "W-H03"]
        assert f.tingkat == "kritis"


def test_version_banner_and_expired_cert():
    o = obs(headers={**HARDENED, "server": "nginx/1.18.0"}, tls={"ok": True, "expired": True, "expires": "2020-01-01"})
    found = {f.id: f.tingkat for f in evaluate(o)}
    assert found.get("W-H09") == "rendah" and found.get("W-A02-03") == "tinggi"


def test_offscope_redirect_flagged():
    assert "W-H08" in ids(obs(headers=HARDENED, offscope_redirect="https://lain.example/"))


def test_csp_present_but_weak_flagged():
    o = obs(headers={**HARDENED, "content-security-policy": "default-src 'self'; script-src 'self' 'unsafe-inline'"})
    assert "W-H01-02" in ids(o)


def test_csp_unsafe_inline_with_nonce_not_flagged():
    o = obs(headers={**HARDENED, "content-security-policy": "script-src 'self' 'unsafe-inline' 'nonce-abc123'"})
    assert "W-H01-02" not in ids(o)


def test_hsts_present_but_weak_flagged():
    assert "W-A02-05" in ids(obs(headers={**HARDENED, "strict-transport-security": "max-age=300"}))


def test_cookie_samesite_none_without_secure_flagged():
    assert "W-A07-02" in ids(obs(headers=HARDENED, set_cookies=["sid=x; SameSite=None"]))
    assert "W-A07-02" not in ids(obs(headers=HARDENED, set_cookies=["sid=x; SameSite=None; Secure; HttpOnly"]))


def test_sca_outdated_library_flagged():
    assert "W-A06-01" in ids(obs(headers=HARDENED, skrip=["https://cdn.x/jquery-3.4.1.min.js"]))
    assert "W-A06-01" not in ids(obs(headers=HARDENED, skrip=["https://cdn.x/jquery-3.6.0.min.js"]))  # versi aman


def test_cuplikan_siap_tempel_attached_by_id():
    # temuan dengan id ber-cuplikan mendapat blok nginx/apache; id tak terdaftar -> dict kosong
    [xfo] = [x for x in evaluate(obs()) if x.id == "W-H04"]
    assert "X-Frame-Options" in xfo.cuplikan.get("nginx", "") and "apache" in xfo.cuplikan
    [banner] = [x for x in evaluate(obs(headers={"server": "nginx/1.0"})) if x.id == "W-H09"]
    assert banner.cuplikan == {}


def test_edukasi_card_attached_by_id():
    [xfo] = [x for x in evaluate(obs()) if x.id == "W-H04"]
    assert set(xfo.edukasi) == {"apa", "kenapa", "dampak"}


def test_subresource_without_sri_flagged():
    assert "W-A08-01" in ids(obs(headers=HARDENED, subresources=[{"url": "https://cdn.other/x.js"}]))
    assert "W-A08-01" not in ids(obs(headers=HARDENED))
