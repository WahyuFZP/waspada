"""Kirim alert ke Discord sebagai embed berwarna sesuai severity."""
import logging
import os

import httpx

COLORS = {"low": 0x3498DB, "medium": 0xF1C40F, "high": 0xE67E22, "critical": 0xE74C3C}


def discord_payload(alert):
    lines = [f"`{e['timestamp']}` **{e['source']}** ({e['region']}) {e['event_type']}: {e['title']}"
             for e in alert["events"]]
    group = ", ".join(f"{k}={v}" for k, v in alert["group"].items())
    return {"embeds": [{
        "title": f"[{alert['severity'].upper()}] {alert['rule']}",
        "description": f"{group}\n\n" + "\n".join(lines)[:3800],  # batas description Discord 4096
        "color": COLORS.get(alert["severity"], 0x95A5A6),
        "timestamp": alert["timestamp"],
        "footer": {"text": "WASPADA OSINT-SIEM"},
    }]}


async def send(alert):
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not url:
        return
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            (await client.post(url, json=discord_payload(alert))).raise_for_status()
    except httpx.HTTPError as exc:  # webhook gagal tidak boleh menghentikan pipeline; alert tetap di DB & dashboard
        logging.warning("Discord webhook gagal: %s", exc)
