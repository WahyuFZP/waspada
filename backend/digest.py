"""Ringkasan berita harian ke WhatsApp tim jaga.

Alert korelasi berita jarang terpicu (butuh beberapa berita yang saling terkait), jadi berita penting lain hanya
terlihat di dashboard. Skrip ini mengirim SATU pesan per jadwal berisi berita teratas sejak jadwal sebelumnya:
kuota WhatsApp tetap hemat (2 pesan/hari bawaan) dan tim jaga tetap mendapat gambaran.

  python digest.py --once           # kirim ringkasan 12 jam terakhir sekarang juga
  python digest.py --once --lihat   # tampilkan teksnya saja, tanpa mengirim
  python digest.py --loop           # kirim tiap jam di DIGEST_JAM (bawaan "7,19" WIB)
"""
import argparse
import os
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

import httpx

import notify

WIB = timezone(timedelta(hours=7))
MAKS = 7  # berita per pesan: cukup untuk gambaran, tetap terbaca di layar HP
URUT_KATEGORI = {"news.incident": 0, "news.military": 1, "news.diplomatic": 2, "news.economic": 3}
LABEL_KATEGORI = {"news.incident": "Insiden", "news.military": "Militer", "news.diplomatic": "Diplomatik",
                  "news.economic": "Ekonomi"}


def pilih(events, maks=MAKS):
    """Berita nyata (bukan simulasi), satu per judul, diurutkan: insiden dulu, dalam negeri dulu, terbaru dulu."""
    unik = {}
    for e in events:
        if not e.get("event_type", "").startswith("news.") or e.get("demo"):
            continue
        kunci = " ".join(e.get("title", "").lower().split())  # media yang sama sering memuat ulang judul identik
        if kunci and (kunci not in unik or e["timestamp"] > unik[kunci]["timestamp"]):
            unik[kunci] = e
    berita = sorted(unik.values(), key=lambda e: e["timestamp"], reverse=True)
    berita.sort(key=lambda e: (URUT_KATEGORI.get(e["event_type"], 9), e.get("region") != "domestic"))  # sort stabil
    return berita[:maks], len(berita)


def teks(berita, total, sejak, sampai):
    """Pesan WA. Tanda * dan _ di judul dibuang agar format tebal/miring WhatsApp tidak kacau."""
    bersih = lambda s: s.replace("*", "").replace("_", " ")
    baris = [f"*WASPADA · Ringkasan berita* ({sampai:%d %b, %H.%M} WIB)",
             f"{total} berita sejak {sejak:%d %b %H.%M}. {len(berita)} teratas:", ""]
    for i, e in enumerate(berita, 1):
        wilayah = "Dalam negeri" if e.get("region") == "domestic" else "Luar negeri"
        label = " · ".join(filter(None, [str(e.get("topic", "")).capitalize(), LABEL_KATEGORI.get(e["event_type"]), wilayah]))
        baris += [f"{i}. *{bersih(e['title'])}*", f"   [{label}] {urlsplit(e.get('url') or '').hostname or e.get('source', '')}"]
        if e.get("url"):
            baris.append(f"   {e['url']}")
    baris += ["", f"Selengkapnya: {os.environ.get('DASHBOARD_URL', 'http://localhost:3000')}/pemantauan#arus-berita"]
    return "\n".join(baris)


def jadwal_jam():
    return sorted({int(h) for h in os.environ.get("DIGEST_JAM", "7,19").split(",") if h.strip()})


def slot_berikut(now, jam):
    """Waktu kirim berikutnya (> now) dari daftar jam WIB."""
    for h in jam:
        t = now.replace(hour=h, minute=0, second=0, microsecond=0)
        if t > now:
            return t
    return (now + timedelta(days=1)).replace(hour=jam[0], minute=0, second=0, microsecond=0)


def slot_sebelum(t, jam):
    """Waktu kirim terakhir sebelum t: awal jendela berita untuk pesan di t."""
    for h in reversed(jam):
        s = t.replace(hour=h, minute=0, second=0, microsecond=0)
        if s < t:
            return s
    return (t - timedelta(days=1)).replace(hour=jam[-1], minute=0, second=0, microsecond=0)


def kirim(store, sejak, sampai, lihat=False):
    berita, total = pilih(store.events_since(sejak))
    if not berita:
        print(f"{sampai:%d %b %H.%M}: tidak ada berita baru, tidak ada pesan.")
        return
    pesan = teks(berita, total, sejak.astimezone(WIB), sampai.astimezone(WIB))
    req = notify.wa_request(pesan)
    if lihat or not req:
        print(pesan if lihat else "WhatsApp belum diatur (OPENWA_* / WA_ALERT_CHAT kosong); pesan tidak dikirim.")
        return
    url, payload, header = req
    try:
        httpx.post(url, json=payload, headers=header, timeout=15).raise_for_status()
        print(f"{sampai:%d %b %H.%M}: ringkasan {len(berita)} dari {total} berita terkirim.")
    except httpx.HTTPError as exc:  # gagal kirim: catat saja, coba lagi di jadwal berikutnya
        print(f"Gagal mengirim ringkasan: {type(exc).__name__}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Ringkasan berita harian ke WhatsApp.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--once", action="store_true", help="kirim ringkasan 12 jam terakhir sekarang")
    g.add_argument("--loop", action="store_true", help="kirim tiap jam di DIGEST_JAM (WIB)")
    ap.add_argument("--lihat", action="store_true", help="hanya tampilkan teks, jangan kirim")
    a = ap.parse_args(argv)

    from store import Store  # impor di sini agar logika di atas bisa diuji tanpa database
    store = Store(os.environ.get("DATABASE_URL", "postgresql://waspada:waspada@localhost:5433/waspada"))
    if a.once:
        now = datetime.now(WIB)
        kirim(store, now - timedelta(hours=12), now, a.lihat)
        return
    jam = jadwal_jam()
    while True:
        t = slot_berikut(datetime.now(WIB), jam)
        print(f"ringkasan berikutnya {t:%d %b %H.%M} WIB", flush=True)
        time.sleep(max(0, (t - datetime.now(WIB)).total_seconds()))
        kirim(store, slot_sebelum(t, jam), t, a.lihat)


if __name__ == "__main__":
    main()
