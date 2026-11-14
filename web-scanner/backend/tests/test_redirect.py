"""Penjaga lingkup di fetch.observe: redirect ke host lain tidak diikuti, badan respons dibatasi."""
import httpx

import fetch


def _app(req):
    if req.url.host != "app.test":
        raise AssertionError(f"pemeriksa tidak boleh menyentuh host lain: {req.url}")
    if req.url.path == "/":
        return httpx.Response(302, headers={"location": "/login"})  # dalam lingkup: diikuti
    if req.url.path == "/login":
        return httpx.Response(302, headers={"location": "https://sso.lain.example/"})  # luar lingkup: berhenti
    return httpx.Response(200, content=b"x" * 3_000_000, headers={"content-type": "text/html"})


def _mock(monkeypatch):
    asli = httpx.Client
    monkeypatch.setattr(fetch.httpx, "Client", lambda **kw: asli(transport=httpx.MockTransport(_app), **kw))


def test_redirect_keluar_host_dicatat_tidak_diikuti(monkeypatch):
    _mock(monkeypatch)
    obs = fetch.observe("http://app.test", "app.test", delay=0, cek_exposed=False)
    assert obs["offscope_redirect"] == "https://sso.lain.example/"
    assert obs["final_url"] == "http://app.test/login" and obs["status"] == 302


def test_badan_respons_dibatasi():
    with httpx.Client(transport=httpx.MockTransport(_app)) as c:
        _, body = fetch._get(c, "http://app.test/besar")
    assert len(body) == fetch.MAX_BODY
