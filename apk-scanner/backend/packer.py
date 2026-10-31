"""Deteksi packer/obfuscator lewat CLI APKiD (lisensi GPL/komersial: dipanggil sebagai proses terpisah)."""
import json
import subprocess

# Kategori APKiD yang berarti kode sengaja disembunyikan. Kategori lain (compiler, anti_vm, ...) hanya info:
# aplikasi sah pun sering ditandai "r8 without marker (suspicious)" di kategori compiler.
SUSPICIOUS = ("packer", "obfuscator", "protector")


def summarize(apkid_json):
    """Output `apkid -j` -> {terdeteksi, detail, info_lain}."""
    detail, info = [], {}
    for f in apkid_json.get("files", []):
        for category, names in (f.get("matches") or {}).items():
            target = detail if category in SUSPICIOUS else info.setdefault(category, [])
            target.extend(n for n in names if n not in target)
    return {"terdeteksi": bool(detail), "detail": detail, "info_lain": info}


def scan(path):
    try:
        r = subprocess.run(["apkid", "-j", path], capture_output=True, text=True, timeout=60)
        return summarize(json.loads(r.stdout))
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as exc:
        # APKiD gagal tidak boleh menggagalkan scan; dicatat agar analis tahu bagian ini tidak diperiksa
        return {"terdeteksi": False, "detail": [], "info_lain": {}, "galat": f"APKiD tidak berhasil dijalankan: {exc}"}
