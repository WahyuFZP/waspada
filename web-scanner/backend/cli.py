"""Pemeriksa keamanan web PASIF untuk aset milik sendiri / berizin.

  python cli.py https://app-saya.example --authorized
  python cli.py http://localhost:3000 --authorized --json

Tanpa --authorized, pemeriksaan ditolak (lihat scope.py). Hanya host target yang disentuh; tidak ada
muatan serangan. Cek aktif (ZAP/Nuclei) adalah tahap lanjut, bukan bagian MVP pasif ini.
"""
import argparse
import json
import sys
from urllib.parse import urlsplit

import ci
import fetch
import final
import report
import rules
import scoring
import siem
import tls
from scope import OutOfScope, authorize


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pemeriksa keamanan web pasif (aset milik sendiri/berizin).")
    ap.add_argument("target", help="URL target, mis. https://app-saya.example")
    ap.add_argument("--authorized", action="store_true",
                    help="konfirmasi Anda memiliki / diizinkan menguji target ini")
    ap.add_argument("--no-exposed", action="store_true", help="lewati pengecekan berkas terekspos")
    ap.add_argument("--delay", type=float, default=0.5, help="jeda antar-permintaan, detik (default 0.5)")
    ap.add_argument("--json", action="store_true", help="cetak laporan JSON lengkap")
    ap.add_argument("--fail-on", choices=["info", "rendah", "sedang", "tinggi", "kritis"],
                    help="exit non-nol bila ada temuan >= tingkat ini (gerbang CI)")
    ap.add_argument("--sarif", metavar="FILE", help="tulis temuan sebagai SARIF 2.1.0 ke FILE")
    ap.add_argument("--baseline", metavar="FILE", help="laporan JSON acuan; gerbang hanya pada temuan BARU")
    ap.add_argument("--operator", help="label operator untuk rekaman otorisasi/audit (opsional)")
    ap.add_argument("--tls", action="store_true",
                    help="probe TLS lanjutan (AKTIF: buka beberapa handshake; hanya aset milik/berizin)")
    a = ap.parse_args(argv)

    try:
        base, host = authorize(a.target, a.authorized)
    except OutOfScope as e:
        sys.exit(f"DITOLAK: {e}")

    obs = fetch.observe(base, host, delay=a.delay, cek_exposed=not a.no_exposed)
    findings = rules.evaluate(obs)
    errors = obs.get("errors", [])
    if a.tls:  # #20 probe TLS AKTIF, opt-in
        temuan_tls, catatan = tls.probe(host, urlsplit(base).port or 443)
        findings += temuan_tls
        if catatan:
            errors.append(catatan)
    nilai = scoring.nilai(findings)
    akhir = final.conclude(findings, nilai)
    rep = report.build(base, findings, nilai, akhir, errors, a.operator)
    siem.kirim(rep)  # #16 jembatan ke SIEM (opt-in via SIEM_INGEST_URL, fail-safe)

    if a.sarif:
        with open(a.sarif, "w", encoding="utf-8") as fh:
            json.dump(ci.sarif(rep), fh, ensure_ascii=False, indent=2)
    digerbang = rep["temuan"]
    if a.baseline:
        with open(a.baseline, encoding="utf-8") as fh:
            digerbang = ci.temuan_baru(rep, json.load(fh))
    kode = ci.exit_code(digerbang, a.fail_on)

    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return kode

    print(f"Target : {base}")
    print(f"Postur : {nilai['postur']}  (tertinggi: {nilai['tertinggi']}, jumlah: {nilai['jumlah']})")
    for f in sorted(findings, key=lambda f: scoring.PERINGKAT[f.tingkat], reverse=True):
        print(f"  [{f.tingkat:7}] {f.id:9} {f.judul}")
        for b in f.bukti:
            print(f"              - {b}")
    if obs.get("errors"):
        print("  tahap gagal:", obs["errors"])
    print(f"\n  Analisa Akhir: {akhir['status']}")
    for s in akhir["saran"]:
        print(f"    -> {s}")
    if a.fail_on:
        print(f"\n  GERBANG CI (--fail-on {a.fail_on}): {len(digerbang)} temuan dinilai -> exit {kode}")
    return kode


if __name__ == "__main__":
    sys.exit(main())
