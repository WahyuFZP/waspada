"""Susun laporan JSON sesuai schema PRD v1.2 §9."""
import uuid
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

import kepatuhan
import redaksi

WIB = timezone(timedelta(hours=7))
CATATAN = "Hasil ini adalah indikasi static-analysis untuk ditinjau manusia, bukan vonis malware final."


def _temuan(f):
    d = asdict(f)
    d["bukti"] = [redaksi.redaksi(b) for b in d["bukti"]]  # samarkan rahasia di bukti sebelum disimpan (#11)
    return d


def build(filename, size, parsed, packer, findings, skor, level, akhir):
    return {
        "schema_version": "1.2",
        "scan_id": str(uuid.uuid4()),
        "scanned_at": datetime.now(WIB).isoformat(timespec="seconds"),
        "file": {"nama": filename, "ukuran_bytes": size, "sha256": parsed["sha256"]},
        "aplikasi": {k: parsed[k] for k in ("package", "version_name", "version_code", "min_sdk", "target_sdk")},
        "permission": {"semua": parsed["permissions"], "berbahaya": parsed["dangerous_permissions"]},
        "packer": packer,
        "url_ip": [redaksi.redaksi(x) for x in (parsed["urls"] + [ip for ip in parsed["ips"] if not any(ip in u for u in parsed["urls"])])],
        "temuan": [_temuan(f) for f in findings],
        "skor": skor,
        "level_risiko": level,
        "analisa_akhir": akhir,
        "konteks_kepatuhan": kepatuhan.konteks(akhir["status"], [f.rule_id for f in findings]),
        "tahap_gagal": parsed["galat"],  # bagian yang tidak terperiksa; skor bisa lebih rendah dari seharusnya
        "catatan": CATATAN,
    }
