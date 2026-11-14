"""Cuplikan konfigurasi siap-tempel per temuan, dipetakan via id rule (#7). Murni memperkaya laporan:
pemilik tinggal menyalin blok nginx/apache. Tak semua temuan punya cuplikan server (CORS, SCA, SRI
idealnya di aplikasi/kode); temuan tanpa entri cukup tak menampilkan cuplikan."""

_HSTS = {
    "nginx": "add_header Strict-Transport-Security \"max-age=31536000; includeSubDomains\" always;",
    "apache": "Header always set Strict-Transport-Security \"max-age=31536000; includeSubDomains\"",
}
_COOKIE = {
    "nginx": "# idealnya diset di aplikasi; via reverse proxy (nginx >= 1.19.3):\nproxy_cookie_flags ~ secure httponly samesite=lax;",
    "apache": "# idealnya diset di aplikasi; via Apache mod_headers:\nHeader edit Set-Cookie ^(.*)$ \"$1; Secure; HttpOnly; SameSite=Lax\"",
}

CUPLIKAN = {
    "W-H01": {
        "nginx": "add_header Content-Security-Policy \"default-src 'self'\" always;",
        "apache": "Header always set Content-Security-Policy \"default-src 'self'\"",
    },
    "W-H01-02": {
        "nginx": "add_header Content-Security-Policy \"default-src 'self'; script-src 'self'\" always;",
        "apache": "Header always set Content-Security-Policy \"default-src 'self'; script-src 'self'\"",
    },
    "W-A02-02": _HSTS,
    "W-A02-05": _HSTS,
    "W-H04": {
        "nginx": "add_header X-Frame-Options \"DENY\" always;",
        "apache": "Header always set X-Frame-Options \"DENY\"",
    },
    "W-H05": {
        "nginx": "add_header X-Content-Type-Options \"nosniff\" always;",
        "apache": "Header always set X-Content-Type-Options \"nosniff\"",
    },
    "W-H06": {
        "nginx": "add_header Referrer-Policy \"strict-origin-when-cross-origin\" always;",
        "apache": "Header always set Referrer-Policy \"strict-origin-when-cross-origin\"",
    },
    "W-H07": {
        "nginx": "add_header Permissions-Policy \"geolocation=(), camera=(), microphone=()\" always;",
        "apache": "Header always set Permissions-Policy \"geolocation=(), camera=(), microphone=()\"",
    },
    "W-A07-01": _COOKIE,
    "W-A07-02": _COOKIE,
    "W-H03": {
        "nginx": "location ~ /\\.(git|env|htaccess|DS_Store) {\n    deny all;\n    return 404;\n}",
        "apache": "RedirectMatch 404 \"/\\.(git|env|htaccess|DS_Store)\"",
    },
}
