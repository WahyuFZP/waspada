"""Probe TLS AKTIF ringkas (#20): deteksi hal yang tak terlihat dari header pasif —
protokol usang (TLS 1.0/1.1), cipher lemah yang diterima, dan tidak adanya PFS.

BERBEDA dari pemeriksaan lain di suite ini: ini AKTIF (membuka beberapa handshake ke host target),
jadi OPT-IN (flag periksa_tls) dan tetap authorization-first. TANPA probe eksploit (tak ada
Heartbleed/ROBOT/CCS dsb.) — hanya menegosiasikan handshake untuk melihat apa yang server terima.
Maksimal ~4 handshake per target. Hanya stdlib `ssl`.
"""
import socket
import ssl

from models import Finding

_USANG = (("TLS 1.0", ssl.TLSVersion.TLSv1), ("TLS 1.1", ssl.TLSVersion.TLSv1_1))
# penanda algoritma yang dianggap lemah/usang pada nama cipher OpenSSL
_LEMAH = ("RC4", "3DES", "DES-CBC", "DES40", "NULL", "EXP", "MD5", "ANON", "ADH", "AECDH", "RC2", "SEED", "IDEA")
_CIPHER_LEMAH = "RC4:3DES:DES:NULL:eNULL:aNULL:EXPORT:MD5:SEED:IDEA:@SECLEVEL=0"  # ditawari khusus utk uji penerimaan


def _tanpa_pfs(nama):
    """TLS 1.2 tanpa pertukaran kunci ephemeral (ECDHE/DHE) = tanpa PFS. (TLS 1.3 selalu PFS — cek di caller.)"""
    u = nama.upper()
    return "ECDHE" not in u and "DHE" not in u


def _lemah(nama, bits):
    """Alasan sebuah cipher dianggap lemah, atau None. Murni (diuji unit)."""
    if bits and bits < 128:
        return f"kekuatan kunci {bits} bit (< 128)"
    hit = [m for m in _LEMAH if m in nama.upper()]
    return ("algoritma usang: " + ", ".join(hit)) if hit else None


def _coba_versi(host, port, ver, timeout):
    """True bila server menyelesaikan handshake yang DIBATASI pada satu versi protokol.
    SECLEVEL=0 agar klien bersedia MENAWARKAN protokol lama (menguji sisi server, bukan menyerang)."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.minimum_version = ctx.maximum_version = ver
    try:
        ctx.set_ciphers("ALL:@SECLEVEL=0")
    except ssl.SSLError:
        pass
    try:
        with socket.create_connection((host, port), timeout) as s, ctx.wrap_socket(s, server_hostname=host):
            return True
    except (OSError, ssl.SSLError):
        return False


def _koneksi(host, port, timeout):
    """Koneksi best-effort: terima protokol & cipher APA PUN (termasuk lama) agar server legacy/lemah —
    yang justru paling perlu dideteksi — tetap terbaca. -> (versi, nama_cipher, bits). Melempar bila tak ada TLS.
    (Jangan pakai create_default_context: ia menolak TLS 1.0/1.1 & cipher lemah, jadi server rentan tampak 'tak ada TLS'.)"""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        ctx.minimum_version = ssl.TLSVersion.TLSv1
    except ValueError:
        pass
    try:
        ctx.set_ciphers("ALL:@SECLEVEL=0")
    except ssl.SSLError:
        pass
    with socket.create_connection((host, port), timeout) as s, ctx.wrap_socket(s, server_hostname=host) as ss:
        return ss.version(), ss.cipher()[0], ss.cipher()[2]


def _cipher_lemah_diterima(host, port, timeout):
    """Nama cipher lemah yang server TERIMA saat hanya cipher lemah ditawarkan, atau None (menolak = baik).
    Dibatasi <=TLS 1.2: set_ciphers tak mengatur suite TLS 1.3 (yang selalu kuat), jadi TLS 1.3 harus dikecualikan
    agar tak salah lapor cipher kuat sebagai lemah."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.maximum_version = ssl.TLSVersion.TLSv1_2
    try:
        ctx.set_ciphers(_CIPHER_LEMAH)
    except ssl.SSLError:
        return None
    try:
        with socket.create_connection((host, port), timeout) as s, ctx.wrap_socket(s, server_hostname=host) as ss:
            nama, bits = ss.cipher()[0], ss.cipher()[2]
            return nama if _lemah(nama, bits) else None  # pastikan yang dinegosiasikan benar-benar lemah
    except (OSError, ssl.SSLError):
        return None


def _f(id_, judul, tingkat, perbaikan, bukti, dampak, cwe, lok):
    return Finding(id=id_, kategori="A02:2021 Cryptographic Failures", judul=judul, tingkat=tingkat,
                   perbaikan=perbaikan, bukti=bukti, lokasi=lok, cwe=cwe, dampak=dampak)


def probe(host, port=443, timeout=6):
    """-> (findings, catatan_gagal). Membuka beberapa handshake AKTIF; bila host tak punya TLS,
    kembalikan [] + catatan (bukan error) agar scan tetap jalan."""
    try:
        versi, nama, bits = _koneksi(host, port, timeout)
    except (OSError, ssl.SSLError) as e:
        return [], f"Probe TLS {host}:{port} dilewati: tak ada layanan TLS yang dapat dihubungi ({type(e).__name__})"

    lok = f"{host}:{port}"
    findings = []

    usang = [n for n, v in _USANG if _coba_versi(host, port, v, timeout)]
    if usang:
        findings.append(_f("W-TLS01", f"Protokol usang masih aktif: {', '.join(usang)}", "tinggi",
                           "Nonaktifkan TLS 1.0 & 1.1 di konfigurasi server; sisakan minimal TLS 1.2.",
                           [f"{lok} menyelesaikan handshake {u}" for u in usang],
                           "Protokol lama (era BEAST/POODLE) di bawah standar PCI-DSS dan browser modern.", "CWE-326", lok))

    lemah_nama = _cipher_lemah_diterima(host, port, timeout)
    if lemah_nama:
        alasan = _lemah(lemah_nama, None) or "tergolong usang"
        findings.append(_f("W-TLS02", "Server menerima cipher lemah", "tinggi",
                           "Batasi daftar cipher ke suite kuat (AEAD, >=128 bit); hapus RC4/3DES/DES/NULL/EXPORT.",
                           [f"{lok} menerima {lemah_nama} ({alasan})"],
                           "Cipher lemah memungkinkan dekripsi atau pemalsuan lalu lintas.", "CWE-327", lok))

    if not versi.startswith("TLSv1.3") and _tanpa_pfs(nama):
        findings.append(_f("W-TLS03", "Tanpa Perfect Forward Secrecy (PFS)", "sedang",
                           "Prioritaskan cipher ECDHE/DHE agar sesi lampau tetap aman bila kunci privat bocor.",
                           [f"{lok}: {versi}, cipher {nama} ({bits} bit)"],
                           "Tanpa PFS, bocornya kunci privat server membuka seluruh lalu lintas yang terekam.", "CWE-310", lok))

    return findings, None
