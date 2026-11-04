"""Rule pasif: ubah amatan (fetch.observe) menjadi daftar Finding berbukti. Setiap rule hanya
menghasilkan temuan bila terpicu. Bisa diuji tanpa jaringan dengan amatan buatan (lihat tests)."""
import re

import cuplikan as cuplikan_db
import edukasi
import sca
from models import Finding

MISC = "A05:2021 Security Misconfiguration"
CRYPTO = "A02:2021 Cryptographic Failures"
AUTH = "A07:2021 Identification and Authentication Failures"
INTEG = "A08:2021 Software and Data Integrity Failures"
KOMPONEN = "A06:2021 Vulnerable and Outdated Components"

# header keamanan yang diharapkan ada -> (id, tingkat, judul, perbaikan, cwe). HSTS hanya relevan di HTTPS.
SECURITY_HEADERS = [
    ("content-security-policy", "W-H01", "sedang", "Content-Security-Policy tidak ada",
     "Tambahkan CSP yang membatasi sumber skrip; mulai dengan mode Report-Only lalu perketat.", "CWE-693"),
    ("strict-transport-security", "W-A02-02", "sedang", "Strict-Transport-Security (HSTS) tidak ada",
     "Tambahkan header HSTS agar browser selalu memakai HTTPS untuk domain ini.", "CWE-319"),
    ("x-content-type-options", "W-H05", "rendah", "X-Content-Type-Options tidak ada",
     "Set 'X-Content-Type-Options: nosniff' agar browser tidak menebak tipe konten.", "CWE-16"),
    ("referrer-policy", "W-H06", "rendah", "Referrer-Policy tidak ada",
     "Set Referrer-Policy (mis. strict-origin-when-cross-origin) agar URL tidak bocor ke situs lain.", "CWE-200"),
    ("permissions-policy", "W-H07", "info", "Permissions-Policy tidak ada",
     "Batasi fitur browser (kamera, mikrofon, lokasi) lewat Permissions-Policy bila tidak dipakai.", "CWE-16"),
]


def _csp_script_src(csp):
    """Token efektif untuk skrip pada CSP: script-src bila ada, selain itu default-src; None bila tak ada."""
    d = {}
    for part in csp.split(";"):
        bits = part.split()
        if bits:
            d[bits[0].lower()] = [t.lower() for t in bits[1:]]
    return d.get("script-src", d.get("default-src"))


def evaluate(obs):
    """obs = fetch.observe(...) -> list[Finding]. Amatan gagal (tanpa status) -> tidak ada temuan;
    galatnya dibawa di obs['errors'] dan ditampilkan oleh pemanggil."""
    if not obs.get("status"):
        return []
    h = obs.get("headers", {})
    https = obs.get("https", False)
    lok = obs.get("final_url", obs.get("target", ""))
    found = []

    def hit(id, kategori, judul, tingkat, perbaikan, bukti, cwe="", dampak="", ref=(), keyakinan="tinggi"):
        found.append(Finding(id, kategori, judul, tingkat, perbaikan, list(bukti), lok, cwe, keyakinan, dampak, list(ref)))

    # --- transport / TLS ---
    if not https:
        hit("W-A02-01", CRYPTO, "Situs dilayani lewat HTTP tanpa enkripsi", "tinggi",
            "Paksa HTTPS: alihkan semua HTTP ke HTTPS dan pasang sertifikat yang valid.",
            [f"Respons akhir tetap di {lok}"], "CWE-319",
            "Data (termasuk kredensial & sesi) bisa disadap di jaringan.")
    else:
        tls = obs.get("tls", {})
        if tls.get("expired") or "expired" in str(tls.get("error", "")).lower():
            hit("W-A02-03", CRYPTO, "Sertifikat TLS kedaluwarsa", "tinggi",
                "Perbarui sertifikat TLS dan otomatiskan pembaruannya (mis. ACME/Let's Encrypt).",
                [tls.get("error") or f"Kedaluwarsa {tls.get('expires')}"], "CWE-295")
        elif isinstance(tls.get("days_left"), int) and tls["days_left"] < 15:
            hit("W-A02-04", CRYPTO, f"Sertifikat TLS segera kedaluwarsa ({tls['days_left']} hari)", "sedang",
                "Perbarui sertifikat sebelum kedaluwarsa; otomatiskan agar tidak terlewat.",
                [f"Berlaku s.d. {tls.get('expires')}"], "CWE-295")

    # --- header keamanan ---
    for header, id, tingkat, judul, perbaikan, cwe in SECURITY_HEADERS:
        if header == "strict-transport-security" and not https:
            continue  # HSTS tidak berarti pada HTTP
        if header not in h:
            hit(id, MISC if cwe != "CWE-319" else CRYPTO, judul, tingkat, perbaikan,
                [f"Respons {obs['status']} tanpa header '{header}'"], cwe)

    # --- clickjacking ---
    csp = h.get("content-security-policy", "")
    if "x-frame-options" not in h and "frame-ancestors" not in csp:
        hit("W-H04", MISC, "Tidak ada proteksi clickjacking", "sedang",
            "Set 'X-Frame-Options: DENY' atau 'frame-ancestors' di CSP.",
            ["Tanpa X-Frame-Options maupun frame-ancestors di CSP"], "CWE-1021",
            "Halaman bisa di-iframe untuk menipu klik pengguna (clickjacking).")

    # --- CSP ada tapi longgar pada sumber skrip ---
    if csp:
        src = _csp_script_src(csp)
        if src is not None:
            lemah = []
            if "*" in src:
                lemah.append("'*' (semua origin)")
            if "'unsafe-eval'" in src:
                lemah.append("'unsafe-eval'")
            if "'unsafe-inline'" in src and not any(
                    t.startswith(("'nonce-", "'sha256-", "'sha384-", "'sha512-")) for t in src):
                lemah.append("'unsafe-inline' tanpa nonce/hash")
            if lemah:
                hit("W-H01-02", MISC, "Content-Security-Policy lemah pada sumber skrip", "sedang",
                    "Hapus '*'/'unsafe-inline'/'unsafe-eval' dari script-src; pakai nonce atau hash per-skrip.",
                    [f"script-src: {', '.join(lemah)}"], "CWE-693",
                    "CSP longgar tak menahan skrip tersuntik, jadi perlindungannya semu.",
                    keyakinan="tinggi" if "*" in src else "sedang")

    # --- HSTS ada tapi lemah (max-age pendek / tanpa includeSubDomains) ---
    hsts = h.get("strict-transport-security", "")
    if https and hsts:
        low = hsts.lower()
        m = re.search(r"max-age\s*=\s*(\d+)", low)
        umur = int(m.group(1)) if m else 0
        lemah = []
        if umur < 15552000:  # < ~180 hari
            lemah.append(f"max-age={umur}" if m else "tanpa max-age")
        if "includesubdomains" not in low:
            lemah.append("tanpa includeSubDomains")
        if lemah:
            hit("W-A02-05", CRYPTO, "Strict-Transport-Security (HSTS) lemah", "rendah",
                "Perpanjang max-age (min. 180 hari, disarankan 1 tahun) dan tambahkan includeSubDomains.",
                [f"{hsts[:120]} — {', '.join(lemah)}"], "CWE-319", keyakinan="sedang")

    # --- flag cookie ---
    for c in obs.get("set_cookies", []):
        nama = c.split("=", 1)[0].strip()
        low = c.lower()
        kurang = [flag for flag, tok in (("Secure", "secure"), ("HttpOnly", "httponly"), ("SameSite", "samesite"))
                  if tok not in low and not (flag == "Secure" and not https)]
        if kurang:
            hit("W-A07-01", AUTH, f"Cookie '{nama}' tanpa {', '.join(kurang)}", "sedang",
                "Set HttpOnly (tak terbaca JS), Secure (hanya HTTPS), dan SameSite pada cookie sesi.",
                [c[:120]], "CWE-614",
                "Cookie sesi tanpa flag ini lebih mudah dicuri (XSS) atau disalahgunakan lintas situs.")
        if "samesite=none" in low and "secure" not in low:
            hit("W-A07-02", AUTH, f"Cookie '{nama}': SameSite=None tanpa Secure", "sedang",
                "SameSite=None wajib disertai Secure; tanpa Secure cookie ditolak browser modern dan rawan bocor.",
                [c[:120]], "CWE-614",
                "Cookie lintas-situs tanpa Secure bisa terkirim lewat koneksi tak terenkripsi lalu dicuri.")

    # --- CORS longgar ---
    if h.get("access-control-allow-origin") == "*" and h.get("access-control-allow-credentials", "").lower() == "true":
        hit("W-H02", MISC, "CORS mengizinkan semua origin bersama kredensial", "tinggi",
            "Jangan gabungkan 'Access-Control-Allow-Origin: *' dengan kredensial; pakai allowlist origin.",
            ["Access-Control-Allow-Origin: * + Access-Control-Allow-Credentials: true"], "CWE-942",
            "Situs lain bisa membaca respons berkredensial atas nama pengguna.")

    # --- kebocoran versi perangkat lunak ---
    for hdr, label in (("server", "Server"), ("x-powered-by", "X-Powered-By")):
        v = h.get(hdr, "")
        if v and any(ch.isdigit() for ch in v):
            hit("W-H09", MISC, f"Versi perangkat lunak terungkap di header {label}", "rendah",
                f"Sembunyikan/minimalkan header {label} agar versi tepat tidak terekspos.",
                [f"{label}: {v}"], "CWE-200")

    # --- komponen klien usang & rentan (SCA pasif offline, OWASP A06) ---
    for k in sca.periksa(obs.get("skrip", [])):
        cve = ", ".join(k["cve"]) or "lihat referensi"
        hit("W-A06-01", KOMPONEN, f"Pustaka usang & rentan: {k['nama']} {k['versi']}", "sedang",
            k["perbaikan"], [f"{k['url']} ({cve})"], "CWE-1104",
            f"Versi {k['nama']} ini punya kerentanan yang sudah diketahui ({cve}); bisa dieksploitasi di browser pengunjung.",
            k["referensi"], keyakinan="sedang")

    # --- subresource pihak ketiga tanpa SRI (integritas rantai pasok) ---
    subs = obs.get("subresources", [])
    if subs:
        hit("W-A08-01", INTEG, f"{len(subs)} subresource pihak ketiga tanpa Subresource Integrity (SRI)",
            "rendah",
            "Tambahkan atribut integrity= (plus crossorigin) pada tiap tag, atau self-host aset tepercaya.",
            [s["url"] for s in subs][:10], "CWE-353",
            "Bila CDN/host pihak ketiga dibajak, skrip/stylesheet jahat termuat di browser pengguna tanpa terdeteksi.")

    # --- berkas sensitif terekspos ---
    for e in obs.get("exposed", []):
        kritis = e["path"].startswith(("/.git", "/.env"))
        hit("W-H03", MISC, f"Berkas sensitif terekspos: {e['path']}", "kritis" if kritis else "tinggi",
            "Hapus berkas dari web root atau blokir aksesnya di server; putar rahasia bila sempat bocor.",
            [f"GET {e['path']} -> 200 dengan isi cocok"], "CWE-538",
            "Berkas ini bisa membocorkan kode sumber, kredensial, atau konfigurasi internal.")

    # --- redirect keluar lingkup ---
    if obs.get("offscope_redirect"):
        hit("W-H08", MISC, "Redirect keluar dari host target", "rendah",
            "Pastikan tujuan redirect divalidasi (allowlist) agar tidak jadi open redirect.",
            [obs["offscope_redirect"]], "CWE-601")

    for f in found:  # lampirkan cuplikan (#7) + kartu edukasi "Pelajari dulu" (#8) per id
        f.cuplikan = cuplikan_db.CUPLIKAN.get(f.id, {})
        f.edukasi = edukasi.EDUKASI.get(f.id, {})
    return found
