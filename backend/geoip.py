"""Negara dan pemilik jaringan (ASN) untuk IP sumber di log keamanan, dari DB-IP Lite (CC BY 4.0).

Database dibaca offline (diunduh saat build image oleh geoip_fetch.py): IP penyerang tidak pernah dikirim ke layanan luar.
"""
import ipaddress
import os
from pathlib import Path

import maxminddb

DIR = Path(os.environ.get("GEOIP_DIR", "/geoip"))
INTERNAL = [ipaddress.ip_network(n) for n in
            ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8", "fc00::/7", "::1/128")]


def _open(name):
    path = DIR / name
    return maxminddb.open_database(str(path)) if path.exists() else None


# None bila build tanpa internet: event tetap diproses, hanya tanpa negara/pemilik jaringan
COUNTRY, ASN = _open("dbip-country-lite.mmdb"), _open("dbip-asn-lite.mmdb")


def lookup(ip):
    """-> {scope: public | internal | reserved, ...}.

    reserved = rentang khusus yang bukan milik siapa pun, mis. 203.0.113.0/24 (dokumentasi, dipakai skenario demo).
    """
    addr = ipaddress.ip_address(ip)
    if any(addr in net for net in INTERNAL):
        return {"scope": "internal"}
    if not addr.is_global:
        return {"scope": "reserved"}
    country = ((COUNTRY.get(ip) or {}).get("country") or {}) if COUNTRY else {}
    owner = (ASN.get(ip) or {}) if ASN else {}
    return {
        "scope": "public",
        "country_code": country.get("iso_code"),
        "country": (country.get("names") or {}).get("en"),
        "asn": owner.get("autonomous_system_number"),
        "org": owner.get("autonomous_system_organization"),
    }
