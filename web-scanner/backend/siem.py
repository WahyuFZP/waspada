"""Jembatan opsional temuan pemeriksa web -> SIEM WASPADA (#16).

Opt-in: aktif hanya bila env SIEM_INGEST_URL diatur (mis. http://127.0.0.1:8000/ingest).
Satu arah dan fail-safe: SIEM mati/lambat tidak boleh menggagalkan pemindaian. Hanya
scan yang tingkat tertingginya layak-alert (kritis/tinggi) yang dibridge; sisanya diam
agar SIEM tetap bersih. Tidak mengirim ke mana pun selain SIEM_INGEST_URL.
"""
import logging
import os
from urllib.parse import urlsplit

import httpx

_SEV = {"kritis": "critical", "tinggi": "high"}  # band bawah tidak dibridge
_DASH = os.environ.get("WASPADA_DASHBOARD_URL", "http://localhost:3000").rstrip("/")
log = logging.getLogger("waspada.siem")


def kirim(laporan):
    """Kirim ringkasan satu pemindaian ke SIEM bila diaktifkan. Tidak pernah melempar (fail-safe)."""
    url = os.environ.get("SIEM_INGEST_URL")
    sev = _SEV.get(laporan["ringkasan"]["tertinggi"])
    if not url or not sev:
        return
    try:
        host = urlsplit(laporan["target"]).hostname or laporan["target"]
        event = {
            "kind": "scanner", "scanner": "web",
            "timestamp": laporan["scanned_at"],
            "host": host,
            "severity": sev,
            "title": f"Pemeriksa Web: postur {laporan['ringkasan']['postur']} di {host}",
            "url": f"{_DASH}/web/{laporan['scan_id']}",
            "temuan": [{"judul": t["judul"], "tingkat": t["tingkat"]} for t in laporan["temuan"][:8]],
            "saran": laporan["analisa_akhir"]["saran"],
        }
        httpx.post(url, json=event, timeout=5).raise_for_status()
    except Exception as exc:  # SIEM mati/lambat/menolak: catat saja, jangan ganggu hasil scan
        log.warning("Gagal mengirim ke SIEM (%s): %s", url, type(exc).__name__)
