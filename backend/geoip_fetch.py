"""Unduh database lokasi IP DB-IP Lite (CC BY 4.0, https://db-ip.com) saat build image. Dibaca offline oleh geoip.py."""
import gzip
import sys
import urllib.request
from datetime import date
from pathlib import Path

DIR = Path("/geoip")


def months():
    today = date.today()
    prev = date(today.year - (today.month == 1), (today.month - 2) % 12 + 1, 1)
    return [f"{today:%Y-%m}", f"{prev:%Y-%m}"]  # file bulan ini kadang belum terbit di awal bulan


DIR.mkdir(parents=True, exist_ok=True)
for kind in ("country", "asn"):
    for month in months():
        url = f"https://download.db-ip.com/free/dbip-{kind}-lite-{month}.mmdb.gz"
        try:
            # user-agent bawaan Python-urllib ditolak (403) oleh CDN db-ip.com
            req = urllib.request.Request(url, headers={"User-Agent": "WASPADA-GeoIP/1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                (DIR / f"dbip-{kind}-lite.mmdb").write_bytes(gzip.decompress(resp.read()))
            print("GeoIP diunduh:", url)
            break
        except OSError as exc:
            print("GeoIP gagal:", url, exc, file=sys.stderr)
    else:
        # build tetap berhasil tanpa internet; event keamanan hanya tidak mendapat negara/pemilik jaringan
        print(f"GeoIP {kind} tidak tersedia, pengayaan lokasi dilewati", file=sys.stderr)
