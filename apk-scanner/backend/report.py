"""Susun laporan JSON sesuai schema PRD v1.1 §9."""
import uuid
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

WIB = timezone(timedelta(hours=7))
CATATAN = "Hasil ini adalah indikasi static-analysis untuk ditinjau manusia, bukan vonis malware final."


def build(filename, size, parsed, packer, findings, skor, level):
    return {
        "schema_version": "1.1",
        "scan_id": str(uuid.uuid4()),
        "scanned_at": datetime.now(WIB).isoformat(timespec="seconds"),
        "file": {"nama": filename, "ukuran_bytes": size, "sha256": parsed["sha256"]},
        "aplikasi": {k: parsed[k] for k in ("package", "version_name", "version_code", "min_sdk", "target_sdk")},
        "permission": {"semua": parsed["permissions"], "berbahaya": parsed["dangerous_permissions"]},
        "packer": packer,
        "url_ip": parsed["urls"] + [ip for ip in parsed["ips"] if not any(ip in u for u in parsed["urls"])],
        "temuan": [asdict(f) for f in findings],
        "skor": skor,
        "level_risiko": level,
        "catatan": CATATAN,
    }
