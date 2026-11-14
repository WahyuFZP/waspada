"""SCA pasif (OWASP A06): deteksi pustaka JS/CSS klien usang dari URL <script>/<link>, cocokkan ke
basis data kerentanan offline (gaya retire.js, dirawat manual di sca_db.json). TANPA jaringan.

Versi diambil dari NAMA FILE (mis. jquery-3.4.1.min.js); pustaka tanpa versi di nama file dilewati.
Query CVE daring (OSV.dev) untuk versi server dari W-H09 ditunda — lihat docs/web-scanner-concept.md.
"""
import json
import os
import re

# nama pustaka diikuti versi: "jquery-3.4.1", "bootstrap.3.3.7", "angular/1.5.8", "lib@2.0.0"
NAMA_VERSI = r"[.\-_/@]?v?(\d+\.\d+(?:\.\d+)?)"


def _muat_db():
    try:
        with open(os.path.join(os.path.dirname(__file__), "sca_db.json"), encoding="utf-8") as fh:
            return json.load(fh).get("pustaka", {})
    except (OSError, ValueError):
        return {}


DB = _muat_db()


def _tuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", v))


def periksa(urls):
    """-> list[{nama, versi, url, cve, perbaikan, referensi}] untuk pustaka yang versinya masuk
    rentang rentan di DB (sejak <= versi < sampai). Satu pustaka per URL."""
    out = []
    for url in urls:
        low = url.lower()
        for nama, rentang in DB.items():
            m = re.search(re.escape(nama) + NAMA_VERSI, low)
            if not m:
                continue
            vt = _tuple(m.group(1))
            for r in rentang:
                if _tuple(r.get("sejak", "0")) <= vt < _tuple(r["sampai"]):
                    out.append({"nama": nama, "versi": m.group(1), "url": url, "cve": r.get("cve", []),
                                "perbaikan": f"Perbarui {nama} ke versi {r['sampai']} atau lebih baru.",
                                "referensi": r.get("referensi", [])})
                    break
            break  # nama pustaka sudah cocok untuk URL ini
    return out
