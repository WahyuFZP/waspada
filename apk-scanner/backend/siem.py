"""Jembatan opsional temuan pemeriksa APK -> SIEM WASPADA (#16).

Opt-in: aktif hanya bila env SIEM_INGEST_URL diatur (mis. http://127.0.0.1:8000/ingest).
Satu arah dan fail-safe: SIEM mati/lambat tidak boleh menggagalkan analisis. Hanya APK
level Tinggi (Berbahaya) / Sedang (Mencurigakan) yang dibridge; level Rendah diam agar
SIEM tetap bersih. Tidak mengirim ke mana pun selain SIEM_INGEST_URL.
"""
import logging
import os

import httpx

_SEV = {"Tinggi": "critical", "Sedang": "high"}  # Rendah tidak dibridge
_DASH = os.environ.get("WASPADA_DASHBOARD_URL", "http://localhost:3000").rstrip("/")
log = logging.getLogger("waspada.siem")


def kirim(laporan):
    """Kirim ringkasan satu analisis APK ke SIEM bila diaktifkan. Tidak pernah melempar (fail-safe)."""
    url = os.environ.get("SIEM_INGEST_URL")
    sev = _SEV.get(laporan["level_risiko"])
    if not url or not sev:
        return
    try:
        pkg = laporan["aplikasi"]["package"]
        event = {
            "kind": "scanner", "scanner": "apk",
            "timestamp": laporan["scanned_at"],
            "host": pkg,
            "severity": sev,
            "title": f"Pemeriksa APK: {laporan['analisa_akhir']['status']} — {pkg}",
            "url": f"{_DASH}/apk/{laporan['scan_id']}",
            "temuan": [{"judul": t["judul"], "tingkat": t["tingkat"]} for t in laporan["temuan"][:8]],
            "saran": laporan["analisa_akhir"]["saran"],
        }
        token = os.environ.get("INGEST_TOKEN")  # wajib dikirim bila SIEM memasang INGEST_TOKEN, kalau tidak ditolak 401
        httpx.post(url, json=event, headers={"X-Ingest-Token": token} if token else {}, timeout=5).raise_for_status()
    except Exception as exc:  # SIEM mati/lambat/menolak: catat saja, jangan ganggu hasil analisis
        log.warning("Gagal mengirim ke SIEM (%s): %s", url, type(exc).__name__)
