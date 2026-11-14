"""Laporan JSON pemeriksaan web pasif (skema awal web-0.1)."""
import uuid
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

import kepatuhan
import redaksi

WIB = timezone(timedelta(hours=7))
CATATAN = "Pemeriksaan PASIF; indikasi untuk ditinjau & diperbaiki pemilik, bukan vonis keamanan final."


def _temuan(f):
    d = asdict(f)
    d["bukti"] = [redaksi.redaksi(b) for b in d["bukti"]]  # samarkan rahasia di bukti sebelum disimpan (#11)
    return d


def build(target, findings, nilai, akhir, errors, operator=None):
    waktu = datetime.now(WIB).isoformat(timespec="seconds")
    return {
        "schema_version": "web-0.1",
        "scan_id": str(uuid.uuid4()),
        "scanned_at": waktu,
        "target": target,
        "otorisasi": {  # rekaman authorization-first yang bisa DIBUKTIKAN (#13), bukan flag yang dibuang
            "dikonfirmasi": True,
            "pernyataan": "Pemilik mengonfirmasi memiliki atau diizinkan menguji target ini.",
            "target": target,
            "waktu": waktu,
            "operator": operator,
        },
        "temuan": [_temuan(f) for f in findings],
        "ringkasan": nilai,
        "analisa_akhir": akhir,
        "konteks_kepatuhan": kepatuhan.konteks(nilai["tertinggi"], [f.id for f in findings]),
        "tahap_gagal": errors,
        "catatan": CATATAN,
    }
