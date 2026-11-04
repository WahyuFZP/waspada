"""Pengambil bukti PASIF.

Mengambil respons target dan mengamati header/cookie/TLS, lalu mengecek sejumlah kecil path yang
sering ter-ekspos tak sengaja. Non-destruktif: hanya GET, ber-rate-limit, batas waktu, dan tidak
keluar lingkup host. TIDAK ada muatan serangan, tidak mengubah state, tidak brute-force.
"""
import socket
import ssl
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

import httpx

from scope import in_scope

UA = "WASPADA-WebScanner/0.1 (pasif; hanya untuk pemeriksaan berizin)"

# Path yang kehadirannya (isi cocok) menandakan berkas internal bocor ke web root. Sengaja pendek dan
# ber-tanda-isi: hanya ditandai bila isinya benar-benar cocok, agar halaman 200 catch-all tidak memicu
# false positive. Ini BUKAN pemindai direktori — hanya cek beberapa kebocoran paling umum.
EXPOSED = ("/.git/HEAD", "/.git/config", "/.env", "/.DS_Store", "/server-status", "/.htaccess")


def _is_hex40(b):
    s = b.strip()
    return len(s) == 40 and all(c in b"0123456789abcdef" for c in s.lower())


def _looks_exposed(path, body, ctype):
    html = b"<html" in body[:512].lower() or "html" in ctype.lower()
    if path == "/.git/HEAD":
        return body[:4].lower() == b"ref:" or _is_hex40(body)
    if path == "/.git/config":
        return b"[core]" in body
    if path == "/.DS_Store":
        return b"Bud1" in body[:16]
    if path == "/.env":
        return not html and b"=" in body and not body.lstrip().startswith((b"{", b"<"))
    if path == "/server-status":
        return b"Server Status" in body
    if path == "/.htaccess":
        return not html and any(k in body for k in (b"RewriteEngine", b"Require ", b"Order ", b"Deny "))
    return False


class _Subresources(HTMLParser):
    """Kumpulkan <script src> dan <link rel=stylesheet href> beserta ada/tidaknya atribut integrity."""

    def __init__(self):
        super().__init__()
        self.found = []  # list[(url, has_integrity)]

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "script" and a.get("src"):
            self.found.append((a["src"], "integrity" in a))
        elif tag == "link" and a.get("href") and "stylesheet" in (a.get("rel") or "").lower():
            self.found.append((a["href"], "integrity" in a))


def _subresources(html, base_url, host):
    """-> list[{url}] untuk subresource LINTAS-ORIGIN tanpa integrity (kandidat W-A08-01).
    Hanya membaca HTML host sendiri; URL subresource tidak pernah diambil."""
    p = _Subresources()
    try:
        p.feed(html)
    except Exception:
        pass  # HTML rusak: pakai yang sempat terbaca, jangan gagalkan amatan
    out = []
    for url, has_integrity in p.found:
        if has_integrity:
            continue
        abs_url = urljoin(base_url, url)
        if (urlsplit(abs_url).hostname or host) != host:
            out.append({"url": abs_url})
    return out


def _skrip_urls(html, base_url):
    """-> semua URL <script src>/<link stylesheet> (absolut) untuk SCA komponen usang (OWASP A06)."""
    p = _Subresources()
    try:
        p.feed(html)
    except Exception:
        pass
    return [urljoin(base_url, url) for url, _ in p.found]


def _tls(host, port):
    """Postur TLS dasar (kedalaman penuh diserahkan ke testssl.sh nanti)."""
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((host, port), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ss:
                cert = ss.getpeercert()
                proto = ss.version()
        exp = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        return {"ok": True, "protocol": proto, "expires": exp.date().isoformat(),
                "expired": exp < datetime.now(timezone.utc),
                "days_left": (exp - datetime.now(timezone.utc)).days}
    except Exception as e:
        # sertifikat kedaluwarsa/salah nama/self-signed akan jatuh ke sini; pesannya jadi bukti
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def _probe_exposed(client, base, host, delay):
    hits = []
    for path in EXPOSED:
        time.sleep(delay)  # rate-limit: jangan membebani server sendiri
        try:
            r = client.get(base + path, follow_redirects=False)
        except httpx.HTTPError:
            continue
        if r.status_code == 200 and in_scope(str(r.url), host) \
                and _looks_exposed(path, r.content[:4096], r.headers.get("content-type", "")):
            hits.append({"path": path, "status": 200})
    return hits


def observe(target, host, delay=0.5, cek_exposed=True):
    """target = base_url hasil scope.authorize. -> dict amatan untuk rules.evaluate."""
    obs = {"target": target, "errors": []}
    with httpx.Client(headers={"User-Agent": UA}, timeout=15.0, follow_redirects=True, max_redirects=5) as client:
        try:
            r = client.get(target)
        except httpx.HTTPError as e:
            obs["errors"].append(f"Gagal mengambil {target}: {type(e).__name__}: {e}")
            return obs
        final = str(r.url)
        obs["status"] = r.status_code
        obs["final_url"] = final
        obs["headers"] = {k.lower(): v for k, v in r.headers.items()}
        obs["set_cookies"] = [v for k, v in r.headers.multi_items() if k.lower() == "set-cookie"]
        obs["https"] = final.lower().startswith("https://")  # setelah redirect: http->https terhitung aman
        obs["offscope_redirect"] = None if in_scope(final, host) else final
        ctype = obs["headers"].get("content-type", "")
        obs["subresources"] = _subresources(r.text, final, host) if "html" in ctype.lower() else []
        obs["skrip"] = _skrip_urls(r.text, final) if "html" in ctype.lower() else []
        if obs["https"] and in_scope(final, host):
            fu = urlsplit(final)
            obs["tls"] = _tls(fu.hostname, fu.port or 443)
        if cek_exposed:
            obs["exposed"] = _probe_exposed(client, target, host, delay)
    return obs
