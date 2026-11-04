"""Tes logika penjadwal (#19): jatuh tempo + deteksi regresi (murni, tanpa scan/DB)."""
from datetime import datetime, timedelta, timezone

import jadwal

WIB = timezone(timedelta(hours=7))
NOW = datetime(2026, 11, 4, 12, 0, tzinfo=WIB)


def _diff(tl, tb, baru=(), hilang=()):
    return {"baru": list(baru), "hilang": list(hilang),
            "delta": {"tertinggi_lama": tl, "tertinggi_baru": tb}}


def test_jatuh_tempo():
    assert jadwal.jatuh_tempo({"last_run": None, "interval_jam": 24}, NOW)  # belum pernah
    baru = (NOW - timedelta(hours=1)).isoformat()
    assert not jadwal.jatuh_tempo({"last_run": baru, "interval_jam": 24}, NOW)  # belum lewat
    lama = (NOW - timedelta(hours=25)).isoformat()
    assert jadwal.jatuh_tempo({"last_run": lama, "interval_jam": 24}, NOW)  # sudah lewat


def test_regresi_postur_memburuk():
    status, detail = jadwal.nilai_regresi(_diff("sedang", "kritis"))
    assert status == "regresi" and "memburuk" in detail


def test_regresi_temuan_serius_baru_meski_postur_sama():
    status, _ = jadwal.nilai_regresi(_diff("tinggi", "tinggi", baru=[{"tingkat": "tinggi", "id": "W-X", "judul": "x"}]))
    assert status == "regresi"


def test_membaik():
    status, _ = jadwal.nilai_regresi(_diff("kritis", "rendah", hilang=[{"tingkat": "kritis", "id": "W-Y", "judul": "y"}]))
    assert status == "membaik"


def test_tetap():
    status, _ = jadwal.nilai_regresi(_diff("sedang", "sedang"))
    assert status == "tetap"


def test_temuan_baru_ringan_bukan_regresi():
    # temuan baru tapi hanya 'rendah' + postur tak berubah -> bukan regresi
    status, _ = jadwal.nilai_regresi(_diff("sedang", "sedang", baru=[{"tingkat": "rendah", "id": "W-Z", "judul": "z"}]))
    assert status == "tetap"
