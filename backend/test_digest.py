"""Ringkasan berita harian: pemilihan berita, teks pesan, dan jadwal. Murni, tanpa database dan tanpa WhatsApp."""
from datetime import datetime

import digest
from digest import WIB


def berita(judul, et="news.incident", region="foreign", ts="2026-11-15T01:00:00Z", **kw):
    return {"event_type": et, "title": judul, "region": region, "timestamp": ts, "topic": "siber",
            "url": "https://contoh.example/a", "source": "contoh", **kw}


def test_pilih_mengurutkan_dan_membuang_simulasi_dobel_dan_log():
    events = [
        berita("Latihan militer di Natuna", et="news.military", region="domestic"),
        berita("Ransomware lumpuhkan rumah sakit", ts="2026-11-15T02:00:00Z"),
        berita("ransomware  LUMPUHKAN rumah sakit", ts="2026-11-15T03:00:00Z"),  # judul sama dari media lain
        berita("Data instansi bocor", region="domestic"),
        berita("Skenario demo", demo=True),
        {"event_type": "auth.success", "timestamp": "2026-11-15T04:00:00Z", "title": "login"},
    ]
    dipilih, total = digest.pilih(events)
    assert total == 3
    # insiden dalam negeri dulu, lalu insiden luar negeri (versi terbaru dari judul dobel), lalu militer
    assert [e["title"] for e in dipilih] == ["Data instansi bocor", "ransomware  LUMPUHKAN rumah sakit", "Latihan militer di Natuna"]


def test_pilih_dibatasi_maks():
    dipilih, total = digest.pilih([berita(f"Berita {i}") for i in range(12)], maks=7)
    assert len(dipilih) == 7 and total == 12


def test_teks_memuat_judul_label_dan_tautan_tanpa_merusak_format():
    t = digest.teks([berita("Peretas *anonim* serang_bank", region="domestic")], 1,
                    datetime(2026, 11, 15, 7, tzinfo=WIB), datetime(2026, 11, 15, 19, tzinfo=WIB))
    assert "*WASPADA · Ringkasan berita* (15 Nov, 19.00 WIB)" in t
    assert "1. *Peretas anonim serang bank*" in t and "[Siber · Insiden · Dalam negeri] contoh.example" in t
    assert "https://contoh.example/a" in t and "/pemantauan#arus-berita" in t


def test_jadwal_berikut_dan_jendela_sebelumnya():
    jam = [7, 19]
    pagi = datetime(2026, 11, 15, 6, 30, tzinfo=WIB)
    assert digest.slot_berikut(pagi, jam) == datetime(2026, 11, 15, 7, tzinfo=WIB)
    malam = datetime(2026, 11, 15, 20, tzinfo=WIB)
    assert digest.slot_berikut(malam, jam) == datetime(2026, 11, 16, 7, tzinfo=WIB)
    # pesan jam 07.00 merangkum sejak 19.00 kemarin; pesan 19.00 sejak 07.00 hari itu
    assert digest.slot_sebelum(datetime(2026, 11, 16, 7, tzinfo=WIB), jam) == datetime(2026, 11, 15, 19, tzinfo=WIB)
    assert digest.slot_sebelum(datetime(2026, 11, 15, 19, tzinfo=WIB), jam) == datetime(2026, 11, 15, 7, tzinfo=WIB)
