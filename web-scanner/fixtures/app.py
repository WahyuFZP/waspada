#!/usr/bin/env python3
"""Target latihan WASPADA: web yang SENGAJA salah-konfigurasi, untuk menguji web-scanner pasif.

JINAK — gaya EICAR / APK decoy di proyek ini: tidak ada kode serangan, tidak ada data asli, tidak
mengubah state apa pun. "Rentan"-nya murni dari SINYAL yang diamati pemeriksa pasif: header keamanan
hilang, cookie tanpa flag, CORS * digabung kredensial, banner versi, berkas umpan (.git/.env/...)
ter-"ekspos", dan redirect keluar host. Seluruh isi berkas umpan adalah placeholder PALSU.

Berkas umpan di-inline (bukan folder .git/.env nyata di disk) agar tidak membuat repo-git bersarang
atau menaruh berkas mirip-rahasia yang bisa salah ter-commit.

Jalankan:
    python3 app.py
    # 8003 = situs salah-konfigurasi (+ berkas umpan)
    # 8004 = open-redirect ke host lain; pemeriksa berhenti di sana (tidak mem-follow) -> W-H08 + header respons 302 itu

Lalu pindai dengan web-scanner (service pada :8002):
    curl -X POST localhost:8002/webscan -H 'content-type: application/json' \\
         -d '{"target":"http://localhost:8003","authorized":true}'
"""
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "127.0.0.1"          # lokal saja: jangan pernah ekspos target rentan ke jaringan
MAIN_PORT = 8003
REDIR_PORT = 8004
# host berbeda (127.0.0.1) dari 'localhost' yang dipindai -> keluar lingkup -> memicu W-H08.
# Pemeriksa tidak mem-follow keluar host: yang dinilai adalah respons 302 dari :8004 sendiri, plus W-H08.
REDIR_TO = f"http://{HOST}:{MAIN_PORT}/"

BANNER_SERVER = "Apache/2.4.29 (Ubuntu)"   # banner palsu berisi versi -> W-H09
BANNER_XPB = "PHP/7.2.0"                     # idem -> W-H09

HOME = """<!doctype html>
<html lang="id"><head><meta charset="utf-8"><title>Target Latihan WASPADA</title>
<!-- subresource pihak ketiga TANPA integrity (host contoh/reserved; pemeriksa tak mengambilnya) -> W-A08-01 -->
<!-- pustaka JS usang (jQuery 3.4.1 < 3.5.0: CVE-2020-11022/11023) -> W-A06-01; host reserved, tak diambil -->
<script src="https://cdn.example.com/jquery-3.4.1.min.js"></script>
<script src="https://cdn.example.com/vendor/analytics.js"></script>
<link rel="stylesheet" href="https://cdn.example.com/vendor/theme.css"></head>
<body style="font-family:system-ui;max-width:720px;margin:3rem auto;padding:0 1rem;line-height:1.6">
<h1>Target Latihan Kerentanan Web — WASPADA</h1>
<p><strong>Situs ini sengaja dibuat rentan</strong> untuk menguji pemeriksa keamanan web WASPADA.
Sepenuhnya <strong>jinak</strong>: tidak ada kode serangan, tidak ada data asli — semua "rahasia"
pada berkas umpan adalah nilai palsu.</p>
<h2>Kelemahan yang ditanam (sinyal pasif)</h2>
<ul>
<li>Dilayani lewat HTTP polos, tanpa TLS</li>
<li>CSP ada tapi longgar (wildcard, 'unsafe-inline'/'unsafe-eval'); tanpa X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy</li>
<li>Cookie sesi tanpa HttpOnly, dan SameSite=None tanpa Secure</li>
<li>CORS: Access-Control-Allow-Origin: * digabung Access-Control-Allow-Credentials: true</li>
<li>Banner versi: header Server &amp; X-Powered-By mengungkap versi</li>
<li>Memuat skrip &amp; CSS pihak ketiga tanpa Subresource Integrity (SRI)</li>
<li>Memuat pustaka JS usang yang rentan (jQuery 3.4.1)</li>
<li>Berkas umpan ter-"ekspos": /.git/HEAD, /.git/config, /.env, /.DS_Store, /server-status, /.htaccess</li>
</ul>
<p>Pindai dengan WASPADA Web, lalu bandingkan temuannya dengan daftar di atas.</p>
</body></html>
"""

# Isi PALSU, hanya cukup untuk mencocokkan tanda-isi pemeriksa (backend/fetch.py: _looks_exposed),
# supaya target benar-benar memicu W-H03. Diuji offline di test_fixture.py.
_DS_STORE = b"\x00\x00\x00\x01Bud1" + b"\x00" * 32  # tanda 'Bud1' di 16 byte pertama
DECOYS = {
    "/.git/HEAD": (b"ref: refs/heads/main\n", "text/plain"),
    "/.git/config": (
        b"[core]\n\trepositoryformatversion = 0\n\tbare = false\n"
        b'[remote "origin"]\n\turl = https://github.com/contoh/target-latihan.git\n',
        "text/plain"),
    "/.env": (
        b"# BERKAS UMPAN - nilai palsu untuk latihan, bukan rahasia asli\n"
        b"APP_ENV=production\nAPP_DEBUG=true\n"
        b"DB_HOST=127.0.0.1\nDB_USERNAME=demo\nDB_PASSWORD=contoh-bukan-password-asli\n"
        b"API_KEY=DEMO-0000-0000-0000\n",
        "text/plain"),
    "/.DS_Store": (_DS_STORE, "application/octet-stream"),
    "/server-status": (
        b"<html><head><title>Apache Status</title></head><body>"
        b"<h1>Apache Server Status for localhost</h1>"
        b"<dl><dt>Server Version: Apache/2.4.29 (Ubuntu)</dt></dl></body></html>",
        "text/html"),
    "/.htaccess": (
        b"RewriteEngine On\nRewriteRule ^admin$ /admin.php [L]\n"
        b"Order allow,deny\nAllow from all\n",
        "text/plain"),
}


class Rentan(BaseHTTPRequestHandler):
    """Situs salah-konfigurasi di MAIN_PORT."""

    def version_string(self):
        return BANNER_SERVER  # ganti 'BaseHTTP/x Python/y' -> banner palsu di header Server

    def _send(self, status, body, ctype, extra=()):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(status)                     # otomatis: Server (banner palsu) + Date
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Powered-By", BANNER_XPB)   # -> W-H09
        for k, v in extra:
            self.send_header(k, v)
        # SENGAJA tidak mengirim CSP / X-Frame-Options / X-Content-Type-Options /
        # Referrer-Policy / Permissions-Policy / HSTS
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/":
            self._send(200, HOME, "text/html; charset=utf-8", extra=[
                # CSP ADA tapi longgar (wildcard + unsafe-inline/eval) -> W-H01-02 (bukan W-H01 'hilang')
                ("Content-Security-Policy", "default-src *; script-src 'unsafe-inline' 'unsafe-eval'"),
                # tanpa HttpOnly -> W-A07-01; SameSite=None tanpa Secure -> W-A07-02
                ("Set-Cookie", "SESSIONID=8f3b2a1c9d4e; Path=/; SameSite=None"),
                ("Access-Control-Allow-Origin", "*"),               # + kredensial -> W-H02
                ("Access-Control-Allow-Credentials", "true"),
            ])
        elif path in DECOYS:
            body, ctype = DECOYS[path]
            self._send(200, body, ctype)                            # -> W-H03
        else:
            self._send(404, "<h1>404</h1>", "text/html; charset=utf-8")

    do_HEAD = do_GET

    def log_message(self, *a):
        pass  # senyap


class Redir(BaseHTTPRequestHandler):
    """Open-redirect di REDIR_PORT: apa pun path-nya, 302 ke host lain -> memicu W-H08."""

    def version_string(self):
        return BANNER_SERVER

    def do_GET(self):
        self.send_response(302)
        self.send_header("Location", REDIR_TO)
        self.send_header("Content-Length", "0")
        self.end_headers()

    do_HEAD = do_GET

    def log_message(self, *a):
        pass


def main():
    main_srv = ThreadingHTTPServer((HOST, MAIN_PORT), Rentan)
    redir_srv = ThreadingHTTPServer((HOST, REDIR_PORT), Redir)
    print("Target latihan WASPADA aktif:")
    print(f"  http://localhost:{MAIN_PORT}  situs salah-konfigurasi (+ berkas umpan)")
    print(f"  http://localhost:{REDIR_PORT}  open-redirect ke :{MAIN_PORT} (demo W-H08)")
    print("Ctrl-C untuk berhenti.")
    threading.Thread(target=redir_srv.serve_forever, daemon=True).start()
    try:
        main_srv.serve_forever()
    except KeyboardInterrupt:
        print("\nberhenti.")
    finally:
        main_srv.shutdown()
        redir_srv.shutdown()


if __name__ == "__main__":
    main()
