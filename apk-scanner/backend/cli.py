"""Jalankan pipeline analisis dari terminal: python cli.py app.apk [app2.apk ...] [--fail-on ...] [--sarif ...] [--baseline ...]

Mencetak satu baris VERDICT= (clean|suspicious|malicious <- Rendah|Sedang|Tinggi) per APK, dipakai run_scan.py
korpus fixture. Flag gerbang CI (#9) opsional: menilai temuan gabungan semua APK lalu menentukan exit-code.
APKiD yang tidak terpasang dicatat oleh packer, tidak menggagalkan.
"""
import argparse
import json
import sys
from dataclasses import asdict

import ci
import packer
import parser as apk_parser
import rules
import scoring

VERDICT = {"Rendah": "clean", "Sedang": "suspicious", "Tinggi": "malicious"}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pemeriksa APK dari terminal (+ gerbang CI opsional).")
    ap.add_argument("paths", nargs="+", help="berkas .apk")
    ap.add_argument("--fail-on", choices=["rendah", "sedang", "tinggi"],
                    help="exit non-nol bila ada temuan >= tingkat ini (gerbang CI)")
    ap.add_argument("--sarif", metavar="FILE", help="tulis temuan sebagai SARIF 2.1.0 ke FILE")
    ap.add_argument("--baseline", metavar="FILE", help="laporan JSON acuan; gerbang hanya pada temuan BARU")
    a = ap.parse_args(argv)

    pasangan = []  # (nama_apk, temuan_dict) untuk SARIF & gerbang gabungan
    for path in a.paths:
        parsed = apk_parser.parse(path)
        findings = rules.evaluate(parsed, packer.scan(path))
        skor, level = scoring.score(findings)
        temuan = ", ".join(f"{f.rule_id}({f.bobot})" for f in findings) or "-"
        nama = path.rsplit("/", 1)[-1]
        print(f"VERDICT={VERDICT[level]} skor={skor} level={level}  {nama}  [{temuan}]")
        pasangan += [(nama, asdict(f)) for f in findings]

    if a.sarif:
        with open(a.sarif, "w", encoding="utf-8") as fh:
            json.dump(ci.sarif(pasangan), fh, ensure_ascii=False, indent=2)
    dinilai = [f for _, f in pasangan]
    if a.baseline:
        with open(a.baseline, encoding="utf-8") as fh:
            dinilai = ci.temuan_baru(dinilai, json.load(fh))
    kode = ci.exit_code(dinilai, a.fail_on)
    if a.fail_on:
        print(f"GERBANG CI (--fail-on {a.fail_on}): {len(dinilai)} temuan dinilai -> exit {kode}")
    return kode


if __name__ == "__main__":
    sys.exit(main())
