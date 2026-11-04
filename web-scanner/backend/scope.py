"""Gerbang otorisasi & penguncian lingkup.

Memindai web tanpa izin melanggar hukum (di Indonesia: UU ITE) dan etika. Alat ini HANYA untuk aset
milik sendiri atau yang Anda punya izin menguji. Dua penjaga: (1) otorisasi harus dikonfirmasi
eksplisit sebelum apa pun diambil, (2) hanya host target yang disentuh — redirect/aset ke host lain
diabaikan dan dicatat, tidak diikuti.

Catatan SSRF: untuk pemakaian CLI oleh pemilik, target boleh localhost/host privat (justru kasus
utama: menguji aplikasi sendiri). Bila modul ini kelak diekspos sebagai layanan publik, tambahkan
allowlist egress / blokir rentang internal di lapisan layanan, bukan di sini.
"""
from urllib.parse import urlsplit


class OutOfScope(ValueError):
    pass


def authorize(target, authorized):
    """-> (base_url, host). Menolak bila otorisasi tak dikonfirmasi atau URL tak sah."""
    if not authorized:
        raise OutOfScope(
            "otorisasi tidak dikonfirmasi. Jalankan hanya terhadap web yang Anda miliki atau "
            "diizinkan menguji (mis. --authorized pada CLI).")
    u = urlsplit(target if "://" in target else "https://" + target)
    if u.scheme not in ("http", "https") or not u.hostname:
        raise OutOfScope(f"target tidak sah: {target!r}")
    return f"{u.scheme}://{u.netloc}", u.hostname


def in_scope(url, host):
    """True bila URL masih pada host yang sama. Lingkup dikunci ke host: skema/port boleh beda
    (http->https saat redirect itu wajar), host lain tidak."""
    try:
        return (urlsplit(url).hostname or "") == host
    except ValueError:
        return False
