"""Kirim alert ke Discord (embed berwarna sesuai severity) dan WhatsApp lewat gateway OpenWA. Keduanya opsional."""
import logging
import os
from urllib.parse import quote

import httpx

COLORS = {"low": 0x3498DB, "medium": 0xF1C40F, "high": 0xE67E22, "critical": 0xE74C3C}
# WA hanya untuk yang mendesak: nomor gateway tidak resmi bisa diblokir bila mengirim terlalu sering
WA_SEVERITIES = {"high", "critical"}
WA_ENV = ("OPENWA_URL", "OPENWA_API_KEY", "OPENWA_SESSION", "WA_ALERT_CHAT")


def discord_payload(alert):
    # judul jadi link Discord [judul](url) supaya analis bisa langsung membuka berita aslinya
    # region hanya ada di berita; log keamanan memakai host sebagai konteks
    lines = [f"`{e['timestamp']}` **{e['source']}** ({e.get('region') or e.get('host', '-')}) {e['event_type']}: "
             + (f"[{e['title']}]({e['url']})" if e.get("url") else e["title"])
             for e in alert["events"]]
    group = ", ".join(f"{k}={v}" for k, v in alert["group"].items())
    mitre = ", ".join(f"{t['id']} {t['name']}" for t in alert.get("mitre", []))
    return {"embeds": [{
        "title": f"[{alert['severity'].upper()}] {alert['rule']}",
        "description": (f"{group}\nMITRE ATT&CK: {mitre}" if mitre else group)
                       + "\n\n" + "\n".join(lines)[:3800],  # batas description Discord 4096
        "color": COLORS.get(alert["severity"], 0x95A5A6),
        "timestamp": alert["timestamp"],
        "footer": {"text": "WASPADA OSINT-SIEM"},
    }]}


def wa_text(alert):
    """Ringkasan saja, tanpa log mentah: pesan WA melewati server Meta. Rinciannya dibuka di dashboard."""
    mitre = ", ".join(t["id"] for t in alert.get("mitre", []))
    return "\n".join(filter(None, [
        f"*WASPADA [{alert['severity'].upper()}]* {alert['rule']}",
        ", ".join(f"{k} {v}" for k, v in alert["group"].items()),
        f"MITRE ATT&CK: {mitre}" if mitre else "",
        f"{len(alert['events'])} kejadian, terakhir {alert['timestamp']}",
        f"Tindak lanjut: {os.environ.get('DASHBOARD_URL', 'http://localhost:3000')}/pemantauan",
    ]))


def targets(alert):
    """(nama, url, payload, header) untuk tiap kanal yang aktif menurut env."""
    out = []
    if url := os.environ.get("DISCORD_WEBHOOK_URL"):
        out.append(("Discord", url, discord_payload(alert), {}))
    wa = {k: os.environ.get(k) for k in WA_ENV}
    if all(wa.values()) and alert["severity"] in WA_SEVERITIES:
        url = f"{wa['OPENWA_URL'].rstrip('/')}/api/sessions/{quote(wa['OPENWA_SESSION'], safe='')}/messages/send-text"
        out.append(("WhatsApp", url, {"chatId": wa["WA_ALERT_CHAT"], "text": wa_text(alert)}, {"X-API-Key": wa["OPENWA_API_KEY"]}))
    return out


async def send(alert):
    channels = targets(alert)
    if not channels:
        return
    async with httpx.AsyncClient(timeout=10) as client:
        for name, url, payload, headers in channels:
            try:
                (await client.post(url, json=payload, headers=headers)).raise_for_status()
            except httpx.HTTPError as exc:  # kanal gagal tidak boleh menghentikan pipeline; alert tetap di DB & dashboard
                logging.warning("Notifikasi %s gagal: %s", name, exc)
